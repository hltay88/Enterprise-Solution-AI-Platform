"""Export jobs for generated deliverables."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import NotFoundError, ValidationAppError
from app.repositories.deliverable_repository import DeliverableRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.deliverable import ExportIn, ExportJobOut
from app.services.audit_service import AuditService
from app.services.rendering.docx_renderer import render_document_docx
from app.services.rendering.pdf_renderer import convert_docx_bytes_to_pdf
from app.services.rendering.pptx_renderer import render_presentation_pptx
from app.services.rendering.xlsx_renderer import render_bom_xlsx

_DOCX_TYPES = {"proposal", "sow", "solution_design"}


class ExportService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = ProjectRepository(db)
        self.repo = DeliverableRepository(db)

    def export(
        self,
        project_id: UUID,
        document_id: UUID,
        user_id: UUID,
        body: ExportIn | None = None,
    ) -> ExportJobOut:
        if self.projects.get_for_user(project_id, user_id) is None:
            raise NotFoundError("Project not found")
        body = body or ExportIn()

        document = self.repo.get_document(document_id, project_id)
        if document is None:
            raise NotFoundError("Deliverable not found")
        if document.current_version_id is None:
            raise ValidationAppError("Document has no version to export")

        doc_type = str(document.document_type or "proposal")
        export_format = body.format
        self._validate_format(doc_type, export_format)

        job = self.repo.create_export_job(
            project_id=project_id,
            document_id=document.id,
            document_version_id=document.current_version_id,
            format=export_format,
            status="processing",
            created_by=user_id,
        )
        self.db.commit()

        try:
            sections = self._load_sections(document.current_version_id)

            if export_format == "pptx":
                data = render_presentation_pptx(
                    title=document.title,
                    status=document.status,
                    slides=sections,
                )
                extension = "pptx"
                label = "presentation PPTX"
            elif export_format == "xlsx":
                data = render_bom_xlsx(
                    title=document.title,
                    status=document.status,
                    sections=sections,
                )
                extension = "xlsx"
                label = "BOM XLSX"
            else:
                docx_bytes = render_document_docx(
                    title=document.title,
                    status=document.status,
                    sections=sections,
                    document_label=doc_type.replace("_", " ").title(),
                )
                if export_format == "pdf":
                    data = convert_docx_bytes_to_pdf(docx_bytes)
                    extension = "pdf"
                    label = f"{doc_type} PDF"
                else:
                    data = docx_bytes
                    extension = "docx"
                    label = f"{doc_type} DOCX"

            checksum = hashlib.sha256(data).hexdigest()
            settings = get_settings()
            root = Path(settings.storage_path)
            out_dir = root / str(project_id) / "exports"
            out_dir.mkdir(parents=True, exist_ok=True)
            filename = f"{uuid4()}_{doc_type}.{extension}"
            path = out_dir / filename
            path.write_bytes(data)

            job.status = "completed"
            job.storage_path = str(path)
            job.checksum_sha256 = checksum
            job.page_count = max(1, len(sections))
            job.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            AuditService(self.db).record(
                project_id=project_id,
                user_id=user_id,
                action="deliverable.export",
                summary=f"Exported {label}",
                resource_type="export_job",
                resource_id=job.id,
                metadata={
                    "checksum": checksum,
                    "format": export_format,
                    "document_type": doc_type,
                },
            )
        except ValidationAppError as exc:
            job.status = "failed"
            job.error = str(exc)[:1000]
            job.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            AuditService(self.db).record(
                project_id=project_id,
                user_id=user_id,
                action="deliverable.export_failed",
                summary="Export failed",
                resource_type="export_job",
                resource_id=job.id,
                metadata={"error": job.error},
            )
            raise
        except Exception as exc:  # noqa: BLE001
            job.status = "failed"
            job.error = str(exc)[:1000]
            job.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            AuditService(self.db).record(
                project_id=project_id,
                user_id=user_id,
                action="deliverable.export_failed",
                summary="Export failed",
                resource_type="export_job",
                resource_id=job.id,
                metadata={"error": job.error},
            )
            raise ValidationAppError(f"Export failed: {exc}") from exc

        return self.to_out(
            job,
            download_name=f"{document.title or doc_type}.{export_format}",
        )

    def render_bytes(
        self,
        document_id: UUID,
        project_id: UUID,
        export_format: str,
    ) -> tuple[bytes, str]:
        """Render deliverable bytes without creating an export job (package ZIP)."""
        document = self.repo.get_document(document_id, project_id)
        if document is None or document.current_version_id is None:
            raise NotFoundError("Deliverable not found")
        doc_type = str(document.document_type or "proposal")
        self._validate_format(doc_type, export_format)
        sections = self._load_sections(document.current_version_id)
        if export_format == "pptx":
            return (
                render_presentation_pptx(
                    title=document.title, status=document.status, slides=sections
                ),
                "pptx",
            )
        if export_format == "xlsx":
            return (
                render_bom_xlsx(
                    title=document.title, status=document.status, sections=sections
                ),
                "xlsx",
            )
        docx_bytes = render_document_docx(
            title=document.title,
            status=document.status,
            sections=sections,
            document_label=doc_type.replace("_", " ").title(),
        )
        if export_format == "pdf":
            return convert_docx_bytes_to_pdf(docx_bytes), "pdf"
        return docx_bytes, "docx"

    def _load_sections(self, version_id: UUID) -> list[dict]:
        sections = []
        for section in self.repo.list_sections(version_id):
            items = [
                {
                    "text": item.text,
                    "content_type": item.content_type,
                    "review_required": item.review_required,
                    "structured_data": item.structured_data or {},
                }
                for item in self.repo.list_content_items(section.id)
            ]
            sections.append(
                {
                    "title": section.title,
                    "section_type": section.section_type,
                    "assumptions": list(section.assumptions_json or []),
                    "content_items": items,
                }
            )
        return sections

    def _validate_format(self, doc_type: str, export_format: str) -> None:
        if doc_type == "presentation":
            if export_format != "pptx":
                raise ValidationAppError("Presentations export as format=pptx only")
            return
        if doc_type == "bom":
            if export_format != "xlsx":
                raise ValidationAppError("BOM exports as format=xlsx only")
            return
        if doc_type in _DOCX_TYPES:
            if export_format not in {"docx", "pdf"}:
                raise ValidationAppError(
                    f"{doc_type} exports as format=docx or format=pdf only"
                )
            return
        raise ValidationAppError(f"Unsupported document type '{doc_type}' for export")

    def get(
        self, project_id: UUID, export_id: UUID, user_id: UUID
    ) -> ExportJobOut:
        if self.projects.get_for_user(project_id, user_id) is None:
            raise NotFoundError("Project not found")
        job = self.repo.get_export_job(export_id, project_id)
        if job is None:
            raise NotFoundError("Export job not found")
        return self.to_out(job)

    def to_out(self, job, *, download_name: str | None = None) -> ExportJobOut:
        return ExportJobOut(
            id=job.id,
            project_id=job.project_id,
            document_id=job.document_id,
            document_version_id=job.document_version_id,
            format=job.format,
            status=job.status,
            storage_path=job.storage_path,
            checksum_sha256=job.checksum_sha256,
            page_count=job.page_count,
            error=job.error,
            created_at=job.created_at,
            completed_at=job.completed_at,
            download_name=download_name,
        )
