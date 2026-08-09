"""Sprint 3.3 Task 5 — product matching helpers."""

from __future__ import annotations

from app.services.architecture_product_matching import (
    infer_component_needs,
    rank_products_for_component,
    score_product_for_component,
)


def test_infer_wifi_component_needs():
    caps, cats = infer_component_needs(
        {
            "name": "Enterprise WLAN",
            "purpose": "Wi-Fi 6 coverage for campus",
            "component_kind": "logical",
        },
    )
    assert "wifi6e" in caps
    assert "wireless_ap" in cats


def test_score_requires_capability_or_category_overlap():
    needed_caps = {"wifi6e"}
    needed_cats = {"wireless_ap"}
    miss = score_product_for_component(
        needed_capabilities=needed_caps,
        needed_categories=needed_cats,
        product={
            "id": "p1",
            "vendor": "X",
            "product_model": "FW",
            "category": "firewall",
            "capabilities": [{"capability_code": "ngfw"}],
        },
    )
    assert miss is None

    hit = score_product_for_component(
        needed_capabilities=needed_caps,
        needed_categories=needed_cats,
        product={
            "id": "p2",
            "vendor": "RefNet",
            "product_model": "RN-AP-6E",
            "category": "wireless_ap",
            "capabilities": [{"capability_code": "wifi6e"}],
            "lifecycle_status": "active",
            "is_stale": False,
        },
    )
    assert hit is not None
    assert hit.fit_score >= 3.0
    assert hit.preference_kind == "technical"


def test_rank_products_orders_by_fit_and_limits():
    component = {"name": "Access switching", "purpose": "PoE access layer"}
    products = [
        {
            "id": "low",
            "vendor": "A",
            "product_model": "SW1",
            "category": "access_switch",
            "capabilities": [{"capability_code": "1g_access"}],
            "lifecycle_status": "active",
        },
        {
            "id": "high",
            "vendor": "B",
            "product_model": "SW2",
            "category": "access_switch",
            "capabilities": [
                {"capability_code": "poe_plus"},
                {"capability_code": "1g_access"},
            ],
            "lifecycle_status": "active",
        },
        {
            "id": "stale",
            "vendor": "C",
            "product_model": "SW3",
            "category": "access_switch",
            "capabilities": [
                {"capability_code": "poe_plus"},
                {"capability_code": "1g_access"},
            ],
            "lifecycle_status": "active",
            "is_stale": True,
        },
    ]
    ranked = rank_products_for_component(component=component, products=products, limit=2)
    assert len(ranked) == 2
    assert ranked[0].product_id == "high"
