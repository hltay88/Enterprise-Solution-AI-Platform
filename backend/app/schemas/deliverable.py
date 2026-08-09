"""Phase 4 deliverable schemas (ATLAS-042…048; Sprint 4.3 SOW/SD)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

DocumentType = Literal["proposal", "presentation", "sow", "solution_design"]
ExportFormat = Literal["docx", "pptx", "pdf"]


class SnapshotCreateIn(BaseModel):
    architecture_id: UUID | None = None


class SourceSnapshotOut(BaseModel):
    id: UUID
    project_id: UUID
    rkm_id: UUID | None = None
    rkm_version_label: str | None = None
    architecture_id: UUID | None = None
    architecture_version_label: str | None = None
    bom_import_id: UUID | None = None
    catalogue_id: UUID | None = None
    catalogue_version_label: str | None = None
    bom_validated: bool = False
    model: str | None = None
    prompt_version: str | None = None
    knowledge_pack_version: str | None = None
    created_at: datetime | None = None


class DeliverableGenerateIn(BaseModel):
    document_type: DocumentType = "proposal"
    snapshot_id: UUID | None = None
    architecture_id: UUID | None = None


class SourceRefIn(BaseModel):
    ref_kind: str
    ref_id: str | None = None
    label: str = ""


class ContentItemIn(BaseModel):
    content_type: str = "paragraph"
    text: str = ""
    structured_data: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0
    review_required: bool = False
    source_refs: list[SourceRefIn] = Field(default_factory=list)


class ProposalSectionIn(BaseModel):
    section_type: str
    title: str
    sequence: int = 0
    confidence: float = 0.0
    assumptions: list[str] = Field(default_factory=list)
    content_items: list[ContentItemIn] = Field(default_factory=list)


class ProposalContentPayload(BaseModel):
    title: str = "Customer Proposal"
    sections: list[ProposalSectionIn]
    provider: str | None = None
    model: str | None = None
    prompt_version: str | None = None


class PresentationSlideIn(BaseModel):
    section_type: str
    title: str
    sequence: int = 0
    objective: str = ""
    key_message: str = ""
    body_content: str = ""
    visual_type: str = "none"
    visual_data: dict[str, Any] = Field(default_factory=dict)
    speaker_notes: str = ""
    confidence: float = 0.0
    review_required: bool = False
    assumptions: list[str] = Field(default_factory=list)
    source_refs: list[SourceRefIn] = Field(default_factory=list)


class PresentationContentPayload(BaseModel):
    title: str = "Solution Presentation"
    slides: list[PresentationSlideIn]
    provider: str | None = None
    model: str | None = None
    prompt_version: str | None = None


class SowSectionIn(BaseModel):
    section_type: str
    title: str
    sequence: int = 0
    confidence: float = 0.0
    assumptions: list[str] = Field(default_factory=list)
    content_items: list[ContentItemIn] = Field(default_factory=list)


class SowContentPayload(BaseModel):
    title: str = "Statement of Work"
    sections: list[SowSectionIn]
    provider: str | None = None
    model: str | None = None
    prompt_version: str | None = None


class SolutionDesignSectionIn(BaseModel):
    section_type: str
    title: str
    sequence: int = 0
    confidence: float = 0.0
    assumptions: list[str] = Field(default_factory=list)
    content_items: list[ContentItemIn] = Field(default_factory=list)


class SolutionDesignContentPayload(BaseModel):
    title: str = "Solution Design"
    sections: list[SolutionDesignSectionIn]
    provider: str | None = None
    model: str | None = None
    prompt_version: str | None = None


class SourceRefOut(BaseModel):
    id: UUID
    ref_kind: str
    ref_id: str | None = None
    label: str = ""


class ContentItemOut(BaseModel):
    id: UUID
    content_type: str
    text: str
    structured_data: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0
    approval_status: str = "draft"
    sort_order: int = 0
    review_required: bool = False
    source_refs: list[SourceRefOut] = Field(default_factory=list)


class DocumentSectionOut(BaseModel):
    id: UUID
    section_type: str
    title: str
    sequence: int
    status: str
    confidence: float = 0.0
    assumptions: list[Any] = Field(default_factory=list)
    content_items: list[ContentItemOut] = Field(default_factory=list)


class GeneratedDocumentOut(BaseModel):
    id: UUID
    project_id: UUID
    document_type: str
    title: str
    status: str
    template_id: UUID | None = None
    template_version_id: UUID | None = None
    source_snapshot_id: UUID
    generation_run_id: UUID | None = None
    current_version_id: UUID | None = None
    version_label: str | None = None
    created_by: UUID | None = None
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    bom_validated: bool | None = None


class SectionPatchIn(BaseModel):
    title: str | None = None
    text: str | None = None
    assumptions: list[str] | None = None


class ReviewIn(BaseModel):
    note: str | None = None


class ApproveIn(BaseModel):
    decision: Literal["approved", "changes_requested"] = "approved"
    note: str | None = None


class ExportIn(BaseModel):
    format: ExportFormat = "docx"


class ExportJobOut(BaseModel):
    id: UUID
    project_id: UUID
    document_id: UUID
    document_version_id: UUID
    format: str
    status: str
    storage_path: str | None = None
    checksum_sha256: str | None = None
    page_count: int | None = None
    error: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None
    download_name: str | None = None


class ValidationIssue(BaseModel):
    code: str
    message: str
    section_type: str | None = None
    severity: str = "error"


class ValidationOut(BaseModel):
    ok: bool
    issues: list[ValidationIssue] = Field(default_factory=list)


class ConsistencyFinding(BaseModel):
    severity: str = "warning"
    message: str
    document_ids: list[UUID] = Field(default_factory=list)
    review_required: bool = True
    code: str = "consistency"


class ConsistencyOut(BaseModel):
    ok: bool = True
    findings: list[ConsistencyFinding] = Field(default_factory=list)


PROPOSAL_SECTION_TYPES: list[tuple[str, str]] = [
    ("cover", "Cover"),
    ("executive_summary", "Executive Summary"),
    ("customer_understanding", "Customer Understanding"),
    ("challenges", "Challenges"),
    ("requirements", "Requirements"),
    ("proposed_solution", "Proposed Solution"),
    ("architecture", "Architecture"),
    ("solution_components", "Solution Components"),
    ("benefits", "Benefits"),
    ("implementation_approach", "Implementation Approach"),
    ("timeline", "Timeline"),
    ("assumptions", "Assumptions"),
    ("risks", "Risks"),
    ("exclusions", "Exclusions"),
    ("support_warranty", "Support / Warranty"),
    ("next_steps", "Next Steps"),
]

PRESENTATION_SECTION_TYPES: list[tuple[str, str]] = [
    ("title", "Title"),
    ("executive_summary", "Executive Summary"),
    ("customer_situation", "Customer Situation"),
    ("challenges", "Challenges"),
    ("requirements", "Requirements"),
    ("proposed_architecture", "Proposed Architecture"),
    ("solution_overview", "Solution Overview"),
    ("key_components", "Key Components"),
    ("technical_highlights", "Technical Highlights"),
    ("benefits", "Benefits"),
    ("implementation", "Implementation"),
    ("timeline", "Timeline"),
    ("risks_assumptions", "Risks / Assumptions"),
    ("next_steps", "Next Steps"),
]

SOW_SECTION_TYPES: list[tuple[str, str]] = [
    ("purpose", "Purpose"),
    ("scope", "Scope"),
    ("solution_overview", "Solution Overview"),
    ("deliverables", "Deliverables"),
    ("implementation_activities", "Implementation Activities"),
    ("testing", "Testing"),
    ("acceptance_criteria", "Acceptance Criteria"),
    ("customer_responsibilities", "Customer Responsibilities"),
    ("provider_responsibilities", "Provider Responsibilities"),
    ("assumptions", "Assumptions"),
    ("exclusions", "Exclusions"),
    ("schedule", "Schedule"),
    ("support_warranty", "Support / Warranty"),
    ("change_control", "Change Control"),
]

SOLUTION_DESIGN_SECTION_TYPES: list[tuple[str, str]] = [
    ("design_objectives", "Design Objectives"),
    ("scope", "Scope"),
    ("requirements_traceability", "Requirements Traceability"),
    ("high_level_architecture", "High-level Architecture"),
    ("logical_design", "Logical Design"),
    ("physical_component_design", "Physical / Component Design"),
    ("capacity", "Capacity"),
    ("security", "Security"),
    ("availability", "Availability"),
    ("integration", "Integration"),
    ("operations", "Operations"),
    ("monitoring", "Monitoring"),
    ("assumptions", "Assumptions"),
    ("risks", "Risks"),
    ("design_decisions", "Design Decisions"),
    ("appendices", "Appendices"),
]

SECTION_TYPES_BY_DOCUMENT: dict[str, list[tuple[str, str]]] = {
    "proposal": PROPOSAL_SECTION_TYPES,
    "presentation": PRESENTATION_SECTION_TYPES,
    "sow": SOW_SECTION_TYPES,
    "solution_design": SOLUTION_DESIGN_SECTION_TYPES,
}
