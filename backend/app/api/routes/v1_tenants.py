"""Sprint 5.5 — tenant APIs under /api/v1."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.api.deps import ApproverUser, CurrentUser, DbSession
from app.core.responses import success_response
from app.schemas.tenant import MemberCreateIn
from app.services.tenant_service import TenantService

router = APIRouter(prefix="/tenants", tags=["v1-tenants"])


@router.get("")
def list_my_tenants(current_user: CurrentUser, db: DbSession) -> dict:
    rows = TenantService(db).list_for_user(current_user.id)
    return success_response(data=[r.model_dump(mode="json") for r in rows])


@router.get("/current")
def current_tenant(current_user: CurrentUser, db: DbSession) -> dict:
    svc = TenantService(db)
    tenant_id = getattr(current_user, "active_tenant_id", None) or svc.get_default_tenant_id(
        current_user.id,
    )
    if tenant_id is None:
        return success_response(data=None)
    tenant = svc.get_tenant(tenant_id)
    memberships = svc.list_for_user(current_user.id)
    role = next((m.role for m in memberships if m.id == tenant.id), None)
    return success_response(
        data={
            "id": str(tenant.id),
            "name": tenant.name,
            "slug": tenant.slug,
            "status": tenant.status,
            "role": role,
        },
    )


@router.get("/{tenant_id}/members")
def list_members(tenant_id: UUID, current_user: CurrentUser, db: DbSession) -> dict:
    rows = TenantService(db).list_members(tenant_id, current_user)
    return success_response(data=[r.model_dump(mode="json") for r in rows])


@router.post("/{tenant_id}/members")
def add_member(
    tenant_id: UUID,
    body: MemberCreateIn,
    current_user: ApproverUser,
    db: DbSession,
) -> dict:
    row = TenantService(db).add_member(
        tenant_id,
        current_user,
        email=body.email,
        role=body.role,
    )
    return success_response(data=row.model_dump(mode="json"), status_code=201)
