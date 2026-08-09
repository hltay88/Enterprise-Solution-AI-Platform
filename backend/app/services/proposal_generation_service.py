"""Proposal generation orchestration (Sprint 4.1, ATLAS-043/044)."""

from __future__ import annotations

from uuid import UUID

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.ai.factory import get_ai_provider
from app.core.exceptions import NotFoundError, ValidationAppError
from app.repositories.deliverable_repository import DeliverableRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.deliverable import (
    DeliverableGenerateIn,
    GeneratedDocumentOut,
    ProposalContentPayload,
    SnapshotCreateIn,
)
from app.services.audit_service import AuditService
from app.services.proposal_content_planner import ProposalContentPlanner
from app.services.source_snapshot_service import SourceSnapshotService
from app.services.template_service import TemplateService


class ProposalGenerationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = ProjectRepository(db)
        self.repo = DeliverableRepository(db)
        self.snapshots = SourceSnapshotService(db)
        self.templates = TemplateService(db)
        self.planner = ProposalContentPlanner()

    async def generate(
        self,
        project_id: UUID,
        user_id: UUID,
        body: DeliverableGenerateIn | None = None,
    ) -> GeneratedDocumentOut:
        if self.projects.get_for_user(project_id, user_id) is None:
            raise NotFoundError("Project not found")
        body = body or DeliverableGenerateIn()
        if body.document_type != "proposal":
            raise ValidationAppError("Sprint 4.1 supports document_type=proposal only")

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

        template, template_version = self.templates.resolve_proposal_template()
        plan = self.planner.build(
            snapshot.payload_json or {},
            list(template_version.sections_json or []),
        )

        prompt_version = "proposal_v1"
        provider = get_ai_provider()
        raw = await provider.generate_proposal_content(
            snapshot.payload_json or {},
            plan,
            prompt_version=prompt_version,
        )
        try:
            payload = ProposalContentPayload.model_validate(raw)
        except ValidationError as exc:
            run = self.repo.create_generation_run(
                project_id=project_id,
                document_type="proposal",
                source_snapshot_id=snapshot.id,
                template_version_id=template_version.id,
                model=str(raw.get("model") or ""),
                prompt_version=prompt_version,
                status="failed",
                raw_payload_json=raw if isinstance(raw, dict) else {"raw": str(raw)},
                error=str(exc),
                created_by=user_id,
            )
            self.db.commit()
            raise ValidationAppError(
                f"Proposal AI output failed schema validation: {exc}"
            ) from exc

        run = self.repo.create_generation_run(
            project_id=project_id,
            document_type="proposal",
            source_snapshot_id=snapshot.id,
            template_version_id=template_version.id,
            model=payload.model or str(raw.get("model") or ""),
            prompt_version=payload.prompt_version or prompt_version,
            status="completed",
            raw_payload_json=raw if isinstance(raw, dict) else payload.model_dump(),
            error=None,
            created_by=user_id,
        )

        document = self.repo.create_document(
            project_id=project_id,
            document_type="proposal",
            title=payload.title,
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

        for section in payload.sections:
            section_row = self.repo.add_section(
                document_version_id=version.id,
                section_type=section.section_type,
                title=section.title,
                sequence=section.sequence,
                status="draft",
                confidence=section.confidence,
                assumptions_json=list(section.assumptions or []),
            )
            for order, item in enumerate(section.content_items):
                content = self.repo.add_content_item(
                    section_id=section_row.id,
                    content_type=item.content_type,
                    text=item.text,
                    structured_data=item.structured_data or {},
                    confidence=item.confidence,
                    approval_status="draft",
                    sort_order=order,
                    review_required=bool(item.review_required),
                )
                for ref in item.source_refs:
                    self.repo.add_source_ref(
                        content_item_id=content.id,
                        ref_kind=ref.ref_kind,
                        ref_id=ref.ref_id,
                        label=ref.label or "",
                    )

        # Pin prompt/model onto snapshot for auditability (immutable row still OK to patch meta once)
        snapshot.prompt_version = payload.prompt_version or prompt_version
        snapshot.model = payload.model or snapshot.model
        self.db.commit()
        self.db.refresh(document)

        AuditService(self.db).record(
            project_id=project_id,
            user_id=user_id,
            action="deliverable.generate",
            summary=f"Generated proposal draft '{document.title}'",
            resource_type="generated_document",
            resource_id=document.id,
            metadata={
                "snapshot_id": str(snapshot.id),
                "generation_run_id": str(run.id),
                "document_type": "proposal",
            },
        )
        return self.to_out(document, bom_validated=bool(snapshot.bom_validated))

    def to_out(self, document, *, bom_validated: bool | None = None) -> GeneratedDocumentOut:
        version_label = None
        if document.current_version_id:
            version = self.repo.get_version(document.current_version_id)
            if version is not None:
                version_label = version.version_label
        return GeneratedDocumentOut(
            id=document.id,
            project_id=document.project_id,
            document_type=document.document_type,
            title=document.title,
            status=document.status,
            template_id=document.template_id,
            template_version_id=document.template_version_id,
            source_snapshot_id=document.source_snapshot_id,
            generation_run_id=document.generation_run_id,
            current_version_id=document.current_version_id,
            version_label=version_label,
            created_by=document.created_by,
            approved_by=document.approved_by,
            approved_at=document.approved_at,
            created_at=document.created_at,
            updated_at=document.updated_at,
            bom_validated=bom_validated,
        )
