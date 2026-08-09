"""Sprint 4.4 document package API (ATLAS-050)."""

from uuid import UUID

from fastapi import APIRouter

from app.api.deps import ApproverUser, CurrentUser, DbSession, EditorUser
from app.core.responses import success_response
from app.schemas.package import PackageApproveIn, PackageAssembleIn
from app.services.package_service import PackageService

router = APIRouter(prefix="/projects", tags=["v1-packages"])


@router.post("/{project_id}/packages/assemble")
async def assemble_package(
    project_id: UUID,
    current_user: EditorUser,
    db: DbSession,
    body: PackageAssembleIn | None = None,
) -> dict:
    result = await PackageService(db).assemble(project_id, current_user.id, body)
    return success_response(data=result.model_dump(mode="json"), status_code=201)


@router.post("/{project_id}/packages/generate")
async def generate_package(
    project_id: UUID,
    current_user: EditorUser,
    db: DbSession,
    body: PackageAssembleIn | None = None,
) -> dict:
    """Alias for assemble (matches Phase 4 API outline)."""
    result = await PackageService(db).assemble(project_id, current_user.id, body)
    return success_response(data=result.model_dump(mode="json"), status_code=201)


@router.get("/{project_id}/packages")
def list_packages(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    result = PackageService(db).list_packages(project_id, current_user.id)
    return success_response(data=[row.model_dump(mode="json") for row in result])


@router.get("/{project_id}/packages/{package_id}")
def get_package(
    project_id: UUID,
    package_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    result = PackageService(db).get(project_id, package_id, current_user.id)
    return success_response(data=result.model_dump(mode="json"))


@router.post("/{project_id}/packages/{package_id}/validate")
def validate_package(
    project_id: UUID,
    package_id: UUID,
    current_user: EditorUser,
    db: DbSession,
) -> dict:
    result = PackageService(db).validate(project_id, package_id, current_user.id)
    return success_response(data=result.model_dump(mode="json"))


@router.post("/{project_id}/packages/{package_id}/approve")
def approve_package(
    project_id: UUID,
    package_id: UUID,
    current_user: ApproverUser,
    db: DbSession,
    body: PackageApproveIn | None = None,
) -> dict:
    result = PackageService(db).approve(project_id, package_id, current_user.id, body)
    return success_response(data=result.model_dump(mode="json"))


@router.post("/{project_id}/packages/{package_id}/export")
def export_package(
    project_id: UUID,
    package_id: UUID,
    current_user: EditorUser,
    db: DbSession,
) -> dict:
    result = PackageService(db).export_zip(project_id, package_id, current_user.id)
    return success_response(data=result.model_dump(mode="json"), status_code=201)
