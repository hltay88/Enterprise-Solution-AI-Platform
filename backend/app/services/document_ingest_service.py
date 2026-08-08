"""Phase 2 Stage B — multi-file async document ingest (ATLAS-027 / ATLAS-029)."""

from __future__ import annotations

import logging
from pathlib import Path
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.constants.file_limits import (
    MAX_BATCH_UPLOAD_MB_PHASE2,
    MAX_UPLOAD_MB_PHASE2,
    MIME_BY_TYPE,
    PHASE2_ALLOWED_EXTENSIONS,
)
from app.core.exceptions import NotFoundError, ValidationAppError
from app.repositories.document_intelligence_repository import DocumentIntelligenceRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.job_repository import JobRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.document import (
    DocumentSummary,
    DocumentUploadBatchResult,
    DocumentUploadItem,
    JobStatus,
)
from app.services.document_intelligence import extract_document
from app.services.document_intelligence.chunking import chunk_pages
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

PREVIEW_CHARS = 500
MAX_FILE_BYTES = MAX_UPLOAD_MB_PHASE2 * 1024 * 1024
MAX_BATCH_BYTES = MAX_BATCH_UPLOAD_MB_PHASE2 * 1024 * 1024


class DocumentIngestService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = ProjectRepository(db)
        self.documents = DocumentRepository(db)
        self.jobs = JobRepository(db)
        self.intel = DocumentIntelligenceRepository(db)
        self.storage = StorageService()

    def list_for_project(self, project_id: UUID, user_id: UUID) -> list[DocumentSummary]:
        self._require_project(project_id, user_id)
        rows = self.documents.list_for_project(project_id)
        return [self._to_summary_with_job(row) for row in rows]

    def get_document(self, document_id: UUID, user_id: UUID) -> DocumentSummary:
        document = self.documents.get(document_id)
        if document is None or document.archived_at is not None:
            raise NotFoundError("Document not found")
        self._require_project(document.project_id, user_id)
        summary = self._to_summary_with_job(document)
        summary.metadata = self.intel.metadata_map(document.id)
        return summary

    def get_job(self, job_id: UUID, user_id: UUID) -> JobStatus:
        job = self.jobs.get(job_id)
        if job is None:
            raise NotFoundError("Job not found")
        self._require_project(job.project_id, user_id)
        return JobStatus.model_validate(job)

    def archive_document(self, document_id: UUID, user_id: UUID) -> None:
        document = self.documents.get(document_id)
        if document is None or document.archived_at is not None:
            raise NotFoundError("Document not found")
        self._require_project(document.project_id, user_id)
        self.documents.soft_archive(document)
        from app.services.audit_service import AuditService

        AuditService(self.db).record(
            project_id=document.project_id,
            user_id=user_id,
            action="document.archive",
            summary=f"Archived document {document.filename}",
            resource_type="document",
            resource_id=document.id,
            metadata={"filename": document.filename},
        )

    async def upload_batch(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        uploads: list[UploadFile],
    ) -> tuple[DocumentUploadBatchResult, list[UUID]]:
        """Validate + store files, enqueue extract jobs. Returns (result, job_ids)."""
        self._require_project(project_id, user_id)

        if not uploads:
            raise ValidationAppError("At least one file is required")

        items: list[DocumentUploadItem] = []
        job_ids: list[UUID] = []
        batch_bytes = 0

        for upload in uploads:
            if not upload.filename:
                raise ValidationAppError("Filename is required")
            file_type = _detect_phase2_type(upload.filename)

            relative_path, size, sha256 = await self.storage.save_upload(
                project_id=project_id,
                upload=upload,
                max_bytes=MAX_FILE_BYTES,
            )
            batch_bytes += size
            if batch_bytes > MAX_BATCH_BYTES:
                self.storage.delete_file(relative_path)
                raise ValidationAppError(
                    f"Batch exceeds maximum aggregate size of {MAX_BATCH_UPLOAD_MB_PHASE2} MB",
                )

            existing = self.documents.find_by_sha256(project_id, sha256)
            if existing is not None:
                self.storage.delete_file(relative_path)
                summary = self._to_summary(existing)
                summary.duplicate_of = existing.id
                items.append(
                    DocumentUploadItem(document=summary, job=None, duplicate=True),
                )
                continue

            document = self.documents.create(
                project_id=project_id,
                filename=upload.filename,
                file_type=file_type,
                storage_path=relative_path,
                extracted_text=None,
                content_sha256=sha256,
                file_size_bytes=size,
                mime_type=MIME_BY_TYPE.get(file_type),
                status="pending",
            )
            job = self.jobs.create(
                project_id=project_id,
                document_id=document.id,
                job_type="document_extract",
                status="queued",
            )
            summary = self._to_summary(document, processing_job_id=job.id)
            items.append(
                DocumentUploadItem(
                    document=summary,
                    job=JobStatus.model_validate(job),
                    duplicate=False,
                ),
            )
            job_ids.append(job.id)

        result = DocumentUploadBatchResult(
            project_id=project_id,
            items=items,
            accepted_count=sum(1 for item in items if not item.duplicate),
            duplicate_count=sum(1 for item in items if item.duplicate),
        )
        if result.accepted_count or result.duplicate_count:
            from app.services.audit_service import AuditService

            AuditService(self.db).record(
                project_id=project_id,
                user_id=user_id,
                action="document.upload",
                summary=(
                    f"Uploaded {result.accepted_count} document(s)"
                    f" ({result.duplicate_count} duplicate(s) skipped)"
                ),
                resource_type="document_batch",
                metadata={
                    "accepted_count": result.accepted_count,
                    "duplicate_count": result.duplicate_count,
                    "filenames": [
                        item.document.filename
                        for item in items
                        if item.document is not None
                    ],
                },
            )
        return result, job_ids

    def process_extract_job(self, job_id: UUID) -> None:
        """Run extract/OCR/normalize/chunk persistence for one job (worker entry)."""
        job = self.jobs.get(job_id)
        if job is None:
            logger.error("Processing job %s not found", job_id)
            return
        if job.document_id is None:
            self.jobs.mark_failed(job, "Job has no document_id")
            return

        document = self.documents.get(job.document_id)
        if document is None:
            self.jobs.mark_failed(job, "Document not found")
            return

        self.jobs.mark_started(job)
        document.status = "processing"
        self.documents.save(document)

        try:
            absolute_path = self.storage.absolute_path(document.storage_path)
            if not Path(absolute_path).exists():
                raise ValidationAppError("Stored file is missing")

            self.jobs.mark_progress(job, 30)
            extraction = extract_document(absolute_path, document.file_type)
            if not extraction.full_text.strip():
                raise ValidationAppError("No extractable text found in the uploaded file")

            self.jobs.mark_progress(job, 70)
            chunks = chunk_pages(extraction.pages)
            self.intel.replace_extraction(
                document_id=document.id,
                pages=extraction.pages,
                chunks=chunks,
                metadata=extraction.metadata,
            )

            document.extracted_text = extraction.full_text
            document.status = "completed"
            document.page_count = len(extraction.pages)
            document.language = extraction.language
            document.ocr_used = extraction.ocr_used
            document.needs_manual_review = extraction.needs_manual_review
            document.error_message = None
            self.documents.save(document)

            self.jobs.mark_completed(
                job,
                result={
                    "document_id": str(document.id),
                    "page_count": document.page_count,
                    "chunk_count": len(chunks),
                    "ocr_used": document.ocr_used,
                    "needs_manual_review": document.needs_manual_review,
                    "warnings": extraction.warnings,
                },
            )
        except Exception as exc:
            logger.exception("Document extract job %s failed", job_id)
            message = str(exc) or "Document extraction failed"
            document.status = "failed"
            document.error_message = message
            self.documents.save(document)
            # Refresh job after document save (session may be dirty).
            job = self.jobs.get(job_id) or job
            self.jobs.mark_failed(job, message)

    def _require_project(self, project_id: UUID, user_id: UUID) -> None:
        project = self.projects.get_for_user(project_id, user_id)
        if project is None:
            raise NotFoundError("Project not found")

    def _to_summary_with_job(self, document) -> DocumentSummary:
        job = self.jobs.latest_for_document(document.id)
        return self._to_summary(
            document,
            processing_job_id=job.id if job else None,
        )

    def _to_summary(
        self,
        document,
        *,
        processing_job_id: UUID | None = None,
    ) -> DocumentSummary:
        text = document.extracted_text
        preview = None
        if text:
            preview = text if len(text) <= PREVIEW_CHARS else f"{text[:PREVIEW_CHARS].rstrip()}…"

        return DocumentSummary(
            id=document.id,
            project_id=document.project_id,
            filename=document.filename,
            file_type=document.file_type,
            storage_path=document.storage_path,
            uploaded_at=document.uploaded_at,
            extracted_text=text,
            extracted_preview=preview,
            content_sha256=document.content_sha256,
            file_size_bytes=document.file_size_bytes,
            mime_type=document.mime_type,
            status=document.status or "completed",
            page_count=document.page_count,
            language=document.language,
            ocr_used=bool(document.ocr_used),
            needs_manual_review=bool(document.needs_manual_review),
            error_message=document.error_message,
            processing_job_id=processing_job_id,
        )


def _detect_phase2_type(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    file_type = PHASE2_ALLOWED_EXTENSIONS.get(suffix)
    if file_type is None:
        allowed = ", ".join(sorted({ext.lstrip(".").upper() for ext in PHASE2_ALLOWED_EXTENSIONS}))
        raise ValidationAppError(f"Unsupported file type. Allowed: {allowed}")
    return file_type


def run_extract_job(job_id: UUID) -> None:
    """Background task entrypoint with its own DB session."""
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        DocumentIngestService(db).process_extract_job(job_id)
    finally:
        db.close()
