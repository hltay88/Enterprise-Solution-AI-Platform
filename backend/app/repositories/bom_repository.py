"""Persistence for BOM imports (Sprint 3.3 Task 7, ATLAS-039).

Imports are immutable evidence snapshots. Validation results are separate rows.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.vendor_bom import BomImport, BomItem, BomValidationResult


class BomRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_import(self, bom_import_id: UUID) -> BomImport | None:
        return self.db.scalars(
            select(BomImport).where(BomImport.id == bom_import_id),
        ).first()

    def get_import_for_project(
        self,
        bom_import_id: UUID,
        project_id: UUID,
    ) -> BomImport | None:
        return self.db.scalars(
            select(BomImport).where(
                BomImport.id == bom_import_id,
                BomImport.project_id == project_id,
            ),
        ).first()

    def list_imports_for_project(
        self,
        project_id: UUID,
        *,
        limit: int = 50,
    ) -> list[BomImport]:
        statement = (
            select(BomImport)
            .where(BomImport.project_id == project_id)
            .order_by(BomImport.created_at.desc())
            .limit(max(1, min(limit, 200)))
        )
        return list(self.db.scalars(statement).all())

    def list_items(self, bom_import_id: UUID) -> list[BomItem]:
        statement = (
            select(BomItem)
            .where(BomItem.bom_import_id == bom_import_id)
            .order_by(BomItem.line_number.asc(), BomItem.created_at.asc())
        )
        return list(self.db.scalars(statement).all())

    def list_validation_results(self, bom_import_id: UUID) -> list[BomValidationResult]:
        statement = (
            select(BomValidationResult)
            .where(BomValidationResult.bom_import_id == bom_import_id)
            .order_by(BomValidationResult.created_at.desc())
        )
        return list(self.db.scalars(statement).all())

    def create_import_tree(
        self,
        *,
        project_id: UUID,
        architecture_id: UUID | None,
        source: str,
        source_filename: str | None,
        notes: str | None,
        imported_by: UUID | None,
        items: list[dict[str, Any]],
        payload_json: dict[str, Any] | None = None,
        commit: bool = True,
    ) -> BomImport:
        """Persist an immutable BOM import + line items.

        ``items`` dicts may include optional ``mapped_product_id``.
        """
        source_text = str(source or "").strip()
        if not source_text:
            raise ValueError("BOM source is required")
        if not items:
            raise ValueError("at least one BOM item is required")

        now = datetime.now(timezone.utc)
        bom = BomImport(
            id=uuid4(),
            project_id=project_id,
            architecture_id=architecture_id,
            source=source_text,
            source_filename=(str(source_filename).strip() if source_filename else None)
            or None,
            notes=(str(notes).strip() if notes else None) or None,
            imported_by=imported_by,
            payload_json=dict(payload_json or {}),
            created_at=now,
        )
        self.db.add(bom)
        self.db.flush()

        for index, item in enumerate(items):
            if not isinstance(item, dict):
                raise ValueError(f"items[{index}] must be an object")
            model = str(item.get("product_model") or "").strip()
            sku = str(item.get("sku") or "").strip() or None
            description = str(item.get("description") or "").strip()
            if not (model or sku or description):
                raise ValueError(
                    f"items[{index}] requires product_model, sku, or description",
                )
            mapped = item.get("mapped_product_id")
            mapped_id = UUID(str(mapped)) if mapped else None
            line_number = item.get("line_number")
            try:
                line_no = int(line_number) if line_number is not None else index + 1
            except (TypeError, ValueError) as exc:
                raise ValueError(f"items[{index}].line_number must be an integer") from exc
            qty = item.get("quantity")
            quantity = float(qty) if qty is not None and qty != "" else None
            self.db.add(
                BomItem(
                    id=uuid4(),
                    bom_import_id=bom.id,
                    line_number=line_no,
                    vendor=str(item.get("vendor") or "").strip(),
                    product_model=model,
                    description=description,
                    quantity=quantity,
                    unit=(str(item.get("unit")).strip() if item.get("unit") else None)
                    or None,
                    category=str(item.get("category") or "").strip(),
                    sku=sku,
                    mapped_product_id=mapped_id,
                    notes=(str(item.get("notes")).strip() if item.get("notes") else None)
                    or None,
                    created_at=now,
                ),
            )

        if commit:
            self.db.commit()
            self.db.refresh(bom)
        else:
            self.db.flush()
        return bom
