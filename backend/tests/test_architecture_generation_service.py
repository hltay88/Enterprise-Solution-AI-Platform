"""Sprint 3.2 Task 6 — ArchitectureGenerationService orchestration."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError, ValidationAppError
from app.services.architecture_generation_service import (
    PROMPT_VERSION,
    ArchitectureGenerationService,
)
from app.services.architecture_scoring import compute_overall_score


def _service() -> ArchitectureGenerationService:
    return ArchitectureGenerationService.__new__(ArchitectureGenerationService)


def _published_rkm():
    return SimpleNamespace(
        id=uuid4(),
        version_label="2.0.0",
        payload_json={
            "functional_requirements": [
                {
                    "id": "REQ-WIFI-1",
                    "title": "WiFi 6 coverage",
                    "description": "Campus wireless",
                },
            ],
        },
    )


def test_generate_requires_published_rkm():
    service = _service()
    service.projects = SimpleNamespace(
        get_for_user=lambda project_id, user_id: SimpleNamespace(id=project_id),
    )
    service.rkms = SimpleNamespace(get_published=lambda _project_id: None)
    service.domains = MagicMock()
    service.architectures = MagicMock()

    with pytest.raises(ValidationAppError, match="Publish a Requirement Knowledge Model"):
        asyncio.run(service.generate(uuid4(), uuid4()))
    service.architectures.create_generation_tree.assert_not_called()


def test_generate_hard_fails_without_domain_analysis():
    service = _service()
    service.projects = SimpleNamespace(
        get_for_user=lambda project_id, user_id: SimpleNamespace(id=project_id),
    )
    service.rkms = SimpleNamespace(get_published=lambda _pid: _published_rkm())
    service.domains = MagicMock()
    service.domains.get_latest.return_value = None
    service.architectures = MagicMock()

    with pytest.raises(ValidationAppError, match="domain identification"):
        asyncio.run(service.generate(uuid4(), uuid4()))
    service.architectures.create_generation_tree.assert_not_called()


def test_generate_persists_and_audits_on_success():
    service = _service()
    service.db = MagicMock()
    project_id = uuid4()
    user_id = uuid4()
    rkm = _published_rkm()
    domain_analysis_id = uuid4()
    generation_id = uuid4()
    option_id = uuid4()

    service.projects = SimpleNamespace(
        get_for_user=lambda pid, uid: SimpleNamespace(id=pid),
    )
    service.rkms = SimpleNamespace(get_published=lambda _pid: rkm)
    service.domains = MagicMock()
    service.domains.get_latest.return_value = SimpleNamespace(
        id=domain_analysis_id,
        version_label="1.0.0",
        rkm_version_label="2.0.0",
        summary="Wi-Fi + campus",
    )
    domain_row_id = uuid4()
    service.domains.list_domains.return_value = [
        SimpleNamespace(
            id=domain_row_id,
            domain_code="wifi",
            name="Wi-Fi",
            confidence=0.8,
            selection_source="requirement",
            mandatory_or_optional="mandatory",
            reason="Coverage",
        ),
    ]
    service.domains.list_requirement_links.return_value = [
        SimpleNamespace(domain_id=domain_row_id, requirement_id="REQ-WIFI-1"),
    ]

    created = SimpleNamespace(
        id=option_id,
        project_id=project_id,
        rkm_id=rkm.id,
        rkm_version_label="2.0.0",
        domain_analysis_id=domain_analysis_id,
        generation_id=generation_id,
        candidate_key="standard",
        title="Standard wifi architecture",
        summary="Vendor-neutral",
        reasoning_summary="local",
        status="draft",
        confidence=0.72,
        overall_score=3.5,
        pattern_codes=["wireless_enterprise", "two_tier_campus"],
        version_label="1.0.0",
        model="local-architecture-candidates",
        prompt_version=PROMPT_VERSION,
        knowledge_pack_version="1.1.0",
        payload_json={
            "summary": "Vendor-neutral",
            "reasoning_summary": "local",
            "high_level_architecture": ["Layered"],
        },
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    component_id = uuid4()
    service.architectures = MagicMock()
    service.architectures.next_version.return_value = (1, 0, 0)
    service.architectures.create_generation_tree.return_value = [created]
    service.architectures.list_components.return_value = [
        SimpleNamespace(
            id=component_id,
            name="Access",
            purpose="Underlay",
            component_kind="logical",
            sort_order=0,
            maps_to_requirements=["REQ-WIFI-1"],
        ),
    ]
    service.architectures.list_relationships.return_value = []
    service.architectures.list_decisions.return_value = []
    service.architectures.list_assumptions.return_value = []
    service.architectures.list_risks.return_value = []
    service.architectures.list_scores.return_value = []
    service.architectures.list_capacity_notes.return_value = []
    service.architectures.add_traceability_rows.return_value = 1

    extraction = {
        "summary": "Candidates",
        "architectures": [
            {
                "candidate_key": "standard",
                "title": "Standard wifi architecture",
                "summary": "Vendor-neutral",
                "pattern_codes": ["wireless_enterprise", "two_tier_campus"],
                "confidence": 0.72,
                "components": [
                    {
                        "name": "Access",
                        "purpose": "Underlay",
                        "maps_to_requirements": ["REQ-WIFI-1"],
                        "temp_id": "c1",
                    },
                ],
                "scores": [
                    {
                        "dimension": "requirement_coverage",
                        "weight": 0.3,
                        "score": 4,
                        "explanation": "Covers Wi-Fi",
                    },
                ],
                "capacity_notes": [
                    {
                        "label": "AP count",
                        "open_question": "Need floor plans",
                        "confidence": 0.2,
                    },
                ],
            },
        ],
        "reasoning_summary": "local",
        "provider": "local",
        "model": "local-architecture-candidates",
    }
    provider = SimpleNamespace(
        recommend_architectures=AsyncMock(return_value=extraction),
    )

    with (
        patch(
            "app.services.architecture_generation_service.get_ai_provider",
            return_value=provider,
        ),
        patch(
            "app.services.architecture_generation_service.build_pattern_pack_context",
            return_value="pattern pack",
        ),
        patch(
            "app.services.architecture_generation_service.catalog_version",
            return_value="1.1.0",
        ),
        patch(
            "app.services.architecture_generation_service.AuditService",
        ) as audit_cls,
    ):
        audit = audit_cls.return_value
        result = asyncio.run(service.generate(project_id, user_id))

    assert result.generation_id == generation_id
    assert result.version_label == "1.0.0"
    assert len(result.architectures) == 1
    service.architectures.create_generation_tree.assert_called_once()
    kwargs = service.architectures.create_generation_tree.call_args.kwargs
    assert kwargs["rkm_id"] == rkm.id
    assert kwargs["domain_analysis_id"] == domain_analysis_id
    assert kwargs["prompt_version"] == PROMPT_VERSION
    assert kwargs["knowledge_pack_version"] == "1.1.0"
    assert kwargs["architectures"][0]["candidate_key"] == "standard"
    assert kwargs["architectures"][0]["overall_score"] is not None
    assert 0 <= kwargs["architectures"][0]["overall_score"] <= 5
    assert len(kwargs["architectures"][0]["scores"]) == 9
    assert "scoring" in kwargs["architectures"][0]["payload_json"]
    service.architectures.add_traceability_rows.assert_called_once()
    trace_kwargs = service.architectures.add_traceability_rows.call_args.kwargs
    assert trace_kwargs["analysis_id"] == domain_analysis_id
    assert trace_kwargs["rows"]
    assert any(
        row["requirement_id"] == "REQ-WIFI-1" and row.get("component_id") == component_id
        for row in trace_kwargs["rows"]
    )
    provider.recommend_architectures.assert_awaited_once()
    call_kwargs = provider.recommend_architectures.await_args.kwargs
    assert "wifi" in call_kwargs["domain_context"]
    assert call_kwargs["pattern_context"] == "pattern pack"
    audit.record.assert_called_once()
    assert audit.record.call_args.kwargs["action"] == "architectures.generate"
    assert audit.record.call_args.kwargs["metadata"]["candidate_count"] == 1
    assert "traceability_count" in audit.record.call_args.kwargs["metadata"]


def test_generate_does_not_persist_invalid_ai_payload():
    service = _service()
    service.projects = SimpleNamespace(
        get_for_user=lambda project_id, user_id: SimpleNamespace(id=project_id),
    )
    service.rkms = SimpleNamespace(get_published=lambda _pid: _published_rkm())
    service.domains = MagicMock()
    service.domains.get_latest.return_value = SimpleNamespace(
        id=uuid4(),
        version_label="1.0.0",
        rkm_version_label="2.0.0",
        summary="x",
    )
    service.domains.list_domains.return_value = [
        SimpleNamespace(
            domain_code="wifi",
            name="Wi-Fi",
            confidence=0.8,
            selection_source="requirement",
            mandatory_or_optional="mandatory",
            reason="x",
        ),
    ]
    service.architectures = MagicMock()
    provider = SimpleNamespace(
        recommend_architectures=AsyncMock(
            return_value={
                "architectures": [
                    {
                        "candidate_key": "standard",
                        "title": "Bad",
                        "summary": "Missing components",
                        "pattern_codes": ["not-a-real-pattern"],
                        "components": [{"name": "X", "purpose": "y"}],
                    },
                ],
            },
        ),
    )

    with (
        patch(
            "app.services.architecture_generation_service.get_ai_provider",
            return_value=provider,
        ),
        patch(
            "app.services.architecture_generation_service.build_pattern_pack_context",
            return_value="pack",
        ),
        patch(
            "app.services.architecture_generation_service.catalog_version",
            return_value="1.1.0",
        ),
    ):
        with pytest.raises(ValidationAppError, match="failed validation"):
            asyncio.run(service.generate(uuid4(), uuid4()))

    service.architectures.create_generation_tree.assert_not_called()


def test_get_latest_not_found():
    service = _service()
    service.projects = SimpleNamespace(
        get_for_user=lambda project_id, user_id: SimpleNamespace(id=project_id),
    )
    service.architectures = MagicMock()
    service.architectures.get_latest.return_value = None
    with pytest.raises(NotFoundError, match="No architecture options"):
        service.get_latest(uuid4(), uuid4())


def test_weighted_overall_score():
    assert compute_overall_score([]) is None
    assert (
        compute_overall_score(
            [
                {"weight": 0.3, "score": 4},
                {"weight": 0.7, "score": 2},
            ],
        )
        == 2.6
    )
