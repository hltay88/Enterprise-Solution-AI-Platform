"""Sprint 3.1 Task 8 — requirement→domain traceability builder."""

from __future__ import annotations

from app.schemas.domain import SolutionDomainAI
from app.services.domain_traceability import (
    build_requirement_domain_traceability,
    count_uncovered_critical,
    extract_rkm_requirements,
)


def test_extract_rkm_requirements_flattens_sections():
    reqs = extract_rkm_requirements(
        {
            "functional_requirements": [
                {
                    "id": "REQ-1",
                    "title": "WiFi",
                    "description": "Coverage",
                    "priority": "critical",
                },
            ],
            "risks": [
                {"title": "Survey delay", "description": "Plans late", "priority": "high"},
            ],
        },
    )
    assert len(reqs) == 2
    assert reqs[0]["id"] == "REQ-1"
    assert reqs[0]["priority"] == "critical"
    assert reqs[1]["id"] == "Survey delay"


def test_build_traceability_covered_optional_partial_and_not_covered():
    requirements = [
        {"id": "REQ-WIFI", "title": "WiFi", "priority": "critical"},
        {"id": "REQ-OPT", "title": "Guest portal", "priority": "low"},
        {"id": "REQ-GAP", "title": "DR site", "priority": "high"},
    ]
    domains = [
        SolutionDomainAI(
            domain_code="wifi",
            name="Wi-Fi",
            reason="Coverage",
            supporting_requirements=["REQ-WIFI"],
            confidence=0.8,
            mandatory_or_optional="mandatory",
            selection_source="requirement",
        ),
        SolutionDomainAI(
            domain_code="identity",
            name="Identity",
            reason="Dependency for WLAN auth",
            supporting_requirements=["REQ-WIFI"],
            confidence=0.5,
            mandatory_or_optional="mandatory",
            selection_source="dependency",
            dependencies=[
                {
                    "depends_on_domain_code": "wifi",
                    "dependency_kind": "required",
                    "reason": "Auth for WLAN",
                },
            ],
        ),
        SolutionDomainAI(
            domain_code="digital_signage",
            name="Digital Signage",
            reason="Optional guest wayfinding",
            supporting_requirements=["REQ-OPT"],
            confidence=0.4,
            mandatory_or_optional="optional",
            selection_source="optional_alternative",
        ),
    ]

    rows = build_requirement_domain_traceability(requirements, domains)
    by_key = {(row["requirement_id"], row.get("domain_code")): row["status"] for row in rows}

    assert by_key[("REQ-WIFI", "wifi")] == "covered"
    assert by_key[("REQ-WIFI", "identity")] == "partially_covered"
    assert by_key[("REQ-OPT", "digital_signage")] == "optional"
    assert by_key[("REQ-GAP", None)] == "not_covered"
    assert count_uncovered_critical(rows, requirements) == 1


def test_dependency_domain_with_supporting_requirements_is_partial():
    rows = build_requirement_domain_traceability(
        [{"id": "REQ-1", "priority": "medium"}],
        [
            {
                "domain_code": "ztna_vpn",
                "reason": "Remote access path",
                "supporting_requirements": ["REQ-1"],
                "confidence": 0.55,
                "selection_source": "dependency",
                "dependencies": [
                    {
                        "depends_on_domain_code": "identity",
                        "dependency_kind": "required",
                        "reason": "Needs IdP",
                    },
                ],
            },
        ],
    )
    assert len(rows) == 1
    assert rows[0]["status"] == "partially_covered"
    assert rows[0]["domain_code"] == "ztna_vpn"
