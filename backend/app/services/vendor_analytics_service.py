"""Vendor analytics service (Phase 3 P2).

Catalogue health + project/architecture mapping analytics. Never invents SKUs
or commercial figures (ATLAS-035/038).
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.repositories.architecture_option_repository import ArchitectureOptionRepository
from app.repositories.architecture_product_mapping_repository import (
    ArchitectureProductMappingRepository,
)
from app.repositories.project_repository import ProjectRepository
from app.repositories.vendor_catalogue_repository import VendorCatalogueRepository
from app.schemas.vendor_bom import (
    NamedCountOut,
    VendorAnalyticsBundleOut,
    VendorCatalogueAnalyticsOut,
    VendorMappingAnalyticsOut,
)
from app.services.vendor_analytics import (
    catalogue_analytics_from_products,
    mapping_analytics_from_rows,
)


class VendorAnalyticsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = ProjectRepository(db)
        self.catalogues = VendorCatalogueRepository(db)
        self.mappings = ArchitectureProductMappingRepository(db)
        self.architectures = ArchitectureOptionRepository(db)

    def catalogue_analytics(
        self,
        *,
        catalogue_id: UUID | None = None,
    ) -> VendorCatalogueAnalyticsOut:
        if catalogue_id is not None:
            catalogue = self.catalogues.get_catalogue(catalogue_id)
            if catalogue is None:
                raise NotFoundError("Vendor catalogue not found")
            products = self.catalogues.list_products(catalogue_id, include_stale=True)
            raw = catalogue_analytics_from_products(
                [self._product_dict(item) for item in products],
                catalogue_id=str(catalogue.id),
                catalogue_name=catalogue.name,
            )
            return self._catalogue_out(raw)

        catalogues = self.catalogues.list_catalogues(limit=20)
        if not catalogues:
            return VendorCatalogueAnalyticsOut(
                warnings=["No vendor catalogues imported yet — seed or import first"],
            )
        # Default: latest catalogue (seed/import most recent).
        catalogue = catalogues[0]
        products = self.catalogues.list_products(catalogue.id, include_stale=True)
        raw = catalogue_analytics_from_products(
            [self._product_dict(item) for item in products],
            catalogue_id=str(catalogue.id),
            catalogue_name=catalogue.name,
        )
        return self._catalogue_out(raw)

    def mapping_analytics(
        self,
        project_id: UUID,
        user_id: UUID,
        *,
        architecture_id: UUID | None = None,
    ) -> VendorMappingAnalyticsOut:
        self._require_project(project_id, user_id)
        component_ids: list[str] = []
        if architecture_id is not None:
            option = self.architectures.get_for_project(architecture_id, project_id)
            if option is None:
                raise NotFoundError("Architecture option not found")
            rows = self.mappings.list_for_architecture(architecture_id)
            component_ids = [
                str(item.id) for item in self.architectures.list_components(architecture_id)
            ]
        else:
            rows = self.mappings.list_for_project(project_id)
            for option in self.architectures.list_for_project(project_id):
                for component in self.architectures.list_components(option.id):
                    component_ids.append(str(component.id))

        product_ids = [row.product_id for row in rows if row.product_id]
        products = self.mappings.get_products_by_ids(product_ids)
        raw = mapping_analytics_from_rows(
            [
                {
                    "product_id": str(row.product_id),
                    "component_id": str(row.component_id),
                    "status": row.status,
                    "preference_kind": row.preference_kind,
                    "fit_score": row.fit_score,
                    "vendor": None,
                }
                for row in rows
            ],
            {
                str(pid): self._product_dict(product)
                for pid, product in products.items()
            },
            project_id=str(project_id),
            architecture_id=str(architecture_id) if architecture_id else None,
            component_ids=component_ids,
        )
        return self._mapping_out(raw)

    def project_bundle(
        self,
        project_id: UUID,
        user_id: UUID,
        *,
        architecture_id: UUID | None = None,
        catalogue_id: UUID | None = None,
    ) -> VendorAnalyticsBundleOut:
        return VendorAnalyticsBundleOut(
            catalogue=self.catalogue_analytics(catalogue_id=catalogue_id),
            mappings=self.mapping_analytics(
                project_id,
                user_id,
                architecture_id=architecture_id,
            ),
        )

    @staticmethod
    def _product_dict(product) -> dict:
        return {
            "vendor": getattr(product, "vendor", "") or "",
            "category": getattr(product, "category", "") or "",
            "lifecycle_status": getattr(product, "lifecycle_status", "") or "unknown",
            "region": getattr(product, "region", None),
            "confidence": getattr(product, "confidence", 0.0),
            "is_stale": bool(getattr(product, "is_stale", False)),
        }

    @staticmethod
    def _named(items: list[dict]) -> list[NamedCountOut]:
        return [NamedCountOut(key=str(i["key"]), count=int(i["count"])) for i in items]

    def _catalogue_out(self, raw: dict) -> VendorCatalogueAnalyticsOut:
        catalogue_id = raw.get("catalogue_id")
        return VendorCatalogueAnalyticsOut(
            catalogue_id=UUID(str(catalogue_id)) if catalogue_id else None,
            catalogue_name=raw.get("catalogue_name"),
            product_count=int(raw.get("product_count") or 0),
            stale_count=int(raw.get("stale_count") or 0),
            stale_ratio=float(raw.get("stale_ratio") or 0),
            average_confidence=raw.get("average_confidence"),
            by_vendor=self._named(raw.get("by_vendor") or []),
            by_category=self._named(raw.get("by_category") or []),
            by_lifecycle=self._named(raw.get("by_lifecycle") or []),
            by_region=self._named(raw.get("by_region") or []),
            warnings=list(raw.get("warnings") or []),
        )

    def _mapping_out(self, raw: dict) -> VendorMappingAnalyticsOut:
        arch = raw.get("architecture_id")
        unmatched_ids: list[UUID] = []
        for item in raw.get("unmatched_component_ids") or []:
            try:
                unmatched_ids.append(UUID(str(item)))
            except (TypeError, ValueError):
                continue
        return VendorMappingAnalyticsOut(
            project_id=UUID(str(raw["project_id"])),
            architecture_id=UUID(str(arch)) if arch else None,
            mapping_count=int(raw.get("mapping_count") or 0),
            by_status=self._named(raw.get("by_status") or []),
            by_preference_kind=self._named(raw.get("by_preference_kind") or []),
            by_vendor=self._named(raw.get("by_vendor") or []),
            by_lifecycle=self._named(raw.get("by_lifecycle") or []),
            fit_score_buckets=self._named(raw.get("fit_score_buckets") or []),
            component_count=int(raw.get("component_count") or 0),
            mapped_component_count=int(raw.get("mapped_component_count") or 0),
            unmatched_component_count=int(raw.get("unmatched_component_count") or 0),
            unmatched_component_ids=unmatched_ids,
            coverage_ratio=float(raw.get("coverage_ratio") or 0),
            stale_mapped_count=int(raw.get("stale_mapped_count") or 0),
            average_fit_score=raw.get("average_fit_score"),
            selected_count=int(raw.get("selected_count") or 0),
            candidate_count=int(raw.get("candidate_count") or 0),
            rejected_count=int(raw.get("rejected_count") or 0),
            warnings=list(raw.get("warnings") or []),
        )

    def _require_project(self, project_id: UUID, user_id: UUID):
        project = self.projects.get_for_user(project_id, user_id)
        if project is None:
            raise NotFoundError("Project not found")
        return project
