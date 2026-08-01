"""Requirement analysis routes."""

from uuid import UUID

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.core.responses import success_response
from app.services.analysis_service import AnalysisService

router = APIRouter(prefix="/projects", tags=["analysis"])


@router.get("/{project_id}/analysis")
def get_analysis(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    analysis = AnalysisService(db).get_latest(project_id, current_user.id)
    return success_response(data=analysis.model_dump(mode="json"))


@router.post("/{project_id}/analyze")
async def analyze_project(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    analysis = await AnalysisService(db).analyze(project_id, current_user.id)
    return success_response(data=analysis.model_dump(mode="json"), status_code=201)
