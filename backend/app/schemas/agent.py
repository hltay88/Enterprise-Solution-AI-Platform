"""Sprint 5.3 — specialist agent I/O contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


AgentStatus = Literal["ok", "partial", "blocked", "insufficient_evidence"]


class AgentCitation(BaseModel):
    source_kind: str = "knowledge"
    title: str
    knowledge_id: UUID | None = None
    knowledge_version_id: UUID | None = None
    chunk_id: UUID | None = None
    domain_code: str | None = None
    excerpt: str = ""
    ref_label: str | None = None


class SpecialistFinding(BaseModel):
    code: str
    statement: str
    severity: str = "info"  # info | warning | critical
    evidence: list[str] = Field(default_factory=list)


class SpecialistOutput(BaseModel):
    agent_id: str
    domain_code: str
    status: AgentStatus = "ok"
    summary: str
    findings: list[SpecialistFinding] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    citations: list[AgentCitation] = Field(default_factory=list)
    tools_used: list[str] = Field(default_factory=list)


class OrchestratorConflict(BaseModel):
    code: str
    summary: str
    agents: list[str] = Field(default_factory=list)
    severity: str = "warning"


class AgentRunRequest(BaseModel):
    goal: str | None = Field(default=None, max_length=2000)
    focus_domains: list[str] = Field(default_factory=list)
    include_agents: list[str] = Field(default_factory=list)


class AgentSummaryOut(BaseModel):
    id: str
    name: str
    domain_code: str
    description: str
    enabled: bool
    runnable: bool
    version: str


class AgentRunSummaryOut(BaseModel):
    id: UUID
    project_id: UUID
    status: str
    goal: str | None = None
    focus_domains: list[str] = Field(default_factory=list)
    overall_confidence: float | None = None
    conflict_count: int = 0
    created_at: datetime
    completed_at: datetime | None = None


class AgentToolCallOut(BaseModel):
    id: UUID
    agent_id: str | None = None
    tool_name: str
    ok: bool
    error: str | None = None
    latency_ms: int | None = None
    created_at: datetime


class AgentRunDetailOut(AgentRunSummaryOut):
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    specialists: list[SpecialistOutput] = Field(default_factory=list)
    conflicts: list[OrchestratorConflict] = Field(default_factory=list)
    tool_calls: list[AgentToolCallOut] = Field(default_factory=list)
    error: str | None = None
    review_required: bool = False
