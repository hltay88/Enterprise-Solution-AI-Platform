from app.schemas.gap import ClarificationOut
from app.services.gap_analysis_service import GapAnalysisService


def test_merge_preserves_clarification_ids_by_question_text():
    """Simulate the merge logic used when re-running gap analysis."""
    previous = [
        {
            "id": "11111111-1111-1111-1111-111111111111",
            "question": "What firewall throughput is required?",
            "priority": "high",
            "category": "Security",
            "reason": "missing target",
            "affected_requirement_ids": [],
            "status": "open",
            "answer": None,
        },
        {
            "id": "22222222-2222-2222-2222-222222222222",
            "question": "Who is the PIC?",
            "priority": "high",
            "category": "Business",
            "reason": "answered earlier",
            "affected_requirement_ids": [],
            "status": "answered",
            "answer": "Alex",
        },
    ]
    fresh = [
        ClarificationOut(
            id="99999999-9999-9999-9999-999999999999",
            question="What firewall throughput is required?",
            priority="high",
            category="Security",
            reason="missing target",
            affected_requirement_ids=[],
            status="open",
            answer=None,
        ),
        ClarificationOut(
            id="88888888-8888-8888-8888-888888888888",
            question="Which buildings need WiFi?",
            priority="high",
            category="Networking",
            reason="scope unclear",
            affected_requirement_ids=[],
            status="open",
            answer=None,
        ),
    ]

    previous_by_question = {
        str(item.get("question") or "").strip().lower(): item for item in previous
    }
    merged = []
    seen = set()
    for item in fresh:
        data = item.model_dump(mode="json")
        key = str(data.get("question") or "").strip().lower()
        prior = previous_by_question.get(key)
        if prior is not None:
            data["id"] = str(prior.get("id") or data["id"])
            if prior.get("status") == "answered" and prior.get("answer"):
                data["status"] = "answered"
                data["answer"] = prior.get("answer")
        merged.append(data)
        seen.add(key)
    for item in previous:
        key = str(item.get("question") or "").strip().lower()
        if item.get("status") == "answered" and key not in seen:
            merged.append(item)

    by_id = {item["id"]: item for item in merged}
    assert "11111111-1111-1111-1111-111111111111" in by_id
    assert by_id["11111111-1111-1111-1111-111111111111"]["question"].startswith(
        "What firewall",
    )
    assert "22222222-2222-2222-2222-222222222222" in by_id
    assert by_id["22222222-2222-2222-2222-222222222222"]["status"] == "answered"
