"""Phase 3 Sprint 3.1 — Solution Domain Model and AI validation schemas.

Task 3 only: typed contracts for API responses and AI extraction validation.
Does not persist data or call AI providers.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.services.phase3_domain_catalog import DomainCatalogError, require_domain_code

MandatoryOptional = Literal["mandatory", "optional"]
SelectionSource = Literal["requirement", "dependency", "optional_alternative"]
DependencyKind = Literal["required", "recommended"]
TraceabilityStatus = Literal[
    "covered",
    "partially_covered",
    "not_covered",
    "conflict",
    "optional",
]


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


def _normalize_traceability_status(value: Any) -> TraceabilityStatus:
    text = str(value or "").strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "covered": "covered",
        "partially_covered": "partially_covered",
        "partial": "partially_covered",
        "partiallycovered": "partially_covered",
        "not_covered": "not_covered",
        "uncovered": "not_covered",
        "notcovered": "not_covered",
        "conflict": "conflict",
        "optional": "optional",
    }
    normalized = aliases.get(text)
    if normalized is None:
        raise ValueError(
            "status must be one of: covered, partially_covered, not_covered, "
            "conflict, optional",
        )
    return normalized  # type: ignore[return-value]


def _resolve_catalog_code(value: Any) -> str:
    try:
        return require_domain_code(str(value or ""))
    except DomainCatalogError as exc:
        raise ValueError(str(exc)) from exc


# --- AI extraction (provider output) -------------------------------------------------


class DomainDependencyAI(BaseModel):
    depends_on_domain_code: str
    dependency_kind: DependencyKind = "required"
    reason: str = ""

    @field_validator("depends_on_domain_code", mode="before")
    @classmethod
    def _catalog_dep_code(cls, value: Any) -> str:
        return _resolve_catalog_code(value)

    @field_validator("dependency_kind", mode="before")
    @classmethod
    def _normalize_kind(cls, value: Any) -> str:
        text = str(value or "required").strip().lower()
        if text not in {"required", "recommended"}:
            raise ValueError("dependency_kind must be required or recommended")
        return text

    @field_validator("reason", mode="before")
    @classmethod
    def _reason_str(cls, value: Any) -> str:
        return str(value or "").strip()


class DomainOpenQuestionAI(BaseModel):
    question: str
    affects_selection: bool = True
    related_requirement_ids: list[str] = Field(default_factory=list)
    domain_code: str | None = None

    @field_validator("question", mode="before")
    @classmethod
    def _question_required(cls, value: Any) -> str:
        text = str(value or "").strip()
        if not text:
            raise ValueError("open question text is required")
        return text

    @field_validator("domain_code", mode="before")
    @classmethod
    def _optional_domain_code(cls, value: Any) -> str | None:
        if value is None or str(value).strip() == "":
            return None
        return _resolve_catalog_code(value)

    @field_validator("related_requirement_ids", mode="before")
    @classmethod
    def _req_ids(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            text = value.strip()
            return [text] if text else []
        if not isinstance(value, list):
            raise ValueError("related_requirement_ids must be a list")
        out: list[str] = []
        for item in value:
            text = str(item or "").strip()
            if text:
                out.append(text)
        return out


class SolutionDomainAI(BaseModel):
    """Single domain emitted by AI domain identification."""

    domain_code: str = Field(description="Catalog domain code (or resolvable alias)")
    name: str = ""
    reason: str
    supporting_requirements: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    mandatory_or_optional: MandatoryOptional = "mandatory"
    selection_source: SelectionSource = "requirement"
    dependencies: list[DomainDependencyAI] = Field(default_factory=list)
    open_questions: list[DomainOpenQuestionAI] = Field(default_factory=list)

    @field_validator("domain_code", mode="before")
    @classmethod
    def _catalog_code(cls, value: Any) -> str:
        # Accept domain_id as alternate key via model_validator on parent if needed
        return _resolve_catalog_code(value)

    @field_validator("reason", mode="before")
    @classmethod
    def _reason_required(cls, value: Any) -> str:
        text = str(value or "").strip()
        if not text:
            raise ValueError("reason is required for each domain")
        return text

    @field_validator("name", mode="before")
    @classmethod
    def _name_str(cls, value: Any) -> str:
        return str(value or "").strip()

    @field_validator("confidence", mode="before")
    @classmethod
    def _confidence(cls, value: Any) -> float:
        return _normalize_confidence(value if value is not None else 0)

    @field_validator("mandatory_or_optional", mode="before")
    @classmethod
    def _mandatory(cls, value: Any) -> str:
        text = str(value or "mandatory").strip().lower()
        if text in {"must", "required", "mandatory"}:
            return "mandatory"
        if text in {"optional", "nice_to_have", "nice-to-have"}:
            return "optional"
        raise ValueError("mandatory_or_optional must be mandatory or optional")

    @field_validator("selection_source", mode="before")
    @classmethod
    def _selection(cls, value: Any) -> str:
        text = str(value or "requirement").strip().lower().replace(" ", "_").replace("-", "_")
        aliases = {
            "requirement": "requirement",
            "requirements": "requirement",
            "dependency": "dependency",
            "dependencies": "dependency",
            "optional_alternative": "optional_alternative",
            "optional": "optional_alternative",
            "alternative": "optional_alternative",
        }
        normalized = aliases.get(text)
        if normalized is None:
            raise ValueError(
                "selection_source must be requirement, dependency, or optional_alternative",
            )
        return normalized

    @field_validator("supporting_requirements", mode="before")
    @classmethod
    def _supporting_reqs(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            text = value.strip()
            return [text] if text else []
        if not isinstance(value, list):
            raise ValueError("supporting_requirements must be a list")
        out: list[str] = []
        for item in value:
            if isinstance(item, dict):
                text = str(item.get("id") or item.get("requirement_id") or "").strip()
            else:
                text = str(item or "").strip()
            if text:
                out.append(text)
        return out

    @model_validator(mode="after")
    def _evidence_or_dependency(self) -> SolutionDomainAI:
        if self.selection_source == "requirement" and not self.supporting_requirements:
            raise ValueError(
                f"domain {self.domain_code!r} with selection_source=requirement "
                "requires supporting_requirements",
            )
        if self.selection_source == "dependency" and not self.dependencies and not self.reason:
            raise ValueError(
                f"domain {self.domain_code!r} with selection_source=dependency "
                "requires dependencies or a documented reason",
            )
        if (
            self.selection_source == "optional_alternative"
            and not self.supporting_requirements
            and not self.reason
        ):
            raise ValueError(
                f"domain {self.domain_code!r} with selection_source=optional_alternative "
                "requires supporting_requirements or a documented reason",
            )
        return self


class DomainAIExtraction(BaseModel):
    """Validated AI payload for domain identification."""

    summary: str = ""
    domains: list[SolutionDomainAI] = Field(default_factory=list)
    open_questions: list[DomainOpenQuestionAI] = Field(default_factory=list)
    model: str | None = None
    provider: str | None = None
    reasoning_summary: str = ""

    @field_validator("summary", "reasoning_summary", mode="before")
    @classmethod
    def _text(cls, value: Any) -> str:
        return str(value or "").strip()

    @field_validator("domains", mode="before")
    @classmethod
    def _coerce_domains(cls, value: Any) -> Any:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("domains must be a list")
        normalized: list[Any] = []
        for item in value:
            if not isinstance(item, dict):
                raise ValueError("each domain must be an object")
            row = dict(item)
            if "domain_code" not in row and "domain_id" in row:
                row["domain_code"] = row["domain_id"]
            if "domain_code" not in row and "code" in row:
                row["domain_code"] = row["code"]
            normalized.append(row)
        return normalized


def validate_domain_ai_extraction(payload: Any) -> DomainAIExtraction:
    """Parse and validate AI domain identification output.

    Raises ``pydantic.ValidationError`` on invalid payloads.
    """
    if not isinstance(payload, dict):
        raise ValueError("AI domain extraction payload must be an object")
    return DomainAIExtraction.model_validate(payload)


# --- API response DTOs ----------------------------------------------------------------


class DomainDependencyOut(BaseModel):
    id: UUID | None = None
    depends_on_domain_code: str
    dependency_kind: DependencyKind = "required"
    reason: str = ""


class DomainOpenQuestionOut(BaseModel):
    id: UUID | None = None
    domain_id: UUID | None = None
    domain_code: str | None = None
    question: str
    affects_selection: bool = True
    related_requirement_ids: list[str] = Field(default_factory=list)


class SolutionDomainOut(BaseModel):
    id: UUID
    domain_code: str
    name: str
    reason: str = ""
    confidence: float = 0.0
    mandatory_or_optional: MandatoryOptional = "mandatory"
    selection_source: SelectionSource = "requirement"
    sort_order: int = 0
    supporting_requirements: list[str] = Field(default_factory=list)
    dependencies: list[DomainDependencyOut] = Field(default_factory=list)
    open_questions: list[DomainOpenQuestionOut] = Field(default_factory=list)


class TraceabilityOut(BaseModel):
    id: UUID
    project_id: UUID
    analysis_id: UUID
    requirement_id: str
    domain_id: UUID | None = None
    domain_code: str | None = None
    architecture_id: UUID | None = None
    component_id: UUID | None = None
    decision_id: UUID | None = None
    evidence: str | None = None
    status: TraceabilityStatus = "not_covered"
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("status", mode="before")
    @classmethod
    def _status(cls, value: Any) -> str:
        return _normalize_traceability_status(value)


class DomainAnalysisVersionOut(BaseModel):
    id: UUID
    version_label: str
    status: str
    rkm_id: UUID | None = None
    rkm_version_label: str | None = None
    created_at: datetime
    domain_count: int = 0


class DomainAnalysisOut(BaseModel):
    """Reviewable Solution Domain Model for a project analysis version."""

    id: UUID
    project_id: UUID
    rkm_id: UUID | None = None
    rkm_version_label: str | None = None
    status: str
    version_label: str
    summary: str = ""
    reasoning_summary: str = ""
    model: str | None = None
    prompt_version: str | None = None
    knowledge_pack_version: str | None = None
    domains: list[SolutionDomainOut] = Field(default_factory=list)
    open_questions: list[DomainOpenQuestionOut] = Field(default_factory=list)
    traceability: list[TraceabilityOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    payload: dict[str, Any] = Field(default_factory=dict)
