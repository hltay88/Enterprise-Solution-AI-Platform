"""Sprint 3.3 Task 9 — mark_under_review repository helper."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.repositories.architecture_option_repository import ArchitectureOptionRepository


def test_mark_under_review_stamps_fields():
    db = MagicMock()
    repo = ArchitectureOptionRepository(db)
    architecture_id = uuid4()
    user_id = uuid4()
    row = SimpleNamespace(
        id=architecture_id,
        status="draft",
        reviewed_at=None,
        reviewed_by=None,
        review_note=None,
        updated_at=None,
    )
    repo.get_by_id = MagicMock(return_value=row)  # type: ignore[method-assign]

    updated = repo.mark_under_review(
        architecture_id,
        reviewed_by=user_id,
        review_note="  checked  ",
        commit=True,
    )

    assert updated.status == "under_review"
    assert updated.reviewed_by == user_id
    assert updated.review_note == "checked"
    assert updated.reviewed_at is not None
    db.commit.assert_called_once()


def test_mark_under_review_missing():
    repo = ArchitectureOptionRepository(MagicMock())
    repo.get_by_id = MagicMock(return_value=None)  # type: ignore[method-assign]
    with pytest.raises(ValueError, match="not found"):
        repo.mark_under_review(uuid4(), reviewed_by=uuid4(), review_note=None)


def test_mark_complete_stamps_approval():
    db = MagicMock()
    repo = ArchitectureOptionRepository(db)
    architecture_id = uuid4()
    user_id = uuid4()
    row = SimpleNamespace(
        id=architecture_id,
        status="under_review",
        reviewed_at=None,
        reviewed_by=None,
        approved_at=None,
        approved_by=None,
        approval_note=None,
        updated_at=None,
    )
    repo.get_by_id = MagicMock(return_value=row)  # type: ignore[method-assign]

    updated = repo.mark_complete(
        architecture_id,
        approved_by=user_id,
        approval_note="done",
        commit=True,
    )

    assert updated.status == "complete"
    assert updated.approved_by == user_id
    assert updated.approval_note == "done"
    assert updated.reviewed_by == user_id
    db.commit.assert_called_once()
