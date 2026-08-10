"""Sprint 5.1 — KnowledgeItem type vocabulary (extensible via API listing)."""

from __future__ import annotations

KNOWLEDGE_TYPES: tuple[tuple[str, str], ...] = (
    ("engineering_standard", "Engineering Standard"),
    ("reference_architecture", "Reference Architecture"),
    ("design_guide", "Design Guide"),
    ("vendor_guide", "Vendor Guide"),
    ("product_knowledge", "Product Knowledge"),
    ("bom_pattern", "BOM Pattern"),
    ("proposal", "Proposal"),
    ("sow", "SOW"),
    ("solution_design", "Solution Design"),
    ("lessons_learned", "Lessons Learned"),
    ("faq", "FAQ"),
    ("best_practice", "Best Practice"),
)

KNOWLEDGE_TYPE_CODES: frozenset[str] = frozenset(code for code, _ in KNOWLEDGE_TYPES)

DEFAULT_KNOWLEDGE_TYPE = "best_practice"


def normalize_knowledge_type(value: str | None) -> str:
    cleaned = (value or DEFAULT_KNOWLEDGE_TYPE).strip().lower().replace(" ", "_").replace("-", "_")
    if cleaned not in KNOWLEDGE_TYPE_CODES:
        raise ValueError(f"Unknown knowledge type: {value}")
    return cleaned


def knowledge_type_choices() -> list[dict[str, str]]:
    return [{"code": code, "name": name} for code, name in KNOWLEDGE_TYPES]
