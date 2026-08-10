"""Sprint 5.4 — collaboration, audit-events, and usage APIs under /api/v1."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import ApproverUser, CurrentUser, DbSession, EditorUser
from app.constants.permissions import PERM_AUDIT_VIEW, PERM_USAGE_VIEW, has_permission
from app.core.exceptions import ForbiddenError
from app.core.responses import success_response
from app.schemas.collaboration import (
    ApprovalRequestCreate,
    ApprovalRequestResolve,
    CommentCreate,
    ReviewRequestComplete,
    ReviewRequestCreate,
)
from app.services.audit_service import AuditService
from app.services.collaboration_service import CollaborationService
from app.services.usage_service import UsageService

router = APIRouter(tags=["v1-collaboration"])


@router.get("/projects/{project_id}/comments")
def list_comments(project_id: UUID, current_user: CurrentUser, db: DbSession) -> dict:
    rows = CollaborationService(db).list_comments(project_id, current_user.id)
    return success_response(data=[r.model_dump(mode="json") for r in rows])


@router.post("/projects/{project_id}/comments")
def create_comment(
    project_id: UUID,
    body: CommentCreate,
    current_user: EditorUser,
    db: DbSession,
) -> dict:
    row = CollaborationService(db).add_comment(project_id, current_user, body)
    return success_response(data=row.model_dump(mode="json"), status_code=201)


@router.get("/projects/{project_id}/review-requests")
def list_review_requests(project_id: UUID, current_user: CurrentUser, db: DbSession) -> dict:
    rows = CollaborationService(db).list_review_requests(project_id, current_user.id)
    return success_response(data=[r.model_dump(mode="json") for r in rows])


@router.post("/projects/{project_id}/review-requests")
def create_review_request(
    project_id: UUID,
    body: ReviewRequestCreate,
    current_user: EditorUser,
    db: DbSession,
) -> dict:
    row = CollaborationService(db).create_review_request(project_id, current_user, body)
    return success_response(data=row.model_dump(mode="json"), status_code=201)


@router.post("/review-requests/{request_id}/complete")
def complete_review_request(
    request_id: UUID,
    body: ReviewRequestComplete,
    current_user: EditorUser,
    db: DbSession,
) -> dict:
    row = CollaborationService(db).complete_review_request(request_id, current_user, body)
    return success_response(data=row.model_dump(mode="json"))


@router.get("/projects/{project_id}/approval-requests")
def list_approval_requests(project_id: UUID, current_user: CurrentUser, db: DbSession) -> dict:
    rows = CollaborationService(db).list_approval_requests(project_id, current_user.id)
    return success_response(data=[r.model_dump(mode="json") for r in rows])


@router.post("/projects/{project_id}/approval-requests")
def create_approval_request(
    project_id: UUID,
    body: ApprovalRequestCreate,
    current_user: EditorUser,
    db: DbSession,
) -> dict:
    row = CollaborationService(db).create_approval_request(project_id, current_user, body)
    return success_response(data=row.model_dump(mode="json"), status_code=201)


@router.post("/approval-requests/{request_id}/resolve")
def resolve_approval_request(
    request_id: UUID,
    body: ApprovalRequestResolve,
    current_user: ApproverUser,
    db: DbSession,
) -> dict:
    row = CollaborationService(db).resolve_approval_request(request_id, current_user, body)
    return success_response(data=row.model_dump(mode="json"))


@router.get("/projects/{project_id}/activity")
def project_activity(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
    limit: int = Query(default=50, ge=1, le=200),
) -> dict:
    rows = CollaborationService(db).activity(project_id, current_user.id, limit=limit)
    return success_response(data=[r.model_dump(mode="json") for r in rows])


@router.get("/audit-events")
def list_audit_events(
    current_user: ApproverUser,
    db: DbSession,
    project_id: UUID | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict:
    if not has_permission(current_user.role, PERM_AUDIT_VIEW):
        raise ForbiddenError("Permission denied: audit.view")
    rows = AuditService(db).list_events(project_id=project_id, limit=limit)
    return success_response(data=[r.model_dump(mode="json", by_alias=True) for r in rows])


@router.get("/usage")
def list_usage(
    current_user: ApproverUser,
    db: DbSession,
    project_id: UUID | None = Query(default=None),
    event_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict:
    if not has_permission(current_user.role, PERM_USAGE_VIEW):
        raise ForbiddenError("Permission denied: usage.view")
    rows = UsageService(db).list_records(
        project_id=project_id,
        event_type=event_type,
        limit=limit,
    )
    return success_response(data=[r.model_dump(mode="json") for r in rows])


@router.get("/usage/summary")
def usage_summary(
    current_user: ApproverUser,
    db: DbSession,
    project_id: UUID | None = Query(default=None),
) -> dict:
    if not has_permission(current_user.role, PERM_USAGE_VIEW):
        raise ForbiddenError("Permission denied: usage.view")
    summary = UsageService(db).summary(project_id=project_id)
    return success_response(data=summary.model_dump(mode="json"))
