"""Phase 3 solution domain identification APIs under /api/v1 (ATLAS-031)."""

from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession, EditorUser
from app.core.responses import success_response
from app.services.domain_identification_service import DomainIdentificationService

router = APIRouter(prefix="/projects", tags=["v1-domains"])


@router.post("/{project_id}/domains/analyze")
async def analyze_domains(
    project_id: UUID,
    current_user: EditorUser,
    db: DbSession,
) -> dict:
    result = await DomainIdentificationService(db).analyze(project_id, current_user.id)
    return success_response(data=result.model_dump(mode="json"), status_code=201)


@router.get("/{project_id}/domains/versions")
def list_domain_versions(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    result = DomainIdentificationService(db).list_versions(project_id, current_user.id)
    return success_response(
        data=[item.model_dump(mode="json") for item in result],
    )


@router.get("/{project_id}/domains/{analysis_id}")
def get_domain_analysis(
    project_id: UUID,
    analysis_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    result = DomainIdentificationService(db).get_by_id(
        project_id,
        analysis_id,
        current_user.id,
    )
    return success_response(data=result.model_dump(mode="json"))


@router.get("/{project_id}/domains")
def get_latest_domains(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    result = DomainIdentificationService(db).get_latest(project_id, current_user.id)
    return success_response(data=result.model_dump(mode="json"))


@router.get("/{project_id}/traceability")
def get_traceability(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
    analysis_id: UUID | None = Query(default=None),
) -> dict:
    result = DomainIdentificationService(db).get_traceability(
        project_id,
        current_user.id,
        analysis_id=analysis_id,
    )
    return success_response(
        data=[item.model_dump(mode="json") for item in result],
    )
