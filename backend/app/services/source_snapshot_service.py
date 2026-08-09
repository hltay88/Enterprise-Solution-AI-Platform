"""Immutable source snapshots for document generation (ATLAS-043)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.architecture_option import ArchitectureOption
from app.models.vendor_bom import (
    ArchitectureProductMapping,
    BomImport,
    BomItem,
    BomValidationResult,
    VendorCatalogue,
    VendorProduct,
)
from app.repositories.architecture_option_repository import ArchitectureOptionRepository
from app.repositories.deliverable_repository import DeliverableRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.rkm_repository import RkmRepository
from app.schemas.deliverable import SnapshotCreateIn, SourceSnapshotOut
from app.services.audit_service import AuditService


class SourceSnapshotService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = ProjectRepository(db)
        self.rkms = RkmRepository(db)
        self.architectures = ArchitectureOptionRepository(db)
        self.repo = DeliverableRepository(db)

    def create(
        self,
        project_id: UUID,
        user_id: UUID,
        body: SnapshotCreateIn | None = None,
    ) -> SourceSnapshotOut:
        self._require_project(project_id, user_id)
        body = body or SnapshotCreateIn()

        published = self.rkms.get_published(project_id)
        if published is None:
            raise ValidationAppError(
                "Published RKM required before creating a source snapshot (ATLAS-023/043)"
            )

        architecture = self._resolve_complete_architecture(
            project_id, body.architecture_id
        )

        payload = self._assemble_payload(project_id, published, architecture)
        bom_meta = payload.get("bom") or {}
        catalogue_meta = payload.get("catalogue") or {}

        row = self.repo.create_snapshot(
            project_id=project_id,
            rkm_id=published.id,
            rkm_version_label=getattr(published, "version_label", None)
            or f"{published.version_major}.{published.version_minor}.{published.version_patch}",
            architecture_id=architecture.id,
            architecture_version_label=architecture.version_label,
            bom_import_id=_as_uuid(bom_meta.get("bom_import_id")),
            catalogue_id=_as_uuid(catalogue_meta.get("catalogue_id")),
            catalogue_version_label=catalogue_meta.get("version_label"),
            knowledge_pack_version=architecture.knowledge_pack_version,
            prompt_version=None,
            model=None,
            config_json={"document_types": ["proposal"]},
            payload_json=payload,
            bom_validated=bool(bom_meta.get("validated")),
            created_by=user_id,
        )
        self.db.commit()
        self.db.refresh(row)

        AuditService(self.db).record(
            project_id=project_id,
            user_id=user_id,
            action="deliverable.snapshot",
            summary=(
                f"Created source snapshot for architecture "
                f"'{architecture.title or architecture.candidate_key}' "
                f"(bom_validated={row.bom_validated})"
            ),
            resource_type="source_snapshot",
            resource_id=row.id,
            metadata={
                "architecture_id": str(architecture.id),
                "rkm_id": str(published.id),
                "bom_validated": row.bom_validated,
            },
        )
        return self.to_out(row)

    def get(
        self, project_id: UUID, snapshot_id: UUID, user_id: UUID
    ) -> SourceSnapshotOut:
        self._require_project(project_id, user_id)
        row = self.repo.get_snapshot(snapshot_id, project_id)
        if row is None:
            raise NotFoundError("Source snapshot not found")
        return self.to_out(row)

    def to_out(self, row: Any) -> SourceSnapshotOut:
        return SourceSnapshotOut(
            id=row.id,
            project_id=row.project_id,
            rkm_id=row.rkm_id,
            rkm_version_label=row.rkm_version_label,
            architecture_id=row.architecture_id,
            architecture_version_label=row.architecture_version_label,
            bom_import_id=row.bom_import_id,
            catalogue_id=row.catalogue_id,
            catalogue_version_label=row.catalogue_version_label,
            bom_validated=bool(row.bom_validated),
            model=row.model,
            prompt_version=row.prompt_version,
            knowledge_pack_version=row.knowledge_pack_version,
            created_at=row.created_at,
        )

    def _require_project(self, project_id: UUID, user_id: UUID) -> None:
        if self.projects.get_for_user(project_id, user_id) is None:
            raise NotFoundError("Project not found")

    def _resolve_complete_architecture(
        self,
        project_id: UUID,
        architecture_id: UUID | None,
    ) -> ArchitectureOption:
        if architecture_id is not None:
            option = self.architectures.get_for_project(architecture_id, project_id)
            if option is None:
                raise NotFoundError("Architecture option not found")
            if str(option.status or "").lower() != "complete":
                raise ValidationAppError(
                    "Architecture must be Complete before document generation "
                    "(Sprint 4.0 L1)"
                )
            return option

        rows = self.architectures.list_for_project(project_id)
        complete = [
            r for r in rows if str(r.status or "").lower() == "complete"
        ]
        if not complete:
            raise ValidationAppError(
                "No Complete architecture found. Approve/Complete an architecture "
                "before generating deliverables (Sprint 4.0 L1)"
            )
        if len(complete) > 1:
            complete.sort(
                key=lambda r: r.updated_at or r.created_at,
                reverse=True,
            )
        return complete[0]

    def _assemble_payload(
        self,
        project_id: UUID,
        published: Any,
        architecture: ArchitectureOption,
    ) -> dict[str, Any]:
        rkm_payload = getattr(published, "payload_json", None) or {}
        requirements = rkm_payload.get("requirements") or []
        if not isinstance(requirements, list):
            requirements = []

        components = self.architectures.list_components(architecture.id)
        decisions = self.architectures.list_decisions(architecture.id)
        assumptions = self.architectures.list_assumptions(architecture.id)
        risks = self.architectures.list_risks(architecture_id=architecture.id)
        scores = self.architectures.list_scores(architecture.id)
        capacity = self.architectures.list_capacity_notes(architecture.id)

        mappings = list(
            self.db.scalars(
                select(ArchitectureProductMapping).where(
                    ArchitectureProductMapping.architecture_id == architecture.id
                )
            ).all()
        )
        mapping_rows: list[dict[str, Any]] = []
        catalogue_id = None
        catalogue_version = None
        for m in mappings:
            product = self.db.get(VendorProduct, m.product_id)
            mapping_rows.append(
                {
                    "mapping_id": str(m.id),
                    "component_id": str(m.component_id),
                    "product_id": str(m.product_id),
                    "vendor": getattr(product, "vendor", None),
                    "product_model": getattr(product, "product_model", None),
                    "status": m.status,
                }
            )
            if product is not None:
                catalogue_id = product.catalogue_id
        if catalogue_id is not None:
            catalogue = self.db.get(VendorCatalogue, catalogue_id)
            if catalogue is not None:
                catalogue_version = catalogue.version_label

        bom_payload = self._latest_bom(project_id, architecture.id)

        return {
            "rkm": {
                "id": str(published.id),
                "version_label": getattr(published, "version_label", None),
                "project_name": rkm_payload.get("project_name")
                or rkm_payload.get("customer_name"),
                "customer_name": rkm_payload.get("customer_name"),
                "summary": rkm_payload.get("summary") or rkm_payload.get("overview"),
                "requirements": [
                    {
                        "id": str(r.get("id") or r.get("requirement_id") or ""),
                        "statement": r.get("statement") or r.get("text") or "",
                        "priority": r.get("priority") or r.get("criticality"),
                        "category": r.get("category"),
                    }
                    for r in requirements
                    if isinstance(r, dict)
                ][:200],
            },
            "architecture": {
                "id": str(architecture.id),
                "title": architecture.title,
                "summary": architecture.summary,
                "candidate_key": architecture.candidate_key,
                "version_label": architecture.version_label,
                "status": architecture.status,
                "pattern_codes": architecture.pattern_codes or [],
                "components": [
                    {
                        "id": str(c.id),
                        "name": c.name,
                        "purpose": c.purpose,
                        "component_kind": c.component_kind,
                        "maps_to_requirements": c.maps_to_requirements or [],
                    }
                    for c in components
                ],
                "decisions": [
                    {"id": str(d.id), "decision": d.decision, "rationale": getattr(d, "rationale", None)}
                    for d in decisions
                ],
                "assumptions": [
                    {"id": str(a.id), "statement": a.statement}
                    for a in assumptions
                ],
                "risks": [
                    {
                        "id": str(r.id),
                        "title": (r.description or "")[:120],
                        "severity": r.severity,
                        "description": r.description,
                        "mitigation": r.mitigation,
                    }
                    for r in risks
                ],
                "scores": [
                    {
                        "dimension": s.dimension,
                        "score": s.score,
                    }
                    for s in scores
                ],
                "capacity_notes": [
                    {
                        "id": str(c.id),
                        "note": c.label,
                        "result": c.result,
                        "assumption": c.assumption,
                    }
                    for c in capacity
                ],
            },
            "product_mappings": mapping_rows,
            "catalogue": {
                "catalogue_id": str(catalogue_id) if catalogue_id else None,
                "version_label": catalogue_version,
            },
            "bom": bom_payload,
        }

    def _latest_bom(
        self, project_id: UUID, architecture_id: UUID
    ) -> dict[str, Any]:
        imports = list(
            self.db.scalars(
                select(BomImport)
                .where(BomImport.project_id == project_id)
                .order_by(BomImport.created_at.desc())
            ).all()
        )
        if not imports:
            return {"validated": False, "items": [], "note": "No BOM imported"}

        # Prefer imports linked to this architecture if column exists
        chosen = None
        for row in imports:
            linked = getattr(row, "architecture_id", None)
            if linked is not None and linked == architecture_id:
                chosen = row
                break
        if chosen is None:
            chosen = imports[0]

        validation = self.db.scalars(
            select(BomValidationResult)
            .where(BomValidationResult.bom_import_id == chosen.id)
            .order_by(BomValidationResult.created_at.desc())
        ).first()
        validated = bool(
            validation
            and str(validation.status or "").lower()
            in {"passed", "pass", "valid", "ok", "validated"}
        )
        items = list(
            self.db.scalars(
                select(BomItem).where(BomItem.bom_import_id == chosen.id)
            ).all()
        )
        return {
            "validated": validated,
            "bom_import_id": str(chosen.id),
            "validation_status": getattr(validation, "status", None),
            "items": [
                {
                    "vendor": i.vendor,
                    "product_model": i.product_model,
                    "quantity": i.quantity,
                    "category": i.category,
                    "description": i.description,
                }
                for i in items
            ],
            "note": None
            if validated
            else "BOM present but not validated — exclude pricing (ATLAS-047)",
        }


def _as_uuid(value: Any) -> UUID | None:
    if value is None:
        return None
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None
