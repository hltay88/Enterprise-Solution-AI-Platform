"""Clarification question routes."""

from uuid import UUID

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.core.responses import success_response
from app.services.clarification_service import ClarificationService

router = APIRouter(prefix="/projects", tags=["clarifications"])


@router.get("/{project_id}/clarifications")
def list_clarifications(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    questions = ClarificationService(db).list_for_project(project_id, current_user.id)
    return success_response(
        data=[question.model_dump(mode="json") for question in questions],
    )


@router.post("/{project_id}/clarification")
async def generate_clarifications(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    questions = await ClarificationService(db).generate(project_id, current_user.id)
    return success_response(
        data=[question.model_dump(mode="json") for question in questions],
        status_code=201,
    )
