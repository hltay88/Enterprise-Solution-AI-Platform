"""Sprint 3.3 Task 5 — architecture product mapping service."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError, ValidationAppError
from app.schemas.vendor_bom import ArchitectureProductMapIn
from app.services.architecture_product_mapping_service import (
    ArchitectureProductMappingService,
)


def _component(name: str = "Enterprise WLAN", purpose: str = "Wi-Fi coverage"):
    return SimpleNamespace(
        id=uuid4(),
        name=name,
        purpose=purpose,
        component_kind="logical",
    )


def _product(*, category: str = "wireless_ap", caps: list[str] | None = None):
    product_id = uuid4()
    return SimpleNamespace(
        id=product_id,
        vendor="RefNet",
        product_model="RN-AP-6E",
        category=category,
        lifecycle_status="active",
        region="APAC",
        is_stale=False,
        _caps=caps or ["wifi6e", "seamless_roaming"],
    )


def test_map_products_requires_architecture_and_catalogue():
    db = MagicMock()
    service = ArchitectureProductMappingService(db)
    service.projects.get_for_user = MagicMock(return_value=SimpleNamespace(id=uuid4()))  # type: ignore[method-assign]
    service.architectures.get_for_project = MagicMock(return_value=None)  # type: ignore[method-assign]

    with pytest.raises(NotFoundError):
        service.map_products(
            uuid4(),
            uuid4(),
            ArchitectureProductMapIn(architecture_id=uuid4()),
        )

    service.architectures.get_for_project = MagicMock(  # type: ignore[method-assign]
        return_value=SimpleNamespace(id=uuid4(), candidate_key="standard"),
    )
    service.architectures.list_components = MagicMock(return_value=[_component()])  # type: ignore[method-assign]
    service.catalogues.search_products = MagicMock(return_value=[])  # type: ignore[method-assign]

    with pytest.raises(ValidationAppError, match="catalogue products"):
        service.map_products(
            uuid4(),
            uuid4(),
            ArchitectureProductMapIn(architecture_id=uuid4()),
        )


def test_map_products_persists_candidates_and_unmatched():
    db = MagicMock()
    service = ArchitectureProductMappingService(db)
    project_id = uuid4()
    user_id = uuid4()
    architecture_id = uuid4()
    wifi = _component("Enterprise WLAN", "Wi-Fi 6 campus")
    obscure = _component("Custom middleware bridge", "proprietary integration")
    product = _product()

    service.projects.get_for_user = MagicMock(return_value=SimpleNamespace(id=project_id))  # type: ignore[method-assign]
    service.architectures.get_for_project = MagicMock(  # type: ignore[method-assign]
        return_value=SimpleNamespace(id=architecture_id, candidate_key="standard"),
    )
    service.architectures.list_components = MagicMock(return_value=[wifi, obscure])  # type: ignore[method-assign]
    service.catalogues.search_products = MagicMock(return_value=[product])  # type: ignore[method-assign]
    service.catalogues.list_capabilities = MagicMock(  # type: ignore[method-assign]
        return_value=[
            SimpleNamespace(capability_code=code, capability_label=code, confidence=0.8)
            for code in product._caps
        ],
    )
    created_row = SimpleNamespace(
        id=uuid4(),
        project_id=project_id,
        architecture_id=architecture_id,
        component_id=wifi.id,
        product_id=product.id,
        fit_score=4.0,
        rationale="fit",
        status="candidate",
        preference_kind="technical",
        limitations="",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    service.mappings.replace_candidates_for_architecture = MagicMock(  # type: ignore[method-assign]
        return_value=[created_row],
    )
    service.mappings.get_products_by_ids = MagicMock(return_value={product.id: product})  # type: ignore[method-assign]

    with patch(
        "app.services.architecture_product_mapping_service.AuditService",
    ) as audit_cls:
        result = service.map_products(
            project_id,
            user_id,
            ArchitectureProductMapIn(architecture_id=architecture_id, region="APAC"),
        )

    assert result.architecture_id == architecture_id
    assert len(result.mappings) == 1
    assert result.mappings[0].product_model == "RN-AP-6E"
    assert obscure.id in result.unmatched_component_ids
    audit_cls.return_value.record.assert_called_once()
    assert (
        audit_cls.return_value.record.call_args.kwargs["action"]
        == "architectures.map_products"
    )
