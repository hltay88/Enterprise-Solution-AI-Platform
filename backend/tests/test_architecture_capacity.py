"""Sprint 3.2 Task 7 — capacity notes helper (no fabricate)."""

from __future__ import annotations

from app.schemas.architecture_option import validate_architecture_ai_extraction
from app.services.architecture_capacity import (
    enrich_architecture_capacity,
    expected_capacity_labels_for_domains,
    preprocess_capacity_in_extraction,
    sanitize_capacity_note_dict,
)


def test_sanitize_strips_fabricated_result():
    cleaned = sanitize_capacity_note_dict(
        {
            "label": "AP count",
            "result": "42",
            "confidence": 0.9,
        },
    )
    assert cleaned["result"] is None
    assert cleaned["open_question"]
    assert "42" in cleaned["open_question"]
    assert cleaned["confidence"] <= 0.25


def test_sanitize_keeps_evidenced_result():
    cleaned = sanitize_capacity_note_dict(
        {
            "label": "AP count",
            "input_value": "3 floors, 800 clients",
            "unit": "APs",
            "method": "density heuristic",
            "assumption": "Open office ~1 device/person",
            "result": "Preliminary 24 APs — survey required",
            "confidence": 0.4,
        },
    )
    assert cleaned["result"] is not None
    assert "24" in cleaned["result"]


def test_preprocess_makes_fabricated_payload_valid():
    raw = {
        "architectures": [
            {
                "candidate_key": "standard",
                "title": "Standard",
                "summary": "Campus Wi-Fi",
                "pattern_codes": ["wireless_enterprise"],
                "components": [{"name": "WLAN", "purpose": "Coverage"}],
                "capacity_notes": [
                    {"label": "AP count", "result": "99", "confidence": 0.95},
                ],
            },
        ],
    }
    cleaned = preprocess_capacity_in_extraction(raw)
    payload = validate_architecture_ai_extraction(cleaned)
    note = payload.architectures[0].capacity_notes[0]
    assert note.result is None
    assert note.open_question


def test_enrich_adds_open_questions_for_wifi_without_evidence():
    base = validate_architecture_ai_extraction(
        {
            "architectures": [
                {
                    "candidate_key": "standard",
                    "title": "Standard",
                    "summary": "Campus",
                    "pattern_codes": ["wireless_enterprise"],
                    "components": [{"name": "Access", "purpose": "Underlay"}],
                    "capacity_notes": [],
                },
            ],
        },
    )
    enriched = enrich_architecture_capacity(
        base,
        domain_codes=["wifi"],
        rkm_text="Need reliable campus wireless coverage",
        requirements=[
            {
                "id": "REQ-WIFI-1",
                "title": "WiFi coverage",
                "description": "Three floors",
            },
        ],
    )
    labels = {note.label for note in enriched.architectures[0].capacity_notes}
    assert "AP count" in labels
    assert all(
        note.result is None for note in enriched.architectures[0].capacity_notes
    )
    assert all(
        note.open_question for note in enriched.architectures[0].capacity_notes
    )


def test_enrich_skips_when_signal_already_in_rkm():
    base = validate_architecture_ai_extraction(
        {
            "architectures": [
                {
                    "candidate_key": "standard",
                    "title": "Standard",
                    "summary": "Campus",
                    "components": [{"name": "Access", "purpose": "Underlay"}],
                    "capacity_notes": [],
                },
            ],
        },
    )
    enriched = enrich_architecture_capacity(
        base,
        domain_codes=["wifi"],
        rkm_text="Floor plan available; AP count survey scheduled; client density known",
    )
    labels = {note.label for note in enriched.architectures[0].capacity_notes}
    # AP count signal present → not auto-added; concurrent may still appear.
    assert "AP count" not in labels


def test_expected_capacity_labels_for_domains():
    labels = expected_capacity_labels_for_domains(["wifi", "storage"])
    assert "AP count" in labels
    assert "Storage capacity" in labels
