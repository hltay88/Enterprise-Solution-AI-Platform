"""Project persistence."""

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project


class ProjectRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_user(
        self,
        user_id: UUID,
        *,
        tenant_id: UUID | None = None,
    ) -> list[Project]:
        statement = select(Project).where(Project.user_id == user_id)
        if tenant_id is not None:
            statement = statement.where(
                (Project.tenant_id == tenant_id) | (Project.tenant_id.is_(None)),
            )
        statement = statement.order_by(Project.updated_at.desc())
        return list(self.db.scalars(statement).all())

    def get_for_user(
        self,
        project_id: UUID,
        user_id: UUID,
        *,
        tenant_id: UUID | None = None,
    ) -> Project | None:
        statement = select(Project).where(
            Project.id == project_id,
            Project.user_id == user_id,
        )
        project = self.db.scalar(statement)
        if project is None:
            return None
        if tenant_id is not None and project.tenant_id is not None and project.tenant_id != tenant_id:
            return None
        return project

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
        tenant_id: UUID | None = None,
    ) -> Project:
        project = Project(
            user_id=user_id,
            tenant_id=tenant_id,
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
