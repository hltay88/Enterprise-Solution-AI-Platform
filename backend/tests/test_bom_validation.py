"""Sprint 3.3 Task 8 — BOM validation heuristics."""

from __future__ import annotations

from uuid import uuid4

from app.services.bom_validation import derive_validation_status, validate_bom_items
from app.services.bom_validation import BomIssue


def test_detects_unknown_duplicate_and_missing_quantity():
    item_a = {
        "id": uuid4(),
        "line_number": 1,
        "vendor": "RefNet",
        "product_model": "RN-AP-6E",
        "category": "wireless_ap",
        "quantity": None,
    }
    item_b = {
        "id": uuid4(),
        "line_number": 2,
        "vendor": "RefNet",
        "product_model": "RN-AP-6E",
        "category": "wireless_ap",
        "quantity": 10,
    }
    outcome = validate_bom_items(items=[item_a, item_b], products_by_id={}, components=[])
    codes = {issue.code for issue in outcome.issues}
    assert "unknown_model" in codes
    assert "duplicate_component" in codes
    assert "missing_quantity" in codes
    assert outcome.status == "needs_review"


def test_missing_architecture_component_fails():
    outcome = validate_bom_items(
        items=[
            {
                "id": uuid4(),
                "line_number": 1,
                "vendor": "Other",
                "product_model": "MISC-1",
                "category": "misc",
                "quantity": 1,
            },
        ],
        products_by_id={},
        components=[
            {
                "id": uuid4(),
                "name": "Enterprise WLAN",
                "purpose": "Wi-Fi coverage",
                "component_kind": "logical",
            },
        ],
    )
    assert any(issue.code == "missing_component" for issue in outcome.issues)
    assert outcome.status == "failed"


def test_eol_product_is_compatibility_error():
    product_id = uuid4()
    outcome = validate_bom_items(
        items=[
            {
                "id": uuid4(),
                "line_number": 1,
                "vendor": "RefNet",
                "product_model": "RN-OLD",
                "mapped_product_id": product_id,
                "quantity": 2,
                "category": "access_switch",
            },
        ],
        products_by_id={
            product_id: {
                "id": product_id,
                "lifecycle_status": "end_of_support",
                "is_stale": True,
                "specifications": {},
                "confidence": 0.2,
                "category": "access_switch",
            },
        },
    )
    codes = {issue.code for issue in outcome.issues}
    assert "compatibility" in codes
    assert "stale_catalogue" in codes
    assert "uncertain_spec" in codes
    assert outcome.status == "failed"


def test_derive_validation_status():
    assert derive_validation_status([]) == "passed"
    assert (
        derive_validation_status(
            [BomIssue(code="support", severity="info", message="x", requires_human_validation=False)],
        )
        == "passed"
    )
    assert (
        derive_validation_status(
            [BomIssue(code="unknown_model", severity="warning", message="x")],
        )
        == "needs_review"
    )
    assert (
        derive_validation_status(
            [BomIssue(code="missing_component", severity="error", message="x")],
        )
        == "failed"
    )
