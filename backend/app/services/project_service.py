"""Project business logic."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectSummary, ProjectUpdate


class ProjectService:
    def __init__(self, db: Session) -> None:
        self.projects = ProjectRepository(db)

    def list_for_user(self, user_id: UUID) -> list[ProjectSummary]:
        rows = self.projects.list_for_user(user_id)
        return [ProjectSummary.model_validate(row) for row in rows]

    def get_for_user(self, project_id: UUID, user_id: UUID) -> ProjectSummary:
        project = self.projects.get_for_user(project_id, user_id)
        if project is None:
            raise NotFoundError("Project not found")
        return ProjectSummary.model_validate(project)

    def create(self, user_id: UUID, payload: ProjectCreate) -> ProjectSummary:
        project = self.projects.create(
            user_id=user_id,
            project_name=payload.project_name.strip(),
            customer=_clean_optional(payload.customer),
            industry=_clean_optional(payload.industry),
            status=payload.status.strip() or "draft",
        )
        return ProjectSummary.model_validate(project)

    def update(
        self,
        project_id: UUID,
        user_id: UUID,
        payload: ProjectUpdate,
    ) -> ProjectSummary:
        project = self.projects.get_for_user(project_id, user_id)
        if project is None:
            raise NotFoundError("Project not found")

        data = payload.model_dump(exclude_unset=True)
        if "project_name" in data and data["project_name"] is not None:
            project.project_name = data["project_name"].strip()
        if "customer" in data:
            project.customer = _clean_optional(data["customer"])
        if "industry" in data:
            project.industry = _clean_optional(data["industry"])
        if "status" in data and data["status"] is not None:
            project.status = data["status"].strip() or project.status

        project.updated_at = datetime.now(timezone.utc)
        saved = self.projects.save(project)
        return ProjectSummary.model_validate(saved)

    def delete(self, project_id: UUID, user_id: UUID) -> None:
        project = self.projects.get_for_user(project_id, user_id)
        if project is None:
            raise NotFoundError("Project not found")
        self.projects.delete(project)


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None
