"""Sprint 5.5 — tenancy helpers and isolation contracts (no DB)."""

from uuid import uuid4

from app.core.security import create_access_token, decode_access_token
from app.services.billing import NoopBillingProvider, get_billing_provider
from app.services.tenant_service import TenantService
from app.models.project import Project


def test_jwt_includes_tenant_claim():
    tid = uuid4()
    token = create_access_token(user_id=uuid4(), email="a@b.com", tenant_id=tid)
    payload = decode_access_token(token)
    assert payload["tid"] == str(tid)


def test_project_visible_helper_isolates_tenant():
    user_id = uuid4()
    tenant_a = uuid4()
    tenant_b = uuid4()
    project = Project(
        user_id=user_id,
        tenant_id=tenant_a,
        project_name="A",
        status="draft",
    )
    assert TenantService.project_visible(project, user_id=user_id, tenant_id=tenant_a)
    assert not TenantService.project_visible(project, user_id=user_id, tenant_id=tenant_b)
    assert not TenantService.project_visible(project, user_id=uuid4(), tenant_id=tenant_a)


def test_noop_billing_provider():
    provider = get_billing_provider()
    assert isinstance(provider, NoopBillingProvider)
    provider.report_usage(tenant_id=uuid4(), event_type="retrieval", quantity=1)
