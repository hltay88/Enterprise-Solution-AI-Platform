"""Sprint 3.1 Task 9 — dependency validation and open-question enrichment."""

from __future__ import annotations

from app.schemas.domain import DomainAIExtraction, SolutionDomainAI, validate_domain_ai_extraction
from app.services.domain_enrichment import (
    enrich_domains_and_questions,
    preprocess_domain_extraction,
)
from app.services.domain_traceability import build_requirement_domain_traceability


def test_preprocess_drops_unknown_dependency_and_adds_question():
    payload = preprocess_domain_extraction(
        {
            "summary": "demo",
            "domains": [
                {
                    "domain_code": "wifi",
                    "name": "Wi-Fi",
                    "reason": "Coverage",
                    "supporting_requirements": ["REQ-1"],
                    "confidence": 0.7,
                    "dependencies": [
                        {
                            "depends_on_domain_code": "not-a-real-domain",
                            "dependency_kind": "required",
                            "reason": "bad",
                        },
                        {
                            "depends_on_domain_code": "identity",
                            "dependency_kind": "recommended",
                            "reason": "Auth",
                        },
                    ],
                },
            ],
        },
    )
    deps = payload["domains"][0]["dependencies"]
    assert len(deps) == 1
    assert deps[0]["depends_on_domain_code"] == "identity"
    assert any(
        "not a catalog code" in str(q.get("question", "")).lower()
        for q in payload["domains"][0]["open_questions"]
    )
    validate_domain_ai_extraction(payload)


def test_missing_dep_domain_and_uncovered_critical_questions():
    extraction = validate_domain_ai_extraction(
        {
            "summary": "demo",
            "domains": [
                {
                    "domain_code": "wifi",
                    "name": "Wi-Fi",
                    "reason": "Coverage",
                    "supporting_requirements": ["REQ-WIFI"],
                    "confidence": 0.8,
                    "dependencies": [
                        {
                            "depends_on_domain_code": "identity",
                            "dependency_kind": "required",
                            "reason": "802.1X",
                        },
                    ],
                },
            ],
        },
    )
    requirements = [
        {"id": "REQ-WIFI", "title": "WiFi", "priority": "medium", "description": "coverage"},
        {"id": "REQ-DR", "title": "DR site", "priority": "critical", "description": "failover"},
    ]
    trace = build_requirement_domain_traceability(requirements, list(extraction.domains))
    refined = enrich_domains_and_questions(
        extraction,
        requirements=requirements,
        traceability=trace,
        rkm_text="wifi coverage",
    )
    questions = [q.question.lower() for q in refined.open_questions]
    questions += [q.question.lower() for d in refined.domains for q in d.open_questions]
    assert any("identity" in q and "not selected" in q for q in questions)
    assert any("critical requirement" in q and "dr site" in q for q in questions)
    assert any("selection inputs" in q for q in questions)


def test_dependency_cycle_raises_open_question():
    extraction = DomainAIExtraction(
        summary="cycle",
        domains=[
            SolutionDomainAI(
                domain_code="identity",
                name="Identity",
                reason="Auth",
                supporting_requirements=["REQ-1"],
                confidence=0.6,
                dependencies=[
                    {
                        "depends_on_domain_code": "cybersecurity",
                        "dependency_kind": "required",
                        "reason": "policy",
                    },
                ],
            ),
            SolutionDomainAI(
                domain_code="cybersecurity",
                name="Cybersecurity",
                reason="Security",
                supporting_requirements=["REQ-1"],
                confidence=0.6,
                dependencies=[
                    {
                        "depends_on_domain_code": "identity",
                        "dependency_kind": "required",
                        "reason": "iam",
                    },
                ],
            ),
        ],
    )
    requirements = [{"id": "REQ-1", "title": "Secure access", "priority": "high"}]
    trace = build_requirement_domain_traceability(requirements, list(extraction.domains))
    refined = enrich_domains_and_questions(
        extraction,
        requirements=requirements,
        traceability=trace,
        rkm_text="mfa directory sso security",
    )
    assert any("circular domain dependency" in q.question.lower() for q in refined.open_questions)
