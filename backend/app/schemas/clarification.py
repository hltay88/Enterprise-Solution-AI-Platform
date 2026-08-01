"""Clarification API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ClarificationQuestionOut(BaseModel):
    id: UUID
    project_id: UUID
    question: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
