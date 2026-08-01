"""Document upload and listing logic."""

from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.repositories.document_repository import DocumentRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.document import DocumentSummary
from app.services.storage_service import StorageService
from app.services.text_extraction import detect_file_type, extract_text

PREVIEW_CHARS = 500


class DocumentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = ProjectRepository(db)
        self.documents = DocumentRepository(db)
        self.storage = StorageService()

    def list_for_project(self, project_id: UUID, user_id: UUID) -> list[DocumentSummary]:
        self._require_project(project_id, user_id)
        rows = self.documents.list_for_project(project_id)
        return [_to_summary(row) for row in rows]

    async def upload(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        upload: UploadFile,
    ) -> DocumentSummary:
        self._require_project(project_id, user_id)

        if not upload.filename:
            raise ValidationAppError("Filename is required")

        file_type = detect_file_type(upload.filename)
        relative_path, _size = await self.storage.save_upload(
            project_id=project_id,
            upload=upload,
        )
        absolute_path = self.storage.absolute_path(relative_path)

        try:
            text = extract_text(absolute_path, file_type)
        except ValidationAppError:
            absolute_path.unlink(missing_ok=True)
            raise
        except Exception as exc:
            absolute_path.unlink(missing_ok=True)
            raise ValidationAppError("Failed to extract text from uploaded file") from exc

        if not text:
            absolute_path.unlink(missing_ok=True)
            raise ValidationAppError("No extractable text found in the uploaded file")

        document = self.documents.create(
            project_id=project_id,
            filename=upload.filename,
            file_type=file_type,
            storage_path=relative_path,
            extracted_text=text,
        )
        return _to_summary(document)

    def delete(
        self,
        *,
        project_id: UUID,
        document_id: UUID,
        user_id: UUID,
    ) -> None:
        self._require_project(project_id, user_id)
        document = self.documents.get_for_project(project_id, document_id)
        if document is None:
            raise NotFoundError("Document not found")

        storage_path = document.storage_path
        self.documents.delete(document)
        try:
            self.storage.delete_file(storage_path)
        except ValidationAppError:
            # DB row is already removed; ignore invalid legacy paths.
            pass

    def _require_project(self, project_id: UUID, user_id: UUID) -> None:
        project = self.projects.get_for_user(project_id, user_id)
        if project is None:
            raise NotFoundError("Project not found")


def _to_summary(document) -> DocumentSummary:
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
    )
