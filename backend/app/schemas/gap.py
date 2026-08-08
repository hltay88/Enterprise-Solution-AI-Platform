"""Schemas for Stage D gap analysis and RKM clarifications."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class GapItem(BaseModel):
    code: str
    section: str
    severity: str  # critical | high | medium | low
    message: str
    affected_requirement_ids: list[UUID] = Field(default_factory=list)


class PublishBlocker(BaseModel):
    code: str
    message: str


class ConflictItem(BaseModel):
    code: str
    message: str
    affected_requirement_ids: list[UUID] = Field(default_factory=list)


class ClarificationOut(BaseModel):
    id: UUID
    question: str
    priority: str
    category: str
    reason: str
    affected_requirement_ids: list[UUID] = Field(default_factory=list)
    status: str = "open"  # open | answered | dismissed
    answer: str | None = None
    confidence_impact: float | None = None


class GapAnalysisOut(BaseModel):
    project_id: UUID
    rkm_id: UUID
    version_label: str
    completeness_score: float
    confidence_score: float
    consistency_score: float
    evidence_coverage: float
    overall_quality: float
    quality_level: str
    missing_sections: list[str] = Field(default_factory=list)
    gaps: list[GapItem] = Field(default_factory=list)
    conflicts: list[ConflictItem] = Field(default_factory=list)
    publish_blockers: list[PublishBlocker] = Field(default_factory=list)
    clarifications: list[ClarificationOut] = Field(default_factory=list)
    created_at: datetime | None = None


class ClarificationAnswerIn(BaseModel):
    clarification_id: UUID
    answer: str


class ClarificationAnswerBatchIn(BaseModel):
    answers: list[ClarificationAnswerIn]


class ClarificationAnswerResult(BaseModel):
    project_id: UUID
    rkm_id: UUID
    version_label: str
    answered_count: int
    clarifications: list[ClarificationOut]
    draft: dict[str, Any] | None = None
