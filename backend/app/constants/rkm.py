"""RKM enums and helpers (RKM Schema v1.0)."""

from __future__ import annotations

REQUIREMENT_CATEGORIES = {
    "business",
    "functional",
    "non_functional",
    "infrastructure",
    "security",
    "collaboration",
    "audio_visual",
    "smart_building",
}

PRIORITIES = {"critical", "high", "medium", "low"}

REQUIREMENT_STATUSES = {
    "draft",
    "validated",
    "approved",
    "implemented",
    "verified",
    "retired",
}

EVIDENCE_SOURCE_TYPES = {
    "document",
    "sales_intake",
    "workshop",
    "clarification_answer",
}

RKM_SECTIONS = (
    "business_objectives",
    "current_environment",
    "functional_requirements",
    "non_functional_requirements",
    "constraints",
    "dependencies",
    "risks",
    "assumptions",
    "stakeholders",
)

PROMPT_VERSION = "rkm-extraction-1.0"


def normalize_category(value: str | None, *, default: str = "functional") -> str:
    cleaned = (value or default).strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "nfr": "non_functional",
        "nonfunctional": "non_functional",
        "infra": "infrastructure",
        "av": "audio_visual",
        "audio_visuals": "audio_visual",
        "smartbuilding": "smart_building",
        "iot": "smart_building",
    }
    cleaned = aliases.get(cleaned, cleaned)
    return cleaned if cleaned in REQUIREMENT_CATEGORIES else default


def normalize_priority(value: str | None, *, default: str = "medium") -> str:
    cleaned = (value or default).strip().lower()
    return cleaned if cleaned in PRIORITIES else default
