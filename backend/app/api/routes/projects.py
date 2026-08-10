"""Project CRUD routes."""

from uuid import UUID

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.core.responses import success_response
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


def _tenant_id(user) -> UUID | None:
    return getattr(user, "active_tenant_id", None)


@router.get("")
def list_projects(current_user: CurrentUser, db: DbSession) -> dict:
    projects = ProjectService(db).list_for_user(
        current_user.id,
        tenant_id=_tenant_id(current_user),
    )
    return success_response(
        data=[project.model_dump(mode="json") for project in projects],
    )


@router.post("")
def create_project(
    body: ProjectCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    project = ProjectService(db).create(
        current_user.id,
        body,
        default_account_manager=current_user.name,
        tenant_id=_tenant_id(current_user),
    )
    return success_response(data=project.model_dump(mode="json"), status_code=201)


@router.get("/{project_id}")
def get_project(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    project = ProjectService(db).get_for_user(
        project_id,
        current_user.id,
        tenant_id=_tenant_id(current_user),
    )
    return success_response(data=project.model_dump(mode="json"))


@router.put("/{project_id}")
def update_project(
    project_id: UUID,
    body: ProjectUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    project = ProjectService(db).update(project_id, current_user.id, body)
    return success_response(data=project.model_dump(mode="json"))


@router.delete("/{project_id}")
def delete_project(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    ProjectService(db).delete(project_id, current_user.id)
    return success_response(data=None, message="Project deleted")
