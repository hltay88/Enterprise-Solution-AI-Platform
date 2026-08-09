"""Phase 3 singular architecture APIs (MVP aliases — ATLAS-034 / Sprint 3.2 Task 11).

Deprecated in favor of plural ``/architectures`` routes. Kept through Sprint 3.2
as thin aliases onto ``ArchitectureGenerationService``.
"""

from uuid import UUID

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession, EditorUser
from app.core.responses import success_response
from app.services.architecture_generation_service import ArchitectureGenerationService

router = APIRouter(prefix="/projects", tags=["v1-architecture"])


@router.get("/{project_id}/architecture")
def get_architecture(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    """Alias of latest plural architecture option (deprecated)."""
    result = ArchitectureGenerationService(db).get_latest(project_id, current_user.id)
    return success_response(data=result.model_dump(mode="json"))


@router.post("/{project_id}/architecture/generate")
async def generate_architecture(
    project_id: UUID,
    current_user: EditorUser,
    db: DbSession,
) -> dict:
    """Alias of ``POST …/architectures/generate`` (deprecated)."""
    result = await ArchitectureGenerationService(db).generate(
        project_id,
        current_user.id,
    )
    return success_response(data=result.model_dump(mode="json"), status_code=201)
