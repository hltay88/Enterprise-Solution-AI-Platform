"""Phase 4 deliverables API (ATLAS-042)."""

from uuid import UUID

from fastapi import APIRouter

from app.api.deps import ApproverUser, CurrentUser, DbSession, EditorUser
from app.core.responses import success_response
from app.schemas.deliverable import (
    ApproveIn,
    DeliverableGenerateIn,
    ExportIn,
    ReviewIn,
    SectionPatchIn,
    SnapshotCreateIn,
)
from app.services.deliverable_review_service import DeliverableReviewService
from app.services.export_service import ExportService
from app.services.presentation_generation_service import PresentationGenerationService
from app.services.proposal_generation_service import ProposalGenerationService
from app.services.source_snapshot_service import SourceSnapshotService

router = APIRouter(prefix="/projects", tags=["v1-deliverables"])


@router.post("/{project_id}/deliverables/snapshots")
def create_snapshot(
    project_id: UUID,
    current_user: EditorUser,
    db: DbSession,
    body: SnapshotCreateIn | None = None,
) -> dict:
    result = SourceSnapshotService(db).create(project_id, current_user.id, body)
    return success_response(data=result.model_dump(mode="json"), status_code=201)


@router.get("/{project_id}/deliverables/snapshots/{snapshot_id}")
def get_snapshot(
    project_id: UUID,
    snapshot_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    result = SourceSnapshotService(db).get(project_id, snapshot_id, current_user.id)
    return success_response(data=result.model_dump(mode="json"))


@router.post("/{project_id}/deliverables/generate")
async def generate_deliverable(
    project_id: UUID,
    current_user: EditorUser,
    db: DbSession,
    body: DeliverableGenerateIn | None = None,
) -> dict:
    body = body or DeliverableGenerateIn()
    if body.document_type == "presentation":
        result = await PresentationGenerationService(db).generate(
            project_id, current_user.id, body
        )
    else:
        result = await ProposalGenerationService(db).generate(
            project_id, current_user.id, body
        )
    return success_response(data=result.model_dump(mode="json"), status_code=201)


@router.get("/{project_id}/deliverables")
def list_deliverables(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    result = DeliverableReviewService(db).list_documents(project_id, current_user.id)
    return success_response(data=[row.model_dump(mode="json") for row in result])


@router.get("/{project_id}/deliverables/exports/{export_id}")
def get_export(
    project_id: UUID,
    export_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    result = ExportService(db).get(project_id, export_id, current_user.id)
    return success_response(data=result.model_dump(mode="json"))


@router.get("/{project_id}/deliverables/{document_id}")
def get_deliverable(
    project_id: UUID,
    document_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    result = DeliverableReviewService(db).get_document(
        project_id, document_id, current_user.id
    )
    return success_response(data=result.model_dump(mode="json"))


@router.get("/{project_id}/deliverables/{document_id}/sections")
def list_sections(
    project_id: UUID,
    document_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    result = DeliverableReviewService(db).list_sections(
        project_id, document_id, current_user.id
    )
    return success_response(data=[row.model_dump(mode="json") for row in result])


@router.patch("/{project_id}/deliverables/{document_id}/sections/{section_id}")
def patch_section(
    project_id: UUID,
    document_id: UUID,
    section_id: UUID,
    current_user: EditorUser,
    db: DbSession,
    body: SectionPatchIn,
) -> dict:
    result = DeliverableReviewService(db).patch_section(
        project_id, document_id, section_id, current_user.id, body
    )
    return success_response(data=result.model_dump(mode="json"))


@router.post("/{project_id}/deliverables/{document_id}/validate")
def validate_deliverable(
    project_id: UUID,
    document_id: UUID,
    current_user: EditorUser,
    db: DbSession,
) -> dict:
    result = DeliverableReviewService(db).validate(
        project_id, document_id, current_user.id
    )
    return success_response(data=result.model_dump(mode="json"))


@router.post("/{project_id}/deliverables/{document_id}/review")
def review_deliverable(
    project_id: UUID,
    document_id: UUID,
    current_user: EditorUser,
    db: DbSession,
    body: ReviewIn | None = None,
) -> dict:
    result = DeliverableReviewService(db).review(
        project_id, document_id, current_user.id, body
    )
    return success_response(data=result.model_dump(mode="json"))


@router.post("/{project_id}/deliverables/{document_id}/approve")
def approve_deliverable(
    project_id: UUID,
    document_id: UUID,
    current_user: ApproverUser,
    db: DbSession,
    body: ApproveIn | None = None,
) -> dict:
    result = DeliverableReviewService(db).approve(
        project_id, document_id, current_user.id, body
    )
    return success_response(data=result.model_dump(mode="json"))


@router.post("/{project_id}/deliverables/{document_id}/revise")
def revise_deliverable(
    project_id: UUID,
    document_id: UUID,
    current_user: EditorUser,
    db: DbSession,
) -> dict:
    result = DeliverableReviewService(db).revise(
        project_id, document_id, current_user.id
    )
    return success_response(data=result.model_dump(mode="json"), status_code=201)


@router.post("/{project_id}/deliverables/{document_id}/export")
def export_deliverable(
    project_id: UUID,
    document_id: UUID,
    current_user: EditorUser,
    db: DbSession,
    body: ExportIn | None = None,
) -> dict:
    result = ExportService(db).export(project_id, document_id, current_user.id, body)
    return success_response(data=result.model_dump(mode="json"), status_code=201)
