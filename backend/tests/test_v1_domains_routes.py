"""Sprint 3.1 Task 11 — domain API route surface (ATLAS-031)."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.api.deps import get_approver_user, get_current_user, get_db, get_editor_user
from app.api.routes import v1_domains
from app.core.exceptions import AppError, NotFoundError, ValidationAppError
from app.core.responses import error_response
from app.schemas.domain import (
    DomainAnalysisOut,
    DomainAnalysisVersionOut,
    TraceabilityOut,
)


def _user(role: str = "editor"):
    return SimpleNamespace(id=uuid4(), role=role, email="demo@example.com")


def _analysis_out(project_id):
    now = datetime.now(timezone.utc)
    return DomainAnalysisOut(
        id=uuid4(),
        project_id=project_id,
        rkm_id=uuid4(),
        rkm_version_label="1.0.0",
        status="draft",
        version_label="1.0.0",
        summary="Domains",
        created_at=now,
        updated_at=now,
    )


def _app(user) -> FastAPI:
    app = FastAPI()

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError):
        return error_response(exc.code, exc.message, exc.status_code)

    app.include_router(v1_domains.router, prefix="/api/v1")
    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_editor_user] = lambda: user
    app.dependency_overrides[get_approver_user] = lambda: user
    return app


def test_domain_route_paths_registered():
    paths = {route.path for route in v1_domains.router.routes}
    assert "/projects/{project_id}/domains/analyze" in paths
    assert "/projects/{project_id}/domains" in paths
    assert "/projects/{project_id}/domains/versions" in paths
    assert "/projects/{project_id}/domains/{analysis_id}" in paths
    assert "/projects/{project_id}/traceability" in paths


def test_get_latest_domains_ok():
    user = _user()
    project_id = uuid4()
    out = _analysis_out(project_id)
    client = TestClient(_app(user))

    with patch(
        "app.api.routes.v1_domains.DomainIdentificationService",
    ) as service_cls:
        service_cls.return_value.get_latest.return_value = out
        response = client.get(f"/api/v1/projects/{project_id}/domains")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["id"] == str(out.id)
    assert body["data"]["version_label"] == "1.0.0"
    service_cls.return_value.get_latest.assert_called_once_with(project_id, user.id)


def test_analyze_domains_requires_editor_and_returns_201():
    user = _user("editor")
    project_id = uuid4()
    out = _analysis_out(project_id)
    client = TestClient(_app(user))

    with patch(
        "app.api.routes.v1_domains.DomainIdentificationService",
    ) as service_cls:
        service_cls.return_value.analyze = AsyncMock(return_value=out)
        response = client.post(f"/api/v1/projects/{project_id}/domains/analyze")

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["id"] == str(out.id)
    service_cls.return_value.analyze.assert_awaited_once_with(project_id, user.id)


def test_analyze_maps_validation_error():
    user = _user()
    project_id = uuid4()
    client = TestClient(_app(user))

    with patch(
        "app.api.routes.v1_domains.DomainIdentificationService",
    ) as service_cls:
        service_cls.return_value.analyze = AsyncMock(
            side_effect=ValidationAppError("Publish a Requirement Knowledge Model"),
        )
        response = client.post(f"/api/v1/projects/{project_id}/domains/analyze")

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert "Publish a Requirement Knowledge Model" in body["error"]["message"]


def test_list_versions_and_get_by_id():
    user = _user()
    project_id = uuid4()
    analysis_id = uuid4()
    now = datetime.now(timezone.utc)
    versions = [
        DomainAnalysisVersionOut(
            id=analysis_id,
            version_label="1.0.0",
            status="draft",
            created_at=now,
            domain_count=2,
        ),
    ]
    out = _analysis_out(project_id)
    out.id = analysis_id
    client = TestClient(_app(user))

    with patch(
        "app.api.routes.v1_domains.DomainIdentificationService",
    ) as service_cls:
        service_cls.return_value.list_versions.return_value = versions
        service_cls.return_value.get_by_id.return_value = out

        versions_response = client.get(f"/api/v1/projects/{project_id}/domains/versions")
        by_id_response = client.get(
            f"/api/v1/projects/{project_id}/domains/{analysis_id}",
        )

    assert versions_response.status_code == 200
    assert versions_response.json()["data"][0]["domain_count"] == 2
    assert by_id_response.status_code == 200
    assert by_id_response.json()["data"]["id"] == str(analysis_id)


def test_get_traceability_passes_optional_analysis_id():
    user = _user()
    project_id = uuid4()
    analysis_id = uuid4()
    now = datetime.now(timezone.utc)
    rows = [
        TraceabilityOut(
            id=uuid4(),
            project_id=project_id,
            analysis_id=analysis_id,
            requirement_id="REQ-1",
            domain_code="wifi",
            status="covered",
            created_at=now,
            updated_at=now,
        ),
    ]
    client = TestClient(_app(user))

    with patch(
        "app.api.routes.v1_domains.DomainIdentificationService",
    ) as service_cls:
        service_cls.return_value.get_traceability.return_value = rows
        response = client.get(
            f"/api/v1/projects/{project_id}/traceability",
            params={"analysis_id": str(analysis_id)},
        )

    assert response.status_code == 200
    assert response.json()["data"][0]["requirement_id"] == "REQ-1"
    service_cls.return_value.get_traceability.assert_called_once_with(
        project_id,
        user.id,
        analysis_id=analysis_id,
    )


def test_get_latest_maps_not_found():
    user = _user()
    project_id = uuid4()
    client = TestClient(_app(user))

    with patch(
        "app.api.routes.v1_domains.DomainIdentificationService",
    ) as service_cls:
        service_cls.return_value.get_latest.side_effect = NotFoundError(
            "No solution domain analysis found for this project",
        )
        response = client.get(f"/api/v1/projects/{project_id}/domains")

    assert response.status_code == 404
    assert response.json()["success"] is False
