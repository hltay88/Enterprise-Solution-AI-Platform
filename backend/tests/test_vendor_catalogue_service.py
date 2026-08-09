"""Sprint 3.3 Task 3 — vendor catalogue service."""

from __future__ import annotations

from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError, ValidationAppError
from app.schemas.vendor_bom import VendorCatalogueImportIn
from app.services.vendor_catalogue_service import VendorCatalogueService, _is_stale


def test_is_stale_flags_old_source_dates():
    assert _is_stale(date(2020, 1, 1), False) is True
    assert _is_stale(date.today(), False) is False
    assert _is_stale(None, False) is False
    assert _is_stale(date.today(), True) is True


def test_import_catalogue_maps_validation_errors():
    service = VendorCatalogueService(MagicMock())
    service.catalogues.create_catalogue_tree = MagicMock(  # type: ignore[method-assign]
        side_effect=ValueError("duplicate vendor/product_model"),
    )
    body = VendorCatalogueImportIn(
        source="internal",
        products=[
            {
                "vendor": "A",
                "product_model": "M1",
                "source": "internal",
            },
        ],
    )
    with pytest.raises(ValidationAppError, match="duplicate"):
        service.import_catalogue(body, uuid4())


def test_import_catalogue_returns_out():
    db = MagicMock()
    service = VendorCatalogueService(db)
    catalogue_id = uuid4()
    product_id = uuid4()
    now = datetime.now(timezone.utc)
    catalogue = SimpleNamespace(
        id=catalogue_id,
        name="Seed",
        source="Approved internal catalogue",
        source_date=date(2026, 1, 15),
        version_label="1.0.0",
        region="APAC",
        notes=None,
        created_at=now,
    )
    product = SimpleNamespace(
        id=product_id,
        catalogue_id=catalogue_id,
        vendor="ExampleNet",
        product_family="Access",
        product_model="EN-AP-6E",
        category="wireless_ap",
        specifications={"band": "6 GHz"},
        licensing=None,
        lifecycle_status="active",
        source="Approved internal catalogue",
        source_date=date(2026, 1, 15),
        region="APAC",
        confidence=0.8,
        is_stale=False,
        created_at=now,
        updated_at=now,
    )
    service.catalogues.create_catalogue_tree = MagicMock(return_value=catalogue)  # type: ignore[method-assign]
    service.catalogues.list_products = MagicMock(return_value=[product])  # type: ignore[method-assign]
    service.catalogues.list_capabilities = MagicMock(return_value=[])  # type: ignore[method-assign]

    body = VendorCatalogueImportIn(
        name="Seed",
        source="Approved internal catalogue",
        source_date=date(2026, 1, 15),
        region="APAC",
        products=[
            {
                "vendor": "ExampleNet",
                "product_model": "EN-AP-6E",
                "source": "Approved internal catalogue",
                "source_date": date(2026, 1, 15),
                "specifications": {"band": "6 GHz"},
            },
        ],
    )
    out = service.import_catalogue(body, uuid4())
    assert out.id == catalogue_id
    assert out.product_count == 1
    assert out.products[0].product_model == "EN-AP-6E"
    assert out.products[0].specifications == {"band": "6 GHz"}


def test_get_catalogue_not_found():
    service = VendorCatalogueService(MagicMock())
    service.catalogues.get_catalogue = MagicMock(return_value=None)  # type: ignore[method-assign]
    with pytest.raises(NotFoundError):
        service.get_catalogue(uuid4())
