"""Validate generated deliverable content (ATLAS-047; Sprint 4.3 SOW/SD)."""

from __future__ import annotations

import re
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.repositories.deliverable_repository import DeliverableRepository
from app.schemas.deliverable import (
    SECTION_TYPES_BY_DOCUMENT,
    ValidationIssue,
    ValidationOut,
)

_PRICE_RE = re.compile(
    r"(\$\s?\d|\bUSD\b|\bpricing\b|\bunit price\b|\bdiscount\b|\bquotation\b)",
    re.I,
)
# ATLAS-047: stating that pricing is omitted/unavailable is compliant, not a breach.
_PRICE_DISCLAIMER_RE = re.compile(
    r"\b(omitted|excluded|not included|unavailable|not present|without|"
    r"no authoritative|do not invent|exclude pricing|pricing excluded|"
    r"commercial figures are omitted|commercial pricing is excluded)\b",
    re.I,
)
_DATE_COMMIT_RE = re.compile(
    r"\b(shall be completed by|go-live on|warranty of \d+|SLA of)\b",
    re.I,
)
_SOW_CONTRACT_RE = re.compile(
    r"\b(penalty|penalties|liquidated damages|service level agreement|\bSLA\b|"
    r"warranty period|shall warrant|guaranteed uptime|fixed price due|"
    r"must accept by|acceptance shall)\b",
    re.I,
)

_TECHNICAL_SECTIONS = {
    "architecture",
    "solution_components",
    "proposed_solution",
    "requirements",
    "proposed_architecture",
    "key_components",
    "technical_highlights",
    "solution_overview",
    "high_level_architecture",
    "logical_design",
    "physical_component_design",
    "requirements_traceability",
    "design_decisions",
    "capacity",
    "security",
    "availability",
    "integration",
}


class DeliverableValidationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = DeliverableRepository(db)

    def validate_document(
        self, project_id: UUID, document_id: UUID
    ) -> ValidationOut:
        document = self.repo.get_document(document_id, project_id)
        if document is None:
            raise NotFoundError("Deliverable not found")
        if document.current_version_id is None:
            return ValidationOut(
                ok=False,
                issues=[
                    ValidationIssue(
                        code="missing_version",
                        message="Document has no current version",
                    )
                ],
            )
        sections = self.repo.list_sections(document.current_version_id)
        snapshot = self.repo.get_snapshot(document.source_snapshot_id, project_id)
        bom_validated = bool(snapshot.bom_validated) if snapshot else False
        return self.validate_sections(
            sections,
            bom_validated=bom_validated,
            document_type=document.document_type,
            snapshot_payload=(snapshot.payload_json or {}) if snapshot else {},
        )

    def validate_sections(
        self,
        sections: list,
        *,
        bom_validated: bool,
        document_type: str = "proposal",
        load_content: bool = True,
        snapshot_payload: dict | None = None,
    ) -> ValidationOut:
        issues: list[ValidationIssue] = []
        present = {s.section_type for s in sections}
        section_types = SECTION_TYPES_BY_DOCUMENT.get(
            document_type, SECTION_TYPES_BY_DOCUMENT["proposal"]
        )
        required = {code for code, _ in section_types}

        for missing in sorted(required - present):
            issues.append(
                ValidationIssue(
                    code="missing_section",
                    message=f"Required section '{missing}' is missing",
                    section_type=missing,
                )
            )

        for section in sections:
            content_items = (
                self.repo.list_content_items(section.id) if load_content else []
            )
            if load_content and not content_items:
                issues.append(
                    ValidationIssue(
                        code="empty_section",
                        message=f"Section '{section.section_type}' has no content",
                        section_type=section.section_type,
                        severity="warning",
                    )
                )

            if document_type == "presentation" and load_content:
                key_message = ""
                for item in content_items:
                    structured = getattr(item, "structured_data", None) or {}
                    slide = structured.get("slide") or {}
                    if slide.get("key_message"):
                        key_message = str(slide.get("key_message") or "")
                        break
                if not key_message.strip():
                    issues.append(
                        ValidationIssue(
                            code="missing_key_message",
                            message=(
                                f"Slide '{section.section_type}' requires a key_message "
                                "(one primary message per slide)"
                            ),
                            section_type=section.section_type,
                        )
                    )

            for item in content_items:
                text = item.text or ""
                structured = getattr(item, "structured_data", None) or {}
                slide = structured.get("slide") or {}
                combined = " ".join(
                    [
                        text,
                        str(slide.get("key_message") or ""),
                        str(slide.get("speaker_notes") or ""),
                    ]
                )
                if (
                    not bom_validated
                    and _PRICE_RE.search(combined)
                    and not _PRICE_DISCLAIMER_RE.search(combined)
                ):
                    issues.append(
                        ValidationIssue(
                            code="pricing_without_authority",
                            message=(
                                "Pricing/commercial language present without validated "
                                "BOM / approved pricing data (ATLAS-047)"
                            ),
                            section_type=section.section_type,
                        )
                    )
                if _DATE_COMMIT_RE.search(combined) and item.review_required is False:
                    issues.append(
                        ValidationIssue(
                            code="contractual_commitment",
                            message=(
                                "Possible contractual date/SLA/warranty commitment "
                                "without REVIEW REQUIRED flag (ATLAS-047)"
                            ),
                            section_type=section.section_type,
                            severity="warning",
                        )
                    )
                if (
                    document_type == "sow"
                    and _SOW_CONTRACT_RE.search(combined)
                    and item.review_required is False
                ):
                    issues.append(
                        ValidationIssue(
                            code="sow_contractual_invention",
                            message=(
                                "Possible contractual/penalty/SLA language without "
                                "REVIEW REQUIRED (ATLAS-047)"
                            ),
                            section_type=section.section_type,
                            severity="warning",
                        )
                    )

                content_type = getattr(item, "content_type", "paragraph")
                if (
                    section.section_type in _TECHNICAL_SECTIONS
                    and content_type != "speaker_notes"
                ):
                    refs = self.repo.list_source_refs(item.id)
                    if not refs and not item.review_required:
                        issues.append(
                            ValidationIssue(
                                code="missing_source_ref",
                                message=(
                                    f"Technical content in '{section.section_type}' "
                                    "needs source refs or REVIEW REQUIRED"
                                ),
                                section_type=section.section_type,
                                severity="warning",
                            )
                        )

        blocking = [i for i in issues if i.severity == "error"]
        return ValidationOut(ok=len(blocking) == 0, issues=issues)
