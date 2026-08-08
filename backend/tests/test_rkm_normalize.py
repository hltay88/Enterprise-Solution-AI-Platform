from app.ai.common import normalize_rkm_extraction
from app.constants.rkm import normalize_category, normalize_priority
from app.services.rkm_generation_service import _compute_scores, _confidence


def test_normalize_rkm_extraction_accepts_string_items():
    payload = normalize_rkm_extraction(
        {
            "business_objectives": ["Improve campus WiFi reliability"],
            "functional_requirements": [
                {
                    "title": "Provide WiFi coverage",
                    "description": "Cover hostel and south block",
                    "category": "infrastructure",
                    "priority": "high",
                    "confidence": 70,
                },
            ],
            "current_environment": {
                "summary": "Existing schematic available",
                "items": ["Server room present"],
            },
            "reasoning_summary": "Derived from intake + drawing",
        },
    )
    assert payload["business_objectives"][0]["title"].startswith("Improve campus")
    assert payload["functional_requirements"][0]["category"] == "infrastructure"
    assert payload["current_environment"]["items"][0]["title"].startswith("Server room")


def test_normalize_category_and_priority():
    assert normalize_category("Infra") == "infrastructure"
    assert normalize_category("nfr") == "non_functional"
    assert normalize_priority("HIGH") == "high"
    assert normalize_priority("nope") == "medium"


def test_confidence_and_scores():
    assert _confidence(0.8, default=50) == 80
    assert _confidence(65, default=50) == 65
    scores = _compute_scores(
        business=[{"confidence": 60}],
        functional=[{"confidence": 70}],
        non_functional=[],
        evidence_count=3,
        linked_count=4,
        has_intake=True,
        has_docs=True,
    )
    assert scores["completeness_score"] >= 70
    assert scores["confidence_score"] == 65.0
    assert scores["evidence_coverage"] > 0
