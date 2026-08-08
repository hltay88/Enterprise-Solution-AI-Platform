"""Deterministic RKM scoring (REQUIREMENT_SCORING.md) — Stage D."""

from __future__ import annotations

from typing import Any

SECTION_WEIGHTS: dict[str, float] = {
    "business_objectives": 10,
    "current_environment": 10,
    "functional_requirements": 20,
    "non_functional_requirements": 20,
    "constraints": 10,
    "dependencies": 10,
    "risks": 10,
    "stakeholders": 5,
    "assumptions": 5,
}


def _section_items(payload: dict[str, Any], section: str) -> list[dict[str, Any]]:
    if section == "current_environment":
        env = payload.get("current_environment") or {}
        items = list(env.get("items") or [])
        summary = str(env.get("summary") or "").strip()
        if summary and not items:
            return [{"title": "Environment summary", "description": summary, "confidence": 50, "evidence_ids": []}]
        return [item for item in items if isinstance(item, dict)]
    raw = payload.get(section) or []
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict)]


def section_filled(payload: dict[str, Any], section: str) -> bool:
    return len(_section_items(payload, section)) > 0


def compute_completeness_score(payload: dict[str, Any]) -> float:
    score = 0.0
    for section, weight in SECTION_WEIGHTS.items():
        if section_filled(payload, section):
            score += weight
    return round(min(100.0, score), 1)


def compute_evidence_coverage(payload: dict[str, Any]) -> float:
    items: list[dict[str, Any]] = []
    for section in SECTION_WEIGHTS:
        items.extend(_section_items(payload, section))
    if not items:
        return 0.0
    covered = 0
    for item in items:
        evidence_ids = item.get("evidence_ids") or []
        if isinstance(evidence_ids, list) and len(evidence_ids) > 0:
            covered += 1
    return round((covered / len(items)) * 100.0, 1)


def compute_confidence_score(payload: dict[str, Any]) -> float:
    items: list[dict[str, Any]] = []
    for section in (
        "business_objectives",
        "functional_requirements",
        "non_functional_requirements",
        "constraints",
        "dependencies",
        "risks",
        "assumptions",
    ):
        items.extend(_section_items(payload, section))
    if not items:
        return 20.0

    confidences: list[float] = []
    for item in items:
        try:
            confidences.append(float(item.get("confidence") or 50))
        except (TypeError, ValueError):
            confidences.append(50.0)
    avg = sum(confidences) / len(confidences)
    evidence = compute_evidence_coverage(payload)
    # Blend item confidence with evidence coverage.
    blended = (avg * 0.7) + (evidence * 0.3)
    return round(max(0.0, min(100.0, blended)), 1)


def compute_consistency_score(payload: dict[str, Any], conflicts: list[dict[str, Any]]) -> float:
    base = 80.0
    if section_filled(payload, "functional_requirements") and section_filled(
        payload,
        "non_functional_requirements",
    ):
        base += 10.0
    penalty = min(40.0, len(conflicts) * 10.0)
    return round(max(0.0, min(100.0, base - penalty)), 1)


def quality_level(score: float) -> str:
    if score >= 95:
        return "enterprise_ready"
    if score >= 90:
        return "excellent"
    if score >= 80:
        return "good"
    if score >= 70:
        return "requires_review"
    return "incomplete"


def overall_quality(completeness: float, confidence: float) -> float:
    return round((completeness * 0.55) + (confidence * 0.45), 1)
