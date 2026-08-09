"""Sprint 3.2 Task 3 — architecture candidate AI/API Pydantic schemas."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.architecture_option import (
    ArchitectureOptionOut,
    DEFAULT_SCORE_WEIGHTS,
    validate_architecture_ai_extraction,
)


def _minimal_candidate(**overrides):
    base = {
        "candidate_key": "standard",
        "title": "Standard campus + Wi-Fi",
        "summary": "Vendor-neutral campus LAN with enterprise WLAN",
        "pattern_codes": ["wireless_enterprise", "two_tier_campus"],
        "confidence": 80,
        "components": [
            {
                "name": "Access switching",
                "purpose": "Wired underlay for APs and endpoints",
                "component_kind": "logical",
                "maps_to_requirements": ["REQ-WIFI-1"],
                "temp_id": "c1",
            },
            {
                "name": "WLAN controllers / cloud mgmt",
                "purpose": "Wireless policy and RF management",
                "maps_to_requirements": ["REQ-WIFI-1"],
                "temp_id": "c2",
            },
        ],
        "relationships": [
            {
                "from_component": "c2",
                "to_component": "c1",
                "relationship_kind": "depends_on",
                "description": "APs need wired underlay",
            },
        ],
        "decisions": [
            {
                "decision": "Keep design vendor-neutral",
                "rationale": "ATLAS-035",
                "impact": "Product selection deferred to Sprint 3.3",
            },
        ],
        "assumptions": [
            {
                "statement": "Existing cabling can support AP power",
                "reason": "Customer stated reuse of cabling",
                "validation_required": True,
            },
        ],
        "risks": [
            {
                "description": "Survey delay may slip AP placement",
                "category": "capacity",
                "severity": "medium",
                "probability": "medium",
                "mitigation": "Schedule early walkthrough",
                "related_requirement_ids": ["REQ-WIFI-1"],
            },
        ],
        "scores": [
            {
                "dimension": "requirement_coverage",
                "score": 4,
                "explanation": "Covers Wi-Fi and campus underlay requirements",
            },
            {
                "dimension": "security",
                "score": 3,
                "explanation": "Assumes 802.1X; details pending",
            },
        ],
        "capacity_notes": [
            {
                "label": "AP count (preliminary)",
                "input_value": "3 floors, 800 clients",
                "unit": "APs",
                "method": "density heuristic pending survey",
                "assumption": "Open office density ~1 device/person",
                "result": "Preliminary only — survey required",
                "confidence": 0.4,
                "open_question": "Confirm floor plans and wall materials",
            },
        ],
    }
    base.update(overrides)
    return base


def test_valid_multi_candidate_extraction():
    payload = validate_architecture_ai_extraction(
        {
            "summary": "Two candidates for campus wireless",
            "architectures": [
                _minimal_candidate(),
                _minimal_candidate(
                    candidate_key="high_availability",
                    title="HA campus + Wi-Fi",
                    summary="Adds redundant controllers and dual uplinks",
                ),
            ],
        },
    )
    assert len(payload.architectures) == 2
    assert payload.architectures[0].pattern_codes == [
        "wireless_enterprise",
        "two_tier_campus",
    ]
    assert payload.architectures[0].confidence == 0.8
    assert payload.architectures[0].scores[0].weight == DEFAULT_SCORE_WEIGHTS[
        "requirement_coverage"
    ]


def test_accepts_singular_architecture_key_and_aliases():
    payload = validate_architecture_ai_extraction(
        {
            "architecture": {
                "name": "Standard",
                "summary": "Simple option",
                "solution_components": [
                    {"name": "Core", "purpose": "Routing", "maps_to_requirements": ["R1"]},
                ],
                "architecture_decisions": [
                    {"decision": "Two-tier", "rationale": "Site size"},
                ],
                "pattern_codes": ["SD-WAN"],
            },
        },
    )
    assert len(payload.architectures) == 1
    assert payload.architectures[0].candidate_key == "standard"
    assert payload.architectures[0].title == "Standard"
    assert payload.architectures[0].pattern_codes == ["sdwan"]
    assert payload.architectures[0].components[0].name == "Core"
    assert payload.architectures[0].decisions[0].decision == "Two-tier"


def test_rejects_unknown_pattern_code():
    with pytest.raises(ValidationError):
        validate_architecture_ai_extraction(
            {
                "architectures": [
                    _minimal_candidate(pattern_codes=["cisco-magic-pattern"]),
                ],
            },
        )


def test_rejects_empty_components():
    with pytest.raises(ValidationError, match="at least one component"):
        validate_architecture_ai_extraction(
            {
                "architectures": [
                    _minimal_candidate(components=[]),
                ],
            },
        )


def test_rejects_duplicate_candidate_keys():
    with pytest.raises(ValidationError, match="unique"):
        validate_architecture_ai_extraction(
            {
                "architectures": [
                    _minimal_candidate(candidate_key="standard"),
                    _minimal_candidate(candidate_key="standard", title="Dup"),
                ],
            },
        )


def test_rejects_score_without_explanation():
    bad = _minimal_candidate(
        scores=[{"dimension": "security", "score": 4, "explanation": ""}],
    )
    with pytest.raises(ValidationError):
        validate_architecture_ai_extraction({"architectures": [bad]})


def test_rejects_fabricated_capacity_result():
    bad = _minimal_candidate(
        capacity_notes=[
            {
                "label": "AP count",
                "result": "42",
                "confidence": 0.9,
            },
        ],
    )
    with pytest.raises(ValidationError, match="fabricate|open_question|input"):
        validate_architecture_ai_extraction({"architectures": [bad]})


def test_capacity_open_question_without_result_ok():
    payload = validate_architecture_ai_extraction(
        {
            "architectures": [
                _minimal_candidate(
                    capacity_notes=[
                        {
                            "label": "Internet bandwidth",
                            "open_question": "What peak egress Mbps is required?",
                            "confidence": 0.2,
                        },
                    ],
                ),
            ],
        },
    )
    assert payload.architectures[0].capacity_notes[0].result is None
    assert payload.architectures[0].capacity_notes[0].open_question


def test_architecture_option_out_round_trip_shape():
    now = datetime.now(timezone.utc)
    out = ArchitectureOptionOut(
        id=uuid4(),
        project_id=uuid4(),
        generation_id=uuid4(),
        candidate_key="standard",
        title="Option A",
        version_label="1.0.0",
        created_at=now,
        updated_at=now,
        components=[],
    )
    dumped = out.model_dump(mode="json")
    assert dumped["candidate_key"] == "standard"
    assert dumped["version_label"] == "1.0.0"
