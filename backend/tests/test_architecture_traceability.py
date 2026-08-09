"""Sprint 3.2 Task 10 — architecture-stage requirement traceability."""

from __future__ import annotations

from uuid import uuid4

from app.services.architecture_traceability import (
    build_requirement_architecture_traceability,
    count_architecture_uncovered_critical,
)


def test_build_covers_mapped_component_with_domain_link():
    arch_id = uuid4()
    component_id = uuid4()
    domain_id = uuid4()
    rows = build_requirement_architecture_traceability(
        requirements=[
            {"id": "REQ-WIFI-1", "title": "WiFi", "priority": "critical"},
            {"id": "REQ-GAP", "title": "DR", "priority": "high"},
        ],
        architectures=[
            {
                "id": arch_id,
                "candidate_key": "standard",
                "components": [
                    {
                        "id": component_id,
                        "name": "Enterprise WLAN",
                        "maps_to_requirements": ["REQ-WIFI-1"],
                    },
                ],
            },
        ],
        domain_links=[
            {
                "requirement_id": "REQ-WIFI-1",
                "domain_id": domain_id,
                "domain_code": "wifi",
                "status": "covered",
            },
        ],
    )
    covered = next(
        row
        for row in rows
        if row["requirement_id"] == "REQ-WIFI-1" and row["component_id"] == component_id
    )
    assert covered["status"] == "covered"
    assert covered["architecture_id"] == arch_id
    assert covered["domain_id"] == domain_id
    assert "Enterprise WLAN" in covered["evidence"]

    gap = next(row for row in rows if row["requirement_id"] == "REQ-GAP")
    assert gap["status"] == "not_covered"
    assert gap["architecture_id"] == arch_id
    assert gap["component_id"] is None


def test_build_partial_when_component_maps_without_domain():
    arch_id = uuid4()
    component_id = uuid4()
    rows = build_requirement_architecture_traceability(
        requirements=[{"id": "REQ-1", "title": "X", "priority": "medium"}],
        architectures=[
            {
                "id": arch_id,
                "candidate_key": "standard",
                "components": [
                    {
                        "id": component_id,
                        "name": "Core",
                        "maps_to_requirements": ["REQ-1"],
                    },
                ],
            },
        ],
        domain_links=[],
    )
    assert rows[0]["status"] == "partially_covered"
    assert rows[0]["domain_id"] is None


def test_count_architecture_uncovered_critical():
    arch_id = uuid4()
    rows = [
        {
            "requirement_id": "REQ-A",
            "architecture_id": arch_id,
            "status": "not_covered",
        },
        {
            "requirement_id": "REQ-B",
            "architecture_id": arch_id,
            "status": "not_covered",
        },
        {
            "requirement_id": "REQ-C",
            "architecture_id": arch_id,
            "status": "covered",
        },
    ]
    count = count_architecture_uncovered_critical(
        rows,
        [
            {"id": "REQ-A", "priority": "critical"},
            {"id": "REQ-B", "priority": "low"},
            {"id": "REQ-C", "priority": "high"},
        ],
    )
    assert count == 1
