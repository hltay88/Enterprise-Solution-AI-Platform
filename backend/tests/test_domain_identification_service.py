"""Sprint 3.1 Task 7 — DomainIdentificationService orchestration."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import ValidationAppError
from app.services.domain_identification_service import (
    PROMPT_VERSION,
    DomainIdentificationService,
)


def _service() -> DomainIdentificationService:
    return DomainIdentificationService.__new__(DomainIdentificationService)


def test_analyze_requires_published_rkm():
    service = _service()
    service.projects = SimpleNamespace(
        get_for_user=lambda project_id, user_id: SimpleNamespace(id=project_id),
    )
    service.rkms = SimpleNamespace(get_published=lambda _project_id: None)
    service.domains = MagicMock()

    with pytest.raises(ValidationAppError, match="Publish a Requirement Knowledge Model"):
        asyncio.run(service.analyze(uuid4(), uuid4()))
    service.domains.create_analysis_tree.assert_not_called()


def test_analyze_rejects_empty_published_rkm_requirements():
    service = _service()
    service.projects = SimpleNamespace(
        get_for_user=lambda project_id, user_id: SimpleNamespace(id=project_id),
    )
    service.rkms = SimpleNamespace(
        get_published=lambda _project_id: SimpleNamespace(
            id=uuid4(),
            version_label="1.0.0",
            payload_json={"functional_requirements": []},
        ),
    )
    service.domains = MagicMock()

    with pytest.raises(ValidationAppError, match="no requirements"):
        asyncio.run(service.analyze(uuid4(), uuid4()))
    service.domains.create_analysis_tree.assert_not_called()


def test_analyze_persists_and_audits_on_success():
    service = _service()
    service.db = MagicMock()
    project_id = uuid4()
    user_id = uuid4()
    rkm_id = uuid4()
    analysis_id = uuid4()

    service.projects = SimpleNamespace(
        get_for_user=lambda pid, uid: SimpleNamespace(id=pid),
    )
    service.rkms = SimpleNamespace(
        get_published=lambda _pid: SimpleNamespace(
            id=rkm_id,
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
        ),
    )
    created = SimpleNamespace(
        id=analysis_id,
        project_id=project_id,
        rkm_id=rkm_id,
        rkm_version_label="2.0.0",
        status="draft",
        version_label="1.0.0",
        summary="Domains",
        model="local-domain-heuristics",
        prompt_version=PROMPT_VERSION,
        knowledge_pack_version="1.0.0",
        payload_json={"summary": "Domains", "reasoning_summary": "ok"},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    service.domains = MagicMock()
    service.domains.next_version.return_value = (1, 0, 0)
    service.domains.create_analysis_tree.return_value = created
    service.domains.list_domains.return_value = []
    service.domains.list_requirement_links.return_value = []
    service.domains.list_dependencies.return_value = []
    service.domains.list_open_questions.return_value = []
    service.domains.list_traceability.return_value = []

    extraction = {
        "summary": "Wi-Fi domain",
        "domains": [
            {
                "domain_code": "wifi",
                "name": "Wi-Fi",
                "reason": "Coverage requirements",
                "supporting_requirements": ["REQ-WIFI-1"],
                "confidence": 0.8,
                "mandatory_or_optional": "mandatory",
                "selection_source": "requirement",
                "dependencies": [],
                "open_questions": [],
            },
        ],
        "open_questions": [],
        "reasoning_summary": "local",
        "provider": "local",
        "model": "local-domain-heuristics",
    }

    provider = SimpleNamespace(
        identify_solution_domains=AsyncMock(return_value=extraction),
    )

    with (
        patch(
            "app.services.domain_identification_service.get_ai_provider",
            return_value=provider,
        ),
        patch(
            "app.services.domain_identification_service.build_domain_pack_context",
            return_value="pack",
        ),
        patch(
            "app.services.domain_identification_service.pack_version",
            return_value="1.0.0",
        ),
        patch(
            "app.services.domain_identification_service.AuditService",
        ) as audit_cls,
    ):
        audit = audit_cls.return_value
        result = asyncio.run(service.analyze(project_id, user_id))

    assert result.id == analysis_id
    assert result.version_label == "1.0.0"
    assert result.knowledge_pack_version == "1.0.0"
    service.domains.create_analysis_tree.assert_called_once()
    kwargs = service.domains.create_analysis_tree.call_args.kwargs
    assert kwargs["rkm_id"] == rkm_id
    assert kwargs["prompt_version"] == PROMPT_VERSION
    assert kwargs["knowledge_pack_version"] == "1.0.0"
    assert kwargs["domains"][0]["domain_code"] == "wifi"
    assert kwargs["traceability"]
    assert any(
        row["requirement_id"] == "REQ-WIFI-1" and row["status"] == "covered"
        for row in kwargs["traceability"]
    )
    audit.record.assert_called_once()
    assert audit.record.call_args.kwargs["action"] == "domain.analyze"
    assert "traceability_count" in audit.record.call_args.kwargs["metadata"]


def test_analyze_does_not_persist_invalid_ai_payload():
    service = _service()
    service.projects = SimpleNamespace(
        get_for_user=lambda project_id, user_id: SimpleNamespace(id=project_id),
    )
    service.rkms = SimpleNamespace(
        get_published=lambda _project_id: SimpleNamespace(
            id=uuid4(),
            version_label="1.0.0",
            payload_json={
                "functional_requirements": [
                    {"id": "REQ-1", "title": "X", "description": "Y"},
                ],
            },
        ),
    )
    service.domains = MagicMock()
    provider = SimpleNamespace(
        identify_solution_domains=AsyncMock(
            return_value={
                "domains": [
                    {
                        "domain_code": "not-a-catalog-domain",
                        "reason": "bad",
                        "supporting_requirements": ["REQ-1"],
                        "confidence": 0.5,
                    },
                ],
            },
        ),
    )

    with (
        patch(
            "app.services.domain_identification_service.get_ai_provider",
            return_value=provider,
        ),
        patch(
            "app.services.domain_identification_service.build_domain_pack_context",
            return_value="pack",
        ),
        patch(
            "app.services.domain_identification_service.pack_version",
            return_value="1.0.0",
        ),
    ):
        with pytest.raises(ValidationAppError, match="failed validation"):
            asyncio.run(service.analyze(uuid4(), uuid4()))

    service.domains.create_analysis_tree.assert_not_called()
