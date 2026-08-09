"""Solution design generation orchestration (Sprint 4.3)."""

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
    SnapshotCreateIn,
    SolutionDesignContentPayload,
)
from app.services.audit_service import AuditService
from app.services.proposal_generation_service import ProposalGenerationService
from app.services.solution_design_content_planner import SolutionDesignContentPlanner
from app.services.source_snapshot_service import SourceSnapshotService
from app.services.template_service import TemplateService


class SolutionDesignGenerationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = ProjectRepository(db)
        self.repo = DeliverableRepository(db)
        self.snapshots = SourceSnapshotService(db)
        self.templates = TemplateService(db)
        self.planner = SolutionDesignContentPlanner()
        self._proposal = ProposalGenerationService(db)

    async def generate(
        self,
        project_id: UUID,
        user_id: UUID,
        body: DeliverableGenerateIn | None = None,
    ) -> GeneratedDocumentOut:
        if self.projects.get_for_user(project_id, user_id) is None:
            raise NotFoundError("Project not found")
        body = body or DeliverableGenerateIn(document_type="solution_design")
        if body.document_type != "solution_design":
            raise ValidationAppError(
                "SolutionDesignGenerationService expects document_type=solution_design"
            )

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

        template, template_version = self.templates.resolve_solution_design_template()
        plan = self.planner.build(
            snapshot.payload_json or {},
            list(template_version.sections_json or []),
        )

        prompt_version = "solution_design_v1"
        provider = get_ai_provider()
        raw = await provider.generate_solution_design_content(
            snapshot.payload_json or {},
            plan,
            prompt_version=prompt_version,
        )
        try:
            payload = SolutionDesignContentPayload.model_validate(raw)
        except ValidationError as exc:
            self.repo.create_generation_run(
                project_id=project_id,
                document_type="solution_design",
                source_snapshot_id=snapshot.id,
                template_version_id=template_version.id,
                model=str(raw.get("model") or "") if isinstance(raw, dict) else "",
                prompt_version=prompt_version,
                status="failed",
                raw_payload_json=raw if isinstance(raw, dict) else {"raw": str(raw)},
                error=str(exc),
                created_by=user_id,
            )
            self.db.commit()
            raise ValidationAppError(
                f"Solution design AI output failed schema validation: {exc}"
            ) from exc

        run = self.repo.create_generation_run(
            project_id=project_id,
            document_type="solution_design",
            source_snapshot_id=snapshot.id,
            template_version_id=template_version.id,
            model=payload.model
            or (str(raw.get("model") or "") if isinstance(raw, dict) else ""),
            prompt_version=payload.prompt_version or prompt_version,
            status="completed",
            raw_payload_json=raw if isinstance(raw, dict) else payload.model_dump(),
            error=None,
            created_by=user_id,
        )

        document = self.repo.create_document(
            project_id=project_id,
            document_type="solution_design",
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

        snapshot.prompt_version = payload.prompt_version or prompt_version
        snapshot.model = payload.model or snapshot.model
        self.db.commit()
        self.db.refresh(document)

        AuditService(self.db).record(
            project_id=project_id,
            user_id=user_id,
            action="deliverable.generate",
            summary=f"Generated solution design draft '{document.title}'",
            resource_type="generated_document",
            resource_id=document.id,
            metadata={
                "snapshot_id": str(snapshot.id),
                "generation_run_id": str(run.id),
                "document_type": "solution_design",
            },
        )
        return self._proposal.to_out(
            document, bom_validated=bool(snapshot.bom_validated)
        )
