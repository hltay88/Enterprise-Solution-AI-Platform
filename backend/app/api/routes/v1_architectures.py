"""Phase 3 plural architecture APIs under /api/v1 (Sprint 3.2 Task 11, ATLAS-031).

Review/approve stay Sprint 3.3. Singular MVP paths are aliased in
``v1_architecture.py``.
"""

from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession, EditorUser
from app.core.responses import success_response
from app.services.architecture_generation_service import ArchitectureGenerationService

router = APIRouter(prefix="/projects", tags=["v1-architectures"])


@router.post("/{project_id}/architectures/generate")
async def generate_architectures(
    project_id: UUID,
    current_user: EditorUser,
    db: DbSession,
) -> dict:
    result = await ArchitectureGenerationService(db).generate(
        project_id,
        current_user.id,
    )
    return success_response(data=result.model_dump(mode="json"), status_code=201)


@router.get("/{project_id}/architectures")
def list_architectures(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    result = ArchitectureGenerationService(db).list_options(project_id, current_user.id)
    return success_response(
        data=[item.model_dump(mode="json") for item in result],
    )


@router.get("/{project_id}/architectures/{architecture_id}")
def get_architecture_option(
    project_id: UUID,
    architecture_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    result = ArchitectureGenerationService(db).get_by_id(
        project_id,
        architecture_id,
        current_user.id,
    )
    return success_response(data=result.model_dump(mode="json"))


@router.get("/{project_id}/risks")
def list_risks(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
    architecture_id: UUID | None = Query(default=None),
) -> dict:
    result = ArchitectureGenerationService(db).list_risks(
        project_id,
        current_user.id,
        architecture_id=architecture_id,
    )
    return success_response(
        data=[item.model_dump(mode="json") for item in result],
    )


@router.get("/{project_id}/assumptions")
def list_assumptions(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
    architecture_id: UUID | None = Query(default=None),
) -> dict:
    result = ArchitectureGenerationService(db).list_assumptions(
        project_id,
        current_user.id,
        architecture_id=architecture_id,
    )
    return success_response(
        data=[item.model_dump(mode="json") for item in result],
    )
