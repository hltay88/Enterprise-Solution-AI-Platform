"""Requirement analysis orchestration."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.factory import get_ai_provider
from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.project import Project
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
        project = self._require_project(project_id, user_id)
        source_text = self._build_analysis_source(project)
        if not source_text:
            raise ValidationAppError(
                "Add sales intake requirement details and/or upload at least one "
                "requirement document with extractable text before analysis",
            )

        provider = get_ai_provider()
        result = await provider.analyze_requirements(source_text)

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

    def _require_project(self, project_id: UUID, user_id: UUID) -> Project:
        project = self.projects.get_for_user(project_id, user_id)
        if project is None:
            raise NotFoundError("Project not found")
        return project

    def _build_analysis_source(self, project: Project) -> str:
        parts: list[str] = []
        intake = _format_sales_intake(project)
        if intake:
            parts.append(intake)
        documents = self._combined_document_text(project.id)
        if documents:
            parts.append("# Uploaded requirement documents\n\n" + documents)
        return "\n\n".join(parts).strip()

    def _combined_document_text(self, project_id: UUID) -> str:
        docs = self.documents.list_for_project(project_id)
        parts = [
            f"# Document: {doc.filename}\n{doc.extracted_text.strip()}"
            for doc in docs
            if doc.extracted_text and doc.extracted_text.strip()
        ]
        return "\n\n".join(parts).strip()


def _format_sales_intake(project: Project) -> str:
    lines = ["# Sales intake"]
    pairs = [
        ("Project name", project.project_name),
        ("Customer name", project.customer),
        ("Industry", project.industry),
        ("Account manager", project.account_manager),
        ("Deal ID", project.deal_id),
        ("Deal name", project.deal_name),
        ("Request type", project.request_type),
        ("PIC name", project.pic_name),
        ("PIC contact", project.pic_contact),
        ("PIC designation", project.pic_designation),
        ("Budget information", project.budget_information),
        (
            "Required completion date",
            project.required_completion_date.isoformat()
            if project.required_completion_date
            else None,
        ),
        (
            "Winning probability %",
            str(project.winning_probability)
            if project.winning_probability is not None
            else None,
        ),
        ("Project status", project.status),
    ]
    for label, value in pairs:
        if value and str(value).strip():
            lines.append(f"- {label}: {str(value).strip()}")

    details = (project.requirement_details or "").strip()
    if details:
        lines.append("")
        lines.append("## Requirement details")
        lines.append(details)

    # Only intake header means no useful content.
    if len(lines) <= 1:
        return ""
    return "\n".join(lines).strip()
