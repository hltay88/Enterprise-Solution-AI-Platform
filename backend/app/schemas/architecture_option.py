"""Phase 3 Sprint 3.2 — architecture candidate AI + API schemas.

Task 3 only: typed contracts for AI extraction validation and API responses.
Does not persist data or call AI providers. MVP ``schemas/architecture.py``
remains for the transitional singular generate/get path (ATLAS-034).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.services.phase3_pattern_catalog import PatternCatalogError, require_pattern_code

ArchitectureStatus = Literal["draft", "recommended"]
ComponentKind = Literal["business", "functional", "logical", "physical", "technology", "operations"]
RiskProbability = Literal["low", "medium", "high"]
RiskSeverity = Literal["low", "medium", "high", "critical"]
AssumptionStatus = Literal["unvalidated", "validated", "rejected"]

DEFAULT_SCORE_WEIGHTS: dict[str, float] = {
    "requirement_coverage": 0.30,
    "technical_fit": 0.20,
    "security": 0.10,
    "availability_resilience": 0.10,
    "scalability": 0.10,
    "operability": 0.05,
    "lifecycle": 0.05,
    "complexity": 0.05,
    "commercial_suitability": 0.05,
}

ALLOWED_SCORE_DIMENSIONS: frozenset[str] = frozenset(DEFAULT_SCORE_WEIGHTS)


def _normalize_confidence(value: Any) -> float:
    """Accept 0–1 or 0–100; return clamped 0–1."""
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("confidence must be a number") from exc
    if number > 1.0:
        number = number / 100.0
    if number < 0.0 or number > 1.0:
        raise ValueError("confidence must be between 0 and 1 (or 0–100)")
    return round(number, 4)


def _normalize_score_0_5(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("score must be a number") from exc
    if number < 0.0 or number > 5.0:
        raise ValueError("score must be between 0 and 5")
    return round(number, 2)


def _string_list(value: Any, *, field: str) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    out: list[str] = []
    for item in value:
        if isinstance(item, dict):
            text = str(item.get("id") or item.get("requirement_id") or "").strip()
        else:
            text = str(item or "").strip()
        if text:
            out.append(text)
    return out


def _resolve_pattern_code(value: Any) -> str:
    try:
        return require_pattern_code(str(value or ""))
    except PatternCatalogError as exc:
        raise ValueError(str(exc)) from exc


# --- AI extraction -------------------------------------------------------------------


class ArchitectureComponentAI(BaseModel):
    name: str
    purpose: str = ""
    component_kind: ComponentKind = "logical"
    maps_to_requirements: list[str] = Field(default_factory=list)
    temp_id: str | None = None

    @field_validator("name", mode="before")
    @classmethod
    def _name_required(cls, value: Any) -> str:
        text = str(value or "").strip()
        if not text:
            raise ValueError("component name is required")
        return text

    @field_validator("purpose", mode="before")
    @classmethod
    def _purpose(cls, value: Any) -> str:
        return str(value or "").strip()

    @field_validator("component_kind", mode="before")
    @classmethod
    def _kind(cls, value: Any) -> str:
        text = str(value or "logical").strip().lower()
        aliases = {
            "business": "business",
            "functional": "functional",
            "logical": "logical",
            "physical": "physical",
            "technology": "technology",
            "tech": "technology",
            "operations": "operations",
            "ops": "operations",
        }
        normalized = aliases.get(text)
        if normalized is None:
            raise ValueError(
                "component_kind must be one of: business, functional, logical, "
                "physical, technology, operations",
            )
        return normalized

    @field_validator("maps_to_requirements", mode="before")
    @classmethod
    def _reqs(cls, value: Any) -> list[str]:
        return _string_list(value, field="maps_to_requirements")

    @field_validator("temp_id", mode="before")
    @classmethod
    def _temp_id(cls, value: Any) -> str | None:
        text = str(value or "").strip()
        return text or None


class ArchitectureRelationshipAI(BaseModel):
    from_component: str
    to_component: str
    relationship_kind: str = "connects_to"
    description: str = ""

    @field_validator("from_component", "to_component", mode="before")
    @classmethod
    def _endpoint(cls, value: Any) -> str:
        text = str(value or "").strip()
        if not text:
            raise ValueError("relationship endpoints are required")
        return text

    @field_validator("relationship_kind", mode="before")
    @classmethod
    def _kind(cls, value: Any) -> str:
        text = str(value or "").strip()
        return text or "connects_to"

    @field_validator("description", mode="before")
    @classmethod
    def _description(cls, value: Any) -> str:
        return str(value or "").strip()


class DesignDecisionAI(BaseModel):
    decision: str
    rationale: str = ""
    impact: str = ""

    @field_validator("decision", mode="before")
    @classmethod
    def _decision_required(cls, value: Any) -> str:
        text = str(value or "").strip()
        if not text:
            raise ValueError("decision is required")
        return text

    @field_validator("rationale", "impact", mode="before")
    @classmethod
    def _text(cls, value: Any) -> str:
        return str(value or "").strip()


class ArchitectureAssumptionAI(BaseModel):
    statement: str
    reason: str = ""
    affected_components: list[str] = Field(default_factory=list)
    validation_required: bool = True
    status: AssumptionStatus = "unvalidated"

    @field_validator("statement", mode="before")
    @classmethod
    def _statement_required(cls, value: Any) -> str:
        text = str(value or "").strip()
        if not text:
            raise ValueError("assumption statement is required")
        return text

    @field_validator("reason", mode="before")
    @classmethod
    def _reason(cls, value: Any) -> str:
        return str(value or "").strip()

    @field_validator("affected_components", mode="before")
    @classmethod
    def _components(cls, value: Any) -> list[str]:
        return _string_list(value, field="affected_components")

    @field_validator("status", mode="before")
    @classmethod
    def _status(cls, value: Any) -> str:
        text = str(value or "unvalidated").strip().lower()
        if text not in {"unvalidated", "validated", "rejected"}:
            raise ValueError("assumption status must be unvalidated, validated, or rejected")
        return text


class SolutionRiskAI(BaseModel):
    description: str
    category: str = "technical"
    cause: str = ""
    impact: str = ""
    probability: RiskProbability = "medium"
    severity: RiskSeverity = "medium"
    mitigation: str = ""
    owner: str | None = None
    related_requirement_ids: list[str] = Field(default_factory=list)

    @field_validator("description", mode="before")
    @classmethod
    def _description_required(cls, value: Any) -> str:
        text = str(value or "").strip()
        if not text:
            raise ValueError("risk description is required")
        return text

    @field_validator("category", "cause", "impact", "mitigation", mode="before")
    @classmethod
    def _text(cls, value: Any) -> str:
        return str(value or "").strip()

    @field_validator("probability", mode="before")
    @classmethod
    def _probability(cls, value: Any) -> str:
        text = str(value or "medium").strip().lower()
        if text not in {"low", "medium", "high"}:
            raise ValueError("probability must be low, medium, or high")
        return text

    @field_validator("severity", mode="before")
    @classmethod
    def _severity(cls, value: Any) -> str:
        text = str(value or "medium").strip().lower()
        if text not in {"low", "medium", "high", "critical"}:
            raise ValueError("severity must be low, medium, high, or critical")
        return text

    @field_validator("owner", mode="before")
    @classmethod
    def _owner(cls, value: Any) -> str | None:
        text = str(value or "").strip()
        return text or None

    @field_validator("related_requirement_ids", mode="before")
    @classmethod
    def _reqs(cls, value: Any) -> list[str]:
        return _string_list(value, field="related_requirement_ids")


class SolutionScoreAI(BaseModel):
    dimension: str
    weight: float | None = None
    score: float
    explanation: str

    @field_validator("dimension", mode="before")
    @classmethod
    def _dimension(cls, value: Any) -> str:
        text = str(value or "").strip().lower().replace(" ", "_").replace("-", "_")
        aliases = {
            "requirement_coverage": "requirement_coverage",
            "coverage": "requirement_coverage",
            "technical_fit": "technical_fit",
            "security": "security",
            "availability_resilience": "availability_resilience",
            "availability": "availability_resilience",
            "resilience": "availability_resilience",
            "scalability": "scalability",
            "operability": "operability",
            "lifecycle": "lifecycle",
            "complexity": "complexity",
            "commercial_suitability": "commercial_suitability",
            "commercial": "commercial_suitability",
        }
        normalized = aliases.get(text)
        if normalized is None or normalized not in ALLOWED_SCORE_DIMENSIONS:
            raise ValueError(
                "score dimension must be one of: "
                + ", ".join(sorted(ALLOWED_SCORE_DIMENSIONS)),
            )
        return normalized

    @field_validator("score", mode="before")
    @classmethod
    def _score(cls, value: Any) -> float:
        return _normalize_score_0_5(value)

    @field_validator("weight", mode="before")
    @classmethod
    def _weight(cls, value: Any) -> float | None:
        if value is None or value == "":
            return None
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("weight must be a number") from exc
        if number < 0.0 or number > 1.0:
            raise ValueError("weight must be between 0 and 1")
        return round(number, 4)

    @field_validator("explanation", mode="before")
    @classmethod
    def _explanation_required(cls, value: Any) -> str:
        text = str(value or "").strip()
        if not text:
            raise ValueError("score explanation is required")
        return text

    @model_validator(mode="after")
    def _default_weight(self) -> SolutionScoreAI:
        if self.weight is None:
            self.weight = DEFAULT_SCORE_WEIGHTS[self.dimension]
        return self


class CapacityNoteAI(BaseModel):
    label: str
    input_value: str | None = None
    unit: str | None = None
    method: str | None = None
    assumption: str | None = None
    result: str | None = None
    confidence: float = 0.0
    related_requirement_ids: list[str] = Field(default_factory=list)
    open_question: str | None = None

    @field_validator("label", mode="before")
    @classmethod
    def _label_required(cls, value: Any) -> str:
        text = str(value or "").strip()
        if not text:
            raise ValueError("capacity note label is required")
        return text

    @field_validator(
        "input_value",
        "unit",
        "method",
        "assumption",
        "result",
        "open_question",
        mode="before",
    )
    @classmethod
    def _optional_text(cls, value: Any) -> str | None:
        text = str(value or "").strip()
        return text or None

    @field_validator("confidence", mode="before")
    @classmethod
    def _confidence(cls, value: Any) -> float:
        return _normalize_confidence(value if value is not None else 0)

    @field_validator("related_requirement_ids", mode="before")
    @classmethod
    def _reqs(cls, value: Any) -> list[str]:
        return _string_list(value, field="related_requirement_ids")

    @model_validator(mode="after")
    def _no_fabricated_result(self) -> CapacityNoteAI:
        has_result = bool(self.result)
        has_inputs = bool(self.input_value and self.method)
        if has_result and not has_inputs and not self.assumption:
            raise ValueError(
                f"capacity note {self.label!r} has a result without input/method/assumption; "
                "do not fabricate sizing — provide evidence or an open_question",
            )
        if not has_result and not self.open_question and not has_inputs:
            raise ValueError(
                f"capacity note {self.label!r} needs inputs+method or an open_question "
                "when result is missing",
            )
        return self


class ArchitectureCandidateAI(BaseModel):
    """Single candidate architecture emitted by AI."""

    candidate_key: str = "standard"
    title: str
    summary: str
    reasoning_summary: str = ""
    pattern_codes: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    high_level_architecture: list[str] = Field(default_factory=list)
    logical_architecture: list[str] = Field(default_factory=list)
    physical_architecture: list[str] = Field(default_factory=list)
    technology_stack: list[dict[str, Any]] = Field(default_factory=list)
    components: list[ArchitectureComponentAI] = Field(default_factory=list)
    relationships: list[ArchitectureRelationshipAI] = Field(default_factory=list)
    decisions: list[DesignDecisionAI] = Field(default_factory=list)
    assumptions: list[ArchitectureAssumptionAI] = Field(default_factory=list)
    risks: list[SolutionRiskAI] = Field(default_factory=list)
    scores: list[SolutionScoreAI] = Field(default_factory=list)
    capacity_notes: list[CapacityNoteAI] = Field(default_factory=list)
    advantages: list[str] = Field(default_factory=list)
    disadvantages: list[str] = Field(default_factory=list)

    @field_validator("candidate_key", mode="before")
    @classmethod
    def _candidate_key(cls, value: Any) -> str:
        text = str(value or "standard").strip().lower().replace(" ", "_").replace("-", "_")
        return text or "standard"

    @field_validator("title", mode="before")
    @classmethod
    def _title_required(cls, value: Any) -> str:
        text = str(value or "").strip()
        if not text:
            raise ValueError("architecture title is required")
        return text

    @field_validator("summary", mode="before")
    @classmethod
    def _summary_required(cls, value: Any) -> str:
        text = str(value or "").strip()
        if not text:
            raise ValueError("architecture summary is required")
        return text

    @field_validator("reasoning_summary", mode="before")
    @classmethod
    def _reasoning(cls, value: Any) -> str:
        return str(value or "").strip()

    @field_validator("pattern_codes", mode="before")
    @classmethod
    def _patterns(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [_resolve_pattern_code(value)]
        if not isinstance(value, list):
            raise ValueError("pattern_codes must be a list")
        return [_resolve_pattern_code(item) for item in value]

    @field_validator("confidence", mode="before")
    @classmethod
    def _confidence(cls, value: Any) -> float:
        return _normalize_confidence(value if value is not None else 0)

    @field_validator(
        "high_level_architecture",
        "logical_architecture",
        "physical_architecture",
        "advantages",
        "disadvantages",
        mode="before",
    )
    @classmethod
    def _string_lists(cls, value: Any) -> list[str]:
        return _string_list(value, field="architecture narrative lists")

    @model_validator(mode="after")
    def _components_required(self) -> ArchitectureCandidateAI:
        if not self.components:
            raise ValueError(
                f"architecture {self.candidate_key!r} requires at least one component",
            )
        return self


class ArchitectureAIExtraction(BaseModel):
    """Validated AI payload for multi-candidate architecture generation."""

    summary: str = ""
    reasoning_summary: str = ""
    architectures: list[ArchitectureCandidateAI] = Field(default_factory=list)
    model: str | None = None
    provider: str | None = None

    @field_validator("summary", "reasoning_summary", mode="before")
    @classmethod
    def _text(cls, value: Any) -> str:
        return str(value or "").strip()

    @field_validator("architectures", mode="before")
    @classmethod
    def _coerce_architectures(cls, value: Any) -> Any:
        if value is None:
            return []
        # Accept singular "architecture" object via parent validate helper.
        if isinstance(value, dict):
            items: list[Any] = [value]
        elif isinstance(value, list):
            items = value
        else:
            raise ValueError("architectures must be a list")
        normalized: list[Any] = []
        for item in items:
            if isinstance(item, ArchitectureCandidateAI):
                normalized.append(item.model_dump(mode="python"))
                continue
            if hasattr(item, "model_dump"):
                normalized.append(item.model_dump(mode="python"))
                continue
            if not isinstance(item, dict):
                raise ValueError("each architecture must be an object")
            row = dict(item)
            if "components" not in row and "solution_components" in row:
                row["components"] = row["solution_components"]
            if "decisions" not in row and "architecture_decisions" in row:
                row["decisions"] = row["architecture_decisions"]
            if "candidate_key" not in row and "name" in row and "title" not in row:
                row["candidate_key"] = str(row.get("name") or "standard")
            if "title" not in row and "name" in row:
                row["title"] = row["name"]
            normalized.append(row)
        return normalized

    @model_validator(mode="after")
    def _at_least_one(self) -> ArchitectureAIExtraction:
        if not self.architectures:
            raise ValueError("at least one architecture candidate is required")
        keys = [item.candidate_key for item in self.architectures]
        if len(keys) != len(set(keys)):
            raise ValueError("architecture candidate_key values must be unique in one extraction")
        return self


def validate_architecture_ai_extraction(payload: Any) -> ArchitectureAIExtraction:
    """Parse and validate AI architecture generation output."""
    if not isinstance(payload, dict):
        raise ValueError("AI architecture extraction payload must be an object")
    data = dict(payload)
    if "architectures" not in data and "architecture" in data:
        data["architectures"] = data["architecture"]
    return ArchitectureAIExtraction.model_validate(data)


# --- API response DTOs ---------------------------------------------------------------


class ArchitectureComponentOut(BaseModel):
    id: UUID
    name: str
    purpose: str = ""
    component_kind: ComponentKind = "logical"
    sort_order: int = 0
    maps_to_requirements: list[str] = Field(default_factory=list)


class ArchitectureRelationshipOut(BaseModel):
    id: UUID
    from_component_id: UUID
    to_component_id: UUID
    relationship_kind: str = "connects_to"
    description: str = ""


class DesignDecisionOut(BaseModel):
    id: UUID
    decision: str
    rationale: str = ""
    impact: str = ""


class ArchitectureAssumptionOut(BaseModel):
    id: UUID
    architecture_id: UUID | None = None
    project_id: UUID | None = None
    statement: str
    reason: str = ""
    affected_component_ids: list[UUID] = Field(default_factory=list)
    validation_required: bool = True
    status: AssumptionStatus = "unvalidated"


class SolutionRiskOut(BaseModel):
    id: UUID
    architecture_id: UUID | None = None
    project_id: UUID | None = None
    description: str
    category: str = "technical"
    cause: str = ""
    impact: str = ""
    probability: RiskProbability = "medium"
    severity: RiskSeverity = "medium"
    mitigation: str = ""
    owner: str | None = None
    related_requirement_ids: list[str] = Field(default_factory=list)


class SolutionScoreOut(BaseModel):
    id: UUID
    dimension: str
    weight: float
    score: float
    explanation: str


class CapacityNoteOut(BaseModel):
    id: UUID
    label: str
    input_value: str | None = None
    unit: str | None = None
    method: str | None = None
    assumption: str | None = None
    result: str | None = None
    confidence: float = 0.0
    related_requirement_ids: list[str] = Field(default_factory=list)
    open_question: str | None = None


class ArchitectureOptionSummaryOut(BaseModel):
    id: UUID
    project_id: UUID
    generation_id: UUID
    candidate_key: str
    title: str
    summary: str = ""
    status: ArchitectureStatus | str = "draft"
    confidence: float = 0.0
    overall_score: float | None = None
    pattern_codes: list[str] = Field(default_factory=list)
    version_label: str
    rkm_version_label: str | None = None
    domain_analysis_id: UUID | None = None
    created_at: datetime


class ArchitectureOptionOut(BaseModel):
    """Full reviewable architecture candidate."""

    id: UUID
    project_id: UUID
    rkm_id: UUID | None = None
    rkm_version_label: str | None = None
    domain_analysis_id: UUID | None = None
    generation_id: UUID
    candidate_key: str
    title: str
    summary: str = ""
    reasoning_summary: str = ""
    status: ArchitectureStatus | str = "draft"
    confidence: float = 0.0
    overall_score: float | None = None
    pattern_codes: list[str] = Field(default_factory=list)
    version_label: str
    model: str | None = None
    prompt_version: str | None = None
    knowledge_pack_version: str | None = None
    high_level_architecture: list[str] = Field(default_factory=list)
    logical_architecture: list[str] = Field(default_factory=list)
    physical_architecture: list[str] = Field(default_factory=list)
    technology_stack: list[dict[str, Any]] = Field(default_factory=list)
    components: list[ArchitectureComponentOut] = Field(default_factory=list)
    relationships: list[ArchitectureRelationshipOut] = Field(default_factory=list)
    decisions: list[DesignDecisionOut] = Field(default_factory=list)
    assumptions: list[ArchitectureAssumptionOut] = Field(default_factory=list)
    risks: list[SolutionRiskOut] = Field(default_factory=list)
    scores: list[SolutionScoreOut] = Field(default_factory=list)
    capacity_notes: list[CapacityNoteOut] = Field(default_factory=list)
    advantages: list[str] = Field(default_factory=list)
    disadvantages: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    payload: dict[str, Any] = Field(default_factory=dict)


class ArchitectureGenerateOut(BaseModel):
    """Response for POST …/architectures/generate (one generation batch)."""

    generation_id: UUID
    version_label: str
    architectures: list[ArchitectureOptionOut] = Field(default_factory=list)
