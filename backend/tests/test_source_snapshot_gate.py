"""Unit tests for source snapshot input gate (Sprint 4.1 L1)."""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.core.exceptions import ValidationAppError
from app.services.source_snapshot_service import SourceSnapshotService


def test_snapshot_requires_published_rkm():
    db = MagicMock()
    service = SourceSnapshotService(db)
    service.projects.get_for_user = MagicMock(return_value=object())
    service.rkms.get_published = MagicMock(return_value=None)
    with pytest.raises(ValidationAppError, match="Published RKM"):
        service.create(uuid4(), uuid4())


def test_snapshot_requires_complete_architecture():
    db = MagicMock()
    service = SourceSnapshotService(db)
    service.projects.get_for_user = MagicMock(return_value=object())
    published = MagicMock()
    published.id = uuid4()
    published.version_label = "1.0.0"
    published.version_major = 1
    published.version_minor = 0
    published.version_patch = 0
    published.payload_json = {"requirements": []}
    service.rkms.get_published = MagicMock(return_value=published)
    service.architectures.list_for_project = MagicMock(return_value=[])
    with pytest.raises(ValidationAppError, match="Complete architecture"):
        service.create(uuid4(), uuid4())
