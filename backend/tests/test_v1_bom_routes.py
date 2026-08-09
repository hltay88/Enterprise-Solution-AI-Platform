"""Sprint 3.3 Task 7 — BOM import API routes."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.api.deps import get_current_user, get_db, get_editor_user
from app.api.routes import v1_bom
from app.core.exceptions import AppError, NotFoundError
from app.core.responses import error_response
from app.schemas.vendor_bom import BomImportOut, BomItemOut


def _user(role: str = "editor"):
    return SimpleNamespace(id=uuid4(), role=role, email="demo@example.com")


def _app(user) -> FastAPI:
    app = FastAPI()

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError):
        return error_response(exc.code, exc.message, exc.status_code)

    app.include_router(v1_bom.router, prefix="/api/v1")
    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_editor_user] = lambda: user
    return app


def test_bom_route_paths_registered():
    paths = {route.path for route in v1_bom.router.routes}
    assert "/projects/{project_id}/bom/import" in paths
    assert "/projects/{project_id}/bom" in paths
    assert "/projects/{project_id}/bom/{bom_import_id}" in paths


def test_import_bom_returns_201():
    user = _user("editor")
    project_id = uuid4()
    bom_id = uuid4()
    now = datetime.now(timezone.utc)
    out = BomImportOut(
        id=bom_id,
        project_id=project_id,
        source="Distributor CSV",
        source_filename="quote.csv",
        item_count=1,
        created_at=now,
        items=[
            BomItemOut(
                id=uuid4(),
                bom_import_id=bom_id,
                line_number=1,
                vendor="RefNet",
                product_model="RN-AP-6E",
                quantity=10,
                created_at=now,
            ),
        ],
    )
    client = TestClient(_app(user))

    with patch("app.api.routes.v1_bom.BomService") as service_cls:
        service_cls.return_value.import_bom.return_value = out
        response = client.post(
            f"/api/v1/projects/{project_id}/bom/import",
            json={
                "source": "Distributor CSV",
                "source_filename": "quote.csv",
                "items": [
                    {
                        "line_number": 1,
                        "vendor": "RefNet",
                        "product_model": "RN-AP-6E",
                        "quantity": 10,
                    },
                ],
            },
        )

    assert response.status_code == 201
    body = response.json()["data"]
    assert body["id"] == str(bom_id)
    assert body["item_count"] == 1
    service_cls.return_value.import_bom.assert_called_once()


def test_list_and_get_bom_import():
    user = _user("viewer")
    project_id = uuid4()
    bom_id = uuid4()
    now = datetime.now(timezone.utc)
    listed = BomImportOut(
        id=bom_id,
        project_id=project_id,
        source="quote",
        item_count=2,
        created_at=now,
        items=[],
    )
    detailed = BomImportOut(
        id=bom_id,
        project_id=project_id,
        source="quote",
        item_count=2,
        created_at=now,
        items=[
            BomItemOut(
                id=uuid4(),
                bom_import_id=bom_id,
                line_number=1,
                product_model="A",
                created_at=now,
            ),
        ],
    )
    client = TestClient(_app(user))

    with patch("app.api.routes.v1_bom.BomService") as service_cls:
        service_cls.return_value.list_imports.return_value = [listed]
        service_cls.return_value.get_import.return_value = detailed
        list_resp = client.get(f"/api/v1/projects/{project_id}/bom")
        get_resp = client.get(f"/api/v1/projects/{project_id}/bom/{bom_id}")

    assert list_resp.status_code == 200
    assert list_resp.json()["data"][0]["item_count"] == 2
    assert get_resp.status_code == 200
    assert len(get_resp.json()["data"]["items"]) == 1


def test_get_bom_import_not_found():
    user = _user()
    project_id = uuid4()
    client = TestClient(_app(user))

    with patch("app.api.routes.v1_bom.BomService") as service_cls:
        service_cls.return_value.get_import.side_effect = NotFoundError("BOM import not found")
        response = client.get(f"/api/v1/projects/{project_id}/bom/{uuid4()}")

    assert response.status_code == 404
