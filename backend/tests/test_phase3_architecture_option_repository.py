"""Sprint 3.2 Task 4 — architecture option repository helpers and tree create."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.architecture_option import (
    ArchitectureAssumption,
    ArchitectureComponent,
    ArchitectureOption,
    ArchitectureRelationship,
    CapacityNote,
    DesignDecision,
    SolutionRisk,
    SolutionScore,
)
from app.repositories.architecture_option_repository import (
    ArchitectureOptionRepository,
    compute_next_architecture_version,
)


def test_compute_next_architecture_version_from_empty():
    assert compute_next_architecture_version(None) == (1, 0, 0)


def test_compute_next_architecture_version_bumps_minor():
    latest = SimpleNamespace(version_major=1, version_minor=2, version_patch=5)
    assert compute_next_architecture_version(latest) == (1, 3, 0)


def test_next_version_uses_latest():
    db = MagicMock()
    repo = ArchitectureOptionRepository(db)
    latest = SimpleNamespace(version_major=2, version_minor=0, version_patch=0)
    repo.get_latest = MagicMock(return_value=latest)  # type: ignore[method-assign]
    assert repo.next_version(uuid4()) == (2, 1, 0)


def test_list_risks_requires_scope():
    repo = ArchitectureOptionRepository(MagicMock())
    with pytest.raises(ValueError, match="architecture_id or project_id"):
        repo.list_risks()


def test_create_generation_tree_requires_candidates():
    repo = ArchitectureOptionRepository(MagicMock())
    with pytest.raises(ValueError, match="non-empty"):
        repo.create_generation_tree(
            project_id=uuid4(),
            rkm_id=None,
            rkm_version_label=None,
            domain_analysis_id=None,
            created_by=None,
            version_major=1,
            version_minor=0,
            version_patch=0,
            model=None,
            prompt_version=None,
            knowledge_pack_version=None,
            architectures=[],
        )


def test_create_generation_tree_persists_nested_rows():
    db = MagicMock()
    repo = ArchitectureOptionRepository(db)
    project_id = uuid4()
    rkm_id = uuid4()
    domain_analysis_id = uuid4()
    user_id = uuid4()
    generation_id = uuid4()

    options = repo.create_generation_tree(
        project_id=project_id,
        rkm_id=rkm_id,
        rkm_version_label="2.0.0",
        domain_analysis_id=domain_analysis_id,
        created_by=user_id,
        version_major=1,
        version_minor=0,
        version_patch=0,
        model="local",
        prompt_version="architecture-2.0",
        knowledge_pack_version="1.1.0",
        generation_id=generation_id,
        architectures=[
            {
                "candidate_key": "standard",
                "title": "Standard campus Wi-Fi",
                "summary": "Two-tier + WLAN",
                "confidence": 0.8,
                "pattern_codes": ["wireless_enterprise", "two_tier_campus"],
                "high_level_architecture": ["Campus underlay", "Enterprise WLAN"],
                "components": [
                    {
                        "name": "Access switching",
                        "purpose": "Underlay",
                        "temp_id": "c1",
                        "maps_to_requirements": ["REQ-1"],
                    },
                    {
                        "name": "WLAN",
                        "purpose": "Wireless",
                        "temp_id": "c2",
                        "maps_to_requirements": ["REQ-1"],
                    },
                ],
                "relationships": [
                    {
                        "from_component": "c2",
                        "to_component": "c1",
                        "relationship_kind": "depends_on",
                    },
                ],
                "decisions": [
                    {
                        "decision": "Vendor-neutral",
                        "rationale": "ATLAS-035",
                    },
                ],
                "assumptions": [
                    {
                        "statement": "Cabling reusable",
                        "affected_components": ["c1"],
                    },
                ],
                "risks": [
                    {
                        "description": "Survey delay",
                        "severity": "medium",
                    },
                ],
                "scores": [
                    {
                        "dimension": "requirement_coverage",
                        "weight": 0.3,
                        "score": 4,
                        "explanation": "Covers Wi-Fi req",
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
            {
                "candidate_key": "high_availability",
                "title": "HA campus Wi-Fi",
                "summary": "Adds redundancy",
                "components": [
                    {"name": "Redundant core", "purpose": "HA", "temp_id": "h1"},
                ],
            },
        ],
    )

    assert len(options) == 2
    assert all(isinstance(item, ArchitectureOption) for item in options)
    assert options[0].version_label == "1.0.0"
    assert options[0].generation_id == generation_id
    assert options[0].domain_analysis_id == domain_analysis_id
    assert options[0].knowledge_pack_version == "1.1.0"
    assert "high_level_architecture" in options[0].payload_json
    assert options[1].candidate_key == "high_availability"

    assert db.flush.call_count >= 2
    db.commit.assert_called_once()
    assert db.refresh.call_count == 2

    added = [call.args[0] for call in db.add.call_args_list]
    assert sum(isinstance(obj, ArchitectureOption) for obj in added) == 2
    assert sum(isinstance(obj, ArchitectureComponent) for obj in added) == 3
    assert sum(isinstance(obj, ArchitectureRelationship) for obj in added) == 1
    assert sum(isinstance(obj, DesignDecision) for obj in added) == 1
    assert sum(isinstance(obj, ArchitectureAssumption) for obj in added) == 1
    assert sum(isinstance(obj, SolutionRisk) for obj in added) == 1
    assert sum(isinstance(obj, SolutionScore) for obj in added) == 1
    assert sum(isinstance(obj, CapacityNote) for obj in added) == 1

    relationship = next(obj for obj in added if isinstance(obj, ArchitectureRelationship))
    components = [obj for obj in added if isinstance(obj, ArchitectureComponent)]
    by_temp = {obj.name: obj.id for obj in components}
    assert relationship.from_component_id == by_temp["WLAN"]
    assert relationship.to_component_id == by_temp["Access switching"]


def test_create_generation_tree_rejects_duplicate_candidate_keys():
    repo = ArchitectureOptionRepository(MagicMock())
    with pytest.raises(ValueError, match="duplicate candidate_key"):
        repo.create_generation_tree(
            project_id=uuid4(),
            rkm_id=None,
            rkm_version_label=None,
            domain_analysis_id=None,
            created_by=None,
            version_major=1,
            version_minor=0,
            version_patch=0,
            model=None,
            prompt_version=None,
            knowledge_pack_version=None,
            architectures=[
                {
                    "candidate_key": "standard",
                    "title": "A",
                    "components": [{"name": "X", "purpose": "y"}],
                },
                {
                    "candidate_key": "standard",
                    "title": "B",
                    "components": [{"name": "Z", "purpose": "w"}],
                },
            ],
        )
