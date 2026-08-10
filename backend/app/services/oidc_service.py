"""OIDC adapter with local mock issuer for Phase 5 enterprise identity completion.

Enable with:
  ATLAS_OIDC_ENABLED=true
  ATLAS_OIDC_ISSUER=mock://local   # portable local mock
  # or a real issuer URL + ATLAS_OIDC_CLIENT_ID / ATLAS_OIDC_CLIENT_SECRET
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import UnauthorizedError, ValidationAppError
from app.core.security import create_access_token, hash_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginData, UserPublic
from app.services.tenant_service import TenantService

# In-memory auth codes for mock flow (process-local; fine for Mac demo)
_MOCK_CODES: dict[str, dict[str, Any]] = {}


@dataclass
class OidcStart:
    authorization_url: str
    state: str


class OidcService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    @property
    def enabled(self) -> bool:
        return bool(settings.atlas_oidc_enabled)

    @property
    def is_mock(self) -> bool:
        issuer = (settings.atlas_oidc_issuer or "").strip().lower()
        return issuer.startswith("mock://")

    def start_login(self, *, redirect_uri: str, email_hint: str | None = None) -> OidcStart:
        if not self.enabled:
            raise ValidationAppError("OIDC is disabled")
        state = secrets.token_urlsafe(24)
        if self.is_mock:
            # Point browser/API clients at our mock authorize endpoint
            q = urlencode(
                {
                    "state": state,
                    "redirect_uri": redirect_uri,
                    "email": email_hint or settings.demo_user_email,
                },
            )
            return OidcStart(authorization_url=f"/api/auth/oidc/mock/authorize?{q}", state=state)

        if not settings.atlas_oidc_issuer or not settings.atlas_oidc_client_id:
            raise ValidationAppError("OIDC issuer/client_id not configured")
        # Generic authorize URL shape (real discovery can be added when needed)
        authorize = settings.atlas_oidc_issuer.rstrip("/") + "/authorize"
        q = urlencode(
            {
                "response_type": "code",
                "client_id": settings.atlas_oidc_client_id,
                "redirect_uri": redirect_uri,
                "scope": "openid email profile",
                "state": state,
            },
        )
        return OidcStart(authorization_url=f"{authorize}?{q}", state=state)

    def mock_authorize(self, *, state: str, redirect_uri: str, email: str) -> str:
        if not self.enabled or not self.is_mock:
            raise ValidationAppError("Mock OIDC is not enabled")
        code = secrets.token_urlsafe(16)
        _MOCK_CODES[code] = {"email": email.lower().strip(), "state": state}
        q = urlencode({"code": code, "state": state})
        sep = "&" if "?" in redirect_uri else "?"
        return f"{redirect_uri}{sep}{q}"

    def exchange_code(self, *, code: str, state: str | None = None) -> LoginData:
        if not self.enabled:
            raise ValidationAppError("OIDC is disabled")
        if self.is_mock:
            payload = _MOCK_CODES.pop(code, None)
            if not payload:
                raise UnauthorizedError("Invalid OIDC code")
            if state and payload.get("state") != state:
                raise UnauthorizedError("OIDC state mismatch")
            email = str(payload["email"])
            return self._login_or_provision(email=email, name=email.split("@")[0].title())

        # Real token exchange — requires network + client secret; not used on Mac mock path.
        raise ValidationAppError(
            "Real OIDC token exchange requires ATLAS_OIDC_CLIENT_SECRET and a live issuer; "
            "use ATLAS_OIDC_ISSUER=mock://local for local completion tests.",
        )

    def _login_or_provision(self, *, email: str, name: str) -> LoginData:
        user = self.users.get_by_email(email)
        if user is None:
            # Deterministic local password hash (unused for OIDC sessions)
            seed = hashlib.sha256(f"oidc:{email}".encode()).hexdigest()[:24]
            user = self.users.create(
                name=name or email,
                email=email,
                password_hash=hash_password(seed),
                role="editor",
            )
        tenants = TenantService(self.db)
        tenants.ensure_demo_tenant(user)
        memberships = tenants.list_for_user(user.id)
        tenant_id = tenants.get_default_tenant_id(user.id)
        tenant_name = next((t.name for t in memberships if t.id == tenant_id), None)
        token = create_access_token(user_id=user.id, email=user.email, tenant_id=tenant_id)
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
            tenants=[t.model_dump(mode="json") for t in memberships],
        )
