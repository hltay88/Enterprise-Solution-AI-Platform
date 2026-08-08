"""Clarification answers must update Draft RKM content, not only evidence links."""

from app.services.gap_analysis_service import GapAnalysisService, _merge_answer_into_text


class _DummyService(GapAnalysisService):
    def __init__(self):
        self.db = None
        self.projects = None
        self.rkms = None


def test_merge_answer_replaces_thin_description():
    merged = _merge_answer_into_text("short", "Block A floors 1-3, 40 concurrent users per AP")
    assert "Block A floors 1-3" in merged
    assert "Prior note: short" in merged


def test_merge_answer_appends_to_rich_description():
    existing = "Need reliable WiFi coverage across hostel blocks for students."
    merged = _merge_answer_into_text(existing, "Block A/B, 80 users per floor")
    assert existing in merged
    assert "Customer clarification: Block A/B, 80 users per floor" in merged


def test_apply_answer_enriches_affected_functional_requirement():
    service = _DummyService()
    req_id = "44444444-4444-4444-4444-444444444444"
    payload = {
        "business_objectives": [],
        "current_environment": {"summary": "", "items": []},
        "functional_requirements": [
            {
                "id": req_id,
                "title": "Campus WiFi",
                "description": "Need reliable WiFi coverage across hostel blocks",
                "confidence": 40,
                "evidence_ids": [],
            }
        ],
        "non_functional_requirements": [],
        "constraints": [],
        "dependencies": [],
        "risks": [],
        "assumptions": [],
        "stakeholders": [],
        "evidence": [],
    }
    answer = "Blocks A and B, floors 1-4, ~60 concurrent users per floor."
    evidence_id = "55555555-5555-5555-5555-555555555555"
    service._apply_clarification_answer(
        payload,
        clarification={
            "question": "Which buildings/floors need WiFi coverage, and what concurrent user density is expected?",
            "section": "functional_requirements",
            "affected_requirement_ids": [req_id],
            "confidence_impact": 10,
            "priority": "high",
        },
        answer_text=answer,
        evidence_id=evidence_id,
    )
    item = payload["functional_requirements"][0]
    assert answer in item["description"]
    assert "Customer clarification:" in item["description"]
    assert evidence_id in item["evidence_ids"]
    assert item["confidence"] >= 50


def test_apply_answer_creates_missing_business_objective():
    service = _DummyService()
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
        "evidence": [],
    }
    answer = "Improve student connectivity NPS by 20 points within 6 months."
    evidence_id = "66666666-6666-6666-6666-666666666666"
    service._apply_clarification_answer(
        payload,
        clarification={
            "question": "What business outcomes and success metrics are mandatory for go-live?",
            "reason": "Section 'business_objectives' is missing or empty in the Draft RKM.",
            "section": "business_objectives",
            "affected_requirement_ids": [],
            "confidence_impact": 8,
            "priority": "critical",
        },
        answer_text=answer,
        evidence_id=evidence_id,
    )
    assert len(payload["business_objectives"]) == 1
    created = payload["business_objectives"][0]
    assert created["description"] == answer
    assert created["title"]
    assert evidence_id in created["evidence_ids"]


def test_apply_answer_creates_environment_and_summary():
    service = _DummyService()
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
    answer = "2 hostel blocks, existing Cisco switches, no controller today."
    service._apply_clarification_answer(
        payload,
        clarification={
            "question": "What is the as-is environment?",
            "section": "current_environment",
            "affected_requirement_ids": [],
            "priority": "high",
        },
        answer_text=answer,
        evidence_id="77777777-7777-7777-7777-777777777777",
    )
    env = payload["current_environment"]
    assert env["summary"] == answer
    assert len(env["items"]) == 1
    assert env["items"][0]["description"] == answer


def test_apply_answer_creates_stakeholder_from_free_text():
    service = _DummyService()
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
    service._apply_clarification_answer(
        payload,
        clarification={
            "question": "Who are the decision-makers?",
            "section": "stakeholders",
            "affected_requirement_ids": [],
            "priority": "high",
        },
        answer_text="Alex Tan, IT Manager, alex@example.com",
        evidence_id="88888888-8888-8888-8888-888888888888",
    )
    assert len(payload["stakeholders"]) == 1
    person = payload["stakeholders"][0]
    assert person["name"] == "Alex Tan"
    assert "IT Manager" in (person.get("role") or "")
    assert "alex@example.com" in person["designation"]
