"""Clarification question orchestration."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.factory import get_ai_provider
from app.core.exceptions import NotFoundError, ValidationAppError
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.clarification_repository import ClarificationRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.clarification import ClarificationQuestionOut
from app.services.analysis_service import AnalysisService
from app.services.domain_checklists import build_checklist_context, detect_domains


class ClarificationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = ProjectRepository(db)
        self.analyses = AnalysisRepository(db)
        self.clarifications = ClarificationRepository(db)
        self.analysis_service = AnalysisService(db)

    def list_for_project(
        self,
        project_id: UUID,
        user_id: UUID,
    ) -> list[ClarificationQuestionOut]:
        self._require_project(project_id, user_id)
        rows = self.clarifications.list_for_project(project_id)
        return [ClarificationQuestionOut.model_validate(row) for row in rows]

    async def generate(
        self,
        project_id: UUID,
        user_id: UUID,
    ) -> list[ClarificationQuestionOut]:
        project = self._require_project(project_id, user_id)
        analysis = self.analyses.get_latest_for_project(project_id)
        if analysis is None:
            raise ValidationAppError(
                "Run requirement analysis before generating clarification questions",
            )

        analysis_payload = analysis.analysis_json or {
            "business_objectives": analysis.business_objectives,
            "functional_requirements": analysis.functional_requirements,
            "non_functional_requirements": analysis.non_functional_requirements,
            "assumptions": analysis.assumptions,
            "risks": analysis.risks,
        }

        document_text = self.analysis_service.build_source_text(project)
        analysis_blob = "\n".join(str(value) for value in analysis_payload.values())
        domains = detect_domains(document_text, analysis_blob)
        checklist_context = build_checklist_context(domains)
        min_questions, max_questions = _question_budget(domains)

        provider = get_ai_provider()
        questions = await provider.generate_clarifications(
            analysis_payload,
            document_text=document_text,
            checklist_context=checklist_context,
            detected_domains=domains,
            min_questions=min_questions,
            max_questions=max_questions,
        )
        if not questions:
            raise ValidationAppError("AI provider returned no clarification questions")

        rows = self.clarifications.replace_for_project(
            project_id=project_id,
            questions=questions,
        )
        return [ClarificationQuestionOut.model_validate(row) for row in rows]

    def _require_project(self, project_id: UUID, user_id: UUID):
        project = self.projects.get_for_user(project_id, user_id)
        if project is None:
            raise NotFoundError("Project not found")
        return project


def _question_budget(domains: list[str]) -> tuple[int, int]:
    count = len(domains)
    if count == 0:
        return 8, 12
    if count == 1:
        return 12, 18
    if count == 2:
        return 14, 20
    if count == 3:
        return 16, 22
    return 18, 24
