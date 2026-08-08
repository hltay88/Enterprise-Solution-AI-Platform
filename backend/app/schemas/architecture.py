"""Phase 3 architecture recommendation schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class TechStackItem(BaseModel):
    layer: str
    category: str
    rationale: str = ""


class SolutionComponent(BaseModel):
    name: str
    purpose: str = ""
    maps_to_requirements: list[str] = Field(default_factory=list)


class ArchitectureDecision(BaseModel):
    decision: str
    rationale: str = ""
    impact: str = ""


class ArchitectureAlternative(BaseModel):
    name: str
    summary: str = ""
    tradeoffs: str = ""


class ArchitectureOut(BaseModel):
    id: UUID
    project_id: UUID
    rkm_id: UUID | None = None
    rkm_version_label: str | None = None
    status: str
    version_label: str
    summary: str = ""
    high_level_architecture: list[str] = Field(default_factory=list)
    logical_architecture: list[str] = Field(default_factory=list)
    physical_architecture: list[str] = Field(default_factory=list)
    technology_stack: list[TechStackItem] = Field(default_factory=list)
    solution_components: list[SolutionComponent] = Field(default_factory=list)
    design_assumptions: list[str] = Field(default_factory=list)
    technical_risks: list[str] = Field(default_factory=list)
    architecture_decisions: list[ArchitectureDecision] = Field(default_factory=list)
    alternatives: list[ArchitectureAlternative] = Field(default_factory=list)
    reasoning_summary: str = ""
    model: str | None = None
    prompt_version: str | None = None
    created_at: datetime
    updated_at: datetime
    payload: dict[str, Any] = Field(default_factory=dict)
