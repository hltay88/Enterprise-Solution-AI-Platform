"""Sprint 3.3 Task 7 — BOM import service."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError, ValidationAppError
from app.schemas.vendor_bom import BomImportIn, BomItemIn
from app.services.bom_service import BomService


def test_import_bom_requires_project():
    service = BomService(MagicMock())
    service.projects.get_for_user = MagicMock(return_value=None)  # type: ignore[method-assign]

    with pytest.raises(NotFoundError, match="Project"):
        service.import_bom(
            uuid4(),
            uuid4(),
            BomImportIn(
                source="quote",
                items=[BomItemIn(product_model="X1")],
            ),
        )


def test_import_bom_rejects_foreign_architecture():
    service = BomService(MagicMock())
    project_id = uuid4()
    service.projects.get_for_user = MagicMock(  # type: ignore[method-assign]
        return_value=SimpleNamespace(id=project_id),
    )
    service.architectures.get_for_project = MagicMock(return_value=None)  # type: ignore[method-assign]

    with pytest.raises(NotFoundError, match="Architecture"):
        service.import_bom(
            project_id,
            uuid4(),
            BomImportIn(
                source="quote",
                architecture_id=uuid4(),
                items=[BomItemIn(product_model="X1")],
            ),
        )


def test_import_bom_persists_and_audits():
    db = MagicMock()
    service = BomService(db)
    project_id = uuid4()
    user_id = uuid4()
    bom_id = uuid4()
    product_id = uuid4()
    now = datetime.now(timezone.utc)

    service.projects.get_for_user = MagicMock(  # type: ignore[method-assign]
        return_value=SimpleNamespace(id=project_id),
    )
    service.catalogues.search_products = MagicMock(  # type: ignore[method-assign]
        return_value=[
            SimpleNamespace(
                id=product_id,
                vendor="RefNet",
                product_model="RN-AP-6E",
            ),
        ],
    )
    bom_row = SimpleNamespace(
        id=bom_id,
        project_id=project_id,
        architecture_id=None,
        source="Distributor CSV",
        source_filename="quote.csv",
        notes=None,
        created_at=now,
    )
    item_row = SimpleNamespace(
        id=uuid4(),
        bom_import_id=bom_id,
        line_number=1,
        vendor="RefNet",
        product_model="RN-AP-6E",
        description="",
        quantity=10.0,
        unit="ea",
        category="wireless_ap",
        sku=None,
        mapped_product_id=product_id,
        notes=None,
        created_at=now,
    )
    service.boms.create_import_tree = MagicMock(return_value=bom_row)  # type: ignore[method-assign]
    service.boms.list_items = MagicMock(return_value=[item_row])  # type: ignore[method-assign]

    with patch("app.services.bom_service.AuditService") as audit_cls:
        out = service.import_bom(
            project_id,
            user_id,
            BomImportIn(
                source="Distributor CSV",
                source_filename="quote.csv",
                items=[
                    BomItemIn(
                        line_number=1,
                        vendor="RefNet",
                        product_model="RN-AP-6E",
                        quantity=10,
                        unit="ea",
                        category="wireless_ap",
                    ),
                ],
            ),
        )

    assert out.id == bom_id
    assert out.item_count == 1
    assert out.items[0].mapped_product_id == product_id
    create_kwargs = service.boms.create_import_tree.call_args.kwargs
    assert create_kwargs["items"][0]["mapped_product_id"] == product_id
    audit_cls.return_value.record.assert_called_once()
    assert audit_cls.return_value.record.call_args.kwargs["action"] == "bom.import"


def test_import_bom_maps_validation_errors():
    service = BomService(MagicMock())
    service.projects.get_for_user = MagicMock(  # type: ignore[method-assign]
        return_value=SimpleNamespace(id=uuid4()),
    )
    service.catalogues.search_products = MagicMock(return_value=[])  # type: ignore[method-assign]
    service.boms.create_import_tree = MagicMock(  # type: ignore[method-assign]
        side_effect=ValueError("at least one BOM item is required"),
    )

    with pytest.raises(ValidationAppError, match="BOM item"):
        service.import_bom(
            uuid4(),
            uuid4(),
            BomImportIn(
                source="quote",
                items=[BomItemIn(product_model="X1")],
            ),
        )
