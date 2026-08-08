from app.services.gap_scoring import (
    compute_completeness_score,
    compute_confidence_score,
    compute_evidence_coverage,
    overall_quality,
    quality_level,
)


def _sample_payload(**overrides):
    payload = {
        "business_objectives": [
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "title": "Improve WiFi",
                "description": "Improve campus wireless reliability for students",
                "confidence": 70,
                "evidence_ids": ["22222222-2222-2222-2222-222222222222"],
            }
        ],
        "current_environment": {
            "summary": "Existing schematic",
            "items": [
                {
                    "id": "33333333-3333-3333-3333-333333333333",
                    "title": "Server room",
                    "description": "Core present",
                    "evidence_ids": ["22222222-2222-2222-2222-222222222222"],
                }
            ],
        },
        "functional_requirements": [
            {
                "id": "44444444-4444-4444-4444-444444444444",
                "title": "WiFi coverage",
                "description": "Cover hostel and south block with enterprise WiFi",
                "confidence": 65,
                "evidence_ids": ["22222222-2222-2222-2222-222222222222"],
            }
        ],
        "non_functional_requirements": [
            {
                "id": "55555555-5555-5555-5555-555555555555",
                "title": "Availability",
                "description": "High availability for campus network services",
                "confidence": 60,
                "evidence_ids": [],
            }
        ],
        "constraints": [],
        "dependencies": [],
        "risks": [
            {
                "id": "66666666-6666-6666-6666-666666666666",
                "title": "Incomplete plans",
                "description": "Floor plans may be incomplete for AP placement",
                "confidence": 55,
                "evidence_ids": ["22222222-2222-2222-2222-222222222222"],
            }
        ],
        "assumptions": [
            {
                "id": "77777777-7777-7777-7777-777777777777",
                "title": "Server room stays",
                "description": "Existing server room remains in use",
                "confidence": 50,
                "evidence_ids": ["22222222-2222-2222-2222-222222222222"],
            }
        ],
        "stakeholders": [
            {
                "id": "88888888-8888-8888-8888-888888888888",
                "name": "Site PIC",
                "evidence_ids": ["22222222-2222-2222-2222-222222222222"],
            }
        ],
    }
    payload.update(overrides)
    return payload


def test_completeness_uses_section_weights():
    score = compute_completeness_score(_sample_payload())
    # business 10 + env 10 + functional 20 + nfr 20 + risks 10 + stakeholders 5 + assumptions 5 = 80
    assert score == 80.0


def test_evidence_coverage_and_confidence():
    payload = _sample_payload()
    coverage = compute_evidence_coverage(payload)
    assert coverage > 0
    confidence = compute_confidence_score(payload)
    assert 40 <= confidence <= 90
    assert quality_level(overall_quality(80, confidence)) in {
        "requires_review",
        "good",
        "excellent",
        "incomplete",
        "enterprise_ready",
    }


def test_empty_payload_scores_low():
    payload = {
        "business_objectives": [],
        "current_environment": {"summary": "", "items": []},
        "functional_requirements": [],
        "non_functional_requirements": [],
        "constraints": [],
        "dependencies": [],
        "risks": [],
        "assumptions": [],
        "stakeholders": [],
    }
    assert compute_completeness_score(payload) == 0.0
    assert compute_evidence_coverage(payload) == 0.0
