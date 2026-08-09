"""Persistence for architecture→product mappings (Sprint 3.3 Task 5)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.vendor_bom import ArchitectureProductMapping, VendorProduct


class ArchitectureProductMappingRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_architecture(
        self,
        architecture_id: UUID,
    ) -> list[ArchitectureProductMapping]:
        statement = (
            select(ArchitectureProductMapping)
            .where(ArchitectureProductMapping.architecture_id == architecture_id)
            .order_by(
                ArchitectureProductMapping.component_id.asc(),
                ArchitectureProductMapping.fit_score.desc().nullslast(),
                ArchitectureProductMapping.created_at.asc(),
            )
        )
        return list(self.db.scalars(statement).all())

    def list_for_project(self, project_id: UUID) -> list[ArchitectureProductMapping]:
        statement = (
            select(ArchitectureProductMapping)
            .where(ArchitectureProductMapping.project_id == project_id)
            .order_by(ArchitectureProductMapping.created_at.desc())
        )
        return list(self.db.scalars(statement).all())

    def get_for_project(
        self,
        mapping_id: UUID,
        project_id: UUID,
    ) -> ArchitectureProductMapping | None:
        return self.db.scalars(
            select(ArchitectureProductMapping).where(
                ArchitectureProductMapping.id == mapping_id,
                ArchitectureProductMapping.project_id == project_id,
            ),
        ).first()

    def replace_candidates_for_architecture(
        self,
        *,
        project_id: UUID,
        architecture_id: UUID,
        created_by: UUID | None,
        rows: list[dict[str, Any]],
        commit: bool = True,
    ) -> list[ArchitectureProductMapping]:
        """Replace prior ``candidate`` rows for the architecture; keep selected/rejected.

        Each row: component_id, product_id, fit_score, rationale, limitations,
        preference_kind (optional), status (default candidate).
        """
        # Drop previous auto-candidates only — preserve human selections.
        self.db.execute(
            delete(ArchitectureProductMapping).where(
                ArchitectureProductMapping.architecture_id == architecture_id,
                ArchitectureProductMapping.status == "candidate",
            ),
        )
        self.db.flush()

        now = datetime.now(timezone.utc)
        created: list[ArchitectureProductMapping] = []
        seen: set[tuple[UUID, UUID]] = set()
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                raise ValueError(f"mappings[{index}] must be an object")
            component_id = row.get("component_id")
            product_id = row.get("product_id")
            if component_id is None or product_id is None:
                raise ValueError(
                    f"mappings[{index}] requires component_id and product_id",
                )
            key = (UUID(str(component_id)), UUID(str(product_id)))
            if key in seen:
                continue
            seen.add(key)
            mapping = ArchitectureProductMapping(
                id=uuid4(),
                project_id=project_id,
                architecture_id=architecture_id,
                component_id=key[0],
                product_id=key[1],
                fit_score=(
                    float(row["fit_score"])
                    if row.get("fit_score") is not None
                    else None
                ),
                rationale=str(row.get("rationale") or "").strip(),
                status=str(row.get("status") or "candidate").strip() or "candidate",
                preference_kind=str(row.get("preference_kind") or "technical").strip()
                or "technical",
                limitations=str(row.get("limitations") or "").strip(),
                created_by=created_by,
                created_at=now,
                updated_at=now,
            )
            self.db.add(mapping)
            created.append(mapping)

        if commit:
            self.db.commit()
            for item in created:
                self.db.refresh(item)
        else:
            self.db.flush()
        return created

    def update_mapping(
        self,
        mapping: ArchitectureProductMapping,
        *,
        status: str | None = None,
        preference_kind: str | None = None,
        rationale: str | None = None,
        limitations: str | None = None,
        fit_score: float | None = None,
        commit: bool = True,
    ) -> ArchitectureProductMapping:
        if status is not None:
            mapping.status = status
        if preference_kind is not None:
            mapping.preference_kind = preference_kind
        if rationale is not None:
            mapping.rationale = rationale
        if limitations is not None:
            mapping.limitations = limitations
        if fit_score is not None:
            mapping.fit_score = fit_score
        mapping.updated_at = datetime.now(timezone.utc)
        if commit:
            self.db.commit()
            self.db.refresh(mapping)
        else:
            self.db.flush()
        return mapping

    def get_products_by_ids(self, product_ids: list[UUID]) -> dict[UUID, VendorProduct]:
        if not product_ids:
            return {}
        rows = self.db.scalars(
            select(VendorProduct).where(VendorProduct.id.in_(product_ids)),
        ).all()
        return {row.id: row for row in rows}
