"""Authentication routes."""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedError
from app.core.responses import success_response
from app.db.session import get_db
from app.schemas.auth import LoginData, LoginRequest, UserPublic
from app.services.auth_service import AuthService
from app.services.oidc_service import OidcService
from app.services.tenant_service import TenantService

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)


class OidcStartRequest(BaseModel):
    redirect_uri: str = Field(min_length=1, max_length=2048)
    email_hint: str | None = None


class OidcExchangeRequest(BaseModel):
    code: str = Field(min_length=1, max_length=512)
    state: str | None = None


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)) -> dict:
    data: LoginData = AuthService(db).login(
        email=body.email,
        password=body.password,
    )
    return success_response(data=data.model_dump(mode="json"))


@router.get("/me")
def me(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> dict:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Missing bearer token")

    user = AuthService(db).get_user_from_token(credentials.credentials)
    tenants = TenantService(db)
    tenant_id = getattr(user, "active_tenant_id", None) or tenants.get_default_tenant_id(user.id)
    memberships = tenants.list_for_user(user.id)
    tenant_name = next((t.name for t in memberships if t.id == tenant_id), None)
    public = UserPublic(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        tenant_id=tenant_id,
        tenant_name=tenant_name,
    )
    return success_response(data=public.model_dump(mode="json"))


@router.post("/oidc/start")
def oidc_start(body: OidcStartRequest, db: Session = Depends(get_db)) -> dict:
    start = OidcService(db).start_login(redirect_uri=body.redirect_uri, email_hint=body.email_hint)
    return success_response(
        data={"authorization_url": start.authorization_url, "state": start.state},
    )


@router.get("/oidc/mock/authorize")
def oidc_mock_authorize(
    state: str = Query(...),
    redirect_uri: str = Query(...),
    email: str = Query("demo@example.com"),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    url = OidcService(db).mock_authorize(state=state, redirect_uri=redirect_uri, email=email)
    return RedirectResponse(url=url, status_code=302)


@router.post("/oidc/exchange")
def oidc_exchange(body: OidcExchangeRequest, db: Session = Depends(get_db)) -> dict:
    data = OidcService(db).exchange_code(code=body.code, state=body.state)
    return success_response(data=data.model_dump(mode="json"))
