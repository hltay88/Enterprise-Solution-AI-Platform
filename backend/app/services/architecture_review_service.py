"""Architecture human review (Sprint 3.3 Task 9, ATLAS-037).

Marks an AI-recommended candidate ``under_review``. Approval / Complete gate
is Task 10 (Approver-only).
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.repositories.architecture_option_repository import ArchitectureOptionRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.rkm_repository import RkmRepository
from app.schemas.vendor_bom import ArchitectureReviewIn, ArchitectureReviewOut
from app.services.architecture_traceability import count_architecture_uncovered_critical
from app.services.audit_service import AuditService
from app.services.domain_traceability import extract_rkm_requirements

_REVIEWABLE = frozenset({"draft", "recommended", "under_review"})
_LOCKED = frozenset({"approved", "complete"})


class ArchitectureReviewService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = ProjectRepository(db)
        self.architectures = ArchitectureOptionRepository(db)
        self.rkms = RkmRepository(db)

    def review(
        self,
        project_id: UUID,
        architecture_id: UUID,
        user_id: UUID,
        body: ArchitectureReviewIn | None = None,
    ) -> ArchitectureReviewOut:
        self._require_project(project_id, user_id)
        option = self.architectures.get_for_project(architecture_id, project_id)
        if option is None:
            raise NotFoundError("Architecture option not found")

        status = str(option.status or "draft").strip().lower()
        if status in _LOCKED:
            raise ValidationAppError(
                f"Architecture is already {status}; cannot re-open for review "
                "(ATLAS-037). Generate a new candidate or use approve flow.",
            )
        if status not in _REVIEWABLE:
            raise ValidationAppError(
                f"Architecture status '{option.status}' cannot be moved to under_review",
            )

        body = body or ArchitectureReviewIn()
        try:
            updated = self.architectures.mark_under_review(
                architecture_id,
                reviewed_by=user_id,
                review_note=body.note,
                commit=True,
            )
        except ValueError as exc:
            raise NotFoundError(str(exc)) from exc

        uncovered = self._uncovered_critical_count(project_id, architecture_id)
        out = ArchitectureReviewOut(
            id=updated.id,
            project_id=updated.project_id,
            status=updated.status,
            reviewed_at=updated.reviewed_at,
            reviewed_by=updated.reviewed_by,
            review_note=updated.review_note,
            approved_at=updated.approved_at,
            approved_by=updated.approved_by,
            approval_note=updated.approval_note,
            uncovered_critical_count=uncovered,
        )
        AuditService(self.db).record(
            project_id=project_id,
            user_id=user_id,
            action="architectures.review",
            summary=(
                f"Marked architecture '{updated.title or updated.candidate_key}' "
                f"under_review (uncovered critical/high={uncovered})"
            ),
            resource_type="architecture_option",
            resource_id=updated.id,
            metadata={
                "candidate_key": updated.candidate_key,
                "prior_status": status,
                "uncovered_critical_count": uncovered,
                "note": (body.note or "")[:200] or None,
            },
        )
        return out

    def _uncovered_critical_count(
        self,
        project_id: UUID,
        architecture_id: UUID,
    ) -> int:
        """Soft signal for reviewers; hard Complete gate is Task 10."""
        rows = self.architectures.list_traceability_for_architecture(architecture_id)
        trace = [
            {
                "requirement_id": row.requirement_id,
                "architecture_id": row.architecture_id,
                "status": row.status,
            }
            for row in rows
        ]
        published = self.rkms.get_published(project_id)
        requirements: list[dict] = []
        if published is not None:
            requirements = extract_rkm_requirements(dict(published.payload_json or {}))
        return count_architecture_uncovered_critical(trace, requirements)

    def _require_project(self, project_id: UUID, user_id: UUID):
        project = self.projects.get_for_user(project_id, user_id)
        if project is None:
            raise NotFoundError("Project not found")
        return project
