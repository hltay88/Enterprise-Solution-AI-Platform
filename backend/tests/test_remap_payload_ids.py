from app.services.gap_analysis_service import _remap_payload_entity_ids


def test_remap_payload_assigns_new_requirement_and_evidence_ids():
    original_req = "11111111-1111-1111-1111-111111111111"
    original_ev = "22222222-2222-2222-2222-222222222222"
    payload = {
        "functional_requirements": [
            {
                "id": original_req,
                "title": "WiFi",
                "description": "Coverage required",
                "evidence_ids": [original_ev],
            }
        ],
        "business_objectives": [],
        "non_functional_requirements": [],
        "constraints": [],
        "dependencies": [],
        "risks": [],
        "assumptions": [],
        "stakeholders": [],
        "current_environment": {"summary": "", "items": []},
        "evidence": [
            {
                "id": original_ev,
                "source_type": "document",
                "excerpt": "wifi",
            }
        ],
        "clarification_questions": [
            {
                "id": "33333333-3333-3333-3333-333333333333",
                "question": "Where?",
                "affected_requirement_ids": [original_req],
                "status": "open",
            }
        ],
    }

    remapped = _remap_payload_entity_ids(payload)
    new_req = remapped["functional_requirements"][0]["id"]
    new_ev = remapped["evidence"][0]["id"]
    assert new_req != original_req
    assert new_ev != original_ev
    assert remapped["functional_requirements"][0]["evidence_ids"] == [new_ev]
    assert remapped["clarification_questions"][0]["affected_requirement_ids"] == [new_req]
    # Clarification question ids stay stable.
    assert (
        remapped["clarification_questions"][0]["id"]
        == "33333333-3333-3333-3333-333333333333"
    )
