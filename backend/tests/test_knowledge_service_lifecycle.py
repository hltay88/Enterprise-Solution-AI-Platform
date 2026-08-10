"""Sprint 5.1 — knowledge service lifecycle with mocked repository (no Postgres)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import pytest

from app.constants.knowledge_lifecycle import (
    STATUS_APPROVED,
    STATUS_PUBLISHED,
    STATUS_REVIEW,
)
from app.constants.roles import ROLE_APPROVER, ROLE_EDITOR, role_allows
from app.core.exceptions import ConflictError
from app.schemas.knowledge import KnowledgeUpdateIn
from app.services.knowledge_service import KnowledgeService


@dataclass
class FakeUser:
    id: Any = field(default_factory=uuid4)
    email: str = "editor@example.com"
    role: str = ROLE_EDITOR


@dataclass
class FakeVersion:
    id: Any
    knowledge_item_id: Any
    version_number: int = 1
    version_label: str = "1"
    status: str = "draft"
    content_text: str | None = "body"
    content_location: str | None = None
    change_summary: str | None = "init"
    metadata_json: dict = field(default_factory=dict)
    tags: list = field(default_factory=list)
    effective_date: Any = None
    expiry_date: Any = None
    next_review_date: Any = None
    source_document_name: str | None = None
    created_by: Any = None
    reviewed_by: Any = None
    approved_by: Any = None
    published_by: Any = None
    reviewed_at: Any = None
    approved_at: Any = None
    published_at: Any = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    sources: list = field(default_factory=list)


@dataclass
class FakeItem:
    id: Any
    tenant_id: Any = None
    project_id: Any = None
    title: str = "Item"
    description: str | None = None
    knowledge_type: str = "best_practice"
    domain_code: str = "networking"
    owner_user_id: Any = None
    sensitivity: str = "internal"
    current_version_id: Any = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    versions: list = field(default_factory=list)


class FakeRepo:
    def __init__(self, item: FakeItem, version: FakeVersion) -> None:
        self.item = item
        self.versions = {version.id: version}
        item.versions = [version]
        item.current_version_id = version.id
        self.audits: list[dict] = []

    def get_item(self, item_id):
        return self.item if self.item.id == item_id else None

    def get_version(self, version_id):
        return self.versions.get(version_id)

    def get_current_version(self, item):
        return self.versions.get(item.current_version_id)

    def max_version_number(self, item_id):
        return max(v.version_number for v in self.versions.values())

    def add_version(self, version, *, commit=True):
        if getattr(version, "id", None) is None:
            version.id = uuid4()
        self.versions[version.id] = version
        self.item.versions.append(version)
        return version

    def record_audit(self, **kwargs):
        self.audits.append(kwargs)
        return kwargs


def test_published_is_immutable_requires_new_version():
    item_id = uuid4()
    ver_id = uuid4()
    item = FakeItem(id=item_id, title="Std")
    version = FakeVersion(id=ver_id, knowledge_item_id=item_id, status=STATUS_PUBLISHED)
    repo = FakeRepo(item, version)

    svc = KnowledgeService.__new__(KnowledgeService)
    svc.db = None
    svc.repo = repo
    svc.projects = None
    svc.storage = None

    editor = FakeUser(role=ROLE_EDITOR)

    with pytest.raises(ConflictError):
        svc.update_draft(item_id, KnowledgeUpdateIn(content_text="hack"), editor)

    detail = svc.new_version(item_id, editor)
    assert detail.status == "draft"
    assert detail.version_number == 2
    assert version.status == STATUS_PUBLISHED


def test_approver_required_for_publish_role_gate():
    assert role_allows(ROLE_APPROVER, ROLE_APPROVER)
    assert not role_allows(ROLE_EDITOR, ROLE_APPROVER)


def test_lifecycle_transition_audit_on_approve():
    item_id = uuid4()
    ver_id = uuid4()
    item = FakeItem(id=item_id)
    version = FakeVersion(id=ver_id, knowledge_item_id=item_id, status=STATUS_REVIEW)
    repo = FakeRepo(item, version)

    svc = KnowledgeService.__new__(KnowledgeService)
    svc.db = None
    svc.repo = repo
    svc.projects = None
    svc.storage = None

    approver = FakeUser(role=ROLE_APPROVER)
    detail = svc.approve(item_id, approver)
    assert detail.status == STATUS_APPROVED
    assert repo.audits[-1]["action"] == "knowledge.approve"

    detail = svc.publish(item_id, approver)
    assert detail.status == STATUS_PUBLISHED
    assert version.published_by == approver.id
