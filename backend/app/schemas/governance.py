"""Pydantic schemas for Stage E RKM governance (review / approve / publish / compare)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.gap import PublishBlocker
from app.schemas.rkm import RkmDraftOut


class RequirementEditIn(BaseModel):
    id: UUID
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=20000)
    priority: str | None = Field(default=None, max_length=32)


class ReviewIn(BaseModel):
    edits: list[RequirementEditIn] = Field(default_factory=list)
    change_summary: str | None = Field(default=None, max_length=500)
    reasoning_note: str | None = Field(default=None, max_length=2000)


class ApproveIn(BaseModel):
    note: str | None = Field(default=None, max_length=2000)


class PublishIn(BaseModel):
    note: str | None = Field(default=None, max_length=2000)


class VersionForkIn(BaseModel):
    """Create a new active Draft from a published (or any) version snapshot."""

    from_version: str | None = Field(
        default=None,
        description="Source version label; defaults to current published RKM",
        max_length=64,
    )
    change_summary: str | None = Field(default=None, max_length=500)


class PublishResult(BaseModel):
    project_id: UUID
    rkm_id: UUID
    version_label: str
    status: str
    published_at: datetime
    draft: RkmDraftOut
    publish_blockers: list[PublishBlocker] = Field(default_factory=list)


class ApproveResult(BaseModel):
    project_id: UUID
    rkm_id: UUID
    version_label: str
    status: str
    approved_by: str | None = None
    approved_at: datetime | None = None
    draft: RkmDraftOut


class ReviewResult(BaseModel):
    project_id: UUID
    rkm_id: UUID
    version_label: str
    edited_count: int
    draft: RkmDraftOut


class VersionDiffItem(BaseModel):
    section: str
    change_type: str  # added | removed | modified
    item_id: str | None = None
    title: str | None = None
    before: str | None = None
    after: str | None = None


class VersionCompareOut(BaseModel):
    project_id: UUID
    from_version: str
    to_version: str
    from_status: str
    to_status: str
    from_reasoning: str = ""
    to_reasoning: str = ""
    diffs: list[VersionDiffItem] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)
