"""Sprint 3.3 Task 8 — BOM validation service wiring."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError
from app.schemas.vendor_bom import BomValidateIn
from app.services.bom_service import BomService


def test_validate_bom_persists_result_and_audits():
    db = MagicMock()
    service = BomService(db)
    project_id = uuid4()
    user_id = uuid4()
    bom_id = uuid4()
    result_id = uuid4()
    now = datetime.now(timezone.utc)

    service.projects.get_for_user = MagicMock(  # type: ignore[method-assign]
        return_value=SimpleNamespace(id=project_id),
    )
    service.boms.get_import_for_project = MagicMock(  # type: ignore[method-assign]
        return_value=SimpleNamespace(
            id=bom_id,
            project_id=project_id,
            architecture_id=None,
        ),
    )
    service.boms.list_items = MagicMock(  # type: ignore[method-assign]
        return_value=[
            SimpleNamespace(
                id=uuid4(),
                line_number=1,
                vendor="UnknownCo",
                product_model="UX-1",
                description="",
                quantity=None,
                unit=None,
                category="",
                sku=None,
                mapped_product_id=None,
                notes=None,
            ),
        ],
    )
    row = SimpleNamespace(
        id=result_id,
        bom_import_id=bom_id,
        project_id=project_id,
        status="needs_review",
        summary="needs review",
        issues=[
            {
                "code": "unknown_model",
                "severity": "warning",
                "message": "unknown",
                "bom_item_id": None,
                "line_number": 1,
                "related_component_id": None,
                "requires_human_validation": True,
            },
        ],
        created_at=now,
    )
    service.boms.create_validation_result = MagicMock(return_value=row)  # type: ignore[method-assign]

    with patch("app.services.bom_service.AuditService") as audit_cls:
        out = service.validate_bom(project_id, user_id, bom_id, BomValidateIn())

    assert out.id == result_id
    assert out.status == "needs_review"
    assert out.issues[0].code == "unknown_model"
    service.boms.create_validation_result.assert_called_once()
    assert audit_cls.return_value.record.call_args.kwargs["action"] == "bom.validate"


def test_get_validation_not_found():
    service = BomService(MagicMock())
    project_id = uuid4()
    bom_id = uuid4()
    service.projects.get_for_user = MagicMock(  # type: ignore[method-assign]
        return_value=SimpleNamespace(id=project_id),
    )
    service.boms.get_import_for_project = MagicMock(  # type: ignore[method-assign]
        return_value=SimpleNamespace(id=bom_id, project_id=project_id),
    )
    service.boms.get_latest_validation = MagicMock(return_value=None)  # type: ignore[method-assign]

    with pytest.raises(NotFoundError, match="validation"):
        service.get_validation(project_id, uuid4(), bom_id)


def test_validate_rejects_missing_architecture():
    service = BomService(MagicMock())
    project_id = uuid4()
    bom_id = uuid4()
    service.projects.get_for_user = MagicMock(  # type: ignore[method-assign]
        return_value=SimpleNamespace(id=project_id),
    )
    service.boms.get_import_for_project = MagicMock(  # type: ignore[method-assign]
        return_value=SimpleNamespace(
            id=bom_id,
            project_id=project_id,
            architecture_id=None,
        ),
    )
    service.architectures.get_for_project = MagicMock(return_value=None)  # type: ignore[method-assign]

    with pytest.raises(NotFoundError, match="Architecture"):
        service.validate_bom(
            project_id,
            uuid4(),
            bom_id,
            BomValidateIn(architecture_id=uuid4()),
        )
