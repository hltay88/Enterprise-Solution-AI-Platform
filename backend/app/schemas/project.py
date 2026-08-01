"""Project schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ProjectSummary(BaseModel):
    id: UUID
    project_name: str
    customer: str | None = None
    industry: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
