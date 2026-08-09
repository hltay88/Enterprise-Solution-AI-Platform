"""BOM import service (Sprint 3.3 Task 7, ATLAS-039).

External/distributor BOMs are immutable evidence. Validation is Task 8.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.vendor_bom import BomImport, BomItem
from app.repositories.architecture_option_repository import ArchitectureOptionRepository
from app.repositories.bom_repository import BomRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.vendor_catalogue_repository import VendorCatalogueRepository
from app.schemas.vendor_bom import BomImportIn, BomImportOut, BomItemOut
from app.services.audit_service import AuditService


class BomService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = ProjectRepository(db)
        self.boms = BomRepository(db)
        self.architectures = ArchitectureOptionRepository(db)
        self.catalogues = VendorCatalogueRepository(db)

    def import_bom(
        self,
        project_id: UUID,
        user_id: UUID,
        body: BomImportIn,
    ) -> BomImportOut:
        self._require_project(project_id, user_id)
        if body.architecture_id is not None:
            option = self.architectures.get_for_project(body.architecture_id, project_id)
            if option is None:
                raise NotFoundError("Architecture option not found")

        items: list[dict] = []
        for item in body.items:
            data = item.model_dump(mode="python")
            data["mapped_product_id"] = self._soft_link_product(
                vendor=item.vendor,
                product_model=item.product_model,
                sku=item.sku,
            )
            items.append(data)

        try:
            bom = self.boms.create_import_tree(
                project_id=project_id,
                architecture_id=body.architecture_id,
                source=body.source,
                source_filename=body.source_filename,
                notes=body.notes,
                imported_by=user_id,
                items=items,
                payload_json={
                    "imported_at": datetime.now(timezone.utc).isoformat(),
                    "item_count": len(items),
                    "evidence": True,
                },
                commit=True,
            )
        except ValueError as exc:
            raise ValidationAppError(str(exc)) from exc

        out = self._import_out(bom, include_items=True)
        AuditService(self.db).record(
            project_id=project_id,
            user_id=user_id,
            action="bom.import",
            summary=f"Imported BOM evidence ({out.item_count} lines) from {body.source}",
            resource_type="bom_import",
            resource_id=bom.id,
            metadata={
                "source": body.source,
                "item_count": out.item_count,
                "architecture_id": str(body.architecture_id)
                if body.architecture_id
                else None,
            },
        )
        return out

    def get_import(
        self,
        project_id: UUID,
        user_id: UUID,
        bom_import_id: UUID,
    ) -> BomImportOut:
        self._require_project(project_id, user_id)
        bom = self.boms.get_import_for_project(bom_import_id, project_id)
        if bom is None:
            raise NotFoundError("BOM import not found")
        return self._import_out(bom, include_items=True)

    def list_imports(
        self,
        project_id: UUID,
        user_id: UUID,
        *,
        limit: int = 50,
    ) -> list[BomImportOut]:
        self._require_project(project_id, user_id)
        rows = self.boms.list_imports_for_project(project_id, limit=limit)
        return [self._import_out(row, include_items=False) for row in rows]

    def _soft_link_product(
        self,
        *,
        vendor: str,
        product_model: str,
        sku: str | None,
    ) -> UUID | None:
        """Best-effort catalogue link on exact vendor+model (or model-only) match."""
        model = (product_model or "").strip()
        if not model and not sku:
            return None
        query = model or (sku or "")
        hits = self.catalogues.search_products(
            query=query,
            vendor=vendor.strip() or None,
            include_stale=True,
            limit=20,
        )
        model_l = model.lower()
        vendor_l = vendor.strip().lower()
        for product in hits:
            if model_l and product.product_model.strip().lower() == model_l:
                if not vendor_l or product.vendor.strip().lower() == vendor_l:
                    return product.id
        return None

    def _import_out(self, bom: BomImport, *, include_items: bool) -> BomImportOut:
        items_out: list[BomItemOut] = []
        if include_items:
            for item in self.boms.list_items(bom.id):
                items_out.append(self._item_out(item))
        else:
            items_out = []
        count = len(items_out) if include_items else len(self.boms.list_items(bom.id))
        return BomImportOut(
            id=bom.id,
            project_id=bom.project_id,
            architecture_id=bom.architecture_id,
            source=bom.source,
            source_filename=bom.source_filename,
            notes=bom.notes,
            item_count=count,
            created_at=bom.created_at,
            items=items_out,
        )

    @staticmethod
    def _item_out(item: BomItem) -> BomItemOut:
        return BomItemOut(
            id=item.id,
            bom_import_id=item.bom_import_id,
            line_number=item.line_number,
            vendor=item.vendor or "",
            product_model=item.product_model or "",
            description=item.description or "",
            quantity=item.quantity,
            unit=item.unit,
            category=item.category or "",
            sku=item.sku,
            mapped_product_id=item.mapped_product_id,
            notes=item.notes,
            created_at=item.created_at,
        )

    def _require_project(self, project_id: UUID, user_id: UUID):
        project = self.projects.get_for_user(project_id, user_id)
        if project is None:
            raise NotFoundError("Project not found")
        return project
