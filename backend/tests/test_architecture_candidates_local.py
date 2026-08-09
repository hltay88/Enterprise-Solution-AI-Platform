"""Sprint 3.2 Task 5 — multi-candidate architecture AI (local + normalize)."""

from __future__ import annotations

import asyncio

import pytest

from app.ai.common import normalize_architecture_candidates
from app.ai.local_provider import LocalAIProvider
from app.core.exceptions import AppError


def test_local_recommend_architectures_from_wifi_rkm():
    provider = LocalAIProvider()
    rkm = {
        "business_objectives": [
            {"id": "OBJ-1", "title": "Improve coverage", "description": "Reliable campus WiFi"},
        ],
        "functional_requirements": [
            {
                "id": "REQ-WIFI-1",
                "title": "WiFi 6 coverage",
                "description": "3 floors with seamless roaming and 802.1X",
            }
        ],
        "non_functional_requirements": [
            {
                "id": "NFR-HA-1",
                "title": "High availability",
                "description": "Redundant controllers preferred",
            }
        ],
        "constraints": [],
        "risks": [{"id": "RISK-1", "title": "Survey delay", "description": "Floor plans late"}],
        "assumptions": [],
    }
    result = asyncio.run(
        provider.recommend_architectures(
            rkm,
            domain_context="Primary domains: wifi, campus_lan, identity",
            pattern_context="Patterns: wireless_enterprise, two_tier_campus",
        ),
    )
    assert result["provider"] == "local"
    assert len(result["architectures"]) >= 2
    keys = {item["candidate_key"] for item in result["architectures"]}
    assert "standard" in keys
    assert "high_availability" in keys
    standard = next(item for item in result["architectures"] if item["candidate_key"] == "standard")
    assert standard["components"]
    assert "wireless_enterprise" in standard["pattern_codes"]
    assert any(note.get("open_question") for note in standard["capacity_notes"])
    assert all(
        "cisco" not in str(item).lower() and "aruba" not in str(item).lower()
        for item in result["architectures"]
    )


def test_normalize_architecture_candidates_rejects_empty():
    with pytest.raises(AppError, match="invalid architecture candidates"):
        normalize_architecture_candidates({"architectures": []})


def test_normalize_architecture_candidates_accepts_valid_payload():
    payload = normalize_architecture_candidates(
        {
            "summary": "One candidate",
            "architectures": [
                {
                    "candidate_key": "standard",
                    "title": "Standard campus",
                    "summary": "Two-tier campus",
                    "pattern_codes": ["two_tier_campus"],
                    "components": [
                        {
                            "name": "Access",
                            "purpose": "Endpoints",
                            "maps_to_requirements": ["R1"],
                        },
                    ],
                    "capacity_notes": [
                        {
                            "label": "Ports",
                            "open_question": "How many access ports?",
                            "confidence": 0.1,
                        },
                    ],
                },
            ],
        },
    )
    assert payload["architectures"][0]["pattern_codes"] == ["two_tier_campus"]
