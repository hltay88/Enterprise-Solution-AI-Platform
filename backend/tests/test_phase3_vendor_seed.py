"""Sprint 3.3 Task 4 — vendor seed catalogue pack."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.services.phase3_vendor_seed import (
    SEED_CATALOGUE_NAME,
    SEED_SOURCE,
    build_seed_catalogue_import,
    clear_vendor_seed_cache,
    load_seed_catalogue_payload,
    seed_catalogue_path,
    seed_version,
)
from app.services.vendor_catalogue_service import VendorCatalogueService


@pytest.fixture(autouse=True)
def _clear_seed_cache():
    clear_vendor_seed_cache()
    yield
    clear_vendor_seed_cache()


def test_seed_file_exists_and_loads():
    assert seed_catalogue_path().is_file()
    payload = load_seed_catalogue_payload()
    assert payload["name"] == SEED_CATALOGUE_NAME
    assert payload["source"] == SEED_SOURCE
    assert len(payload["products"]) >= 8
    assert seed_version() == "1.0.0"


def test_build_seed_catalogue_import_validates():
    body = build_seed_catalogue_import()
    assert body.name == SEED_CATALOGUE_NAME
    assert body.source == SEED_SOURCE
    assert len(body.products) >= 8
    models = {item.product_model for item in body.products}
    assert "RN-AP-6E" in models
    assert "SE-FW-1000" in models
    # All products must carry a stated source (ATLAS-038).
    assert all(item.source for item in body.products)


def test_seed_products_are_fictional_vendors():
    body = build_seed_catalogue_import()
    vendors = {item.vendor.lower() for item in body.products}
    banned = {"cisco", "aruba", "hpe", "dell", "huawei", "juniper", "fortinet"}
    assert vendors.isdisjoint(banned)


def test_seed_default_catalogue_is_idempotent():
    db = MagicMock()
    service = VendorCatalogueService(db)
    catalogue_id = uuid4()
    now = datetime.now(timezone.utc)
    existing = SimpleNamespace(
        id=catalogue_id,
        name=SEED_CATALOGUE_NAME,
        source=SEED_SOURCE,
        source_date=None,
        version_label="1.0.0",
        region="APAC",
        notes=None,
        created_at=now,
        payload_json={"seed": True},
    )
    service.catalogues.get_by_name_and_source = MagicMock(return_value=existing)  # type: ignore[method-assign]
    service.catalogues.list_products = MagicMock(return_value=[])  # type: ignore[method-assign]
    service.import_catalogue = MagicMock()  # type: ignore[method-assign]

    out = service.seed_default_catalogue(uuid4(), force=False)
    assert out.id == catalogue_id
    service.import_catalogue.assert_not_called()


def test_seed_force_reimports():
    from app.schemas.vendor_bom import VendorCatalogueOut

    db = MagicMock()
    service = VendorCatalogueService(db)
    catalogue_id = uuid4()
    now = datetime.now(timezone.utc)
    created = SimpleNamespace(
        id=catalogue_id,
        name=SEED_CATALOGUE_NAME,
        source=SEED_SOURCE,
        source_date=None,
        version_label="1.0.0",
        region="APAC",
        notes="seed",
        created_at=now,
        payload_json={},
    )
    service.catalogues.get_catalogue = MagicMock(return_value=created)  # type: ignore[method-assign]
    service.catalogues.list_products = MagicMock(return_value=[])  # type: ignore[method-assign]
    service.import_catalogue = MagicMock(  # type: ignore[method-assign]
        return_value=VendorCatalogueOut(
            id=catalogue_id,
            name=SEED_CATALOGUE_NAME,
            source=SEED_SOURCE,
            version_label="1.0.0",
            product_count=0,
            created_at=now,
            products=[],
        ),
    )
    out = service.seed_default_catalogue(uuid4(), force=True)
    assert out.id == catalogue_id
    service.import_catalogue.assert_called_once()
    db.commit.assert_called()
