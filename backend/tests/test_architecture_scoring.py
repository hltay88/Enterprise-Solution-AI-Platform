"""Sprint 3.2 Task 9 — architecture scoring engine."""

from __future__ import annotations

from app.schemas.architecture_option import (
    DEFAULT_SCORE_WEIGHTS,
    validate_architecture_ai_extraction,
)
from app.services.architecture_scoring import (
    SCORE_DIMENSION_ORDER,
    compute_overall_score,
    default_score_weights,
    enrich_architecture_scores,
    preprocess_scores_in_extraction,
    sanitize_score_dict,
    score_summary_for_candidate,
)


def test_default_weights_match_doc():
    weights = default_score_weights()
    assert weights == DEFAULT_SCORE_WEIGHTS
    assert abs(sum(weights.values()) - 1.0) < 1e-9


def test_sanitize_fills_missing_explanation_and_weight():
    cleaned = sanitize_score_dict({"dimension": "security", "score": 4})
    assert cleaned is not None
    assert cleaned["weight"] == DEFAULT_SCORE_WEIGHTS["security"]
    assert cleaned["explanation"]
    assert cleaned["score"] == 4.0


def test_sanitize_drops_unknown_dimension():
    assert sanitize_score_dict({"dimension": "vibes", "score": 5, "explanation": "x"}) is None


def test_preprocess_and_validate_scores_without_explanations():
    raw = {
        "architectures": [
            {
                "candidate_key": "standard",
                "title": "Standard",
                "summary": "Campus",
                "components": [{"name": "Access", "purpose": "Underlay"}],
                "scores": [
                    {"dimension": "coverage", "score": 4},
                    {"dimension": "vibes", "score": 5, "explanation": "nope"},
                ],
            },
        ],
    }
    cleaned = preprocess_scores_in_extraction(raw)
    payload = validate_architecture_ai_extraction(cleaned)
    assert len(payload.architectures[0].scores) == 1
    assert payload.architectures[0].scores[0].dimension == "requirement_coverage"
    assert payload.architectures[0].scores[0].explanation


def test_enrich_fills_all_dimensions_with_explanations():
    base = validate_architecture_ai_extraction(
        {
            "architectures": [
                {
                    "candidate_key": "high_availability",
                    "title": "HA campus",
                    "summary": "Redundant campus Wi-Fi",
                    "pattern_codes": ["wireless_enterprise", "two_tier_campus"],
                    "components": [
                        {
                            "name": "WLAN",
                            "purpose": "Coverage",
                            "maps_to_requirements": ["REQ-WIFI-1"],
                        },
                        {
                            "name": "Identity",
                            "purpose": "802.1X",
                            "maps_to_requirements": ["REQ-WIFI-1"],
                        },
                    ],
                    "scores": [
                        {
                            "dimension": "requirement_coverage",
                            "score": 4,
                            "explanation": "Covers Wi-Fi req",
                        },
                    ],
                    "capacity_notes": [
                        {
                            "label": "AP count",
                            "open_question": "Need floor plans",
                            "confidence": 0.2,
                        },
                    ],
                },
            ],
        },
    )
    enriched = enrich_architecture_scores(
        base,
        requirements=[
            {
                "id": "REQ-WIFI-1",
                "title": "WiFi",
                "description": "Coverage",
            },
        ],
    )
    candidate = enriched.architectures[0]
    dims = [item.dimension for item in candidate.scores]
    assert dims == list(SCORE_DIMENSION_ORDER)
    assert all(item.explanation for item in candidate.scores)
    assert all(item.weight == DEFAULT_SCORE_WEIGHTS[item.dimension] for item in candidate.scores)
    ha = next(
        item for item in candidate.scores if item.dimension == "availability_resilience"
    )
    assert ha.score >= 3.5
    summary = score_summary_for_candidate(candidate)
    assert summary["overall_score"] == compute_overall_score(list(candidate.scores))
    assert "decision support" in summary["governance_note"].lower()


def test_compute_overall_score():
    assert compute_overall_score([]) is None
    assert (
        compute_overall_score(
            [
                {"weight": 0.3, "score": 4},
                {"weight": 0.7, "score": 2},
            ],
        )
        == 2.6
    )
