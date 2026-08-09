"""Sprint 3.2 Task 9 — architecture scoring engine.

Pure helpers (no DB/AI). Aligns with docs/Phase 3/11_SOLUTION_SCORING.md:
default weights, 0–5 scale, every score needs an explanation. Scores are
decision support only — not automatic approval.
"""

from __future__ import annotations

from typing import Any

from app.schemas.architecture_option import (
    ALLOWED_SCORE_DIMENSIONS,
    ArchitectureAIExtraction,
    ArchitectureCandidateAI,
    DEFAULT_SCORE_WEIGHTS,
    SolutionScoreAI,
)

# Stable dimension order for persist/API readability.
SCORE_DIMENSION_ORDER: tuple[str, ...] = tuple(DEFAULT_SCORE_WEIGHTS.keys())


def default_score_weights() -> dict[str, float]:
    """Return a copy of the documented default weight profile."""
    return dict(DEFAULT_SCORE_WEIGHTS)


def compute_overall_score(
    scores: list[dict[str, Any]] | list[SolutionScoreAI],
) -> float | None:
    """Weighted average on 0–5 scale using each score's weight."""
    total_weight = 0.0
    weighted = 0.0
    for item in scores:
        if isinstance(item, SolutionScoreAI):
            weight = float(item.weight or 0)
            score = float(item.score or 0)
        elif isinstance(item, dict):
            try:
                weight = float(item.get("weight") or 0)
                score = float(item.get("score") or 0)
            except (TypeError, ValueError):
                continue
        else:
            continue
        if weight <= 0:
            continue
        total_weight += weight
        weighted += weight * score
    if total_weight <= 0:
        return None
    return round(weighted / total_weight, 2)


def preprocess_scores_in_extraction(
    payload: dict[str, Any],
    *,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Normalize score rows before schema validation.

    Drops unknown dimensions, clamps scores to 0–5, applies weights, and ensures
    a non-empty explanation (required by governance).
    """
    if not isinstance(payload, dict):
        return payload
    weight_profile = _resolve_weights(weights)
    architectures = payload.get("architectures")
    if architectures is None and "architecture" in payload:
        architectures = payload.get("architecture")
    if isinstance(architectures, dict):
        architectures = [architectures]
    if not isinstance(architectures, list):
        return payload

    out_arch: list[Any] = []
    for item in architectures:
        if not isinstance(item, dict):
            out_arch.append(item)
            continue
        row = dict(item)
        scores_in = row.get("scores") or []
        if not isinstance(scores_in, list):
            scores_in = []
        cleaned: list[dict[str, Any]] = []
        seen: set[str] = set()
        for raw in scores_in:
            note = sanitize_score_dict(raw, weights=weight_profile)
            if note is None:
                continue
            dim = note["dimension"]
            if dim in seen:
                continue
            seen.add(dim)
            cleaned.append(note)
        row["scores"] = cleaned
        out_arch.append(row)

    result = dict(payload)
    result["architectures"] = out_arch
    if "architecture" in result and not isinstance(result.get("architecture"), list):
        result["architecture"] = out_arch[0] if out_arch else result["architecture"]
    return result


def sanitize_score_dict(
    note: Any,
    *,
    weights: dict[str, float] | None = None,
) -> dict[str, Any] | None:
    """Return a normalized score dict, or None if dimension is unknown."""
    if not isinstance(note, dict):
        return None
    weight_profile = _resolve_weights(weights)
    dimension = _normalize_dimension(note.get("dimension"))
    if dimension is None:
        return None
    score = _clamp_score(note.get("score"))
    explanation = str(note.get("explanation") or "").strip()
    if not explanation:
        explanation = (
            f"{dimension.replace('_', ' ').title()} scored {score}/5; "
            "explanation pending architecture review"
        )
    weight = note.get("weight")
    if weight is None or weight == "":
        resolved_weight = weight_profile[dimension]
    else:
        try:
            resolved_weight = float(weight)
        except (TypeError, ValueError):
            resolved_weight = weight_profile[dimension]
        if resolved_weight < 0 or resolved_weight > 1:
            resolved_weight = weight_profile[dimension]
    return {
        "dimension": dimension,
        "weight": round(resolved_weight, 4),
        "score": score,
        "explanation": explanation,
    }


def enrich_architecture_scores(
    extraction: ArchitectureAIExtraction,
    *,
    weights: dict[str, float] | None = None,
    requirements: list[dict[str, Any]] | None = None,
) -> ArchitectureAIExtraction:
    """Ensure all default dimensions exist with explanations; fill gaps heuristically.

    Does not auto-approve. Missing dimensions get conservative heuristic scores
    with explicit explanations marked as heuristic.
    """
    weight_profile = _resolve_weights(weights)
    refined: list[ArchitectureCandidateAI] = []

    for candidate in extraction.architectures:
        by_dim: dict[str, SolutionScoreAI] = {}
        for item in candidate.scores:
            cleaned = sanitize_score_dict(item.model_dump(), weights=weight_profile)
            if cleaned is None:
                continue
            by_dim[cleaned["dimension"]] = SolutionScoreAI.model_validate(cleaned)

        for dimension in SCORE_DIMENSION_ORDER:
            if dimension in by_dim:
                # Re-apply project/default weight while keeping AI score/explanation.
                existing = by_dim[dimension]
                by_dim[dimension] = existing.model_copy(
                    update={"weight": weight_profile[dimension]},
                )
                continue
            score, explanation = _heuristic_score(
                dimension,
                candidate,
                requirements=requirements,
            )
            by_dim[dimension] = SolutionScoreAI(
                dimension=dimension,
                weight=weight_profile[dimension],
                score=score,
                explanation=explanation,
            )

        ordered = [by_dim[dim] for dim in SCORE_DIMENSION_ORDER if dim in by_dim]
        refined.append(candidate.model_copy(update={"scores": ordered}))

    return extraction.model_copy(update={"architectures": refined})


def score_summary_for_candidate(
    candidate: ArchitectureCandidateAI,
    *,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Build audit-friendly scoring metadata for one candidate."""
    weight_profile = _resolve_weights(weights)
    overall = compute_overall_score(list(candidate.scores))
    return {
        "overall_score": overall,
        "score_weights": weight_profile,
        "score_scale": {"min": 0, "max": 5},
        "governance_note": (
            "Scores are decision support only — not automatic architecture approval"
        ),
        "dimensions": [
            {
                "dimension": item.dimension,
                "weight": item.weight,
                "score": item.score,
                "explanation": item.explanation,
            }
            for item in candidate.scores
        ],
    }


def _resolve_weights(weights: dict[str, float] | None) -> dict[str, float]:
    profile = default_score_weights()
    if not weights:
        return profile
    for key, value in weights.items():
        dim = _normalize_dimension(key)
        if dim is None:
            continue
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if 0.0 <= number <= 1.0:
            profile[dim] = round(number, 4)
    # Keep sum informative but do not force renormalize (doc: weights recorded as used).
    return profile


def _normalize_dimension(value: Any) -> str | None:
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
        return None
    return normalized


def _clamp_score(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 3.0
    if number < 0:
        number = 0.0
    if number > 5:
        number = 5.0
    return round(number, 2)


def _heuristic_score(
    dimension: str,
    candidate: ArchitectureCandidateAI,
    *,
    requirements: list[dict[str, Any]] | None,
) -> tuple[float, str]:
    """Conservative fill-in when AI omitted a dimension."""
    req_count = len(requirements or [])
    mapped = {
        req
        for component in candidate.components
        for req in (component.maps_to_requirements or [])
    }
    has_patterns = bool(candidate.pattern_codes)
    is_ha = "availability" in candidate.candidate_key or candidate.candidate_key in {
        "high_availability",
        "ha",
        "resilient",
    }
    open_capacity = sum(
        1 for note in candidate.capacity_notes if note.open_question and not note.result
    )
    risk_count = len(candidate.risks)
    securityish = any(
        token in " ".join(candidate.pattern_codes).lower()
        or token in (candidate.summary or "").lower()
        for token in ("zero_trust", "security", "802.1x", "nac")
    ) or any(
        "security" in (component.name or "").lower()
        or "identity" in (component.name or "").lower()
        for component in candidate.components
    )

    if dimension == "requirement_coverage":
        if req_count and mapped:
            ratio = min(1.0, len(mapped) / max(1, min(req_count, 8)))
            score = round(2.5 + 2.0 * ratio, 2)
            return score, (
                f"Heuristic: {len(mapped)} component-linked requirement id(s) "
                f"against {req_count} published requirement(s)"
            )
        if candidate.components:
            return 3.0, "Heuristic: components present but requirement mapping is thin"
        return 2.0, "Heuristic: few components mapped to published requirements"

    if dimension == "technical_fit":
        if has_patterns and candidate.components:
            return 3.5, (
                "Heuristic: catalog pattern_codes and components present "
                f"({', '.join(candidate.pattern_codes[:3])})"
            )
        if has_patterns:
            return 3.0, "Heuristic: pattern codes present; component detail limited"
        return 2.5, "Heuristic: limited pattern alignment signals"

    if dimension == "security":
        if securityish:
            return 3.5, "Heuristic: security/identity signals present in candidate"
        return 2.5, "Heuristic: security controls not strongly evidenced — review needed"

    if dimension == "availability_resilience":
        if is_ha:
            return 4.0, "Heuristic: HA/resilience candidate key indicates stronger resilience"
        return 2.5, "Heuristic: standard resilience posture pending HA requirements"

    if dimension == "scalability":
        if open_capacity:
            return 2.5, (
                f"Heuristic: {open_capacity} open capacity question(s) limit "
                "scalability confidence"
            )
        return 3.0, "Heuristic: no blocking capacity gaps detected for scalability"

    if dimension == "operability":
        return 3.0, "Heuristic: baseline operability pending day-2 tooling detail"

    if dimension == "lifecycle":
        return 3.0, "Heuristic: vendor-neutral design defers lifecycle/SKU specifics"

    if dimension == "complexity":
        # Higher score = better (less painful). HA adds complexity → lower score.
        if is_ha or risk_count >= 3:
            return 2.5, "Heuristic: HA and/or multiple risks increase solution complexity"
        return 3.5, "Heuristic: relatively simple candidate relative to HA alternate"

    if dimension == "commercial_suitability":
        return 3.0, (
            "Heuristic: commercial fit deferred — no SKUs; treat as neutral "
            "decision-support score"
        )

    return 3.0, f"Heuristic: default acceptable score for {dimension}"
