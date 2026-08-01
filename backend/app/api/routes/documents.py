"""Document upload and list routes."""

from uuid import UUID

from fastapi import APIRouter, File, UploadFile

from app.api.deps import CurrentUser, DbSession
from app.core.responses import success_response
from app.services.document_service import DocumentService

router = APIRouter(prefix="/projects", tags=["documents"])


@router.get("/{project_id}/documents")
def list_documents(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    documents = DocumentService(db).list_for_project(project_id, current_user.id)
    return success_response(
        data=[document.model_dump(mode="json") for document in documents],
    )


@router.post("/{project_id}/upload")
async def upload_document(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
    file: UploadFile = File(...),
) -> dict:
    document = await DocumentService(db).upload(
        project_id=project_id,
        user_id=current_user.id,
        upload=file,
    )
    return success_response(data=document.model_dump(mode="json"), status_code=201)
