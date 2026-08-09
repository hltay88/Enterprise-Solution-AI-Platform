"""Sprint 3.3 Task 7 — BOM import repository."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.vendor_bom import BomImport, BomItem
from app.repositories.bom_repository import BomRepository


def test_create_import_tree_requires_source_and_items():
    repo = BomRepository(MagicMock())
    with pytest.raises(ValueError, match="at least one BOM item"):
        repo.create_import_tree(
            project_id=uuid4(),
            architecture_id=None,
            source="distributor quote",
            source_filename=None,
            notes=None,
            imported_by=None,
            items=[],
        )
    with pytest.raises(ValueError, match="source is required"):
        repo.create_import_tree(
            project_id=uuid4(),
            architecture_id=None,
            source="  ",
            source_filename=None,
            notes=None,
            imported_by=None,
            items=[{"product_model": "X1"}],
        )


def test_create_import_tree_persists_import_and_items():
    db = MagicMock()
    repo = BomRepository(db)
    project_id = uuid4()
    user_id = uuid4()
    product_id = uuid4()

    bom = repo.create_import_tree(
        project_id=project_id,
        architecture_id=None,
        source="Distributor CSV",
        source_filename="quote.csv",
        notes="evidence only",
        imported_by=user_id,
        items=[
            {
                "line_number": 1,
                "vendor": "RefNet",
                "product_model": "RN-AP-6E",
                "description": "Access point",
                "quantity": 24,
                "unit": "ea",
                "category": "wireless_ap",
                "mapped_product_id": product_id,
            },
            {
                "line_number": 2,
                "sku": "SW-48",
                "description": "Access switch",
                "quantity": 4,
            },
        ],
        payload_json={"evidence": True},
        commit=True,
    )

    assert isinstance(bom, BomImport)
    assert bom.source == "Distributor CSV"
    assert bom.imported_by == user_id
    assert bom.payload_json["evidence"] is True
    assert db.add.call_count == 3  # import + 2 items
    item_adds = [c.args[0] for c in db.add.call_args_list if isinstance(c.args[0], BomItem)]
    assert len(item_adds) == 2
    assert item_adds[0].mapped_product_id == product_id
    assert item_adds[1].sku == "SW-48"
    db.commit.assert_called_once()
