"""Sprint 3.3 Task 3 — vendor catalogue API routes."""

from __future__ import annotations

from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.api.deps import get_current_user, get_db, get_editor_user
from app.api.routes import v1_vendors
from app.core.exceptions import AppError, NotFoundError, ValidationAppError
from app.core.responses import error_response
from app.schemas.vendor_bom import VendorCatalogueOut, VendorCatalogueSearchOut


def _user(role: str = "editor"):
    return SimpleNamespace(id=uuid4(), role=role, email="demo@example.com")


def _app(user) -> FastAPI:
    app = FastAPI()

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError):
        return error_response(exc.code, exc.message, exc.status_code)

    app.include_router(v1_vendors.router, prefix="/api/v1")
    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_editor_user] = lambda: user
    return app


def test_vendor_route_paths_registered():
    paths = {route.path for route in v1_vendors.router.routes}
    assert "/vendors/catalogue/import" in paths
    assert "/vendors/catalogue/search" in paths
    assert "/vendors/catalogue/{catalogue_id}" in paths


def test_import_catalogue_returns_201():
    user = _user("editor")
    catalogue_id = uuid4()
    now = datetime.now(timezone.utc)
    out = VendorCatalogueOut(
        id=catalogue_id,
        name="Seed",
        source="Approved internal catalogue",
        source_date=date(2026, 1, 15),
        version_label="1.0.0",
        product_count=1,
        created_at=now,
        products=[],
    )
    client = TestClient(_app(user))

    with patch("app.api.routes.v1_vendors.VendorCatalogueService") as service_cls:
        service_cls.return_value.import_catalogue.return_value = out
        response = client.post(
            "/api/v1/vendors/catalogue/import",
            json={
                "source": "Approved internal catalogue",
                "products": [
                    {
                        "vendor": "ExampleNet",
                        "product_model": "EN-AP-6E",
                        "source": "Approved internal catalogue",
                    },
                ],
            },
        )

    assert response.status_code == 201
    assert response.json()["data"]["id"] == str(catalogue_id)
    service_cls.return_value.import_catalogue.assert_called_once()


def test_import_maps_validation_error():
    user = _user()
    client = TestClient(_app(user))

    with patch("app.api.routes.v1_vendors.VendorCatalogueService") as service_cls:
        service_cls.return_value.import_catalogue.side_effect = ValidationAppError(
            "duplicate vendor/product_model",
        )
        response = client.post(
            "/api/v1/vendors/catalogue/import",
            json={
                "source": "internal",
                "products": [
                    {"vendor": "A", "product_model": "M1", "source": "internal"},
                ],
            },
        )

    assert response.status_code == 422
    assert "duplicate" in response.json()["error"]["message"]


def test_search_and_get_catalogue():
    user = _user("viewer")
    catalogue_id = uuid4()
    now = datetime.now(timezone.utc)
    client = TestClient(_app(user))
    search = VendorCatalogueSearchOut(query="wifi", total=0, products=[])
    detail = VendorCatalogueOut(
        id=catalogue_id,
        name="Seed",
        source="internal",
        version_label="1.0.0",
        product_count=0,
        created_at=now,
    )

    with patch("app.api.routes.v1_vendors.VendorCatalogueService") as service_cls:
        service_cls.return_value.search.return_value = search
        service_cls.return_value.get_catalogue.return_value = detail
        search_response = client.get(
            "/api/v1/vendors/catalogue/search",
            params={"q": "wifi"},
        )
        get_response = client.get(f"/api/v1/vendors/catalogue/{catalogue_id}")

    assert search_response.status_code == 200
    assert search_response.json()["data"]["query"] == "wifi"
    assert get_response.status_code == 200
    assert get_response.json()["data"]["id"] == str(catalogue_id)


def test_get_catalogue_not_found():
    user = _user()
    client = TestClient(_app(user))

    with patch("app.api.routes.v1_vendors.VendorCatalogueService") as service_cls:
        service_cls.return_value.get_catalogue.side_effect = NotFoundError(
            "Vendor catalogue not found",
        )
        response = client.get(f"/api/v1/vendors/catalogue/{uuid4()}")

    assert response.status_code == 404
