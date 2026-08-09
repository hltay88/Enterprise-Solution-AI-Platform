"""Sprint 3.1 Task 6 — local domain identification + schema normalize."""

from __future__ import annotations

import asyncio

import pytest

from app.ai.common import normalize_domain_identification
from app.ai.local_provider import LocalAIProvider
from app.core.exceptions import AppError
from app.schemas.domain import validate_domain_ai_extraction
from app.services.phase3_knowledge_packs import build_domain_pack_context


def test_local_identify_domains_from_wifi_rkm():
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
            },
        ],
        "non_functional_requirements": [],
        "constraints": [],
        "risks": [],
        "assumptions": [],
    }
    pack = build_domain_pack_context(
        "Enterprise WiFi 6 coverage and roaming",
    )
    result = asyncio.run(
        provider.identify_solution_domains(rkm, knowledge_pack_context=pack),
    )
    assert result["provider"] == "local"
    assert result["domains"]
    codes = {item["domain_code"] for item in result["domains"]}
    assert "wifi" in codes
    validated = validate_domain_ai_extraction(result)
    assert validated.domains
    assert any(domain.domain_code == "wifi" for domain in validated.domains)


def test_local_identify_domains_remote_access_example():
    provider = LocalAIProvider()
    rkm = {
        "functional_requirements": [
            {
                "id": "REQ-RA-1",
                "title": "Secure remote access",
                "description": "Employees need ZTNA or VPN with identity MFA",
            },
        ],
    }
    result = asyncio.run(provider.identify_solution_domains(rkm))
    codes = {item["domain_code"] for item in result["domains"]}
    assert "identity" in codes or "ztna_vpn" in codes
    validate_domain_ai_extraction(result)


def test_normalize_domain_identification_rejects_unknown_code():
    with pytest.raises(AppError) as exc:
        normalize_domain_identification(
            {
                "domains": [
                    {
                        "domain_code": "not-a-real-domain",
                        "reason": "x",
                        "supporting_requirements": ["R1"],
                        "confidence": 0.5,
                    },
                ],
            },
        )
    assert exc.value.code == "INTERNAL_ERROR"


def test_normalize_domain_identification_accepts_alias():
    payload = normalize_domain_identification(
        {
            "summary": "ok",
            "domains": [
                {
                    "domain_code": "Wi-Fi",
                    "reason": "Coverage requirements",
                    "supporting_requirements": ["REQ-1"],
                    "confidence": 70,
                },
            ],
        },
    )
    assert payload["domains"][0]["domain_code"] == "wifi"
    assert payload["domains"][0]["confidence"] == 0.7
