"""Requirement document persistence."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.requirement_document import RequirementDocument


class DocumentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_project(self, project_id: UUID) -> list[RequirementDocument]:
        statement = (
            select(RequirementDocument)
            .where(RequirementDocument.project_id == project_id)
            .order_by(RequirementDocument.uploaded_at.desc())
        )
        return list(self.db.scalars(statement).all())

    def create(
        self,
        *,
        project_id: UUID,
        filename: str,
        file_type: str,
        storage_path: str,
        extracted_text: str | None,
    ) -> RequirementDocument:
        document = RequirementDocument(
            project_id=project_id,
            filename=filename,
            file_type=file_type,
            storage_path=storage_path,
            extracted_text=extracted_text,
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document
