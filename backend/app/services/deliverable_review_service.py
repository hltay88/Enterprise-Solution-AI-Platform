"""Deliverable review / approve / revise (ATLAS-045)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.repositories.deliverable_repository import DeliverableRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.deliverable import (
    ApproveIn,
    ContentItemOut,
    DocumentSectionOut,
    GeneratedDocumentOut,
    ReviewIn,
    SectionPatchIn,
    SourceRefOut,
    ValidationOut,
)
from app.services.audit_service import AuditService
from app.services.deliverable_validation_service import DeliverableValidationService
from app.services.proposal_generation_service import ProposalGenerationService

_EDITABLE = frozenset({"draft", "changes_requested"})
_REVIEWABLE = frozenset({"draft", "changes_requested", "in_review"})
_APPROVABLE = frozenset({"in_review"})


class DeliverableReviewService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = ProjectRepository(db)
        self.repo = DeliverableRepository(db)
        self.validation = DeliverableValidationService(db)
        self.generation = ProposalGenerationService(db)

    def list_documents(self, project_id: UUID, user_id: UUID) -> list[GeneratedDocumentOut]:
        self._require_project(project_id, user_id)
        rows = self.repo.list_documents(project_id)
        return [self.generation.to_out(r) for r in rows]

    def get_document(
        self, project_id: UUID, document_id: UUID, user_id: UUID
    ) -> GeneratedDocumentOut:
        document = self._get_document(project_id, document_id, user_id)
        snap = self.repo.get_snapshot(document.source_snapshot_id, project_id)
        return self.generation.to_out(
            document,
            bom_validated=bool(snap.bom_validated) if snap else None,
        )

    def list_sections(
        self, project_id: UUID, document_id: UUID, user_id: UUID
    ) -> list[DocumentSectionOut]:
        document = self._get_document(project_id, document_id, user_id)
        if document.current_version_id is None:
            return []
        return self._sections_out(document.current_version_id)

    def patch_section(
        self,
        project_id: UUID,
        document_id: UUID,
        section_id: UUID,
        user_id: UUID,
        body: SectionPatchIn,
    ) -> DocumentSectionOut:
        document = self._get_document(project_id, document_id, user_id)
        if document.status not in _EDITABLE:
            raise ValidationAppError(
                f"Cannot edit sections while status is '{document.status}'"
            )
        if document.current_version_id is None:
            raise ValidationAppError("Document has no current version")
        section = self.repo.get_section(section_id, document.current_version_id)
        if section is None:
            raise NotFoundError("Section not found")
        if body.title is not None:
            section.title = body.title
        if body.assumptions is not None:
            section.assumptions_json = list(body.assumptions)
        if body.text is not None:
            items = self.repo.list_content_items(section.id)
            if items:
                items[0].text = body.text
            else:
                self.repo.add_content_item(
                    section_id=section.id,
                    content_type="paragraph",
                    text=body.text,
                    sort_order=0,
                )
        section.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        return self._sections_out(document.current_version_id, only_id=section.id)[0]

    def validate(
        self, project_id: UUID, document_id: UUID, user_id: UUID
    ) -> ValidationOut:
        self._get_document(project_id, document_id, user_id)
        result = self.validation.validate_document(project_id, document_id)
        AuditService(self.db).record(
            project_id=project_id,
            user_id=user_id,
            action="deliverable.validate",
            summary=f"Validated deliverable ({'ok' if result.ok else 'issues'})",
            resource_type="generated_document",
            resource_id=document_id,
            metadata={"ok": result.ok, "issue_count": len(result.issues)},
        )
        return result

    def review(
        self,
        project_id: UUID,
        document_id: UUID,
        user_id: UUID,
        body: ReviewIn | None = None,
    ) -> GeneratedDocumentOut:
        document = self._get_document(project_id, document_id, user_id)
        if document.status not in _REVIEWABLE:
            raise ValidationAppError(
                f"Cannot move status '{document.status}' to in_review"
            )
        if document.status == "approved":
            raise ValidationAppError("Approved documents are immutable (ATLAS-045)")
        document.status = "in_review"
        if document.current_version_id:
            version = self.repo.get_version(document.current_version_id)
            if version:
                version.status = "in_review"
        document.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        AuditService(self.db).record(
            project_id=project_id,
            user_id=user_id,
            action="deliverable.review",
            summary="Marked deliverable in_review",
            resource_type="generated_document",
            resource_id=document.id,
            metadata={"note": (body.note if body else None)},
        )
        return self.get_document(project_id, document_id, user_id)

    def approve(
        self,
        project_id: UUID,
        document_id: UUID,
        user_id: UUID,
        body: ApproveIn | None = None,
    ) -> GeneratedDocumentOut:
        document = self._get_document(project_id, document_id, user_id)
        body = body or ApproveIn()
        if document.status not in _APPROVABLE and body.decision == "approved":
            raise ValidationAppError(
                "Deliverable must be in_review before approve (ATLAS-045)"
            )

        if body.decision == "changes_requested":
            document.status = "changes_requested"
            if document.current_version_id:
                version = self.repo.get_version(document.current_version_id)
                if version:
                    version.status = "changes_requested"
            self.repo.add_approval(
                document_version_id=document.current_version_id,
                approver_id=user_id,
                decision="changes_requested",
                note=body.note,
            )
            self.db.commit()
            AuditService(self.db).record(
                project_id=project_id,
                user_id=user_id,
                action="deliverable.changes_requested",
                summary="Requested changes on deliverable",
                resource_type="generated_document",
                resource_id=document.id,
            )
            return self.get_document(project_id, document_id, user_id)

        validation = self.validation.validate_document(project_id, document_id)
        if not validation.ok:
            raise ValidationAppError(
                "Cannot approve deliverable while validation errors remain: "
                + "; ".join(i.message for i in validation.issues if i.severity == "error")[:500]
            )

        now = datetime.now(timezone.utc)
        document.status = "approved"
        document.approved_by = user_id
        document.approved_at = now
        document.updated_at = now
        if document.current_version_id:
            version = self.repo.get_version(document.current_version_id)
            if version:
                version.status = "approved"
                version.approved_by = user_id
                version.approved_at = now
            self.repo.add_approval(
                document_version_id=document.current_version_id,
                approver_id=user_id,
                decision="approved",
                note=body.note,
            )
        self.db.commit()
        AuditService(self.db).record(
            project_id=project_id,
            user_id=user_id,
            action="deliverable.approve",
            summary="Approved deliverable",
            resource_type="generated_document",
            resource_id=document.id,
        )
        return self.get_document(project_id, document_id, user_id)

    def revise(
        self, project_id: UUID, document_id: UUID, user_id: UUID
    ) -> GeneratedDocumentOut:
        document = self._get_document(project_id, document_id, user_id)
        if document.status != "approved":
            raise ValidationAppError("Only approved deliverables can be revised")
        if document.current_version_id is None:
            raise ValidationAppError("Missing current version")

        old_version = self.repo.get_version(document.current_version_id)
        assert old_version is not None
        old_version.status = "superseded"
        document.status = "draft"
        document.approved_by = None
        document.approved_at = None

        new_major = old_version.version_major
        new_minor = old_version.version_minor + 1
        new_patch = 0
        new_version = self.repo.create_version(
            document_id=document.id,
            project_id=project_id,
            version_label=f"{new_major}.{new_minor}.{new_patch}",
            version_major=new_major,
            version_minor=new_minor,
            version_patch=new_patch,
            status="draft",
            source_snapshot_id=document.source_snapshot_id,
            template_version_id=document.template_version_id,
            created_by=user_id,
        )

        for section in self.repo.list_sections(old_version.id):
            new_section = self.repo.add_section(
                document_version_id=new_version.id,
                section_type=section.section_type,
                title=section.title,
                sequence=section.sequence,
                status="draft",
                confidence=section.confidence,
                assumptions_json=list(section.assumptions_json or []),
            )
            for item in self.repo.list_content_items(section.id):
                new_item = self.repo.add_content_item(
                    section_id=new_section.id,
                    content_type=item.content_type,
                    text=item.text,
                    structured_data=item.structured_data or {},
                    confidence=item.confidence,
                    approval_status="draft",
                    sort_order=item.sort_order,
                    review_required=item.review_required,
                )
                for ref in self.repo.list_source_refs(item.id):
                    self.repo.add_source_ref(
                        content_item_id=new_item.id,
                        ref_kind=ref.ref_kind,
                        ref_id=ref.ref_id,
                        label=ref.label,
                    )

        self.repo.set_current_version(document, new_version)
        self.db.commit()
        AuditService(self.db).record(
            project_id=project_id,
            user_id=user_id,
            action="deliverable.revise",
            summary=f"Created revision {new_version.version_label}",
            resource_type="generated_document",
            resource_id=document.id,
        )
        return self.get_document(project_id, document_id, user_id)

    def _get_document(
        self, project_id: UUID, document_id: UUID, user_id: UUID
    ):
        self._require_project(project_id, user_id)
        document = self.repo.get_document(document_id, project_id)
        if document is None:
            raise NotFoundError("Deliverable not found")
        return document

    def _require_project(self, project_id: UUID, user_id: UUID) -> None:
        if self.projects.get_for_user(project_id, user_id) is None:
            raise NotFoundError("Project not found")

    def _sections_out(
        self, version_id: UUID, *, only_id: UUID | None = None
    ) -> list[DocumentSectionOut]:
        out: list[DocumentSectionOut] = []
        for section in self.repo.list_sections(version_id):
            if only_id is not None and section.id != only_id:
                continue
            items_out: list[ContentItemOut] = []
            for item in self.repo.list_content_items(section.id):
                refs = [
                    SourceRefOut(
                        id=ref.id,
                        ref_kind=ref.ref_kind,
                        ref_id=ref.ref_id,
                        label=ref.label or "",
                    )
                    for ref in self.repo.list_source_refs(item.id)
                ]
                items_out.append(
                    ContentItemOut(
                        id=item.id,
                        content_type=item.content_type,
                        text=item.text,
                        structured_data=item.structured_data or {},
                        confidence=item.confidence,
                        approval_status=item.approval_status,
                        sort_order=item.sort_order,
                        review_required=item.review_required,
                        source_refs=refs,
                    )
                )
            out.append(
                DocumentSectionOut(
                    id=section.id,
                    section_type=section.section_type,
                    title=section.title,
                    sequence=section.sequence,
                    status=section.status,
                    confidence=section.confidence,
                    assumptions=list(section.assumptions_json or []),
                    content_items=items_out,
                )
            )
        return out
