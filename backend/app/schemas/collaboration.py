"""Sprint 5.4 — collaboration and usage schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=8000)
    parent_id: UUID | None = None
    resource_type: str | None = Field(default=None, max_length=64)
    resource_id: UUID | None = None


class CommentOut(BaseModel):
    id: UUID
    project_id: UUID
    user_id: UUID | None = None
    parent_id: UUID | None = None
    body: str
    resource_type: str | None = None
    resource_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class ReviewRequestCreate(BaseModel):
    resource_type: str = Field(min_length=1, max_length=64)
    resource_id: UUID | None = None
    assignee_id: UUID | None = None
    message: str = Field(default="", max_length=4000)


class ReviewRequestOut(BaseModel):
    id: UUID
    project_id: UUID
    resource_type: str
    resource_id: UUID | None = None
    requested_by: UUID | None = None
    assignee_id: UUID | None = None
    status: str
    message: str
    resolution_note: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class ReviewRequestComplete(BaseModel):
    resolution_note: str | None = Field(default=None, max_length=4000)


class ApprovalRequestCreate(BaseModel):
    resource_type: str = Field(min_length=1, max_length=64)
    resource_id: UUID | None = None
    assignee_id: UUID | None = None
    message: str = Field(default="", max_length=4000)


class ApprovalRequestOut(BaseModel):
    id: UUID
    project_id: UUID
    resource_type: str
    resource_id: UUID | None = None
    requested_by: UUID | None = None
    assignee_id: UUID | None = None
    status: str
    message: str
    resolution_note: str | None = None
    resolved_by: UUID | None = None
    created_at: datetime
    resolved_at: datetime | None = None


class ApprovalRequestResolve(BaseModel):
    decision: Literal["approved", "rejected"]
    resolution_note: str | None = Field(default=None, max_length=4000)


class ActivityItemOut(BaseModel):
    kind: str
    id: UUID
    project_id: UUID | None = None
    summary: str
    actor_user_id: UUID | None = None
    resource_type: str | None = None
    resource_id: UUID | None = None
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuditEventOut(BaseModel):
    id: UUID
    project_id: UUID | None = None
    user_id: UUID | None = None
    action: str
    resource_type: str | None = None
    resource_id: UUID | None = None
    summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class UsageRecordOut(BaseModel):
    id: UUID
    event_type: str
    provider: str | None = None
    model: str | None = None
    latency_ms: int | None = None
    token_input: int | None = None
    token_output: int | None = None
    estimated_cost_usd: float | None = None
    success: bool
    error_code: str | None = None
    user_id: UUID | None = None
    project_id: UUID | None = None
    tenant_id: UUID | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class UsageSummaryOut(BaseModel):
    total: int
    success_count: int
    failure_count: int
    by_event_type: dict[str, int] = Field(default_factory=dict)
    avg_latency_ms: float | None = None
