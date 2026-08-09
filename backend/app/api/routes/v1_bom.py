"""Project-scoped BOM APIs under /api/v1 (Sprint 3.3 Task 7, ATLAS-031/039).

Import creates an immutable evidence snapshot. Validation lands in Task 8.
"""

from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession, EditorUser
from app.core.responses import success_response
from app.schemas.vendor_bom import BomImportIn
from app.services.bom_service import BomService

router = APIRouter(prefix="/projects", tags=["v1-bom"])


@router.post("/{project_id}/bom/import")
def import_bom(
    project_id: UUID,
    body: BomImportIn,
    current_user: EditorUser,
    db: DbSession,
) -> dict:
    result = BomService(db).import_bom(project_id, current_user.id, body)
    return success_response(data=result.model_dump(mode="json"), status_code=201)


@router.get("/{project_id}/bom")
def list_bom_imports(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
    limit: int = Query(default=50, ge=1, le=200),
) -> dict:
    result = BomService(db).list_imports(project_id, current_user.id, limit=limit)
    return success_response(
        data=[item.model_dump(mode="json") for item in result],
    )


@router.get("/{project_id}/bom/{bom_import_id}")
def get_bom_import(
    project_id: UUID,
    bom_import_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    result = BomService(db).get_import(project_id, current_user.id, bom_import_id)
    return success_response(data=result.model_dump(mode="json"))
