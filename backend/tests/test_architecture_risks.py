"""Sprint 3.2 Task 8 — risk and assumption builder."""

from __future__ import annotations

from app.schemas.architecture_option import validate_architecture_ai_extraction
from app.services.architecture_risks import (
    enrich_architecture_risks_assumptions,
    preprocess_risks_assumptions_in_extraction,
    sanitize_assumption_dict,
    sanitize_risk_dict,
)


def test_sanitize_risk_normalizes_category_alias():
    cleaned = sanitize_risk_dict(
        {
            "description": "Uplink may saturate",
            "category": "ha",
            "probability": "HIGH",
            "severity": "critical",
        },
    )
    assert cleaned["category"] == "availability"
    assert cleaned["probability"] == "high"
    assert cleaned["severity"] == "critical"


def test_sanitize_assumption_never_auto_validates():
    cleaned = sanitize_assumption_dict(
        {
            "statement": "Cabling can be reused",
            "status": "validated",
            "validation_required": False,
        },
    )
    assert cleaned["status"] == "unvalidated"
    assert cleaned["validation_required"] is True


def test_preprocess_accepts_legacy_string_lists():
    raw = {
        "architectures": [
            {
                "candidate_key": "standard",
                "title": "Standard",
                "summary": "Campus",
                "components": [{"name": "Access", "purpose": "Underlay"}],
                "technical_risks": ["Survey delay"],
                "design_assumptions": ["Existing cabling reusable"],
            },
        ],
    }
    cleaned = preprocess_risks_assumptions_in_extraction(raw)
    payload = validate_architecture_ai_extraction(cleaned)
    assert payload.architectures[0].risks[0].description == "Survey delay"
    assert payload.architectures[0].assumptions[0].statement == "Existing cabling reusable"
    assert payload.architectures[0].assumptions[0].status == "unvalidated"


def test_enrich_merges_rkm_risks_and_baseline_assumptions():
    base = validate_architecture_ai_extraction(
        {
            "architectures": [
                {
                    "candidate_key": "standard",
                    "title": "Standard",
                    "summary": "Campus Wi-Fi",
                    "pattern_codes": ["wireless_enterprise"],
                    "components": [{"name": "WLAN", "purpose": "Coverage"}],
                    "risks": [],
                    "assumptions": [],
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
    enriched = enrich_architecture_risks_assumptions(
        base,
        domain_codes=["wifi"],
        rkm_payload={
            "risks": [
                {
                    "id": "RISK-1",
                    "title": "Survey delay",
                    "description": "Floor plans late",
                },
            ],
            "functional_requirements": [
                {
                    "id": "REQ-WIFI-1",
                    "title": "WiFi coverage",
                    "description": "Three floors",
                },
            ],
        },
        requirements=[
            {
                "id": "REQ-WIFI-1",
                "title": "WiFi coverage",
                "description": "Three floors",
            },
        ],
    )
    candidate = enriched.architectures[0]
    risk_text = " ".join(item.description.lower() for item in candidate.risks)
    assert "survey delay" in risk_text or "floor plans late" in risk_text
    statements = " ".join(item.statement.lower() for item in candidate.assumptions)
    assert "vendor selection remain out of scope" in statements
    assert "capacity sizing remains preliminary" in statements
    assert all(item.status == "unvalidated" for item in candidate.assumptions)
    assert all(item.validation_required for item in candidate.assumptions)


def test_enrich_adds_domain_starter_risk_when_no_signal():
    base = validate_architecture_ai_extraction(
        {
            "architectures": [
                {
                    "candidate_key": "standard",
                    "title": "Standard",
                    "summary": "Campus Wi-Fi",
                    "components": [{"name": "WLAN", "purpose": "Coverage"}],
                    "risks": [],
                    "assumptions": [],
                },
            ],
        },
    )
    enriched = enrich_architecture_risks_assumptions(
        base,
        domain_codes=["wifi"],
        rkm_payload={
            "functional_requirements": [
                {
                    "id": "REQ-WIFI-1",
                    "title": "WiFi coverage",
                    "description": "Reliable campus wireless",
                },
            ],
        },
        requirements=[
            {
                "id": "REQ-WIFI-1",
                "title": "WiFi coverage",
                "description": "Reliable campus wireless",
            },
        ],
    )
    risk_text = " ".join(
        item.description.lower() for item in enriched.architectures[0].risks
    )
    assert "rf/site survey" in risk_text or "ap density" in risk_text


def test_enrich_skips_domain_risk_when_signal_present():
    base = validate_architecture_ai_extraction(
        {
            "architectures": [
                {
                    "candidate_key": "standard",
                    "title": "Standard",
                    "summary": "Campus",
                    "components": [{"name": "Access", "purpose": "x"}],
                    "risks": [],
                    "assumptions": [],
                },
            ],
        },
    )
    enriched = enrich_architecture_risks_assumptions(
        base,
        domain_codes=["wifi"],
        rkm_payload={
            "functional_requirements": [
                {
                    "id": "REQ-1",
                    "title": "Survey done",
                    "description": "Floor plan and heatmap already available",
                },
            ],
        },
        requirements=[
            {
                "id": "REQ-1",
                "title": "Survey done",
                "description": "Floor plan and heatmap already available",
            },
        ],
    )
    risk_text = " ".join(item.description.lower() for item in enriched.architectures[0].risks)
    assert "incomplete rf/site survey" not in risk_text
