"""Phase 2 Stage F — audit log APIs under /api/v1."""

from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.core.responses import success_response
from app.services.audit_service import AuditService

router = APIRouter(prefix="/projects", tags=["v1-audit"])


@router.get("/{project_id}/audit-logs")
def list_audit_logs(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
    limit: int = Query(default=100, ge=1, le=500),
) -> dict:
    rows = AuditService(db).list_for_project(project_id, current_user.id, limit=limit)
    return success_response(
        data=[row.model_dump(mode="json", by_alias=True) for row in rows],
    )
