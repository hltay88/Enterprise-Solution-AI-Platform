"""Requirement document persistence."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.requirement_document import RequirementDocument


class DocumentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_project(self, project_id: UUID, *, include_archived: bool = False) -> list[RequirementDocument]:
        statement = select(RequirementDocument).where(RequirementDocument.project_id == project_id)
        if not include_archived:
            statement = statement.where(RequirementDocument.archived_at.is_(None))
        statement = statement.order_by(RequirementDocument.uploaded_at.desc())
        return list(self.db.scalars(statement).all())

    def get(self, document_id: UUID) -> RequirementDocument | None:
        statement = select(RequirementDocument).where(RequirementDocument.id == document_id)
        return self.db.scalars(statement).first()

    def get_for_project(
        self,
        project_id: UUID,
        document_id: UUID,
        *,
        include_archived: bool = False,
    ) -> RequirementDocument | None:
        statement = select(RequirementDocument).where(
            RequirementDocument.id == document_id,
            RequirementDocument.project_id == project_id,
        )
        if not include_archived:
            statement = statement.where(RequirementDocument.archived_at.is_(None))
        return self.db.scalars(statement).first()

    def find_by_sha256(self, project_id: UUID, content_sha256: str) -> RequirementDocument | None:
        statement = (
            select(RequirementDocument)
            .where(
                RequirementDocument.project_id == project_id,
                RequirementDocument.content_sha256 == content_sha256,
                RequirementDocument.archived_at.is_(None),
            )
            .order_by(RequirementDocument.uploaded_at.desc())
        )
        return self.db.scalars(statement).first()

    def delete(self, document: RequirementDocument) -> None:
        self.db.delete(document)
        self.db.commit()

    def soft_archive(self, document: RequirementDocument) -> RequirementDocument:
        from datetime import datetime, timezone

        document.archived_at = datetime.now(timezone.utc)
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def create(
        self,
        *,
        project_id: UUID,
        filename: str,
        file_type: str,
        storage_path: str,
        extracted_text: str | None,
        content_sha256: str | None = None,
        file_size_bytes: int | None = None,
        mime_type: str | None = None,
        status: str = "completed",
        page_count: int | None = None,
        language: str | None = None,
        ocr_used: bool = False,
        needs_manual_review: bool = False,
        error_message: str | None = None,
    ) -> RequirementDocument:
        document = RequirementDocument(
            project_id=project_id,
            filename=filename,
            file_type=file_type,
            storage_path=storage_path,
            extracted_text=extracted_text,
            content_sha256=content_sha256,
            file_size_bytes=file_size_bytes,
            mime_type=mime_type,
            status=status,
            page_count=page_count,
            language=language,
            ocr_used=ocr_used,
            needs_manual_review=needs_manual_review,
            error_message=error_message,
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def save(self, document: RequirementDocument) -> RequirementDocument:
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document
