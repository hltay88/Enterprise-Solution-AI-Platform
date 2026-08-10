"""Sprint 5.1 — Pydantic schemas for Enterprise Knowledge Engine."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeSourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    original_filename: str
    file_type: str
    mime_type: str | None = None
    storage_path: str
    size_bytes: int
    checksum_sha256: str
    page_count: int | None = None
    extract_warnings: list[Any] = Field(default_factory=list)
    section_hints: list[Any] = Field(default_factory=list)
    created_at: datetime


class KnowledgeVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    knowledge_item_id: UUID
    version_number: int
    version_label: str
    status: str
    content_text: str | None = None
    content_location: str | None = None
    change_summary: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_json")
    tags: list[str] = Field(default_factory=list)
    effective_date: date | None = None
    expiry_date: date | None = None
    next_review_date: date | None = None
    source_document_name: str | None = None
    created_by: UUID | None = None
    reviewed_by: UUID | None = None
    approved_by: UUID | None = None
    published_by: UUID | None = None
    reviewed_at: datetime | None = None
    approved_at: datetime | None = None
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    sources: list[KnowledgeSourceOut] = Field(default_factory=list)


class KnowledgeItemSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID | None = None
    project_id: UUID | None = None
    title: str
    description: str | None = None
    knowledge_type: str
    domain_code: str
    owner_user_id: UUID | None = None
    sensitivity: str
    current_version_id: UUID | None = None
    status: str | None = None
    version_label: str | None = None
    version_number: int | None = None
    created_at: datetime
    updated_at: datetime


class KnowledgeItemDetail(KnowledgeItemSummary):
    current_version: KnowledgeVersionOut | None = None
    versions: list[KnowledgeVersionOut] = Field(default_factory=list)


class KnowledgeCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    knowledge_type: str | None = None
    domain_code: str | None = None
    project_id: UUID | None = None
    sensitivity: str = "internal"
    tags: list[str] = Field(default_factory=list)
    content_text: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    change_summary: str | None = "Initial draft"


class KnowledgeUpdateIn(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    knowledge_type: str | None = None
    domain_code: str | None = None
    sensitivity: str | None = None
    tags: list[str] | None = None
    content_text: str | None = None
    metadata: dict[str, Any] | None = None
    change_summary: str | None = None
    effective_date: date | None = None
    expiry_date: date | None = None
    next_review_date: date | None = None


class KnowledgeNewVersionIn(BaseModel):
    change_summary: str | None = "Forked new draft version"
    content_text: str | None = None


class TaxonomyDomainOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    aliases: list[str] = Field(default_factory=list)
    active: bool = True


class KnowledgeTypeOut(BaseModel):
    code: str
    name: str
