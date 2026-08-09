"""Sprint 3.3 Task 3 — vendor catalogue repository."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.vendor_bom import ProductCapability, VendorCatalogue, VendorProduct
from app.repositories.vendor_catalogue_repository import VendorCatalogueRepository


def test_create_catalogue_tree_requires_products_and_source():
    repo = VendorCatalogueRepository(MagicMock())
    with pytest.raises(ValueError, match="at least one product"):
        repo.create_catalogue_tree(
            name="x",
            source="internal",
            source_date=None,
            version_label="1.0.0",
            region=None,
            notes=None,
            imported_by=None,
            products=[],
        )
    with pytest.raises(ValueError, match="source is required"):
        repo.create_catalogue_tree(
            name="x",
            source="  ",
            source_date=None,
            version_label="1.0.0",
            region=None,
            notes=None,
            imported_by=None,
            products=[{"vendor": "A", "product_model": "M1", "source": "s"}],
        )


def test_create_catalogue_tree_persists_nested_rows():
    db = MagicMock()
    repo = VendorCatalogueRepository(db)
    user_id = uuid4()

    catalogue = repo.create_catalogue_tree(
        name="Seed",
        source="Approved internal catalogue",
        source_date=date(2026, 1, 15),
        version_label="1.0.0",
        region="APAC",
        notes=None,
        imported_by=user_id,
        products=[
            {
                "vendor": "ExampleNet",
                "product_family": "Access",
                "product_model": "EN-AP-6E",
                "category": "wireless_ap",
                "specifications": {"band": "6 GHz"},
                "lifecycle_status": "active",
                "source": "Approved internal catalogue",
                "source_date": date(2026, 1, 15),
                "confidence": 0.8,
                "capabilities": [
                    {
                        "capability_code": "wifi6e",
                        "capability_label": "Wi-Fi 6E",
                        "confidence": 0.9,
                    },
                ],
            },
        ],
        commit=True,
    )

    assert isinstance(catalogue, VendorCatalogue)
    assert catalogue.source == "Approved internal catalogue"
    assert catalogue.imported_by == user_id
    assert db.add.call_count >= 3  # catalogue + product + capability
    added_types = {type(call.args[0]) for call in db.add.call_args_list}
    assert VendorCatalogue in added_types
    assert VendorProduct in added_types
    assert ProductCapability in added_types
    db.commit.assert_called_once()


def test_create_catalogue_tree_rejects_duplicate_models():
    repo = VendorCatalogueRepository(MagicMock())
    with pytest.raises(ValueError, match="duplicate"):
        repo.create_catalogue_tree(
            name="Seed",
            source="internal",
            source_date=None,
            version_label="1.0.0",
            region=None,
            notes=None,
            imported_by=None,
            products=[
                {"vendor": "A", "product_model": "M1", "source": "s"},
                {"vendor": "A", "product_model": "M1", "source": "s"},
            ],
        )
