"""Project schemas including Sprint 1.1 sales intake fields."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.constants.request_types import REQUEST_TYPES


class ProjectSummary(BaseModel):
    id: UUID
    project_name: str
    customer: str | None = None
    industry: str | None = None
    status: str
    account_manager: str | None = None
    deal_id: str | None = None
    deal_name: str | None = None
    pic_name: str | None = None
    pic_contact: str | None = None
    pic_designation: str | None = None
    budget_information: str | None = None
    request_type: str | None = None
    required_completion_date: date | None = None
    requirement_details: str | None = None
    winning_probability: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectCreate(BaseModel):
    project_name: str = Field(min_length=1, max_length=255)
    customer: str = Field(min_length=1, max_length=255)
    industry: str | None = Field(default=None, max_length=255)
    status: str = Field(default="draft", min_length=1, max_length=64)
    account_manager: str | None = Field(default=None, max_length=255)
    deal_id: str = Field(min_length=1, max_length=128)
    deal_name: str = Field(min_length=1, max_length=255)
    pic_name: str = Field(min_length=1, max_length=255)
    pic_contact: str | None = Field(default=None, max_length=255)
    pic_designation: str | None = Field(default=None, max_length=255)
    budget_information: str | None = Field(default=None, max_length=255)
    request_type: str = Field(min_length=1, max_length=64)
    required_completion_date: date | None = None
    requirement_details: str = Field(min_length=1, max_length=20000)
    winning_probability: int | None = Field(default=None, ge=0, le=100)

    @field_validator("request_type")
    @classmethod
    def validate_request_type(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned not in REQUEST_TYPES:
            allowed = ", ".join(REQUEST_TYPES)
            raise ValueError(f"request_type must be one of: {allowed}")
        return cleaned


class ProjectUpdate(BaseModel):
    project_name: str | None = Field(default=None, min_length=1, max_length=255)
    customer: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=255)
    status: str | None = Field(default=None, min_length=1, max_length=64)
    account_manager: str | None = Field(default=None, max_length=255)
    deal_id: str | None = Field(default=None, max_length=128)
    deal_name: str | None = Field(default=None, max_length=255)
    pic_name: str | None = Field(default=None, max_length=255)
    pic_contact: str | None = Field(default=None, max_length=255)
    pic_designation: str | None = Field(default=None, max_length=255)
    budget_information: str | None = Field(default=None, max_length=255)
    request_type: str | None = Field(default=None, max_length=64)
    required_completion_date: date | None = None
    requirement_details: str | None = Field(default=None, max_length=20000)
    winning_probability: int | None = Field(default=None, ge=0, le=100)

    @field_validator("request_type")
    @classmethod
    def validate_request_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            return None
        if cleaned not in REQUEST_TYPES:
            allowed = ", ".join(REQUEST_TYPES)
            raise ValueError(f"request_type must be one of: {allowed}")
        return cleaned
