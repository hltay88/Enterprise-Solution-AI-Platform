"""Sprint 5.1 — Enterprise Knowledge Engine APIs under /api/v1/knowledge."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, File, Form, Query, UploadFile

from app.api.deps import ApproverUser, CurrentUser, DbSession, EditorUser
from app.core.responses import success_response
from app.schemas.knowledge import KnowledgeCreateIn, KnowledgeNewVersionIn, KnowledgeUpdateIn
from app.services.knowledge_service import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["v1-knowledge"])


@router.get("/taxonomy/domains")
def list_knowledge_domains(current_user: CurrentUser, db: DbSession) -> dict:
    _ = current_user
    rows = KnowledgeService(db).list_domains()
    return success_response(data=[row.model_dump(mode="json") for row in rows])


@router.get("/taxonomy/types")
def list_knowledge_types(current_user: CurrentUser, db: DbSession) -> dict:
    _ = current_user
    rows = KnowledgeService(db).list_types()
    return success_response(data=[row.model_dump(mode="json") for row in rows])


@router.get("")
def list_knowledge(
    current_user: CurrentUser,
    db: DbSession,
    status: str | None = Query(default=None),
    domain_code: str | None = Query(default=None),
    knowledge_type: str | None = Query(default=None),
    project_id: UUID | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict:
    _ = current_user
    rows = KnowledgeService(db).list_items(
        status=status,
        domain_code=domain_code,
        knowledge_type=knowledge_type,
        project_id=project_id,
        q=q,
        limit=limit,
        offset=offset,
    )
    return success_response(data=[row.model_dump(mode="json") for row in rows])


@router.post("")
async def create_knowledge(
    current_user: EditorUser,
    db: DbSession,
    title: str = Form(...),
    description: str | None = Form(default=None),
    knowledge_type: str | None = Form(default=None),
    domain_code: str | None = Form(default=None),
    project_id: UUID | None = Form(default=None),
    sensitivity: str = Form(default="internal"),
    content_text: str | None = Form(default=None),
    change_summary: str | None = Form(default=None),
    tags: str | None = Form(default=None, description="Comma-separated tags"),
    file: UploadFile | None = File(default=None),
) -> dict:
    tag_list = [t.strip() for t in (tags or "").split(",") if t.strip()]
    body = KnowledgeCreateIn(
        title=title,
        description=description,
        knowledge_type=knowledge_type,
        domain_code=domain_code,
        project_id=project_id,
        sensitivity=sensitivity,
        content_text=content_text,
        change_summary=change_summary,
        tags=tag_list,
    )
    result = await KnowledgeService(db).create(body, current_user, upload=file)
    return success_response(data=result.model_dump(mode="json"), status_code=201)


@router.post("/json")
async def create_knowledge_json(
    body: KnowledgeCreateIn,
    current_user: EditorUser,
    db: DbSession,
) -> dict:
    """JSON create without file upload (useful for tests and API clients)."""
    result = await KnowledgeService(db).create(body, current_user, upload=None)
    return success_response(data=result.model_dump(mode="json"), status_code=201)


@router.get("/{knowledge_id}")
def get_knowledge(knowledge_id: UUID, current_user: CurrentUser, db: DbSession) -> dict:
    _ = current_user
    result = KnowledgeService(db).get_item(knowledge_id)
    return success_response(data=result.model_dump(mode="json"))


@router.get("/{knowledge_id}/versions")
def list_knowledge_versions(knowledge_id: UUID, current_user: CurrentUser, db: DbSession) -> dict:
    _ = current_user
    result = KnowledgeService(db).get_item(knowledge_id, include_versions=True)
    return success_response(
        data=[row.model_dump(mode="json") for row in result.versions],
    )


@router.patch("/{knowledge_id}")
def update_knowledge(
    knowledge_id: UUID,
    body: KnowledgeUpdateIn,
    current_user: EditorUser,
    db: DbSession,
) -> dict:
    result = KnowledgeService(db).update_draft(knowledge_id, body, current_user)
    return success_response(data=result.model_dump(mode="json"))


@router.post("/{knowledge_id}/ingest")
async def ingest_knowledge_file(
    knowledge_id: UUID,
    current_user: EditorUser,
    db: DbSession,
    file: UploadFile = File(...),
) -> dict:
    result = await KnowledgeService(db).ingest_file(knowledge_id, current_user, file)
    return success_response(data=result.model_dump(mode="json"))


@router.post("/{knowledge_id}/submit-review")
def submit_knowledge_review(
    knowledge_id: UUID,
    current_user: EditorUser,
    db: DbSession,
) -> dict:
    result = KnowledgeService(db).submit_review(knowledge_id, current_user)
    return success_response(data=result.model_dump(mode="json"))


@router.post("/{knowledge_id}/approve")
def approve_knowledge(
    knowledge_id: UUID,
    current_user: ApproverUser,
    db: DbSession,
) -> dict:
    result = KnowledgeService(db).approve(knowledge_id, current_user)
    return success_response(data=result.model_dump(mode="json"))


@router.post("/{knowledge_id}/publish")
def publish_knowledge(
    knowledge_id: UUID,
    current_user: ApproverUser,
    db: DbSession,
) -> dict:
    result = KnowledgeService(db).publish(knowledge_id, current_user)
    return success_response(data=result.model_dump(mode="json"))


@router.post("/{knowledge_id}/deprecate")
def deprecate_knowledge(
    knowledge_id: UUID,
    current_user: ApproverUser,
    db: DbSession,
) -> dict:
    result = KnowledgeService(db).deprecate(knowledge_id, current_user)
    return success_response(data=result.model_dump(mode="json"))


@router.post("/{knowledge_id}/archive")
def archive_knowledge(
    knowledge_id: UUID,
    current_user: ApproverUser,
    db: DbSession,
) -> dict:
    result = KnowledgeService(db).archive(knowledge_id, current_user)
    return success_response(data=result.model_dump(mode="json"))


@router.post("/{knowledge_id}/return-draft")
def return_knowledge_draft(
    knowledge_id: UUID,
    current_user: EditorUser,
    db: DbSession,
) -> dict:
    result = KnowledgeService(db).return_to_draft(knowledge_id, current_user)
    return success_response(data=result.model_dump(mode="json"))


@router.post("/{knowledge_id}/new-version")
def new_knowledge_version(
    knowledge_id: UUID,
    current_user: EditorUser,
    db: DbSession,
    body: KnowledgeNewVersionIn | None = None,
) -> dict:
    result = KnowledgeService(db).new_version(knowledge_id, current_user, body)
    return success_response(data=result.model_dump(mode="json"), status_code=201)


@router.post("/{knowledge_id}/reindex")
def reindex_knowledge(
    knowledge_id: UUID,
    current_user: EditorUser,
    db: DbSession,
) -> dict:
    result = KnowledgeService(db).reindex(knowledge_id, current_user)
    return success_response(data=result)
