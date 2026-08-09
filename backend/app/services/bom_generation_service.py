"""Deterministic BOM deliverable generation (Sprint 4.4) — no AI."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.repositories.deliverable_repository import DeliverableRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.deliverable import (
    BOM_SECTION_TYPES,
    DeliverableGenerateIn,
    GeneratedDocumentOut,
    SnapshotCreateIn,
)
from app.services.audit_service import AuditService
from app.services.proposal_generation_service import ProposalGenerationService
from app.services.source_snapshot_service import SourceSnapshotService
from app.services.template_service import TemplateService

_OPTIONAL_HINTS = ("optional", "opt", "nice-to-have", "nice to have")
_RECOMMENDED_HINTS = ("recommended", "reco", "suggest")


def _classify(category: str, notes: str | None) -> str:
    hay = f"{category} {notes or ''}".lower()
    if any(h in hay for h in _OPTIONAL_HINTS):
        return "optional"
    if any(h in hay for h in _RECOMMENDED_HINTS):
        return "recommended"
    if category.strip():
        return "mandatory"
    return "review_required"


class BomGenerationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = ProjectRepository(db)
        self.repo = DeliverableRepository(db)
        self.snapshots = SourceSnapshotService(db)
        self.templates = TemplateService(db)
        self._proposal = ProposalGenerationService(db)

    async def generate(
        self,
        project_id: UUID,
        user_id: UUID,
        body: DeliverableGenerateIn | None = None,
        *,
        auto_approve: bool = False,
    ) -> GeneratedDocumentOut:
        if self.projects.get_for_user(project_id, user_id) is None:
            raise NotFoundError("Project not found")
        body = body or DeliverableGenerateIn(document_type="bom")
        if body.document_type != "bom":
            raise ValidationAppError("BomGenerationService expects document_type=bom")

        if body.snapshot_id is not None:
            snapshot = self.repo.get_snapshot(body.snapshot_id, project_id)
            if snapshot is None:
                raise NotFoundError("Source snapshot not found")
        else:
            created = self.snapshots.create(
                project_id,
                user_id,
                SnapshotCreateIn(architecture_id=body.architecture_id),
            )
            snapshot = self.repo.get_snapshot(created.id, project_id)
            assert snapshot is not None

        if not snapshot.bom_validated:
            raise ValidationAppError(
                "Validated BOM is required to generate BOM deliverable "
                "(Sprint 4.0 L1 / ATLAS-050)"
            )

        payload = snapshot.payload_json or {}
        bom = payload.get("bom") or {}
        items = list(bom.get("items") or [])
        if not items:
            raise ValidationAppError("Validated BOM has no line items")

        template, template_version = self.templates.resolve_bom_template()
        arch = payload.get("architecture") or {}
        rkm = payload.get("rkm") or {}
        title = f"BOM — {arch.get('title') or arch.get('candidate_key') or 'Solution'}"

        run = self.repo.create_generation_run(
            project_id=project_id,
            document_type="bom",
            source_snapshot_id=snapshot.id,
            template_version_id=template_version.id,
            model="deterministic-bom",
            prompt_version="bom_v1",
            status="completed",
            raw_payload_json={"bom_import_id": bom.get("bom_import_id"), "item_count": len(items)},
            error=None,
            created_by=user_id,
        )

        document = self.repo.create_document(
            project_id=project_id,
            document_type="bom",
            title=title,
            status="draft",
            template_id=template.id,
            template_version_id=template_version.id,
            source_snapshot_id=snapshot.id,
            generation_run_id=run.id,
            created_by=user_id,
        )
        version = self.repo.create_version(
            document_id=document.id,
            project_id=project_id,
            version_label="1.0.0",
            version_major=1,
            version_minor=0,
            version_patch=0,
            status="draft",
            source_snapshot_id=snapshot.id,
            template_version_id=template_version.id,
            created_by=user_id,
        )
        self.repo.set_current_version(document, version)

        issues = list(bom.get("issues") or [])
        validation_status = bom.get("validation_status") or "validated"

        for sequence, (section_type, section_title) in enumerate(BOM_SECTION_TYPES):
            section_row = self.repo.add_section(
                document_version_id=version.id,
                section_type=section_type,
                title=section_title,
                sequence=sequence,
                status="draft",
                confidence=0.95,
                assumptions_json=[],
            )
            if section_type == "cover":
                text = (
                    f"{title}\nProject/customer: "
                    f"{rkm.get('customer_name') or rkm.get('project_name') or 'n/a'}\n"
                    f"Architecture: {arch.get('title') or arch.get('candidate_key')}\n"
                    f"BOM import: {bom.get('bom_import_id')}\n"
                    f"Validation: {validation_status}\n"
                    f"Snapshot: {snapshot.id}\n"
                    "Pricing omitted — not present as authoritative approved data (ATLAS-047)."
                )
                self.repo.add_content_item(
                    section_id=section_row.id,
                    content_type="paragraph",
                    text=text,
                    structured_data={
                        "bom_meta": {
                            "bom_import_id": bom.get("bom_import_id"),
                            "validation_status": validation_status,
                            "item_count": len(items),
                        }
                    },
                    confidence=0.95,
                    approval_status="draft",
                    sort_order=0,
                    review_required=False,
                )
            elif section_type == "line_items":
                for order, item in enumerate(items):
                    line = (
                        f"{item.get('vendor') or ''} | "
                        f"{item.get('product_model') or ''} | "
                        f"qty={item.get('quantity')} {item.get('unit') or ''} | "
                        f"{item.get('category') or ''} | "
                        f"{item.get('description') or ''}"
                    ).strip(" |")
                    content = self.repo.add_content_item(
                        section_id=section_row.id,
                        content_type="table",
                        text=line,
                        structured_data={"bom_item": item},
                        confidence=0.95,
                        approval_status="draft",
                        sort_order=order,
                        review_required=False,
                    )
                    self.repo.add_source_ref(
                        content_item_id=content.id,
                        ref_kind="bom_item",
                        ref_id=str(item.get("sku") or item.get("product_model") or order),
                        label=str(item.get("product_model") or "bom_item"),
                    )
            elif section_type == "classification":
                for order, item in enumerate(items):
                    klass = _classify(
                        str(item.get("category") or ""),
                        str(item.get("notes") or item.get("description") or ""),
                    )
                    review = klass == "review_required"
                    self.repo.add_content_item(
                        section_id=section_row.id,
                        content_type="bullet_list",
                        text=(
                            f"{item.get('product_model') or item.get('description')}: "
                            f"{klass}"
                        ),
                        structured_data={
                            "classification": klass,
                            "bom_item": item,
                        },
                        confidence=0.7 if review else 0.9,
                        approval_status="draft",
                        sort_order=order,
                        review_required=review,
                    )
            elif section_type == "issues":
                if issues:
                    for order, issue in enumerate(issues):
                        self.repo.add_content_item(
                            section_id=section_row.id,
                            content_type="bullet_list",
                            text=str(
                                issue.get("message")
                                or issue.get("summary")
                                or issue
                            ),
                            structured_data={"issue": issue},
                            confidence=0.8,
                            approval_status="draft",
                            sort_order=order,
                            review_required=True,
                        )
                else:
                    self.repo.add_content_item(
                        section_id=section_row.id,
                        content_type="paragraph",
                        text="No unresolved BOM validation issues recorded on the snapshot.",
                        structured_data={},
                        confidence=0.9,
                        approval_status="draft",
                        sort_order=0,
                        review_required=False,
                    )
            elif section_type == "sources":
                self.repo.add_content_item(
                    section_id=section_row.id,
                    content_type="paragraph",
                    text=(
                        f"Source snapshot {snapshot.id}; BOM import "
                        f"{bom.get('bom_import_id')}; architecture "
                        f"{arch.get('id') or snapshot.architecture_id}."
                    ),
                    structured_data={
                        "snapshot_id": str(snapshot.id),
                        "bom_import_id": bom.get("bom_import_id"),
                    },
                    confidence=1.0,
                    approval_status="draft",
                    sort_order=0,
                    review_required=False,
                )

        snapshot.prompt_version = "bom_v1"
        snapshot.model = "deterministic-bom"

        if auto_approve:
            from datetime import datetime, timezone

            document.status = "approved"
            document.approved_by = user_id
            document.approved_at = datetime.now(timezone.utc)
            version.status = "approved"
            self.repo.add_approval(
                document_version_id=version.id,
                approver_id=user_id,
                decision="approved",
                note="Auto-approved: deterministic BOM from validated source (ATLAS-050)",
            )

        self.db.commit()
        self.db.refresh(document)

        AuditService(self.db).record(
            project_id=project_id,
            user_id=user_id,
            action="deliverable.generate",
            summary=f"Generated BOM deliverable '{document.title}'",
            resource_type="generated_document",
            resource_id=document.id,
            metadata={
                "snapshot_id": str(snapshot.id),
                "document_type": "bom",
                "auto_approve": auto_approve,
                "item_count": len(items),
            },
        )
        return self._proposal.to_out(
            document, bom_validated=bool(snapshot.bom_validated)
        )
