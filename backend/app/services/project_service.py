"""Project business logic."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectSummary


class ProjectService:
    def __init__(self, db: Session) -> None:
        self.projects = ProjectRepository(db)

    def list_for_user(self, user_id: UUID) -> list[ProjectSummary]:
        rows = self.projects.list_for_user(user_id)
        return [ProjectSummary.model_validate(row) for row in rows]
