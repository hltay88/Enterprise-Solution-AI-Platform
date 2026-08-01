"""Project persistence."""

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project


class ProjectRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_user(self, user_id: UUID) -> list[Project]:
        statement = (
            select(Project)
            .where(Project.user_id == user_id)
            .order_by(Project.updated_at.desc())
        )
        return list(self.db.scalars(statement).all())

    def get_for_user(self, project_id: UUID, user_id: UUID) -> Project | None:
        statement = select(Project).where(
            Project.id == project_id,
            Project.user_id == user_id,
        )
        return self.db.scalar(statement)

    def create(
        self,
        *,
        user_id: UUID,
        project_name: str,
        customer: str | None,
        industry: str | None,
        status: str,
        account_manager: str | None,
        deal_id: str | None,
        deal_name: str | None,
        pic_name: str | None,
        pic_contact: str | None,
        pic_designation: str | None,
        budget_information: str | None,
        request_type: str | None,
        required_completion_date: date | None,
        requirement_details: str | None,
        winning_probability: int | None,
    ) -> Project:
        project = Project(
            user_id=user_id,
            project_name=project_name,
            customer=customer,
            industry=industry,
            status=status,
            account_manager=account_manager,
            deal_id=deal_id,
            deal_name=deal_name,
            pic_name=pic_name,
            pic_contact=pic_contact,
            pic_designation=pic_designation,
            budget_information=budget_information,
            request_type=request_type,
            required_completion_date=required_completion_date,
            requirement_details=requirement_details,
            winning_probability=winning_probability,
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def save(self, project: Project) -> Project:
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def delete(self, project: Project) -> None:
        self.db.delete(project)
        self.db.commit()
