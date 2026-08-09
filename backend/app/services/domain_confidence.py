"""Sprint 3.1 Task 10 — domain confidence normalization and penalties.

Pure helpers. Confidence is always expressed on a 0.0–1.0 scale.
"""

from __future__ import annotations

from typing import Any

from app.schemas.domain import DomainAIExtraction, DomainOpenQuestionAI, SolutionDomainAI

_MIN_CONFIDENCE = 0.05
_MAX_CONFIDENCE = 1.0
_PENALTY_NO_SUPPORTING = 0.20
_PENALTY_SINGLE_SUPPORTING = 0.05
_PENALTY_AFFECTS_SELECTION_QUESTION = 0.08
_PENALTY_ANALYSIS_QUESTION = 0.05
_PENALTY_DEPENDENCY_SOURCE = 0.05
_MAX_QUESTION_PENALTY = 0.35


def clamp_confidence(value: Any) -> float:
    """Normalize 0–1 or 0–100 inputs and clamp to ``[_MIN_CONFIDENCE, 1]`` when >0.

    Zero stays zero (explicit unknown / empty).
    """
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    if number > 1.0:
        number = number / 100.0
    if number <= 0.0:
        return 0.0
    if number > _MAX_CONFIDENCE:
        number = _MAX_CONFIDENCE
    if number < _MIN_CONFIDENCE:
        return _MIN_CONFIDENCE
    return round(number, 4)


def score_domain_confidence(
    domain: SolutionDomainAI,
    *,
    analysis_open_questions: list[DomainOpenQuestionAI] | None = None,
) -> float:
    """Apply evidence / open-question penalties to a domain's base confidence."""
    base = clamp_confidence(domain.confidence)
    if base == 0.0:
        # Still apply a small floor when the domain was emitted with work product.
        base = _MIN_CONFIDENCE

    penalty = 0.0
    supporting = [item for item in domain.supporting_requirements if str(item).strip()]
    if domain.selection_source == "requirement":
        if not supporting:
            penalty += _PENALTY_NO_SUPPORTING
        elif len(supporting) == 1:
            penalty += _PENALTY_SINGLE_SUPPORTING

    if domain.selection_source == "dependency":
        penalty += _PENALTY_DEPENDENCY_SOURCE

    question_penalty = 0.0
    for question in domain.open_questions:
        if question.affects_selection:
            question_penalty += _PENALTY_AFFECTS_SELECTION_QUESTION

    for question in analysis_open_questions or []:
        if not question.affects_selection:
            continue
        if question.domain_code == domain.domain_code:
            question_penalty += _PENALTY_ANALYSIS_QUESTION
        elif domain.domain_code and domain.domain_code in question.question.lower():
            question_penalty += _PENALTY_ANALYSIS_QUESTION

    penalty += min(question_penalty, _MAX_QUESTION_PENALTY)
    adjusted = base - penalty
    return clamp_confidence(adjusted)


def apply_confidence_to_extraction(extraction: DomainAIExtraction) -> DomainAIExtraction:
    """Return extraction with recalculated per-domain confidence values."""
    updated = [
        domain.model_copy(
            update={
                "confidence": score_domain_confidence(
                    domain,
                    analysis_open_questions=list(extraction.open_questions),
                ),
            },
        )
        for domain in extraction.domains
    ]
    return extraction.model_copy(update={"domains": updated})
