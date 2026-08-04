"""Document API schemas (Sprint 1 + Phase 2 Stage B)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentSummary(BaseModel):
    id: UUID
    project_id: UUID
    filename: str
    file_type: str
    storage_path: str
    uploaded_at: datetime
    extracted_text: str | None = None
    extracted_preview: str | None = None
    content_sha256: str | None = None
    file_size_bytes: int | None = None
    mime_type: str | None = None
    status: str = "completed"
    page_count: int | None = None
    language: str | None = None
    ocr_used: bool = False
    needs_manual_review: bool = False
    error_message: str | None = None
    processing_job_id: UUID | None = None
    duplicate_of: UUID | None = None
    metadata: dict[str, str | None] = Field(default_factory=dict)

    model_config = {"from_attributes": True}


class JobStatus(BaseModel):
    id: UUID
    project_id: UUID
    document_id: UUID | None = None
    job_type: str
    status: str
    progress: int = 0
    error_message: str | None = None
    result_json: dict | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class DocumentUploadItem(BaseModel):
    document: DocumentSummary
    job: JobStatus | None = None
    duplicate: bool = False


class DocumentUploadBatchResult(BaseModel):
    project_id: UUID
    items: list[DocumentUploadItem]
    accepted_count: int
    duplicate_count: int
