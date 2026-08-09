"""Sprint 3.3 Task 5 — explicit architecture product mapping (ATLAS-035).

Not invoked by architecture generate. Call ``map_products`` after a catalogue
is available (seed or import). APIs land in Task 6.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.architecture_option import ArchitectureComponent
from app.models.vendor_bom import ArchitectureProductMapping, VendorProduct
from app.repositories.architecture_option_repository import ArchitectureOptionRepository
from app.repositories.architecture_product_mapping_repository import (
    ArchitectureProductMappingRepository,
)
from app.repositories.project_repository import ProjectRepository
from app.repositories.vendor_catalogue_repository import VendorCatalogueRepository
from app.schemas.vendor_bom import (
    ArchitectureProductMapIn,
    ArchitectureProductMappingOut,
    ArchitectureProductMappingUpdateIn,
    ArchitectureProductMapResultOut,
)
from app.services.architecture_product_matching import rank_products_for_component
from app.services.audit_service import AuditService


class ArchitectureProductMappingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = ProjectRepository(db)
        self.architectures = ArchitectureOptionRepository(db)
        self.mappings = ArchitectureProductMappingRepository(db)
        self.catalogues = VendorCatalogueRepository(db)

    def map_products(
        self,
        project_id: UUID,
        user_id: UUID,
        body: ArchitectureProductMapIn,
    ) -> ArchitectureProductMapResultOut:
        self._require_project(project_id, user_id)
        if body.architecture_id is None:
            raise ValidationAppError("architecture_id is required")
        option = self.architectures.get_for_project(body.architecture_id, project_id)
        if option is None:
            raise NotFoundError("Architecture option not found")

        components = self.architectures.list_components(option.id)
        if body.component_ids:
            wanted = {UUID(str(item)) for item in body.component_ids}
            components = [item for item in components if item.id in wanted]
            missing = wanted - {item.id for item in components}
            if missing:
                raise ValidationAppError(
                    f"Unknown component_id(s) for architecture: {sorted(str(x) for x in missing)}",
                )
        if not components:
            raise ValidationAppError("No architecture components available to map")

        products = self._load_catalogue_products(
            catalogue_id=body.catalogue_id,
            region=body.region,
            include_stale=body.include_stale,
        )
        if not products:
            raise ValidationAppError(
                "No catalogue products available. Seed or import a vendor catalogue first.",
            )

        product_dicts = [self._product_dict(item) for item in products]
        rows: list[dict[str, Any]] = []
        matched_components: set[UUID] = set()
        for component in components:
            candidates = rank_products_for_component(
                component=self._component_dict(component),
                products=product_dicts,
                region=body.region,
                limit=3,
            )
            if not candidates:
                continue
            matched_components.add(component.id)
            for candidate in candidates:
                rows.append(
                    {
                        "component_id": component.id,
                        "product_id": UUID(candidate.product_id),
                        "fit_score": candidate.fit_score,
                        "rationale": candidate.rationale,
                        "limitations": candidate.limitations,
                        "preference_kind": candidate.preference_kind,
                        "status": "candidate",
                    },
                )

        try:
            created = self.mappings.replace_candidates_for_architecture(
                project_id=project_id,
                architecture_id=option.id,
                created_by=user_id,
                rows=rows,
                commit=True,
            )
        except ValueError as exc:
            raise ValidationAppError(str(exc)) from exc

        unmatched = [item.id for item in components if item.id not in matched_components]
        product_lookup = self.mappings.get_products_by_ids(
            [item.product_id for item in created],
        )
        outs = [self._mapping_out(item, product_lookup.get(item.product_id)) for item in created]

        AuditService(self.db).record(
            project_id=project_id,
            user_id=user_id,
            action="architectures.map_products",
            summary=(
                f"Mapped products for architecture {option.candidate_key} "
                f"({len(outs)} candidates, {len(unmatched)} unmatched)"
            ),
            resource_type="architecture_option",
            resource_id=option.id,
            metadata={
                "architecture_id": str(option.id),
                "mapping_count": len(outs),
                "unmatched_count": len(unmatched),
                "catalogue_id": str(body.catalogue_id) if body.catalogue_id else None,
            },
        )
        return ArchitectureProductMapResultOut(
            architecture_id=option.id,
            mappings=outs,
            unmatched_component_ids=unmatched,
        )

    def list_mappings(
        self,
        project_id: UUID,
        user_id: UUID,
        architecture_id: UUID,
    ) -> list[ArchitectureProductMappingOut]:
        self._require_project(project_id, user_id)
        option = self.architectures.get_for_project(architecture_id, project_id)
        if option is None:
            raise NotFoundError("Architecture option not found")
        rows = self.mappings.list_for_architecture(architecture_id)
        products = self.mappings.get_products_by_ids([row.product_id for row in rows])
        return [self._mapping_out(row, products.get(row.product_id)) for row in rows]

    def update_mapping(
        self,
        project_id: UUID,
        user_id: UUID,
        mapping_id: UUID,
        body: ArchitectureProductMappingUpdateIn,
    ) -> ArchitectureProductMappingOut:
        self._require_project(project_id, user_id)
        row = self.mappings.get_for_project(mapping_id, project_id)
        if row is None:
            raise NotFoundError("Product mapping not found")
        updated = self.mappings.update_mapping(
            row,
            status=body.status,
            preference_kind=body.preference_kind,
            rationale=body.rationale,
            limitations=body.limitations,
            fit_score=body.fit_score,
            commit=True,
        )
        product = self.catalogues.get_product(updated.product_id)
        AuditService(self.db).record(
            project_id=project_id,
            user_id=user_id,
            action="architectures.map_products.update",
            summary=f"Updated product mapping status={updated.status}",
            resource_type="architecture_product_mapping",
            resource_id=updated.id,
            metadata={"status": updated.status, "preference_kind": updated.preference_kind},
        )
        return self._mapping_out(updated, product)

    def _load_catalogue_products(
        self,
        *,
        catalogue_id: UUID | None,
        region: str | None,
        include_stale: bool,
    ) -> list[VendorProduct]:
        if catalogue_id is not None:
            catalogue = self.catalogues.get_catalogue(catalogue_id)
            if catalogue is None:
                raise NotFoundError("Vendor catalogue not found")
            rows = self.catalogues.list_products(
                catalogue_id,
                include_stale=include_stale,
            )
        else:
            rows = self.catalogues.search_products(
                include_stale=include_stale,
                region=region,
                limit=200,
            )
        # Attach capabilities for scoring.
        enriched: list[VendorProduct] = []
        for product in rows:
            # list_capabilities is separate; stash on a simple namespace via dict path
            enriched.append(product)
        return enriched

    def _product_dict(self, product: VendorProduct) -> dict[str, Any]:
        caps = self.catalogues.list_capabilities(product.id)
        return {
            "id": str(product.id),
            "vendor": product.vendor,
            "product_model": product.product_model,
            "category": product.category,
            "lifecycle_status": product.lifecycle_status,
            "region": product.region,
            "is_stale": bool(product.is_stale),
            "capabilities": [
                {
                    "capability_code": cap.capability_code,
                    "capability_label": cap.capability_label,
                    "confidence": cap.confidence,
                }
                for cap in caps
            ],
        }

    @staticmethod
    def _component_dict(component: ArchitectureComponent) -> dict[str, Any]:
        return {
            "id": str(component.id),
            "name": component.name,
            "purpose": component.purpose,
            "component_kind": component.component_kind,
        }

    @staticmethod
    def _mapping_out(
        row: ArchitectureProductMapping,
        product: VendorProduct | None,
    ) -> ArchitectureProductMappingOut:
        return ArchitectureProductMappingOut(
            id=row.id,
            project_id=row.project_id,
            architecture_id=row.architecture_id,
            component_id=row.component_id,
            product_id=row.product_id,
            fit_score=row.fit_score,
            rationale=row.rationale or "",
            status=row.status,
            preference_kind=row.preference_kind,
            limitations=row.limitations or "",
            vendor=product.vendor if product else None,
            product_model=product.product_model if product else None,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _require_project(self, project_id: UUID, user_id: UUID):
        project = self.projects.get_for_user(project_id, user_id)
        if project is None:
            raise NotFoundError("Project not found")
        return project
