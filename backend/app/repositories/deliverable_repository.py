"""Persistence for Phase 4 deliverables (Sprint 4.1)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.deliverable import (
    ContentItem,
    DocumentApproval,
    DocumentSection,
    DocumentSourceRef,
    DocumentTemplate,
    DocumentVersion,
    ExportJob,
    GeneratedDocument,
    GenerationRun,
    SourceSnapshot,
    TemplateVersion,
)
from app.schemas.deliverable import PROPOSAL_SECTION_TYPES


class DeliverableRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    # --- templates ---------------------------------------------------------

    def get_active_template(
        self, document_type: str, code: str = "default_proposal"
    ) -> DocumentTemplate | None:
        return self.db.scalars(
            select(DocumentTemplate).where(
                DocumentTemplate.document_type == document_type,
                DocumentTemplate.code == code,
                DocumentTemplate.active.is_(True),
            )
        ).first()

    def get_active_template_version(
        self, template_id: UUID
    ) -> TemplateVersion | None:
        return self.db.scalars(
            select(TemplateVersion)
            .where(
                TemplateVersion.template_id == template_id,
                TemplateVersion.status == "active",
            )
            .order_by(
                TemplateVersion.version_major.desc(),
                TemplateVersion.version_minor.desc(),
                TemplateVersion.version_patch.desc(),
            )
        ).first()

    def ensure_proposal_template_seed(self) -> tuple[DocumentTemplate, TemplateVersion]:
        template = self.get_active_template("proposal")
        if template is None:
            template = DocumentTemplate(
                document_type="proposal",
                code="default_proposal",
                name="Default Proposal",
                active=True,
            )
            self.db.add(template)
            self.db.flush()
        version = self.get_active_template_version(template.id)
        if version is None:
            sections = [
                {"section_type": code, "title": title}
                for code, title in PROPOSAL_SECTION_TYPES
            ]
            version = TemplateVersion(
                template_id=template.id,
                version_label="1.0.0",
                version_major=1,
                version_minor=0,
                version_patch=0,
                sections_json=sections,
                styles_json={"format": "docx"},
                rendering_rules_json={"include_draft_watermark": True},
                status="active",
            )
            self.db.add(version)
            self.db.flush()
        return template, version

    # --- snapshots ---------------------------------------------------------

    def create_snapshot(self, **kwargs: Any) -> SourceSnapshot:
        row = SourceSnapshot(**kwargs)
        self.db.add(row)
        self.db.flush()
        return row

    def get_snapshot(
        self, snapshot_id: UUID, project_id: UUID
    ) -> SourceSnapshot | None:
        return self.db.scalars(
            select(SourceSnapshot).where(
                SourceSnapshot.id == snapshot_id,
                SourceSnapshot.project_id == project_id,
            )
        ).first()

    # --- generation / documents --------------------------------------------

    def create_generation_run(self, **kwargs: Any) -> GenerationRun:
        row = GenerationRun(**kwargs)
        self.db.add(row)
        self.db.flush()
        return row

    def create_document(self, **kwargs: Any) -> GeneratedDocument:
        row = GeneratedDocument(**kwargs)
        self.db.add(row)
        self.db.flush()
        return row

    def create_version(self, **kwargs: Any) -> DocumentVersion:
        row = DocumentVersion(**kwargs)
        self.db.add(row)
        self.db.flush()
        return row

    def set_current_version(
        self, document: GeneratedDocument, version: DocumentVersion
    ) -> None:
        document.current_version_id = version.id
        document.updated_at = datetime.now(timezone.utc)
        self.db.flush()

    def get_document(
        self, document_id: UUID, project_id: UUID
    ) -> GeneratedDocument | None:
        return self.db.scalars(
            select(GeneratedDocument).where(
                GeneratedDocument.id == document_id,
                GeneratedDocument.project_id == project_id,
            )
        ).first()

    def list_documents(self, project_id: UUID) -> list[GeneratedDocument]:
        return list(
            self.db.scalars(
                select(GeneratedDocument)
                .where(GeneratedDocument.project_id == project_id)
                .order_by(GeneratedDocument.created_at.desc())
            ).all()
        )

    def get_version(self, version_id: UUID) -> DocumentVersion | None:
        return self.db.scalars(
            select(DocumentVersion).where(DocumentVersion.id == version_id)
        ).first()

    def list_sections(self, version_id: UUID) -> list[DocumentSection]:
        return list(
            self.db.scalars(
                select(DocumentSection)
                .where(DocumentSection.document_version_id == version_id)
                .order_by(DocumentSection.sequence.asc())
            ).all()
        )

    def get_section(
        self, section_id: UUID, version_id: UUID
    ) -> DocumentSection | None:
        return self.db.scalars(
            select(DocumentSection).where(
                DocumentSection.id == section_id,
                DocumentSection.document_version_id == version_id,
            )
        ).first()

    def list_content_items(self, section_id: UUID) -> list[ContentItem]:
        return list(
            self.db.scalars(
                select(ContentItem)
                .where(ContentItem.section_id == section_id)
                .order_by(ContentItem.sort_order.asc())
            ).all()
        )

    def list_source_refs(self, content_item_id: UUID) -> list[DocumentSourceRef]:
        return list(
            self.db.scalars(
                select(DocumentSourceRef).where(
                    DocumentSourceRef.content_item_id == content_item_id
                )
            ).all()
        )

    def add_section(self, **kwargs: Any) -> DocumentSection:
        row = DocumentSection(**kwargs)
        self.db.add(row)
        self.db.flush()
        return row

    def add_content_item(self, **kwargs: Any) -> ContentItem:
        row = ContentItem(**kwargs)
        self.db.add(row)
        self.db.flush()
        return row

    def add_source_ref(self, **kwargs: Any) -> DocumentSourceRef:
        row = DocumentSourceRef(**kwargs)
        self.db.add(row)
        self.db.flush()
        return row

    def add_approval(self, **kwargs: Any) -> DocumentApproval:
        row = DocumentApproval(**kwargs)
        self.db.add(row)
        self.db.flush()
        return row

    def create_export_job(self, **kwargs: Any) -> ExportJob:
        row = ExportJob(**kwargs)
        self.db.add(row)
        self.db.flush()
        return row

    def get_export_job(
        self, export_id: UUID, project_id: UUID
    ) -> ExportJob | None:
        return self.db.scalars(
            select(ExportJob).where(
                ExportJob.id == export_id,
                ExportJob.project_id == project_id,
            )
        ).first()

    def commit(self) -> None:
        self.db.commit()
