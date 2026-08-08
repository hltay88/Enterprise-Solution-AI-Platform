"""Phase 2 Stage D — gap analysis and RKM clarification APIs under /api/v1."""

from uuid import UUID

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.core.responses import success_response
from app.schemas.gap import ClarificationAnswerBatchIn
from app.services.gap_analysis_service import GapAnalysisService

router = APIRouter(prefix="/projects", tags=["v1-gap"])


@router.post("/{project_id}/requirements/gap-analysis")
def run_gap_analysis(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    report = GapAnalysisService(db).run_gap_analysis(project_id, current_user.id)
    return success_response(data=report.model_dump(mode="json"), status_code=201)


@router.get("/{project_id}/clarification")
def list_clarifications(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    items = GapAnalysisService(db).list_clarifications(project_id, current_user.id)
    return success_response(data=[item.model_dump(mode="json") for item in items])


@router.post("/{project_id}/clarification/generate")
def generate_clarifications(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    items = GapAnalysisService(db).generate_clarifications(project_id, current_user.id)
    return success_response(
        data=[item.model_dump(mode="json") for item in items],
        status_code=201,
    )


@router.post("/{project_id}/clarification/answer")
def answer_clarifications(
    project_id: UUID,
    body: ClarificationAnswerBatchIn,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    result = GapAnalysisService(db).answer_clarifications(
        project_id,
        current_user.id,
        body,
    )
    return success_response(data=result.model_dump(mode="json"), status_code=201)
