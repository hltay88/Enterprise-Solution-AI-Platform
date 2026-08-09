"""Sprint 3.1 Task 4 — domain repository helpers and tree create."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.domain_analysis import (
    DomainAnalysis,
    DomainDependency,
    DomainOpenQuestion,
    DomainRequirementLink,
    RequirementTraceability,
    SolutionDomain,
)
from app.repositories.domain_repository import (
    DomainRepository,
    compute_next_domain_version,
)


def test_compute_next_domain_version_from_empty():
    assert compute_next_domain_version(None) == (1, 0, 0)


def test_compute_next_domain_version_bumps_minor():
    latest = SimpleNamespace(version_major=1, version_minor=2, version_patch=5)
    assert compute_next_domain_version(latest) == (1, 3, 0)


def test_next_version_uses_latest():
    db = MagicMock()
    repo = DomainRepository(db)
    latest = SimpleNamespace(version_major=2, version_minor=0, version_patch=0)
    repo.get_latest = MagicMock(return_value=latest)  # type: ignore[method-assign]
    assert repo.next_version(uuid4()) == (2, 1, 0)


def test_list_traceability_requires_scope():
    repo = DomainRepository(MagicMock())
    with pytest.raises(ValueError, match="analysis_id or project_id"):
        repo.list_traceability()


def test_create_analysis_tree_persists_nested_rows():
    db = MagicMock()
    repo = DomainRepository(db)
    project_id = uuid4()
    rkm_id = uuid4()
    user_id = uuid4()

    analysis = repo.create_analysis_tree(
        project_id=project_id,
        rkm_id=rkm_id,
        rkm_version_label="1.0.0",
        created_by=user_id,
        version_major=1,
        version_minor=0,
        version_patch=0,
        summary="Remote access domains",
        model="local",
        prompt_version="domain-1.0",
        knowledge_pack_version="1.0.0",
        payload_json={"raw": True},
        domains=[
            {
                "domain_code": "identity",
                "name": "Identity",
                "reason": "Remote access auth",
                "confidence": 0.8,
                "supporting_requirements": ["REQ-1", {"requirement_id": "REQ-2", "evidence": "doc"}],
                "dependencies": [
                    {
                        "depends_on_domain_code": "cybersecurity",
                        "dependency_kind": "recommended",
                        "reason": "Policy pairing",
                    },
                ],
                "open_questions": [
                    {
                        "question": "Is MFA mandatory?",
                        "affects_selection": True,
                        "related_requirement_ids": ["REQ-1"],
                    },
                ],
            },
            {
                "domain_code": "ztna_vpn",
                "reason": "Secure remote path",
                "selection_source": "dependency",
                "confidence": 0.6,
                "supporting_requirements": [],
                "dependencies": [
                    {
                        "depends_on_domain_code": "identity",
                        "dependency_kind": "required",
                        "reason": "Needs IdP",
                    },
                ],
            },
        ],
        analysis_open_questions=[
            {
                "question": "Which sites need remote access?",
                "domain_code": "ztna_vpn",
                "related_requirement_ids": ["REQ-1"],
            },
        ],
        traceability=[
            {
                "requirement_id": "REQ-1",
                "domain_code": "identity",
                "status": "covered",
                "evidence": "RKM functional",
            },
            {
                "requirement_id": "REQ-MISSING",
                "status": "not_covered",
            },
        ],
    )

    assert isinstance(analysis, DomainAnalysis)
    assert analysis.version_label == "1.0.0"
    assert analysis.knowledge_pack_version == "1.0.0"
    db.add.assert_called()
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(analysis)

    added = [call.args[0] for call in db.add.call_args_list]
    assert sum(isinstance(obj, DomainAnalysis) for obj in added) == 1
    assert sum(isinstance(obj, SolutionDomain) for obj in added) == 2
    assert sum(isinstance(obj, DomainRequirementLink) for obj in added) == 2
    assert sum(isinstance(obj, DomainDependency) for obj in added) == 2
    assert sum(isinstance(obj, DomainOpenQuestion) for obj in added) == 2
    assert sum(isinstance(obj, RequirementTraceability) for obj in added) == 2

    links = [obj for obj in added if isinstance(obj, DomainRequirementLink)]
    assert {link.requirement_id for link in links} == {"REQ-1", "REQ-2"}
    covered = next(
        obj
        for obj in added
        if isinstance(obj, RequirementTraceability) and obj.requirement_id == "REQ-1"
    )
    assert covered.status == "covered"
    assert covered.domain_id is not None


def test_create_analysis_tree_rejects_duplicate_domain_codes():
    repo = DomainRepository(MagicMock())
    with pytest.raises(ValueError, match="duplicate domain_code"):
        repo.create_analysis_tree(
            project_id=uuid4(),
            rkm_id=None,
            rkm_version_label=None,
            created_by=None,
            version_major=1,
            version_minor=0,
            version_patch=0,
            summary=None,
            model=None,
            prompt_version=None,
            knowledge_pack_version=None,
            payload_json={},
            domains=[
                {"domain_code": "wifi", "reason": "a", "supporting_requirements": ["R1"]},
                {"domain_code": "wifi", "reason": "b", "supporting_requirements": ["R2"]},
            ],
        )


def test_create_analysis_tree_rejects_missing_domain_code():
    repo = DomainRepository(MagicMock())
    with pytest.raises(ValueError, match="domain_code is required"):
        repo.create_analysis_tree(
            project_id=uuid4(),
            rkm_id=None,
            rkm_version_label=None,
            created_by=None,
            version_major=1,
            version_minor=0,
            version_patch=0,
            summary=None,
            model=None,
            prompt_version=None,
            knowledge_pack_version=None,
            payload_json={},
            domains=[{"reason": "no code", "supporting_requirements": ["R1"]}],
        )
