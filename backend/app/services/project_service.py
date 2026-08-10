"""Project business logic."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectSummary, ProjectUpdate

_OPTIONAL_TEXT_FIELDS = (
    "customer",
    "industry",
    "account_manager",
    "deal_id",
    "deal_name",
    "pic_name",
    "pic_contact",
    "pic_designation",
    "budget_information",
    "request_type",
    "requirement_details",
)


class ProjectService:
    def __init__(self, db: Session) -> None:
        self.projects = ProjectRepository(db)

    def list_for_user(self, user_id: UUID, *, tenant_id: UUID | None = None) -> list[ProjectSummary]:
        rows = self.projects.list_for_user(user_id, tenant_id=tenant_id)
        return [ProjectSummary.model_validate(row) for row in rows]

    def get_for_user(
        self,
        project_id: UUID,
        user_id: UUID,
        *,
        tenant_id: UUID | None = None,
    ) -> ProjectSummary:
        project = self.projects.get_for_user(project_id, user_id, tenant_id=tenant_id)
        if project is None:
            raise NotFoundError("Project not found")
        return ProjectSummary.model_validate(project)

    def create(
        self,
        user_id: UUID,
        payload: ProjectCreate,
        *,
        default_account_manager: str | None = None,
        tenant_id: UUID | None = None,
    ) -> ProjectSummary:
        account_manager = _clean_optional(payload.account_manager) or _clean_optional(
            default_account_manager
        )
        project = self.projects.create(
            user_id=user_id,
            tenant_id=tenant_id,
            project_name=payload.project_name.strip(),
            customer=payload.customer.strip(),
            industry=_clean_optional(payload.industry),
            status=payload.status.strip() or "draft",
            account_manager=account_manager,
            deal_id=payload.deal_id.strip(),
            deal_name=payload.deal_name.strip(),
            pic_name=payload.pic_name.strip(),
            pic_contact=_clean_optional(payload.pic_contact),
            pic_designation=_clean_optional(payload.pic_designation),
            budget_information=_clean_optional(payload.budget_information),
            request_type=payload.request_type.strip(),
            required_completion_date=payload.required_completion_date,
            requirement_details=payload.requirement_details.strip(),
            winning_probability=payload.winning_probability,
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
        if "status" in data and data["status"] is not None:
            project.status = data["status"].strip() or project.status
        if "required_completion_date" in data:
            project.required_completion_date = data["required_completion_date"]
        if "winning_probability" in data:
            project.winning_probability = data["winning_probability"]

        for field in _OPTIONAL_TEXT_FIELDS:
            if field in data:
                setattr(project, field, _clean_optional(data[field]))

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
