"""Sprint 3.1 Task 3 — domain / AI Pydantic schemas."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.domain import (
    DomainAnalysisOut,
    DomainAIExtraction,
    TraceabilityOut,
    validate_domain_ai_extraction,
)


def test_valid_ai_extraction_with_requirement_source():
    payload = validate_domain_ai_extraction(
        {
            "summary": "Remote access needs identity and edge security",
            "domains": [
                {
                    "domain_id": "identity",
                    "reason": "RKM requires authenticated remote access",
                    "supporting_requirements": ["REQ-1"],
                    "confidence": 80,
                    "mandatory_or_optional": "mandatory",
                    "selection_source": "requirement",
                    "dependencies": [
                        {
                            "depends_on_domain_code": "cybersecurity",
                            "dependency_kind": "recommended",
                            "reason": "Identity controls usually pair with security policy",
                        },
                    ],
                },
                {
                    "code": "ztna_vpn",
                    "reason": "Dependency for secure remote access path",
                    "selection_source": "dependency",
                    "confidence": 0.55,
                    "supporting_requirements": [],
                    "dependencies": [
                        {
                            "depends_on_domain_code": "identity",
                            "dependency_kind": "required",
                            "reason": "ZTNA needs identity",
                        },
                    ],
                },
            ],
            "open_questions": [
                {
                    "question": "Is MFA mandatory for all remote users?",
                    "affects_selection": True,
                    "related_requirement_ids": ["REQ-1"],
                    "domain_code": "identity",
                },
            ],
        },
    )
    assert isinstance(payload, DomainAIExtraction)
    assert payload.domains[0].domain_code == "identity"
    assert payload.domains[0].confidence == 0.8
    assert payload.domains[1].domain_code == "ztna_vpn"
    assert payload.domains[1].selection_source == "dependency"
    assert payload.open_questions[0].domain_code == "identity"


def test_alias_wifi_resolves_to_catalog_code():
    payload = validate_domain_ai_extraction(
        {
            "domains": [
                {
                    "domain_code": "Wi-Fi",
                    "reason": "Coverage requirements in RKM",
                    "supporting_requirements": ["REQ-WIFI-1"],
                    "confidence": 0.7,
                },
            ],
        },
    )
    assert payload.domains[0].domain_code == "wifi"


def test_rejects_unknown_domain_code():
    with pytest.raises(ValidationError):
        validate_domain_ai_extraction(
            {
                "domains": [
                    {
                        "domain_code": "cisco-magic-box",
                        "reason": "Popular product",
                        "supporting_requirements": ["REQ-1"],
                        "confidence": 0.9,
                    },
                ],
            },
        )


def test_rejects_missing_reason():
    with pytest.raises(ValidationError):
        validate_domain_ai_extraction(
            {
                "domains": [
                    {
                        "domain_code": "cloud",
                        "reason": "  ",
                        "supporting_requirements": ["REQ-1"],
                        "confidence": 0.5,
                    },
                ],
            },
        )


def test_rejects_requirement_source_without_supporting_requirements():
    with pytest.raises(ValidationError):
        validate_domain_ai_extraction(
            {
                "domains": [
                    {
                        "domain_code": "cloud",
                        "reason": "Seems useful",
                        "selection_source": "requirement",
                        "supporting_requirements": [],
                        "confidence": 0.5,
                    },
                ],
            },
        )


def test_rejects_invalid_confidence():
    with pytest.raises(ValidationError):
        validate_domain_ai_extraction(
            {
                "domains": [
                    {
                        "domain_code": "storage",
                        "reason": "Capacity mentioned",
                        "supporting_requirements": ["REQ-S"],
                        "confidence": 150,
                    },
                ],
            },
        )


def test_rejects_non_object_payload():
    with pytest.raises(ValueError, match="must be an object"):
        validate_domain_ai_extraction(["not", "an", "object"])


def test_traceability_status_normalization():
    row = TraceabilityOut(
        id=uuid4(),
        project_id=uuid4(),
        analysis_id=uuid4(),
        requirement_id="REQ-1",
        status="Partially Covered",
    )
    assert row.status == "partially_covered"


def test_domain_analysis_out_shape():
    now = datetime.now(timezone.utc)
    out = DomainAnalysisOut(
        id=uuid4(),
        project_id=uuid4(),
        rkm_id=uuid4(),
        rkm_version_label="1.2.0",
        status="draft",
        version_label="1.0.0",
        summary="Demo",
        knowledge_pack_version="1.0.0",
        domains=[],
        open_questions=[],
        traceability=[],
        created_at=now,
        updated_at=now,
    )
    dumped = out.model_dump(mode="json")
    assert dumped["version_label"] == "1.0.0"
    assert dumped["knowledge_pack_version"] == "1.0.0"
    assert dumped["domains"] == []
