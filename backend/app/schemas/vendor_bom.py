"""Phase 3 Sprint 3.3 — vendor catalogue, product mapping, BOM, review/approve DTOs.

Task 2 only: typed contracts for import/search/mapping/BOM/review APIs.
Does not persist data, call AI, or invent SKU specifications (ATLAS-035/038/039).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

LifecycleStatus = Literal[
    "active",
    "end_of_sale",
    "end_of_support",
    "discontinued",
    "unknown",
]
MappingStatus = Literal["candidate", "selected", "rejected"]
PreferenceKind = Literal["customer", "mandatory", "technical", "commercial"]
BomValidationStatus = Literal["passed", "needs_review", "failed"]
BomIssueSeverity = Literal["info", "warning", "error", "critical"]
BomIssueCode = Literal[
    "missing_component",
    "duplicate_component",
    "unknown_model",
    "missing_quantity",
    "compatibility",
    "dependency",
    "licence",
    "subscription",
    "power",
    "optics",
    "accessory",
    "support",
    "uncertain_spec",
    "stale_catalogue",
    "other",
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


def _required_text(value: Any, *, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field} is required")
    return text


def _optional_text(value: Any) -> str:
    return str(value or "").strip()


# --- Catalogue import / search -------------------------------------------------------


class ProductCapabilityIn(BaseModel):
    capability_code: str
    capability_label: str = ""
    details: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0

    @field_validator("capability_code", mode="before")
    @classmethod
    def _code(cls, value: Any) -> str:
        return _required_text(value, field="capability_code").lower().replace(" ", "_")

    @field_validator("capability_label", mode="before")
    @classmethod
    def _label(cls, value: Any) -> str:
        return _optional_text(value)

    @field_validator("details", mode="before")
    @classmethod
    def _details(cls, value: Any) -> dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ValueError("details must be an object")
        return value

    @field_validator("confidence", mode="before")
    @classmethod
    def _confidence(cls, value: Any) -> float:
        if value is None or value == "":
            return 0.0
        return _normalize_confidence(value)


class VendorProductIn(BaseModel):
    """One catalogue product line. Specifications must come from a stated source."""

    vendor: str
    product_family: str = ""
    product_model: str
    category: str = ""
    capabilities: list[ProductCapabilityIn] = Field(default_factory=list)
    specifications: dict[str, Any] = Field(default_factory=dict)
    licensing: str | None = None
    lifecycle_status: LifecycleStatus | str = "unknown"
    source: str
    source_date: date | None = None
    region: str | None = None
    confidence: float = 0.0
    is_stale: bool = False

    @field_validator("vendor", "product_model", "source", mode="before")
    @classmethod
    def _required_fields(cls, value: Any, info) -> str:
        return _required_text(value, field=info.field_name)

    @field_validator("product_family", "category", mode="before")
    @classmethod
    def _optional_fields(cls, value: Any) -> str:
        return _optional_text(value)

    @field_validator("licensing", "region", mode="before")
    @classmethod
    def _nullable_text(cls, value: Any) -> str | None:
        text = _optional_text(value)
        return text or None

    @field_validator("specifications", mode="before")
    @classmethod
    def _specs(cls, value: Any) -> dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ValueError("specifications must be an object")
        return value

    @field_validator("lifecycle_status", mode="before")
    @classmethod
    def _lifecycle(cls, value: Any) -> str:
        text = _optional_text(value).lower().replace("-", "_").replace(" ", "_")
        aliases = {
            "eos": "end_of_sale",
            "eol": "discontinued",
            "eoss": "end_of_support",
            "current": "active",
            "": "unknown",
        }
        return aliases.get(text, text or "unknown")

    @field_validator("confidence", mode="before")
    @classmethod
    def _confidence(cls, value: Any) -> float:
        if value is None or value == "":
            return 0.0
        return _normalize_confidence(value)

    @model_validator(mode="after")
    def _no_invented_specs_without_source(self) -> VendorProductIn:
        # Source already required; block empty-spec claims that look fabricated later
        # in services. Schema layer only enforces source + model presence.
        if self.specifications and not self.source:
            raise ValueError("specifications require a stated source (ATLAS-038)")
        return self


class VendorCatalogueImportIn(BaseModel):
    name: str = ""
    source: str
    source_date: date | None = None
    version_label: str = "1.0.0"
    region: str | None = None
    notes: str | None = None
    products: list[VendorProductIn] = Field(default_factory=list)

    @field_validator("source", mode="before")
    @classmethod
    def _source(cls, value: Any) -> str:
        return _required_text(value, field="source")

    @field_validator("name", mode="before")
    @classmethod
    def _name(cls, value: Any) -> str:
        return _optional_text(value)

    @field_validator("version_label", mode="before")
    @classmethod
    def _version(cls, value: Any) -> str:
        text = _optional_text(value)
        return text or "1.0.0"

    @field_validator("region", "notes", mode="before")
    @classmethod
    def _nullable(cls, value: Any) -> str | None:
        text = _optional_text(value)
        return text or None

    @model_validator(mode="after")
    def _has_products(self) -> VendorCatalogueImportIn:
        if not self.products:
            raise ValueError("at least one product is required for catalogue import")
        return self


class ProductCapabilityOut(BaseModel):
    id: UUID
    product_id: UUID
    capability_code: str
    capability_label: str = ""
    details: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0
    created_at: datetime


class VendorProductOut(BaseModel):
    id: UUID
    catalogue_id: UUID
    vendor: str
    product_family: str = ""
    product_model: str
    category: str = ""
    capabilities: list[ProductCapabilityOut] = Field(default_factory=list)
    specifications: dict[str, Any] = Field(default_factory=dict)
    licensing: str | None = None
    lifecycle_status: str = "unknown"
    source: str
    source_date: date | None = None
    region: str | None = None
    confidence: float = 0.0
    is_stale: bool = False
    created_at: datetime
    updated_at: datetime


class VendorProductSummaryOut(BaseModel):
    id: UUID
    catalogue_id: UUID
    vendor: str
    product_family: str = ""
    product_model: str
    category: str = ""
    lifecycle_status: str = "unknown"
    source: str
    source_date: date | None = None
    region: str | None = None
    confidence: float = 0.0
    is_stale: bool = False


class VendorCatalogueOut(BaseModel):
    id: UUID
    name: str = ""
    source: str
    source_date: date | None = None
    version_label: str
    region: str | None = None
    notes: str | None = None
    product_count: int = 0
    created_at: datetime
    products: list[VendorProductOut] = Field(default_factory=list)


class VendorCatalogueSearchOut(BaseModel):
    query: str = ""
    total: int = 0
    products: list[VendorProductSummaryOut] = Field(default_factory=list)


# --- Product mapping -----------------------------------------------------------------


class ArchitectureProductMapIn(BaseModel):
    """Explicit Map products action body (ATLAS-035 — not auto on generate).

    ``architecture_id`` may be omitted when the route supplies it from the path.
    """

    architecture_id: UUID | None = None
    component_ids: list[UUID] | None = None
    catalogue_id: UUID | None = None
    region: str | None = None
    include_stale: bool = False

    @field_validator("region", mode="before")
    @classmethod
    def _region(cls, value: Any) -> str | None:
        text = _optional_text(value)
        return text or None


class ArchitectureProductMappingOut(BaseModel):
    id: UUID
    project_id: UUID
    architecture_id: UUID
    component_id: UUID
    product_id: UUID
    fit_score: float | None = None
    rationale: str = ""
    status: MappingStatus | str = "candidate"
    preference_kind: PreferenceKind | str = "technical"
    limitations: str = ""
    vendor: str | None = None
    product_model: str | None = None
    created_at: datetime
    updated_at: datetime


class ArchitectureProductMapResultOut(BaseModel):
    architecture_id: UUID
    mappings: list[ArchitectureProductMappingOut] = Field(default_factory=list)
    unmatched_component_ids: list[UUID] = Field(default_factory=list)


class ArchitectureProductMappingUpdateIn(BaseModel):
    status: MappingStatus | None = None
    preference_kind: PreferenceKind | None = None
    rationale: str | None = None
    limitations: str | None = None
    fit_score: float | None = None

    @field_validator("rationale", "limitations", mode="before")
    @classmethod
    def _text(cls, value: Any) -> str | None:
        if value is None:
            return None
        return _optional_text(value)

    @field_validator("fit_score", mode="before")
    @classmethod
    def _fit(cls, value: Any) -> float | None:
        if value is None or value == "":
            return None
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("fit_score must be a number") from exc
        if number < 0.0 or number > 5.0:
            raise ValueError("fit_score must be between 0 and 5")
        return round(number, 2)


# --- BOM -----------------------------------------------------------------------------


class BomItemIn(BaseModel):
    line_number: int = 0
    vendor: str = ""
    product_model: str = ""
    description: str = ""
    quantity: float | None = None
    unit: str | None = None
    category: str = ""
    sku: str | None = None
    notes: str | None = None

    @field_validator("line_number", mode="before")
    @classmethod
    def _line(cls, value: Any) -> int:
        if value is None or value == "":
            return 0
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("line_number must be an integer") from exc

    @field_validator("vendor", "product_model", "description", "category", mode="before")
    @classmethod
    def _text(cls, value: Any) -> str:
        return _optional_text(value)

    @field_validator("unit", "sku", "notes", mode="before")
    @classmethod
    def _nullable(cls, value: Any) -> str | None:
        text = _optional_text(value)
        return text or None

    @field_validator("quantity", mode="before")
    @classmethod
    def _qty(cls, value: Any) -> float | None:
        if value is None or value == "":
            return None
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("quantity must be a number") from exc
        if number < 0:
            raise ValueError("quantity must be >= 0")
        return number

    @model_validator(mode="after")
    def _identifiable(self) -> BomItemIn:
        if not (self.product_model or self.sku or self.description):
            raise ValueError(
                "bom item requires product_model, sku, or description (ATLAS-039)",
            )
        return self


class BomImportIn(BaseModel):
    source: str
    source_filename: str | None = None
    architecture_id: UUID | None = None
    notes: str | None = None
    items: list[BomItemIn] = Field(default_factory=list)

    @field_validator("source", mode="before")
    @classmethod
    def _source(cls, value: Any) -> str:
        return _required_text(value, field="source")

    @field_validator("source_filename", "notes", mode="before")
    @classmethod
    def _nullable(cls, value: Any) -> str | None:
        text = _optional_text(value)
        return text or None

    @model_validator(mode="after")
    def _has_items(self) -> BomImportIn:
        if not self.items:
            raise ValueError("at least one BOM item is required")
        return self


class BomItemOut(BaseModel):
    id: UUID
    bom_import_id: UUID
    line_number: int = 0
    vendor: str = ""
    product_model: str = ""
    description: str = ""
    quantity: float | None = None
    unit: str | None = None
    category: str = ""
    sku: str | None = None
    mapped_product_id: UUID | None = None
    notes: str | None = None
    created_at: datetime


class BomImportOut(BaseModel):
    id: UUID
    project_id: UUID
    architecture_id: UUID | None = None
    source: str
    source_filename: str | None = None
    notes: str | None = None
    item_count: int = 0
    created_at: datetime
    items: list[BomItemOut] = Field(default_factory=list)


class BomValidationIssueOut(BaseModel):
    code: BomIssueCode | str
    severity: BomIssueSeverity | str = "warning"
    message: str
    bom_item_id: UUID | None = None
    line_number: int | None = None
    related_component_id: UUID | None = None
    requires_human_validation: bool = True


class BomValidateIn(BaseModel):
    architecture_id: UUID | None = None
    catalogue_id: UUID | None = None


class BomValidationResultOut(BaseModel):
    id: UUID
    bom_import_id: UUID
    project_id: UUID
    status: BomValidationStatus | str = "needs_review"
    summary: str = ""
    issues: list[BomValidationIssueOut] = Field(default_factory=list)
    created_at: datetime


# --- Architecture review / approve ---------------------------------------------------


class ArchitectureReviewIn(BaseModel):
    note: str = ""

    @field_validator("note", mode="before")
    @classmethod
    def _note(cls, value: Any) -> str:
        return _optional_text(value)


class ArchitectureApproveIn(BaseModel):
    note: str = ""
    """Approver-only. Services hard-fail Complete if criticals uncovered (ATLAS-036/037)."""

    @field_validator("note", mode="before")
    @classmethod
    def _note(cls, value: Any) -> str:
        return _optional_text(value)


class ArchitectureReviewOut(BaseModel):
    id: UUID
    project_id: UUID
    status: str
    reviewed_at: datetime | None = None
    reviewed_by: UUID | None = None
    review_note: str | None = None
    approved_at: datetime | None = None
    approved_by: UUID | None = None
    approval_note: str | None = None
    uncovered_critical_count: int | None = None
