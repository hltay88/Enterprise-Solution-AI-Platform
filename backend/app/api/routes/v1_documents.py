"""Phase 2 document ingest APIs under /api/v1 (ATLAS-026 / ATLAS-027 / ATLAS-029)."""

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, File, Form, UploadFile

from app.api.deps import CurrentUser, DbSession, EditorUser
from app.core.exceptions import ValidationAppError
from app.core.responses import success_response
from app.services.document_ingest_service import DocumentIngestService, run_extract_job

router = APIRouter(tags=["v1-documents"])


@router.post("/documents/upload")
async def upload_documents(
    background_tasks: BackgroundTasks,
    current_user: EditorUser,
    db: DbSession,
    project_id: UUID = Form(...),
    files: list[UploadFile] = File(...),
) -> dict:
    if not files:
        raise ValidationAppError("At least one file is required")

    result, job_ids = await DocumentIngestService(db).upload_batch(
        project_id=project_id,
        user_id=current_user.id,
        uploads=files,
    )
    for job_id in job_ids:
        background_tasks.add_task(run_extract_job, job_id)

    return success_response(data=result.model_dump(mode="json"), status_code=202)


@router.get("/documents/{document_id}")
def get_document(
    document_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    document = DocumentIngestService(db).get_document(document_id, current_user.id)
    return success_response(data=document.model_dump(mode="json"))


@router.get("/projects/{project_id}/documents")
def list_project_documents(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    documents = DocumentIngestService(db).list_for_project(project_id, current_user.id)
    return success_response(
        data=[document.model_dump(mode="json") for document in documents],
    )


@router.delete("/documents/{document_id}")
def delete_document(
    document_id: UUID,
    current_user: EditorUser,
    db: DbSession,
) -> dict:
    DocumentIngestService(db).archive_document(document_id, current_user.id)
    return success_response(data=None, message="Document archived")


@router.get("/jobs/{job_id}")
def get_job(
    job_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    job = DocumentIngestService(db).get_job(job_id, current_user.id)
    return success_response(data=job.model_dump(mode="json"))
