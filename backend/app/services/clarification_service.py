"""Clarification question orchestration."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.factory import get_ai_provider
from app.core.exceptions import NotFoundError, ValidationAppError
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.clarification_repository import ClarificationRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.clarification import ClarificationQuestionOut


class ClarificationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = ProjectRepository(db)
        self.analyses = AnalysisRepository(db)
        self.clarifications = ClarificationRepository(db)

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
        self._require_project(project_id, user_id)
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

        provider = get_ai_provider()
        questions = await provider.generate_clarifications(analysis_payload)
        if not questions:
            raise ValidationAppError("AI provider returned no clarification questions")

        rows = self.clarifications.replace_for_project(
            project_id=project_id,
            questions=questions,
        )
        return [ClarificationQuestionOut.model_validate(row) for row in rows]

    def _require_project(self, project_id: UUID, user_id: UUID) -> None:
        project = self.projects.get_for_user(project_id, user_id)
        if project is None:
            raise NotFoundError("Project not found")
