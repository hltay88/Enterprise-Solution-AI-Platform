"""Sprint 3.3 Task 2 — vendor / BOM / mapping / review Pydantic schemas."""

from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.architecture_option import ArchitectureOptionOut
from app.schemas.vendor_bom import (
    ArchitectureApproveIn,
    ArchitectureProductMapIn,
    ArchitectureReviewIn,
    BomImportIn,
    BomValidateIn,
    VendorCatalogueImportIn,
    VendorProductIn,
)


def _product(**overrides):
    base = {
        "vendor": "ExampleNet",
        "product_family": "Access",
        "product_model": "EN-AP-6E",
        "category": "wireless_ap",
        "capabilities": [
            {
                "capability_code": "wifi6e",
                "capability_label": "Wi-Fi 6E AP",
                "confidence": 90,
            },
        ],
        "specifications": {"band": "2.4/5/6 GHz"},
        "lifecycle_status": "active",
        "source": "Approved internal catalogue",
        "source_date": "2026-01-15",
        "region": "APAC",
        "confidence": 0.8,
    }
    base.update(overrides)
    return base


def test_catalogue_import_requires_source_and_products():
    with pytest.raises(ValidationError):
        VendorCatalogueImportIn(source="", products=[_product()])
    with pytest.raises(ValidationError):
        VendorCatalogueImportIn(source="internal", products=[])

    payload = VendorCatalogueImportIn(
        name="Atlas seed pack",
        source="Approved internal catalogue",
        source_date=date(2026, 1, 15),
        products=[_product()],
    )
    assert payload.products[0].product_model == "EN-AP-6E"
    assert payload.products[0].capabilities[0].confidence == 0.9


def test_vendor_product_requires_model_and_source():
    with pytest.raises(ValidationError):
        VendorProductIn(**_product(product_model=""))
    with pytest.raises(ValidationError):
        VendorProductIn(**_product(source=""))


def test_bom_import_requires_identifiable_items():
    with pytest.raises(ValidationError):
        BomImportIn(source="distributor", items=[])
    with pytest.raises(ValidationError):
        BomImportIn(
            source="distributor",
            items=[{"vendor": "X", "product_model": "", "description": ""}],
        )

    bom = BomImportIn(
        source="Authorized distributor quote",
        source_filename="quote.csv",
        architecture_id=uuid4(),
        items=[
            {
                "line_number": 1,
                "vendor": "ExampleNet",
                "product_model": "EN-AP-6E",
                "quantity": 24,
                "unit": "ea",
            },
        ],
    )
    assert bom.items[0].quantity == 24.0


def test_product_map_in_is_explicit_action_shape():
    architecture_id = uuid4()
    body = ArchitectureProductMapIn(
        architecture_id=architecture_id,
        include_stale=False,
    )
    assert body.architecture_id == architecture_id
    assert body.component_ids is None


def test_review_and_approve_notes_optional():
    assert ArchitectureReviewIn().note == ""
    assert ArchitectureApproveIn(note="Looks good").note == "Looks good"
    BomValidateIn()  # empty body allowed; service may default architecture


def test_architecture_option_out_includes_review_approve_fields():
    now = datetime.now(timezone.utc)
    option = ArchitectureOptionOut(
        id=uuid4(),
        project_id=uuid4(),
        generation_id=uuid4(),
        candidate_key="standard",
        title="Standard",
        version_label="1.0.0",
        status="under_review",
        reviewed_at=now,
        review_note="Checked capacity notes",
        created_at=now,
        updated_at=now,
    )
    assert option.reviewed_at == now
    assert option.approved_at is None
