"""Vendor catalogue import + search (Sprint 3.3 Task 3, ATLAS-038).

Global catalogue (not project-scoped). Never invents SKU specifications.
Marks products stale when source_date is older than STALE_AFTER_DAYS unless
the import already set is_stale.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.vendor_bom import VendorCatalogue, VendorProduct
from app.repositories.vendor_catalogue_repository import VendorCatalogueRepository
from app.schemas.vendor_bom import (
    ProductCapabilityOut,
    VendorCatalogueImportIn,
    VendorCatalogueOut,
    VendorCatalogueSearchOut,
    VendorProductOut,
    VendorProductSummaryOut,
)

STALE_AFTER_DAYS = 365


def _is_stale(source_date: date | None, explicit: bool) -> bool:
    if explicit:
        return True
    if source_date is None:
        return False
    cutoff = date.today() - timedelta(days=STALE_AFTER_DAYS)
    return source_date < cutoff


class VendorCatalogueService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.catalogues = VendorCatalogueRepository(db)

    def import_catalogue(
        self,
        body: VendorCatalogueImportIn,
        user_id: UUID,
    ) -> VendorCatalogueOut:
        products: list[dict] = []
        for item in body.products:
            data = item.model_dump(mode="python")
            data["is_stale"] = _is_stale(item.source_date or body.source_date, item.is_stale)
            # Persist only provided specifications — never fabricate.
            products.append(data)

        try:
            catalogue = self.catalogues.create_catalogue_tree(
                name=body.name or body.source,
                source=body.source,
                source_date=body.source_date,
                version_label=body.version_label,
                region=body.region,
                notes=body.notes,
                imported_by=user_id,
                products=products,
                payload_json={
                    "imported_at": datetime.now(timezone.utc).isoformat(),
                    "product_count": len(products),
                },
                commit=True,
            )
        except ValueError as exc:
            raise ValidationAppError(str(exc)) from exc

        return self._catalogue_out(catalogue, include_products=True)

    def get_catalogue(self, catalogue_id: UUID) -> VendorCatalogueOut:
        catalogue = self.catalogues.get_catalogue(catalogue_id)
        if catalogue is None:
            raise NotFoundError("Vendor catalogue not found")
        return self._catalogue_out(catalogue, include_products=True)

    def search(
        self,
        *,
        query: str = "",
        vendor: str | None = None,
        category: str | None = None,
        region: str | None = None,
        catalogue_id: UUID | None = None,
        include_stale: bool = False,
        limit: int = 50,
    ) -> VendorCatalogueSearchOut:
        rows = self.catalogues.search_products(
            query=query,
            vendor=vendor,
            category=category,
            region=region,
            catalogue_id=catalogue_id,
            include_stale=include_stale,
            limit=limit,
        )
        return VendorCatalogueSearchOut(
            query=query,
            total=len(rows),
            products=[self._product_summary(row) for row in rows],
        )

    def _catalogue_out(
        self,
        catalogue: VendorCatalogue,
        *,
        include_products: bool,
    ) -> VendorCatalogueOut:
        products_out: list[VendorProductOut] = []
        if include_products:
            for product in self.catalogues.list_products(catalogue.id):
                products_out.append(self._product_out(product))
        return VendorCatalogueOut(
            id=catalogue.id,
            name=catalogue.name or "",
            source=catalogue.source,
            source_date=catalogue.source_date,
            version_label=catalogue.version_label,
            region=catalogue.region,
            notes=catalogue.notes,
            product_count=len(products_out)
            if include_products
            else self.catalogues.count_products(catalogue.id),
            created_at=catalogue.created_at,
            products=products_out,
        )

    def _product_out(self, product: VendorProduct) -> VendorProductOut:
        caps = [
            ProductCapabilityOut(
                id=cap.id,
                product_id=cap.product_id,
                capability_code=cap.capability_code,
                capability_label=cap.capability_label or "",
                details=dict(cap.details or {}),
                confidence=float(cap.confidence or 0.0),
                created_at=cap.created_at,
            )
            for cap in self.catalogues.list_capabilities(product.id)
        ]
        return VendorProductOut(
            id=product.id,
            catalogue_id=product.catalogue_id,
            vendor=product.vendor,
            product_family=product.product_family or "",
            product_model=product.product_model,
            category=product.category or "",
            capabilities=caps,
            specifications=dict(product.specifications or {}),
            licensing=product.licensing,
            lifecycle_status=product.lifecycle_status or "unknown",
            source=product.source,
            source_date=product.source_date,
            region=product.region,
            confidence=float(product.confidence or 0.0),
            is_stale=bool(product.is_stale),
            created_at=product.created_at,
            updated_at=product.updated_at,
        )

    def _product_summary(self, product: VendorProduct) -> VendorProductSummaryOut:
        return VendorProductSummaryOut(
            id=product.id,
            catalogue_id=product.catalogue_id,
            vendor=product.vendor,
            product_family=product.product_family or "",
            product_model=product.product_model,
            category=product.category or "",
            lifecycle_status=product.lifecycle_status or "unknown",
            source=product.source,
            source_date=product.source_date,
            region=product.region,
            confidence=float(product.confidence or 0.0),
            is_stale=bool(product.is_stale),
        )
