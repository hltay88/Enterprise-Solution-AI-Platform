"""Phase 3 plural architecture APIs under /api/v1 (ATLAS-031).

Sprint 3.2: generate/list/get + risks/assumptions.
Sprint 3.3 Task 6: explicit product mapping routes.
Review/approve stay later in 3.3. Singular MVP paths are aliased in
``v1_architecture.py``.
"""

from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession, EditorUser
from app.core.responses import success_response
from app.schemas.vendor_bom import (
    ArchitectureProductMapIn,
    ArchitectureProductMappingUpdateIn,
)
from app.services.architecture_generation_service import ArchitectureGenerationService
from app.services.architecture_product_mapping_service import (
    ArchitectureProductMappingService,
)

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


@router.post("/{project_id}/architectures/{architecture_id}/map-products")
def map_architecture_products(
    project_id: UUID,
    architecture_id: UUID,
    current_user: EditorUser,
    db: DbSession,
    body: ArchitectureProductMapIn | None = None,
) -> dict:
    """Explicit Map products action (ATLAS-035 — not run on generate)."""
    payload = body or ArchitectureProductMapIn(architecture_id=architecture_id)
    payload = payload.model_copy(update={"architecture_id": architecture_id})
    result = ArchitectureProductMappingService(db).map_products(
        project_id,
        current_user.id,
        payload,
    )
    return success_response(data=result.model_dump(mode="json"), status_code=201)


@router.get("/{project_id}/architectures/{architecture_id}/product-mappings")
def list_architecture_product_mappings(
    project_id: UUID,
    architecture_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    result = ArchitectureProductMappingService(db).list_mappings(
        project_id,
        current_user.id,
        architecture_id,
    )
    return success_response(
        data=[item.model_dump(mode="json") for item in result],
    )


@router.patch("/{project_id}/product-mappings/{mapping_id}")
def update_product_mapping(
    project_id: UUID,
    mapping_id: UUID,
    body: ArchitectureProductMappingUpdateIn,
    current_user: EditorUser,
    db: DbSession,
) -> dict:
    result = ArchitectureProductMappingService(db).update_mapping(
        project_id,
        current_user.id,
        mapping_id,
        body,
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
