"""Sprint 5.5 — tenant bootstrap and membership helpers."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationAppError
from app.models.project import Project
from app.models.tenant import Tenant, TenantMembership
from app.models.user import User
from app.schemas.tenant import MemberOut, TenantOut

DEMO_TENANT_ID = UUID("00000000-0000-4000-8000-000000000001")
DEMO_TENANT_SLUG = "atlas-demo"


class TenantService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def ensure_demo_tenant(self, demo_user: User | None = None) -> Tenant:
        tenant = self.db.scalar(select(Tenant).where(Tenant.slug == DEMO_TENANT_SLUG))
        if tenant is None:
            tenant = Tenant(
                id=DEMO_TENANT_ID,
                name="Atlas Demo",
                slug=DEMO_TENANT_SLUG,
                status="active",
            )
            self.db.add(tenant)
            self.db.flush()
        if demo_user is not None:
            self.ensure_membership(tenant.id, demo_user.id, role=demo_user.role or "approver")
            # Backfill legacy projects into demo tenant
            self.db.execute(
                update(Project)
                .where(Project.tenant_id.is_(None), Project.user_id == demo_user.id)
                .values(tenant_id=tenant.id),
            )
        self.db.commit()
        self.db.refresh(tenant)
        return tenant

    def ensure_membership(self, tenant_id: UUID, user_id: UUID, *, role: str = "editor") -> TenantMembership:
        row = self.db.scalar(
            select(TenantMembership).where(
                TenantMembership.tenant_id == tenant_id,
                TenantMembership.user_id == user_id,
            ),
        )
        if row is None:
            row = TenantMembership(tenant_id=tenant_id, user_id=user_id, role=role)
            self.db.add(row)
            self.db.flush()
        return row

    def list_for_user(self, user_id: UUID) -> list[TenantOut]:
        rows = list(
            self.db.execute(
                select(Tenant, TenantMembership.role)
                .join(TenantMembership, TenantMembership.tenant_id == Tenant.id)
                .where(TenantMembership.user_id == user_id, Tenant.status == "active")
                .order_by(Tenant.name.asc()),
            ).all(),
        )
        return [
            TenantOut(id=t.id, name=t.name, slug=t.slug, status=t.status, role=role)
            for t, role in rows
        ]

    def get_default_tenant_id(self, user_id: UUID) -> UUID | None:
        memberships = self.list_for_user(user_id)
        if not memberships:
            return None
        for m in memberships:
            if m.slug == DEMO_TENANT_SLUG:
                return m.id
        return memberships[0].id

    def require_membership(self, tenant_id: UUID, user_id: UUID) -> TenantMembership:
        row = self.db.scalar(
            select(TenantMembership).where(
                TenantMembership.tenant_id == tenant_id,
                TenantMembership.user_id == user_id,
            ),
        )
        if row is None:
            raise ForbiddenError("Not a member of this tenant")
        return row

    def get_tenant(self, tenant_id: UUID) -> Tenant:
        row = self.db.get(Tenant, tenant_id)
        if row is None or row.status != "active":
            raise NotFoundError("Tenant not found")
        return row

    def list_members(self, tenant_id: UUID, actor: User) -> list[MemberOut]:
        self.require_membership(tenant_id, actor.id)
        rows = list(
            self.db.execute(
                select(TenantMembership, User)
                .join(User, User.id == TenantMembership.user_id)
                .where(TenantMembership.tenant_id == tenant_id)
                .order_by(User.email.asc()),
            ).all(),
        )
        return [
            MemberOut(
                user_id=u.id,
                email=u.email,
                name=u.name,
                role=m.role,
                membership_id=m.id,
            )
            for m, u in rows
        ]

    def add_member(self, tenant_id: UUID, actor: User, *, email: str, role: str = "editor") -> MemberOut:
        self.require_membership(tenant_id, actor.id)
        if (actor.role or "").lower() != "approver" and getattr(actor, "tenant_role", None) != "approver":
            # Tenant admins: require global approver OR membership role approver
            membership = self.require_membership(tenant_id, actor.id)
            if membership.role != "approver":
                raise ForbiddenError("Approver role required to add members")
        user = self.db.scalar(select(User).where(User.email == email.lower().strip()))
        if user is None:
            raise ValidationAppError("User not found — create the user before inviting")
        membership = self.ensure_membership(tenant_id, user.id, role=role)
        self.db.commit()
        return MemberOut(
            user_id=user.id,
            email=user.email,
            name=user.name,
            role=membership.role,
            membership_id=membership.id,
        )

    @staticmethod
    def project_visible(project: Project, *, user_id: UUID, tenant_id: UUID | None) -> bool:
        if project.user_id != user_id:
            return False
        if tenant_id is None:
            return True
        return project.tenant_id is None or project.tenant_id == tenant_id
