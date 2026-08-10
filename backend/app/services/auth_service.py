"""Authentication business logic."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.constants.roles import ROLE_APPROVER, normalize_role
from app.core.exceptions import UnauthorizedError
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginData, UserPublic
from app.services.audit_service import AuditService
from app.services.tenant_service import TenantService


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def login(self, *, email: str, password: str) -> LoginData:
        cleaned = email.lower().strip()
        user = self.users.get_by_email(cleaned)
        if user is None or not verify_password(password, user.password_hash):
            try:
                AuditService(self.db).record(
                    project_id=None,
                    user_id=None,
                    action="auth.login.failed",
                    summary="Login failed",
                    metadata={"email": cleaned},
                )
            except Exception:
                pass
            raise UnauthorizedError("Invalid email or password")

        tenants_svc = TenantService(self.db)
        tenants_svc.ensure_demo_tenant(user)
        tenants = tenants_svc.list_for_user(user.id)
        tenant_id = tenants_svc.get_default_tenant_id(user.id)
        tenant_name = next((t.name for t in tenants if t.id == tenant_id), None)

        token = create_access_token(
            user_id=user.id,
            email=user.email,
            tenant_id=tenant_id,
        )
        try:
            AuditService(self.db).record(
                project_id=None,
                user_id=user.id,
                action="auth.login",
                summary="Login succeeded",
                metadata={"email": user.email, "tenant_id": str(tenant_id) if tenant_id else None},
            )
        except Exception:
            pass

        public = UserPublic(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            tenant_id=tenant_id,
            tenant_name=tenant_name,
        )
        return LoginData(
            access_token=token,
            user=public,
            tenant_id=tenant_id,
            tenants=[t.model_dump(mode="json") for t in tenants],
        )

    def get_user_from_token(self, token: str) -> User:
        payload = decode_access_token(token)
        subject = payload.get("sub")
        if not subject:
            raise UnauthorizedError("Invalid token payload")

        try:
            user_id = UUID(subject)
        except ValueError as exc:
            raise UnauthorizedError("Invalid token subject") from exc

        user = self.users.get_by_id(user_id)
        if user is None:
            raise UnauthorizedError("User not found")

        tid_raw = payload.get("tid")
        active_tenant_id: UUID | None = None
        if tid_raw:
            try:
                active_tenant_id = UUID(str(tid_raw))
                TenantService(self.db).require_membership(active_tenant_id, user.id)
            except Exception:
                # Fall back to default rather than hard-failing old tokens mid-sprint
                active_tenant_id = TenantService(self.db).get_default_tenant_id(user.id)
        else:
            active_tenant_id = TenantService(self.db).get_default_tenant_id(user.id)

        # Attach session tenant context for downstream services
        setattr(user, "active_tenant_id", active_tenant_id)
        return user


def ensure_demo_user(db: Session, *, name: str, email: str, password: str) -> User:
    """Create the Sprint 1 demo user if missing; ensure Approver role for local demos."""
    repo = UserRepository(db)
    existing = repo.get_by_email(email.lower().strip())
    if existing is not None:
        if normalize_role(getattr(existing, "role", None)) != ROLE_APPROVER:
            existing.role = ROLE_APPROVER
            db.add(existing)
            db.commit()
            db.refresh(existing)
        TenantService(db).ensure_demo_tenant(existing)
        return existing
    user = repo.create(
        name=name,
        email=email.lower().strip(),
        password_hash=hash_password(password),
        role=ROLE_APPROVER,
    )
    TenantService(db).ensure_demo_tenant(user)
    return user
