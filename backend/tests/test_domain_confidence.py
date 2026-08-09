"""Sprint 3.1 Task 10 — domain confidence scoring."""

from __future__ import annotations

from app.schemas.domain import DomainAIExtraction, DomainOpenQuestionAI, SolutionDomainAI
from app.services.domain_confidence import (
    apply_confidence_to_extraction,
    clamp_confidence,
    score_domain_confidence,
)


def test_clamp_confidence_accepts_percent_and_unit_interval():
    assert clamp_confidence(80) == 0.8
    assert clamp_confidence(0.55) == 0.55
    assert clamp_confidence(150) == 1.0
    assert clamp_confidence(-1) == 0.0
    assert clamp_confidence("nope") == 0.0


def test_thin_evidence_and_open_questions_reduce_confidence():
    strong = SolutionDomainAI(
        domain_code="wifi",
        name="Wi-Fi",
        reason="Coverage",
        supporting_requirements=["REQ-1", "REQ-2"],
        confidence=0.9,
        selection_source="requirement",
    )
    thin = SolutionDomainAI(
        domain_code="wifi",
        name="Wi-Fi",
        reason="Coverage",
        supporting_requirements=["REQ-1"],
        confidence=0.9,
        selection_source="requirement",
        open_questions=[
            DomainOpenQuestionAI(
                question="Need survey?",
                affects_selection=True,
                related_requirement_ids=["REQ-1"],
                domain_code="wifi",
            ),
        ],
    )
    strong_score = score_domain_confidence(strong)
    thin_score = score_domain_confidence(thin)
    assert strong_score == 0.9
    assert thin_score < strong_score
    assert 0.05 <= thin_score <= 1.0


def test_dependency_source_penalty_and_analysis_question():
    domain = SolutionDomainAI(
        domain_code="identity",
        name="Identity",
        reason="Dependency",
        supporting_requirements=["REQ-1"],
        confidence=0.7,
        selection_source="dependency",
        dependencies=[
            {
                "depends_on_domain_code": "wifi",
                "dependency_kind": "required",
                "reason": "WLAN auth",
            },
        ],
    )
    score = score_domain_confidence(
        domain,
        analysis_open_questions=[
            DomainOpenQuestionAI(
                question="Should identity be included?",
                affects_selection=True,
                domain_code="identity",
            ),
        ],
    )
    assert score < 0.7
    assert score >= 0.05


def test_apply_confidence_to_extraction_updates_domains():
    extraction = DomainAIExtraction(
        summary="demo",
        domains=[
            SolutionDomainAI(
                domain_code="cloud",
                name="Cloud",
                reason="Hosting",
                supporting_requirements=["REQ-1"],
                confidence=85,
                selection_source="requirement",
            ),
        ],
        open_questions=[
            DomainOpenQuestionAI(
                question="Cloud residency unclear for cloud",
                affects_selection=True,
                domain_code="cloud",
            ),
        ],
    )
    updated = apply_confidence_to_extraction(extraction)
    assert updated.domains[0].confidence <= 0.85
    assert updated.domains[0].confidence < 0.85 or updated.domains[0].confidence == clamp_confidence(
        0.85 - 0.05 - 0.05,
    )
