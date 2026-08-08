"""Audit log API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    project_id: UUID
    user_id: UUID | None = None
    action: str
    resource_type: str | None = None
    resource_id: UUID | None = None
    summary: str = ""
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="metadata_json",
        serialization_alias="metadata",
    )
    created_at: datetime
