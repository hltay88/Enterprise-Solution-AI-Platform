"""Phase 3 architecture recommendation APIs under /api/v1."""

from uuid import UUID

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession, EditorUser
from app.core.responses import success_response
from app.services.architecture_service import ArchitectureService

router = APIRouter(prefix="/projects", tags=["v1-architecture"])


@router.get("/{project_id}/architecture")
def get_architecture(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    result = ArchitectureService(db).get_latest(project_id, current_user.id)
    return success_response(data=result.model_dump(mode="json"))


@router.post("/{project_id}/architecture/generate")
async def generate_architecture(
    project_id: UUID,
    current_user: EditorUser,
    db: DbSession,
) -> dict:
    result = await ArchitectureService(db).generate(project_id, current_user.id)
    return success_response(data=result.model_dump(mode="json"), status_code=201)
