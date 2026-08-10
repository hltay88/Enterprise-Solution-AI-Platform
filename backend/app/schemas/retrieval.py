"""Sprint 5.2 — retrieval request/response schemas."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class RetrievalSearchIn(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    domain_code: str | None = None
    knowledge_type: str | None = None
    project_id: UUID | None = None
    top_k: int | None = Field(default=None, ge=1, le=50)
    min_score: float | None = None
    max_per_item: int | None = Field(default=2, ge=1, le=10)


class CitationOut(BaseModel):
    knowledge_id: UUID
    knowledge_version_id: UUID
    chunk_id: UUID
    title: str
    version_label: str
    status: str
    domain_code: str | None = None
    knowledge_type: str | None = None
    page_number: int | None = None
    section_label: str | None = None
    source_document_name: str | None = None
    excerpt: str = ""


class RetrievalHitOut(BaseModel):
    rank: int
    chunk_id: UUID
    content: str
    vector_score: float | None = None
    keyword_score: float | None = None
    fused_score: float | None = None
    citation: CitationOut


class RetrievalSearchOut(BaseModel):
    run_id: UUID
    query: str
    insufficient_evidence: bool
    embedding_provider: str
    embedding_model: str
    latency_ms: int
    hits: list[RetrievalHitOut] = Field(default_factory=list)


class RetrievalContextOut(BaseModel):
    run_id: UUID
    query: str
    insufficient_evidence: bool
    review_required: bool
    context_text: str
    citations: list[CitationOut] = Field(default_factory=list)
    hits: list[RetrievalHitOut] = Field(default_factory=list)
    embedding_provider: str
    embedding_model: str
    latency_ms: int
    message: str | None = None
