"""Sprint 3.3 Tasks 9–10 — architecture review + approve Complete gate."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError, ValidationAppError
from app.schemas.vendor_bom import ArchitectureApproveIn, ArchitectureReviewIn
from app.services.architecture_review_service import ArchitectureReviewService


def test_review_marks_under_review_and_audits():
    db = MagicMock()
    service = ArchitectureReviewService(db)
    project_id = uuid4()
    user_id = uuid4()
    architecture_id = uuid4()
    now = datetime.now(timezone.utc)

    service.projects.get_for_user = MagicMock(  # type: ignore[method-assign]
        return_value=SimpleNamespace(id=project_id),
    )
    service.architectures.get_for_project = MagicMock(  # type: ignore[method-assign]
        return_value=SimpleNamespace(
            id=architecture_id,
            project_id=project_id,
            status="recommended",
            title="Standard campus",
            candidate_key="standard",
        ),
    )
    updated = SimpleNamespace(
        id=architecture_id,
        project_id=project_id,
        status="under_review",
        title="Standard campus",
        candidate_key="standard",
        reviewed_at=now,
        reviewed_by=user_id,
        review_note="Looks coherent",
        approved_at=None,
        approved_by=None,
        approval_note=None,
    )
    service.architectures.mark_under_review = MagicMock(return_value=updated)  # type: ignore[method-assign]
    service._uncovered_critical_count = MagicMock(return_value=1)  # type: ignore[method-assign]

    with patch("app.services.architecture_review_service.AuditService") as audit_cls:
        out = service.review(
            project_id,
            architecture_id,
            user_id,
            ArchitectureReviewIn(note="Looks coherent"),
        )

    assert out.status == "under_review"
    assert out.reviewed_by == user_id
    assert out.uncovered_critical_count == 1
    service.architectures.mark_under_review.assert_called_once()
    assert audit_cls.return_value.record.call_args.kwargs["action"] == "architectures.review"


def test_review_rejects_approved():
    service = ArchitectureReviewService(MagicMock())
    project_id = uuid4()
    architecture_id = uuid4()
    service.projects.get_for_user = MagicMock(  # type: ignore[method-assign]
        return_value=SimpleNamespace(id=project_id),
    )
    service.architectures.get_for_project = MagicMock(  # type: ignore[method-assign]
        return_value=SimpleNamespace(
            id=architecture_id,
            project_id=project_id,
            status="approved",
            title="x",
            candidate_key="standard",
        ),
    )

    with pytest.raises(ValidationAppError, match="already approved"):
        service.review(project_id, architecture_id, uuid4(), ArchitectureReviewIn())


def test_review_not_found():
    service = ArchitectureReviewService(MagicMock())
    service.projects.get_for_user = MagicMock(return_value=SimpleNamespace(id=uuid4()))  # type: ignore[method-assign]
    service.architectures.get_for_project = MagicMock(return_value=None)  # type: ignore[method-assign]

    with pytest.raises(NotFoundError):
        service.review(uuid4(), uuid4(), uuid4(), ArchitectureReviewIn())


def test_approve_hard_fails_when_uncovered_criticals():
    service = ArchitectureReviewService(MagicMock())
    project_id = uuid4()
    architecture_id = uuid4()
    now = datetime.now(timezone.utc)
    service.projects.get_for_user = MagicMock(  # type: ignore[method-assign]
        return_value=SimpleNamespace(id=project_id),
    )
    service.architectures.get_for_project = MagicMock(  # type: ignore[method-assign]
        return_value=SimpleNamespace(
            id=architecture_id,
            project_id=project_id,
            status="under_review",
            reviewed_at=now,
            title="x",
            candidate_key="standard",
        ),
    )
    service._uncovered_critical_count = MagicMock(return_value=2)  # type: ignore[method-assign]
    service.architectures.mark_complete = MagicMock()  # type: ignore[method-assign]

    with pytest.raises(ValidationAppError, match="Cannot Complete"):
        service.approve(project_id, architecture_id, uuid4(), ArchitectureApproveIn())

    service.architectures.mark_complete.assert_not_called()


def test_approve_completes_when_coverage_clean():
    service = ArchitectureReviewService(MagicMock())
    project_id = uuid4()
    user_id = uuid4()
    architecture_id = uuid4()
    now = datetime.now(timezone.utc)
    service.projects.get_for_user = MagicMock(  # type: ignore[method-assign]
        return_value=SimpleNamespace(id=project_id),
    )
    service.architectures.get_for_project = MagicMock(  # type: ignore[method-assign]
        return_value=SimpleNamespace(
            id=architecture_id,
            project_id=project_id,
            status="under_review",
            reviewed_at=now,
            title="Standard",
            candidate_key="standard",
        ),
    )
    service._uncovered_critical_count = MagicMock(return_value=0)  # type: ignore[method-assign]
    updated = SimpleNamespace(
        id=architecture_id,
        project_id=project_id,
        status="complete",
        reviewed_at=now,
        reviewed_by=user_id,
        review_note="ok",
        approved_at=now,
        approved_by=user_id,
        approval_note="ship it",
        title="Standard",
        candidate_key="standard",
    )
    service.architectures.mark_complete = MagicMock(return_value=updated)  # type: ignore[method-assign]

    with patch("app.services.architecture_review_service.AuditService") as audit_cls:
        out = service.approve(
            project_id,
            architecture_id,
            user_id,
            ArchitectureApproveIn(note="ship it"),
        )

    assert out.status == "complete"
    assert out.approved_by == user_id
    assert out.uncovered_critical_count == 0
    assert audit_cls.return_value.record.call_args.kwargs["action"] == "architectures.approve"


def test_approve_requires_under_review():
    service = ArchitectureReviewService(MagicMock())
    project_id = uuid4()
    architecture_id = uuid4()
    service.projects.get_for_user = MagicMock(  # type: ignore[method-assign]
        return_value=SimpleNamespace(id=project_id),
    )
    service.architectures.get_for_project = MagicMock(  # type: ignore[method-assign]
        return_value=SimpleNamespace(
            id=architecture_id,
            project_id=project_id,
            status="recommended",
            reviewed_at=None,
            title="x",
            candidate_key="standard",
        ),
    )

    with pytest.raises(ValidationAppError, match="under_review"):
        service.approve(project_id, architecture_id, uuid4(), ArchitectureApproveIn())
