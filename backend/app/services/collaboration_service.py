"""Sprint 5.4 — collaboration (comments, review/approval requests, activity)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants.permissions import (
    PERM_APPROVAL_CREATE,
    PERM_APPROVAL_RESOLVE,
    PERM_COMMENT,
    PERM_REVIEW_COMPLETE,
    PERM_REVIEW_CREATE,
    has_permission,
)
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationAppError
from app.models.collaboration import ApprovalRequest, Comment, ReviewRequest
from app.models.user import User
from app.repositories.audit_repository import AuditRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.collaboration import (
    ActivityItemOut,
    ApprovalRequestCreate,
    ApprovalRequestOut,
    ApprovalRequestResolve,
    CommentCreate,
    CommentOut,
    ReviewRequestComplete,
    ReviewRequestCreate,
    ReviewRequestOut,
)
from app.services.audit_service import AuditService


class CollaborationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = ProjectRepository(db)
        self.audits = AuditService(db)
        self.audit_repo = AuditRepository(db)

    def _require_project(self, project_id: UUID, user_id: UUID):
        project = self.projects.get_for_user(project_id, user_id)
        if project is None:
            raise NotFoundError("Project not found")
        return project

    def _require_perm(self, user: User, permission: str) -> None:
        if not has_permission(user.role, permission):
            raise ForbiddenError(f"Permission denied: {permission}")

    # --- comments ---

    def list_comments(self, project_id: UUID, user_id: UUID) -> list[CommentOut]:
        self._require_project(project_id, user_id)
        rows = list(
            self.db.scalars(
                select(Comment)
                .where(Comment.project_id == project_id, Comment.deleted_at.is_(None))
                .order_by(Comment.created_at.desc())
                .limit(200),
            ).all(),
        )
        return [self._comment_out(r) for r in rows]

    def add_comment(self, project_id: UUID, user: User, body: CommentCreate) -> CommentOut:
        self._require_project(project_id, user.id)
        self._require_perm(user, PERM_COMMENT)
        text = body.body.strip()
        if not text:
            raise ValidationAppError("body is required")
        if body.parent_id is not None:
            parent = self.db.get(Comment, body.parent_id)
            if parent is None or parent.project_id != project_id or parent.deleted_at is not None:
                raise ValidationAppError("parent comment not found")
        row = Comment(
            project_id=project_id,
            user_id=user.id,
            parent_id=body.parent_id,
            body=text,
            resource_type=body.resource_type,
            resource_id=body.resource_id,
        )
        self.db.add(row)
        self.audits.record(
            project_id=project_id,
            user_id=user.id,
            action="comment.created",
            summary=f"Comment added ({len(text)} chars)",
            resource_type=body.resource_type or "project",
            resource_id=body.resource_id or project_id,
            commit=False,
        )
        self.db.commit()
        self.db.refresh(row)
        return self._comment_out(row)

    # --- review requests ---

    def list_review_requests(self, project_id: UUID, user_id: UUID) -> list[ReviewRequestOut]:
        self._require_project(project_id, user_id)
        rows = list(
            self.db.scalars(
                select(ReviewRequest)
                .where(ReviewRequest.project_id == project_id)
                .order_by(ReviewRequest.created_at.desc())
                .limit(100),
            ).all(),
        )
        return [self._review_out(r) for r in rows]

    def create_review_request(
        self,
        project_id: UUID,
        user: User,
        body: ReviewRequestCreate,
    ) -> ReviewRequestOut:
        self._require_project(project_id, user.id)
        self._require_perm(user, PERM_REVIEW_CREATE)
        row = ReviewRequest(
            project_id=project_id,
            resource_type=body.resource_type.strip(),
            resource_id=body.resource_id,
            requested_by=user.id,
            assignee_id=body.assignee_id,
            status="open",
            message=(body.message or "").strip(),
        )
        self.db.add(row)
        self.audits.record(
            project_id=project_id,
            user_id=user.id,
            action="review_request.created",
            summary=f"Review requested on {row.resource_type}",
            resource_type=row.resource_type,
            resource_id=row.resource_id,
            commit=False,
        )
        self.db.commit()
        self.db.refresh(row)
        return self._review_out(row)

    def complete_review_request(
        self,
        request_id: UUID,
        user: User,
        body: ReviewRequestComplete,
    ) -> ReviewRequestOut:
        row = self.db.get(ReviewRequest, request_id)
        if row is None:
            raise NotFoundError("Review request not found")
        self._require_project(row.project_id, user.id)
        self._require_perm(user, PERM_REVIEW_COMPLETE)
        is_assignee = row.assignee_id is None or row.assignee_id == user.id
        if not is_assignee and not has_permission(user.role, PERM_APPROVAL_RESOLVE):
            raise ForbiddenError("Only assignee or approver can complete this review")
        if row.status != "open":
            raise ValidationAppError("Review request is not open")
        row.status = "completed"
        row.resolution_note = body.resolution_note
        row.completed_at = datetime.now(timezone.utc)
        self.audits.record(
            project_id=row.project_id,
            user_id=user.id,
            action="review_request.completed",
            summary="Review request completed",
            resource_type=row.resource_type,
            resource_id=row.resource_id or row.id,
            commit=False,
        )
        self.db.commit()
        self.db.refresh(row)
        return self._review_out(row)

    # --- approval requests ---

    def list_approval_requests(self, project_id: UUID, user_id: UUID) -> list[ApprovalRequestOut]:
        self._require_project(project_id, user_id)
        rows = list(
            self.db.scalars(
                select(ApprovalRequest)
                .where(ApprovalRequest.project_id == project_id)
                .order_by(ApprovalRequest.created_at.desc())
                .limit(100),
            ).all(),
        )
        return [self._approval_out(r) for r in rows]

    def create_approval_request(
        self,
        project_id: UUID,
        user: User,
        body: ApprovalRequestCreate,
    ) -> ApprovalRequestOut:
        self._require_project(project_id, user.id)
        self._require_perm(user, PERM_APPROVAL_CREATE)
        row = ApprovalRequest(
            project_id=project_id,
            resource_type=body.resource_type.strip(),
            resource_id=body.resource_id,
            requested_by=user.id,
            assignee_id=body.assignee_id,
            status="open",
            message=(body.message or "").strip(),
        )
        self.db.add(row)
        self.audits.record(
            project_id=project_id,
            user_id=user.id,
            action="approval_request.created",
            summary=f"Approval requested on {row.resource_type}",
            resource_type=row.resource_type,
            resource_id=row.resource_id,
            commit=False,
        )
        self.db.commit()
        self.db.refresh(row)
        return self._approval_out(row)

    def resolve_approval_request(
        self,
        request_id: UUID,
        user: User,
        body: ApprovalRequestResolve,
    ) -> ApprovalRequestOut:
        row = self.db.get(ApprovalRequest, request_id)
        if row is None:
            raise NotFoundError("Approval request not found")
        self._require_project(row.project_id, user.id)
        self._require_perm(user, PERM_APPROVAL_RESOLVE)
        if row.status != "open":
            raise ValidationAppError("Approval request is not open")
        row.status = body.decision
        row.resolution_note = body.resolution_note
        row.resolved_by = user.id
        row.resolved_at = datetime.now(timezone.utc)
        self.audits.record(
            project_id=row.project_id,
            user_id=user.id,
            action=f"approval_request.{body.decision}",
            summary=f"Approval request {body.decision}",
            resource_type=row.resource_type,
            resource_id=row.resource_id or row.id,
            commit=False,
        )
        self.db.commit()
        self.db.refresh(row)
        return self._approval_out(row)

    def activity(self, project_id: UUID, user_id: UUID, *, limit: int = 50) -> list[ActivityItemOut]:
        self._require_project(project_id, user_id)
        items: list[ActivityItemOut] = []

        for c in self.db.scalars(
            select(Comment)
            .where(Comment.project_id == project_id, Comment.deleted_at.is_(None))
            .order_by(Comment.created_at.desc())
            .limit(limit),
        ).all():
            items.append(
                ActivityItemOut(
                    kind="comment",
                    id=c.id,
                    project_id=project_id,
                    summary=c.body[:240],
                    actor_user_id=c.user_id,
                    resource_type=c.resource_type,
                    resource_id=c.resource_id,
                    created_at=c.created_at,
                ),
            )

        for r in self.db.scalars(
            select(ReviewRequest)
            .where(ReviewRequest.project_id == project_id)
            .order_by(ReviewRequest.created_at.desc())
            .limit(limit),
        ).all():
            items.append(
                ActivityItemOut(
                    kind="review_request",
                    id=r.id,
                    project_id=project_id,
                    summary=f"Review {r.status}: {r.resource_type}",
                    actor_user_id=r.requested_by,
                    resource_type=r.resource_type,
                    resource_id=r.resource_id,
                    created_at=r.created_at,
                    metadata={"status": r.status},
                ),
            )

        for a in self.db.scalars(
            select(ApprovalRequest)
            .where(ApprovalRequest.project_id == project_id)
            .order_by(ApprovalRequest.created_at.desc())
            .limit(limit),
        ).all():
            items.append(
                ActivityItemOut(
                    kind="approval_request",
                    id=a.id,
                    project_id=project_id,
                    summary=f"Approval {a.status}: {a.resource_type}",
                    actor_user_id=a.requested_by,
                    resource_type=a.resource_type,
                    resource_id=a.resource_id,
                    created_at=a.created_at,
                    metadata={"status": a.status},
                ),
            )

        for log in self.audit_repo.list_for_project(project_id, limit=limit):
            items.append(
                ActivityItemOut(
                    kind="audit",
                    id=log.id,
                    project_id=log.project_id,
                    summary=log.summary or log.action,
                    actor_user_id=log.user_id,
                    resource_type=log.resource_type,
                    resource_id=log.resource_id,
                    created_at=log.created_at,
                    metadata={"action": log.action},
                ),
            )

        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[: max(1, min(limit, 200))]

    @staticmethod
    def _comment_out(row: Comment) -> CommentOut:
        return CommentOut(
            id=row.id,
            project_id=row.project_id,
            user_id=row.user_id,
            parent_id=row.parent_id,
            body=row.body,
            resource_type=row.resource_type,
            resource_id=row.resource_id,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _review_out(row: ReviewRequest) -> ReviewRequestOut:
        return ReviewRequestOut(
            id=row.id,
            project_id=row.project_id,
            resource_type=row.resource_type,
            resource_id=row.resource_id,
            requested_by=row.requested_by,
            assignee_id=row.assignee_id,
            status=row.status,
            message=row.message,
            resolution_note=row.resolution_note,
            created_at=row.created_at,
            completed_at=row.completed_at,
        )

    @staticmethod
    def _approval_out(row: ApprovalRequest) -> ApprovalRequestOut:
        return ApprovalRequestOut(
            id=row.id,
            project_id=row.project_id,
            resource_type=row.resource_type,
            resource_id=row.resource_id,
            requested_by=row.requested_by,
            assignee_id=row.assignee_id,
            status=row.status,
            message=row.message,
            resolution_note=row.resolution_note,
            resolved_by=row.resolved_by,
            created_at=row.created_at,
            resolved_at=row.resolved_at,
        )
