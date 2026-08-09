"""Global vendor catalogue APIs under /api/v1 (Sprint 3.3 Task 3, ATLAS-031/038).

Not project-scoped. Import requires Editor+; search/get require authentication.
"""

from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession, EditorUser
from app.core.responses import success_response
from app.schemas.vendor_bom import VendorCatalogueImportIn
from app.services.vendor_analytics_service import VendorAnalyticsService
from app.services.vendor_catalogue_service import VendorCatalogueService

router = APIRouter(prefix="/vendors", tags=["v1-vendors"])


@router.post("/catalogue/import")
def import_catalogue(
    body: VendorCatalogueImportIn,
    current_user: EditorUser,
    db: DbSession,
) -> dict:
    result = VendorCatalogueService(db).import_catalogue(body, current_user.id)
    return success_response(data=result.model_dump(mode="json"), status_code=201)


@router.post("/catalogue/seed")
def seed_catalogue(
    current_user: EditorUser,
    db: DbSession,
    force: bool = Query(default=False),
) -> dict:
    """Load the frozen Atlas seed catalogue (idempotent unless force=true)."""
    result = VendorCatalogueService(db).seed_default_catalogue(
        current_user.id,
        force=force,
    )
    return success_response(data=result.model_dump(mode="json"), status_code=201)


@router.get("/catalogue/search")
def search_catalogue(
    current_user: CurrentUser,
    db: DbSession,
    q: str = Query(default=""),
    vendor: str | None = Query(default=None),
    category: str | None = Query(default=None),
    region: str | None = Query(default=None),
    catalogue_id: UUID | None = Query(default=None),
    include_stale: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
) -> dict:
    result = VendorCatalogueService(db).search(
        query=q,
        vendor=vendor,
        category=category,
        region=region,
        catalogue_id=catalogue_id,
        include_stale=include_stale,
        limit=limit,
    )
    return success_response(data=result.model_dump(mode="json"))


@router.get("/catalogue/analytics")
def catalogue_analytics(
    current_user: CurrentUser,
    db: DbSession,
    catalogue_id: UUID | None = Query(default=None),
) -> dict:
    """Catalogue health aggregates (stale/lifecycle/vendor/category)."""
    result = VendorAnalyticsService(db).catalogue_analytics(catalogue_id=catalogue_id)
    return success_response(data=result.model_dump(mode="json"))


@router.get("/catalogue/{catalogue_id}")
def get_catalogue(
    catalogue_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    result = VendorCatalogueService(db).get_catalogue(catalogue_id)
    return success_response(data=result.model_dump(mode="json"))
