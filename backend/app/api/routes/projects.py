"""Project routes (Dashboard read path)."""

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.core.responses import success_response
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("")
def list_projects(current_user: CurrentUser, db: DbSession) -> dict:
    """Return the current user's projects for the dashboard."""
    projects = ProjectService(db).list_for_user(current_user.id)
    return success_response(
        data=[project.model_dump(mode="json") for project in projects],
    )
