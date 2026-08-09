"""Phase 3 P2 — vendor analytics pure helpers + service wiring."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError
from app.services.vendor_analytics import (
    catalogue_analytics_from_products,
    mapping_analytics_from_rows,
)
from app.services.vendor_analytics_service import VendorAnalyticsService


def test_catalogue_analytics_empty():
    out = catalogue_analytics_from_products([])
    assert out["product_count"] == 0
    assert out["stale_ratio"] == 0.0
    assert out["average_confidence"] is None
    assert out["warnings"] == []


def test_catalogue_analytics_stale_and_lifecycle_warnings():
    products = [
        {
            "vendor": "A",
            "category": "ap",
            "lifecycle_status": "active",
            "region": "APAC",
            "confidence": 0.8,
            "is_stale": True,
        },
        {
            "vendor": "B",
            "category": "switch",
            "lifecycle_status": "end_of_sale",
            "region": None,
            "confidence": 0.6,
            "is_stale": False,
        },
        {
            "vendor": "A",
            "category": "ap",
            "lifecycle_status": "active",
            "region": "APAC",
            "confidence": 1.0,
            "is_stale": True,
        },
        {
            "vendor": "C",
            "category": "fw",
            "lifecycle_status": "active",
            "region": "EMEA",
            "confidence": 0.9,
            "is_stale": False,
        },
    ]
    out = catalogue_analytics_from_products(
        products,
        catalogue_id="cat-1",
        catalogue_name="Seed",
    )
    assert out["catalogue_id"] == "cat-1"
    assert out["product_count"] == 4
    assert out["stale_count"] == 2
    assert out["stale_ratio"] == 0.5
    assert out["average_confidence"] == 0.825
    assert any("stale" in w for w in out["warnings"])
    assert any("end-of-sale" in w.lower() or "end-of" in w.lower() for w in out["warnings"])
    vendors = {item["key"]: item["count"] for item in out["by_vendor"]}
    assert vendors["A"] == 2


def test_mapping_analytics_aggregates_and_warnings():
    pid = str(uuid4())
    c1, c2, c3 = str(uuid4()), str(uuid4()), str(uuid4())
    mappings = [
        {
            "product_id": pid,
            "component_id": c1,
            "status": "candidate",
            "preference_kind": "technical",
            "fit_score": 4.0,
        },
        {
            "product_id": pid,
            "component_id": c2,
            "status": "selected",
            "preference_kind": "commercial",
            "fit_score": 4.5,
        },
    ]
    products = {
        pid: {
            "vendor": "ExampleNet",
            "lifecycle_status": "end_of_support",
            "is_stale": True,
            "confidence": 0.5,
        },
    }
    out = mapping_analytics_from_rows(
        mappings,
        products,
        project_id="proj-1",
        architecture_id="arch-1",
        component_ids=[c1, c2, c3],
    )
    assert out["mapping_count"] == 2
    assert out["selected_count"] == 1
    assert out["candidate_count"] == 1
    assert out["stale_mapped_count"] == 2
    assert out["average_fit_score"] == 4.25
    assert out["component_count"] == 3
    assert out["mapped_component_count"] == 2
    assert out["unmatched_component_count"] == 1
    assert out["coverage_ratio"] == pytest.approx(2 / 3, rel=1e-3)
    assert c3 in out["unmatched_component_ids"]
    buckets = {item["key"]: item["count"] for item in out["fit_score_buckets"]}
    assert buckets["4–5"] == 2
    assert any("stale" in w for w in out["warnings"])
    assert any("lifecycle" in w.lower() or "end-of" in w.lower() for w in out["warnings"])
    assert any("no product mapping" in w.lower() for w in out["warnings"])


def test_mapping_analytics_normalizes_percent_fit_scores():
    pid = str(uuid4())
    out = mapping_analytics_from_rows(
        [
            {
                "product_id": pid,
                "component_id": str(uuid4()),
                "status": "candidate",
                "preference_kind": "technical",
                "fit_score": 80,
            },
        ],
        {pid: {"vendor": "A", "lifecycle_status": "active", "is_stale": False}},
        project_id="proj-1",
    )
    assert out["average_fit_score"] == 4.0
    buckets = {item["key"]: item["count"] for item in out["fit_score_buckets"]}
    assert buckets["4–5"] == 1


def test_service_catalogue_not_found():
    db = MagicMock()
    service = VendorAnalyticsService(db)
    service.catalogues.get_catalogue = MagicMock(return_value=None)  # type: ignore[method-assign]
    with pytest.raises(NotFoundError):
        service.catalogue_analytics(catalogue_id=uuid4())


def test_service_empty_catalogues_warning():
    db = MagicMock()
    service = VendorAnalyticsService(db)
    service.catalogues.list_catalogues = MagicMock(return_value=[])  # type: ignore[method-assign]
    out = service.catalogue_analytics()
    assert out.product_count == 0
    assert out.warnings
    assert "No vendor catalogues" in out.warnings[0]


def test_service_project_bundle():
    db = MagicMock()
    service = VendorAnalyticsService(db)
    project_id = uuid4()
    user_id = uuid4()
    catalogue_id = uuid4()
    product = SimpleNamespace(
        vendor="ExampleNet",
        category="ap",
        lifecycle_status="active",
        region="APAC",
        confidence=0.9,
        is_stale=False,
    )
    catalogue = SimpleNamespace(id=catalogue_id, name="Seed")
    service.catalogues.list_catalogues = MagicMock(return_value=[catalogue])  # type: ignore[method-assign]
    service.catalogues.list_products = MagicMock(return_value=[product])  # type: ignore[method-assign]
    service.projects.get_for_user = MagicMock(  # type: ignore[method-assign]
        return_value=SimpleNamespace(id=project_id),
    )
    service.mappings.list_for_project = MagicMock(return_value=[])  # type: ignore[method-assign]
    service.mappings.get_products_by_ids = MagicMock(return_value={})  # type: ignore[method-assign]
    service.architectures.list_for_project = MagicMock(return_value=[])  # type: ignore[method-assign]

    bundle = service.project_bundle(project_id, user_id)
    assert bundle.catalogue.product_count == 1
    assert bundle.mappings.mapping_count == 0
    assert bundle.mappings.project_id == project_id
