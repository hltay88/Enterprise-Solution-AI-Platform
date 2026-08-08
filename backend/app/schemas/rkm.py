"""Pydantic schemas for Draft RKM APIs (Stage C)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class EvidenceOut(BaseModel):
    id: UUID
    source_type: str
    document_id: UUID | None = None
    page: int | None = None
    excerpt: str | None = None
    field_name: str | None = None
    note: str | None = None


class RequirementOut(BaseModel):
    id: UUID
    category: str | None = None
    subcategory: str | None = None
    title: str
    description: str
    priority: str = "medium"
    status: str = "draft"
    confidence: float = 0
    evidence_ids: list[UUID] = Field(default_factory=list)


class EnvironmentItemOut(BaseModel):
    id: UUID
    title: str
    description: str
    evidence_ids: list[UUID] = Field(default_factory=list)


class StakeholderOut(BaseModel):
    id: UUID
    name: str
    role: str | None = None
    contact: str | None = None
    designation: str | None = None
    evidence_ids: list[UUID] = Field(default_factory=list)


class RkmProjectOut(BaseModel):
    project_name: str
    customer: str | None = None
    industry: str | None = None
    account_manager: str | None = None
    deal_id: str | None = None
    deal_name: str | None = None
    request_type: str | None = None
    required_completion_date: str | None = None
    budget_information: str | None = None
    winning_probability: int | None = None


class RkmAnalysisOut(BaseModel):
    confidence_score: float = 0
    completeness_score: float = 0
    consistency_score: float = 0
    evidence_coverage: float = 0
    reasoning_summary: str = ""
    prompt_version: str | None = None
    model: str | None = None


class RkmVersionOut(BaseModel):
    number: str
    major: int
    minor: int
    patch: int
    created_at: datetime
    updated_at: datetime
    change_summary: str | None = None


class RkmApprovalOut(BaseModel):
    status: str
    reviewed_by: str | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    published_at: datetime | None = None


class RkmDraftOut(BaseModel):
    id: UUID
    project_id: UUID
    project: RkmProjectOut
    business_objectives: list[RequirementOut] = Field(default_factory=list)
    current_environment: dict[str, Any] = Field(default_factory=dict)
    functional_requirements: list[RequirementOut] = Field(default_factory=list)
    non_functional_requirements: list[RequirementOut] = Field(default_factory=list)
    constraints: list[RequirementOut] = Field(default_factory=list)
    dependencies: list[RequirementOut] = Field(default_factory=list)
    risks: list[RequirementOut] = Field(default_factory=list)
    assumptions: list[RequirementOut] = Field(default_factory=list)
    stakeholders: list[StakeholderOut] = Field(default_factory=list)
    clarification_questions: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[EvidenceOut] = Field(default_factory=list)
    analysis: RkmAnalysisOut
    approval: RkmApprovalOut
    version: RkmVersionOut


class RkmVersionSummary(BaseModel):
    id: UUID
    project_id: UUID
    status: str
    version_label: str
    is_active_draft: bool
    confidence_score: float
    completeness_score: float
    created_at: datetime
    updated_at: datetime


class RkmAnalyzeAccepted(BaseModel):
    project_id: UUID
    job_id: UUID
    status: str = "queued"
    message: str = "RKM generation job accepted"
