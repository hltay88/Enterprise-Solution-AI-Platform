from app.services.gap_analysis_service import GapAnalysisService


class _DummyService(GapAnalysisService):
    def __init__(self):
        # Bypass DB init for pure helper tests.
        self.db = None
        self.projects = None
        self.rkms = None


def test_build_clarifications_for_missing_wifi_sections():
    service = _DummyService()
    payload = {
        "business_objectives": [],
        "current_environment": {"summary": "", "items": []},
        "functional_requirements": [
            {
                "id": "44444444-4444-4444-4444-444444444444",
                "title": "Campus WiFi",
                "description": "Need reliable WiFi coverage across hostel blocks",
                "evidence_ids": [],
            }
        ],
        "non_functional_requirements": [],
        "constraints": [],
        "dependencies": [],
        "risks": [],
        "assumptions": [],
        "stakeholders": [],
    }
    missing = [
        "business_objectives",
        "current_environment",
        "non_functional_requirements",
        "constraints",
        "dependencies",
        "risks",
        "stakeholders",
        "assumptions",
    ]
    gaps = service._detect_gaps(payload, missing)
    questions = service._build_clarifications(payload, missing, gaps)
    assert questions
    assert any("WiFi" in q.question or "wifi" in q.question.lower() for q in questions)
    assert any(q.priority in {"critical", "high", "medium", "low"} for q in questions)
    assert all(q.status == "open" for q in questions)


def test_publish_blockers_include_thresholds():
    service = _DummyService()
    blockers = service._publish_blockers(
        completeness=60,
        confidence=70,
        gaps=[],
        payload={"approval": {"status": "ai_generated"}},
    )
    codes = {item.code for item in blockers}
    assert "completeness_below_threshold" in codes
    assert "confidence_below_threshold" in codes
    assert "human_approval_required" in codes
