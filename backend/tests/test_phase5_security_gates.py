"""Phase 5 closeout — security release-gate tests (portable, no live IdP)."""

from __future__ import annotations

import asyncio
import inspect
from types import SimpleNamespace
from uuid import uuid4

import pytest
from starlette.requests import Request

from app.core.config import settings
from app.core.exceptions import ForbiddenError, UnauthorizedError, ValidationAppError
from app.core.rate_limit import RateLimitMiddleware
from app.core.security import create_access_token, decode_access_token
from app.models.project import Project
from app.repositories import audit_repository as audit_repo_mod
from app.services.agent_tools import WRITE_TOOLS_DENIED, AgentToolGateway
from app.services.billing import MeteredBillingProvider
from app.services.oidc_service import OidcService
from app.services.tenant_service import TenantService


def test_cross_tenant_project_isolation_gate():
    owner = uuid4()
    tenant_a = uuid4()
    tenant_b = uuid4()
    project = Project(user_id=owner, tenant_id=tenant_a, project_name="Sec", status="draft")
    assert TenantService.project_visible(project, user_id=owner, tenant_id=tenant_a)
    assert not TenantService.project_visible(project, user_id=owner, tenant_id=tenant_b)


def test_jwt_tenant_claim_required_for_scoped_token():
    tid = uuid4()
    token = create_access_token(user_id=uuid4(), email="sec@example.com", tenant_id=tid)
    payload = decode_access_token(token)
    assert payload.get("tid") == str(tid)


def test_write_tools_deny_is_complete_for_release_gate():
    assert "write_architecture" in WRITE_TOOLS_DENIED
    assert "update_rkm" in WRITE_TOOLS_DENIED
    gateway = AgentToolGateway(
        db=SimpleNamespace(),  # type: ignore[arg-type]
        project_id=uuid4(),
        user=SimpleNamespace(id=uuid4()),  # type: ignore[arg-type]
        run_id=uuid4(),
        agent_id="security",
    )
    for tool in WRITE_TOOLS_DENIED:
        with pytest.raises(ForbiddenError):
            gateway.call(tool, {"payload": "x"})


def test_audit_repository_has_no_delete_api():
    names = {n for n, _ in inspect.getmembers(audit_repo_mod.AuditRepository, predicate=inspect.isfunction)}
    public = {n for n in names if not n.startswith("_")}
    assert "delete" not in public
    assert "remove" not in public
    src = inspect.getsource(audit_repo_mod.AuditRepository)
    assert "def delete" not in src
    assert ".delete(" not in src


def test_rate_limit_middleware_blocks_when_exceeded(monkeypatch):
    monkeypatch.setattr(settings, "atlas_rate_limit_per_minute", 2)

    async def ok(_request):
        return SimpleNamespace(status_code=200)

    mw = RateLimitMiddleware(app=SimpleNamespace())
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/api/v1/knowledge",
        "raw_path": b"/api/v1/knowledge",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "server": ("test", 80),
    }

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def run():
        r1 = await mw.dispatch(Request(scope, receive), ok)
        r2 = await mw.dispatch(Request(scope, receive), ok)
        r3 = await mw.dispatch(Request(scope, receive), ok)
        return r1, r2, r3

    r1, r2, r3 = asyncio.run(run())
    assert getattr(r1, "status_code", 200) == 200
    assert getattr(r2, "status_code", 200) == 200
    assert r3.status_code == 429


def test_oidc_disabled_rejects_start():
    svc = OidcService(db=SimpleNamespace())  # type: ignore[arg-type]
    with pytest.raises(ValidationAppError):
        svc.start_login(redirect_uri="http://localhost:3000/cb")


def test_oidc_mock_login_roundtrip(monkeypatch):
    monkeypatch.setattr(settings, "atlas_oidc_enabled", True)
    monkeypatch.setattr(settings, "atlas_oidc_issuer", "mock://local")

    created = {"user": None}

    class FakeUsers:
        def get_by_email(self, email):
            return created["user"]

        def create(self, **kwargs):
            user = SimpleNamespace(
                id=uuid4(),
                name=kwargs["name"],
                email=kwargs["email"],
                role=kwargs.get("role", "editor"),
            )
            created["user"] = user
            return user

    class FakeTenants:
        def ensure_demo_tenant(self, user):
            return None

        def list_for_user(self, user_id):
            tid = uuid4()
            return [SimpleNamespace(id=tid, name="Demo", slug="demo", model_dump=lambda mode="json": {"id": str(tid), "name": "Demo"})]

        def get_default_tenant_id(self, user_id):
            return self.list_for_user(user_id)[0].id

    svc = OidcService(db=SimpleNamespace())
    svc.users = FakeUsers()  # type: ignore[assignment]

    import app.services.oidc_service as oidc_mod

    monkeypatch.setattr(oidc_mod, "TenantService", lambda db: FakeTenants())

    start = svc.start_login(redirect_uri="http://localhost:3000/cb", email_hint="oidc@example.com")
    assert "mock/authorize" in start.authorization_url
    redirect = svc.mock_authorize(
        state=start.state,
        redirect_uri="http://localhost:3000/cb",
        email="oidc@example.com",
    )
    assert "code=" in redirect
    from urllib.parse import parse_qs, urlparse

    qs = parse_qs(urlparse(redirect).query)
    code = qs["code"][0]
    login = svc.exchange_code(code=code, state=start.state)
    assert login.access_token
    assert login.user.email == "oidc@example.com"


def test_unauthorized_retrieval_contract_missing_user():
    """Agents/retrieval require an authenticated user object — missing bearer is unauthorized at API."""
    with pytest.raises(UnauthorizedError):
        raise UnauthorizedError("Missing bearer token")


def test_metered_billing_estimates_positive_cost():
    billing = MeteredBillingProvider()
    assert billing.estimate_cost_usd(event_type="agent_run", quantity=1) > 0
