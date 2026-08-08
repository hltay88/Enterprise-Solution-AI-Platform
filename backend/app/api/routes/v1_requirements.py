"""Phase 2 Draft RKM APIs under /api/v1 (Stages C + E)."""

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Query

from app.api.deps import CurrentUser, DbSession
from app.core.responses import success_response
from app.schemas.governance import ApproveIn, PublishIn, ReviewIn, VersionForkIn
from app.services.rkm_generation_service import RkmGenerationService, run_rkm_generate_job
from app.services.rkm_governance_service import RkmGovernanceService

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
    draft = RkmGovernanceService(db).get_by_status(project_id, current_user.id, status)
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


@router.get("/{project_id}/requirements/compare")
def compare_requirement_versions(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
    from_version: str = Query(..., alias="from"),
    to_version: str = Query(..., alias="to"),
) -> dict:
    result = RkmGovernanceService(db).compare(
        project_id,
        current_user.id,
        from_version,
        to_version,
    )
    return success_response(data=result.model_dump(mode="json"))


@router.post("/{project_id}/requirements/review")
def review_requirements(
    project_id: UUID,
    body: ReviewIn,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    result = RkmGovernanceService(db).review(
        project_id,
        current_user.id,
        body,
        current_user,
    )
    return success_response(data=result.model_dump(mode="json"), status_code=201)


@router.post("/{project_id}/requirements/approve")
def approve_requirements(
    project_id: UUID,
    body: ApproveIn,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    result = RkmGovernanceService(db).approve(
        project_id,
        current_user.id,
        body,
        current_user,
    )
    return success_response(data=result.model_dump(mode="json"), status_code=201)


@router.post("/{project_id}/requirements/publish")
def publish_requirements(
    project_id: UUID,
    body: PublishIn,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    result = RkmGovernanceService(db).publish(
        project_id,
        current_user.id,
        body,
        current_user,
    )
    return success_response(data=result.model_dump(mode="json"), status_code=201)


@router.post("/{project_id}/requirements/version")
def fork_requirement_version(
    project_id: UUID,
    body: VersionForkIn,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    result = RkmGovernanceService(db).fork_version(
        project_id,
        current_user.id,
        body,
        current_user,
    )
    return success_response(data=result.model_dump(mode="json"), status_code=201)
