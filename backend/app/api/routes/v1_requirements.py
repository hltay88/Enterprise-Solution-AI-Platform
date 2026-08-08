"""Phase 2 Draft RKM APIs under /api/v1 (Stage C)."""

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Query

from app.api.deps import CurrentUser, DbSession
from app.core.responses import success_response
from app.services.rkm_generation_service import RkmGenerationService, run_rkm_generate_job

router = APIRouter(prefix="/projects", tags=["v1-requirements"])


@router.post("/{project_id}/requirements/analyze")
async def analyze_requirements(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    accepted, job_id = RkmGenerationService(db).start_analyze(
        project_id=project_id,
        user_id=current_user.id,
    )
    background_tasks.add_task(run_rkm_generate_job, job_id, current_user.id)
    return success_response(data=accepted.model_dump(mode="json"), status_code=202)


@router.get("/{project_id}/requirements")
def get_requirements(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
    status: str | None = Query(default="draft"),
) -> dict:
    service = RkmGenerationService(db)
    # Stage C: Draft only. Published path arrives in Stage E.
    if status and status.lower() not in {"draft", "ai_generated", "active"}:
        # Still return active draft for now; publish gate is Stage E.
        pass
    draft = service.get_active_draft(project_id, current_user.id)
    return success_response(data=draft.model_dump(mode="json"))


@router.get("/{project_id}/requirements/versions")
def list_requirement_versions(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    versions = RkmGenerationService(db).list_versions(project_id, current_user.id)
    return success_response(data=[row.model_dump(mode="json") for row in versions])


@router.get("/{project_id}/requirements/versions/{version}")
def get_requirement_version(
    project_id: UUID,
    version: str,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    draft = RkmGenerationService(db).get_version(project_id, version, current_user.id)
    return success_response(data=draft.model_dump(mode="json"))
