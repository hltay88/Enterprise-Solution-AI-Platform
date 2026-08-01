"""Project schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectSummary(BaseModel):
    id: UUID
    project_name: str
    customer: str | None = None
    industry: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectCreate(BaseModel):
    project_name: str = Field(min_length=1, max_length=255)
    customer: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=255)
    status: str = Field(default="draft", min_length=1, max_length=64)


class ProjectUpdate(BaseModel):
    project_name: str | None = Field(default=None, min_length=1, max_length=255)
    customer: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=255)
    status: str | None = Field(default=None, min_length=1, max_length=64)
