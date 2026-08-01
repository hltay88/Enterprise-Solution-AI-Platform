"""Requirement analysis orchestration."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.factory import get_ai_provider
from app.core.exceptions import NotFoundError, ValidationAppError
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.analysis import AnalysisResult


class AnalysisService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = ProjectRepository(db)
        self.documents = DocumentRepository(db)
        self.analyses = AnalysisRepository(db)

    def get_latest(self, project_id: UUID, user_id: UUID) -> AnalysisResult:
        self._require_project(project_id, user_id)
        row = self.analyses.get_latest_for_project(project_id)
        if row is None:
            raise NotFoundError("No analysis found for this project")
        return AnalysisResult.model_validate(row)

    async def analyze(self, project_id: UUID, user_id: UUID) -> AnalysisResult:
        self._require_project(project_id, user_id)
        document_text = self._combined_document_text(project_id)
        if not document_text:
            raise ValidationAppError(
                "Upload at least one requirement document with extractable text before analysis",
            )

        provider = get_ai_provider()
        result = await provider.analyze_requirements(document_text)

        row = self.analyses.create(
            project_id=project_id,
            business_objectives=result["business_objectives"],
            functional_requirements=result["functional_requirements"],
            non_functional_requirements=result["non_functional_requirements"],
            assumptions=result["assumptions"],
            risks=result["risks"],
            analysis_json=result,
        )
        return AnalysisResult.model_validate(row)

    def _require_project(self, project_id: UUID, user_id: UUID) -> None:
        project = self.projects.get_for_user(project_id, user_id)
        if project is None:
            raise NotFoundError("Project not found")

    def _combined_document_text(self, project_id: UUID) -> str:
        docs = self.documents.list_for_project(project_id)
        parts = [
            f"# Document: {doc.filename}\n{doc.extracted_text.strip()}"
            for doc in docs
            if doc.extracted_text and doc.extracted_text.strip()
        ]
        return "\n\n".join(parts).strip()
