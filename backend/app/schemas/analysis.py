"""Analysis API schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class AnalysisResult(BaseModel):
    id: UUID
    project_id: UUID
    business_objectives: str | None = None
    functional_requirements: str | None = None
    non_functional_requirements: str | None = None
    assumptions: str | None = None
    risks: str | None = None
    analysis_json: dict[str, Any] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
