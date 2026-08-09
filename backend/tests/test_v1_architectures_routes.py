"""Sprint 3.2 Task 11 — plural architecture API routes (ATLAS-031)."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.api.deps import get_approver_user, get_current_user, get_db, get_editor_user
from app.api.routes import v1_architecture, v1_architectures
from app.core.exceptions import AppError, NotFoundError, ValidationAppError
from app.core.responses import error_response
from app.schemas.architecture_option import (
    ArchitectureGenerateOut,
    ArchitectureOptionOut,
    ArchitectureOptionSummaryOut,
    ArchitectureAssumptionOut,
    SolutionRiskOut,
)
from app.schemas.vendor_bom import (
    ArchitectureProductMappingOut,
    ArchitectureProductMapResultOut,
    ArchitectureReviewOut,
    VendorAnalyticsBundleOut,
    VendorCatalogueAnalyticsOut,
    VendorMappingAnalyticsOut,
)


def _user(role: str = "editor"):
    return SimpleNamespace(id=uuid4(), role=role, email="demo@example.com")


def _option_out(project_id):
    now = datetime.now(timezone.utc)
    return ArchitectureOptionOut(
        id=uuid4(),
        project_id=project_id,
        generation_id=uuid4(),
        candidate_key="standard",
        title="Standard",
        summary="Vendor-neutral",
        version_label="1.0.0",
        created_at=now,
        updated_at=now,
    )


def _app(user) -> FastAPI:
    app = FastAPI()

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError):
        return error_response(exc.code, exc.message, exc.status_code)

    app.include_router(v1_architectures.router, prefix="/api/v1")
    app.include_router(v1_architecture.router, prefix="/api/v1")
    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_editor_user] = lambda: user
    app.dependency_overrides[get_approver_user] = lambda: user
    return app


def test_architecture_route_paths_registered():
    plural = {route.path for route in v1_architectures.router.routes}
    singular = {route.path for route in v1_architecture.router.routes}
    assert "/projects/{project_id}/architectures/generate" in plural
    assert "/projects/{project_id}/architectures" in plural
    assert "/projects/{project_id}/architectures/{architecture_id}" in plural
    assert "/projects/{project_id}/architectures/{architecture_id}/map-products" in plural
    assert (
        "/projects/{project_id}/architectures/{architecture_id}/product-mappings"
        in plural
    )
    assert "/projects/{project_id}/product-mappings/{mapping_id}" in plural
    assert "/projects/{project_id}/architectures/{architecture_id}/review" in plural
    assert "/projects/{project_id}/architectures/{architecture_id}/approve" in plural
    assert "/projects/{project_id}/risks" in plural
    assert "/projects/{project_id}/assumptions" in plural
    assert "/projects/{project_id}/vendor-analytics" in plural
    assert "/projects/{project_id}/architecture" in singular
    assert "/projects/{project_id}/architecture/generate" in singular


def test_map_products_and_list_mappings():
    user = _user("editor")
    project_id = uuid4()
    architecture_id = uuid4()
    mapping_id = uuid4()
    now = datetime.now(timezone.utc)
    mapping = ArchitectureProductMappingOut(
        id=mapping_id,
        project_id=project_id,
        architecture_id=architecture_id,
        component_id=uuid4(),
        product_id=uuid4(),
        fit_score=4.0,
        rationale="capability match",
        status="candidate",
        preference_kind="technical",
        vendor="RefNet",
        product_model="RN-AP-6E",
        created_at=now,
        updated_at=now,
    )
    map_result = ArchitectureProductMapResultOut(
        architecture_id=architecture_id,
        mappings=[mapping],
        unmatched_component_ids=[],
    )
    client = TestClient(_app(user))

    with patch(
        "app.api.routes.v1_architectures.ArchitectureProductMappingService",
    ) as service_cls:
        service_cls.return_value.map_products.return_value = map_result
        service_cls.return_value.list_mappings.return_value = [mapping]
        service_cls.return_value.update_mapping.return_value = mapping.model_copy(
            update={"status": "selected"},
        )
        map_response = client.post(
            f"/api/v1/projects/{project_id}/architectures/{architecture_id}/map-products",
            json={"region": "APAC"},
        )
        list_response = client.get(
            f"/api/v1/projects/{project_id}/architectures/{architecture_id}/product-mappings",
        )
        patch_response = client.patch(
            f"/api/v1/projects/{project_id}/product-mappings/{mapping_id}",
            json={"status": "selected"},
        )

    assert map_response.status_code == 201
    assert map_response.json()["data"]["architecture_id"] == str(architecture_id)
    assert list_response.status_code == 200
    assert list_response.json()["data"][0]["product_model"] == "RN-AP-6E"
    assert patch_response.status_code == 200
    service_cls.return_value.map_products.assert_called_once()
    called_body = service_cls.return_value.map_products.call_args.args[2]
    assert called_body.architecture_id == architecture_id


def test_map_products_maps_validation_error():
    user = _user()
    project_id = uuid4()
    architecture_id = uuid4()
    client = TestClient(_app(user))

    with patch(
        "app.api.routes.v1_architectures.ArchitectureProductMappingService",
    ) as service_cls:
        service_cls.return_value.map_products.side_effect = ValidationAppError(
            "No catalogue products available",
        )
        response = client.post(
            f"/api/v1/projects/{project_id}/architectures/{architecture_id}/map-products",
        )

    assert response.status_code == 422
    assert "catalogue" in response.json()["error"]["message"]


def test_list_and_get_architecture_ok():
    user = _user()
    project_id = uuid4()
    option = _option_out(project_id)
    summary = ArchitectureOptionSummaryOut(
        id=option.id,
        project_id=project_id,
        generation_id=option.generation_id,
        candidate_key="standard",
        title="Standard",
        version_label="1.0.0",
        created_at=option.created_at,
    )
    client = TestClient(_app(user))

    with patch(
        "app.api.routes.v1_architectures.ArchitectureGenerationService",
    ) as service_cls:
        service_cls.return_value.list_options.return_value = [summary]
        service_cls.return_value.get_by_id.return_value = option
        list_response = client.get(f"/api/v1/projects/{project_id}/architectures")
        get_response = client.get(
            f"/api/v1/projects/{project_id}/architectures/{option.id}",
        )

    assert list_response.status_code == 200
    assert list_response.json()["data"][0]["candidate_key"] == "standard"
    assert get_response.status_code == 200
    assert get_response.json()["data"]["id"] == str(option.id)


def test_generate_architectures_returns_201():
    user = _user("editor")
    project_id = uuid4()
    option = _option_out(project_id)
    out = ArchitectureGenerateOut(
        generation_id=option.generation_id,
        version_label="1.0.0",
        architectures=[option],
    )
    client = TestClient(_app(user))

    with patch(
        "app.api.routes.v1_architectures.ArchitectureGenerationService",
    ) as service_cls:
        service_cls.return_value.generate = AsyncMock(return_value=out)
        response = client.post(f"/api/v1/projects/{project_id}/architectures/generate")

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["version_label"] == "1.0.0"
    assert len(body["data"]["architectures"]) == 1
    service_cls.return_value.generate.assert_awaited_once_with(project_id, user.id)


def test_generate_maps_domain_gate_validation():
    user = _user()
    project_id = uuid4()
    client = TestClient(_app(user))

    with patch(
        "app.api.routes.v1_architectures.ArchitectureGenerationService",
    ) as service_cls:
        service_cls.return_value.generate = AsyncMock(
            side_effect=ValidationAppError(
                "Run solution domain identification before generating",
            ),
        )
        response = client.post(f"/api/v1/projects/{project_id}/architectures/generate")

    assert response.status_code == 422
    assert "domain identification" in response.json()["error"]["message"]


def test_list_risks_and_assumptions_pass_architecture_id():
    user = _user()
    project_id = uuid4()
    architecture_id = uuid4()
    client = TestClient(_app(user))
    risks = [
        SolutionRiskOut(
            id=uuid4(),
            architecture_id=architecture_id,
            description="Survey delay",
        ),
    ]
    assumptions = [
        ArchitectureAssumptionOut(
            id=uuid4(),
            architecture_id=architecture_id,
            statement="Vendor-neutral for now",
        ),
    ]

    with patch(
        "app.api.routes.v1_architectures.ArchitectureGenerationService",
    ) as service_cls:
        service_cls.return_value.list_risks.return_value = risks
        service_cls.return_value.list_assumptions.return_value = assumptions
        risks_response = client.get(
            f"/api/v1/projects/{project_id}/risks",
            params={"architecture_id": str(architecture_id)},
        )
        assumptions_response = client.get(
            f"/api/v1/projects/{project_id}/assumptions",
            params={"architecture_id": str(architecture_id)},
        )

    assert risks_response.status_code == 200
    assert risks_response.json()["data"][0]["description"] == "Survey delay"
    assert assumptions_response.status_code == 200
    assert "Vendor-neutral" in assumptions_response.json()["data"][0]["statement"]
    service_cls.return_value.list_risks.assert_called_once_with(
        project_id,
        user.id,
        architecture_id=architecture_id,
    )
    service_cls.return_value.list_assumptions.assert_called_once_with(
        project_id,
        user.id,
        architecture_id=architecture_id,
    )


def test_singular_mvp_aliases_call_generation_service():
    user = _user("editor")
    project_id = uuid4()
    option = _option_out(project_id)
    out = ArchitectureGenerateOut(
        generation_id=option.generation_id,
        version_label="1.0.0",
        architectures=[option],
    )
    client = TestClient(_app(user))

    with patch(
        "app.api.routes.v1_architecture.ArchitectureGenerationService",
    ) as service_cls:
        service_cls.return_value.get_latest.return_value = option
        service_cls.return_value.generate = AsyncMock(return_value=out)
        get_response = client.get(f"/api/v1/projects/{project_id}/architecture")
        post_response = client.post(
            f"/api/v1/projects/{project_id}/architecture/generate",
        )

    assert get_response.status_code == 200
    assert get_response.json()["data"]["candidate_key"] == "standard"
    assert post_response.status_code == 201
    assert post_response.json()["data"]["generation_id"] == str(option.generation_id)


def test_get_architecture_maps_not_found():
    user = _user()
    project_id = uuid4()
    client = TestClient(_app(user))

    with patch(
        "app.api.routes.v1_architectures.ArchitectureGenerationService",
    ) as service_cls:
        service_cls.return_value.get_by_id.side_effect = NotFoundError(
            "Architecture option not found",
        )
        response = client.get(f"/api/v1/projects/{project_id}/architectures/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["success"] is False


def test_review_architecture_returns_200():
    user = _user("editor")
    project_id = uuid4()
    architecture_id = uuid4()
    now = datetime.now(timezone.utc)
    out = ArchitectureReviewOut(
        id=architecture_id,
        project_id=project_id,
        status="under_review",
        reviewed_at=now,
        reviewed_by=user.id,
        review_note="ok",
        uncovered_critical_count=0,
    )
    client = TestClient(_app(user))

    with patch(
        "app.api.routes.v1_architectures.ArchitectureReviewService",
    ) as service_cls:
        service_cls.return_value.review.return_value = out
        response = client.post(
            f"/api/v1/projects/{project_id}/architectures/{architecture_id}/review",
            json={"note": "ok"},
        )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "under_review"
    service_cls.return_value.review.assert_called_once()


def test_approve_architecture_returns_200():
    user = _user("approver")
    project_id = uuid4()
    architecture_id = uuid4()
    now = datetime.now(timezone.utc)
    out = ArchitectureReviewOut(
        id=architecture_id,
        project_id=project_id,
        status="complete",
        reviewed_at=now,
        reviewed_by=user.id,
        approved_at=now,
        approved_by=user.id,
        approval_note="ship",
        uncovered_critical_count=0,
    )
    client = TestClient(_app(user))

    with patch(
        "app.api.routes.v1_architectures.ArchitectureReviewService",
    ) as service_cls:
        service_cls.return_value.approve.return_value = out
        response = client.post(
            f"/api/v1/projects/{project_id}/architectures/{architecture_id}/approve",
            json={"note": "ship"},
        )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "complete"
    service_cls.return_value.approve.assert_called_once()


def test_approve_architecture_maps_validation_error():
    user = _user("approver")
    project_id = uuid4()
    architecture_id = uuid4()
    client = TestClient(_app(user))

    with patch(
        "app.api.routes.v1_architectures.ArchitectureReviewService",
    ) as service_cls:
        service_cls.return_value.approve.side_effect = ValidationAppError(
            "Cannot Complete architecture: 2 critical/high requirement(s) remain uncovered",
        )
        response = client.post(
            f"/api/v1/projects/{project_id}/architectures/{architecture_id}/approve",
            json={},
        )

    assert response.status_code == 422
    assert "Cannot Complete" in response.json()["error"]["message"]


def test_project_vendor_analytics_returns_200():
    user = _user("viewer")
    project_id = uuid4()
    catalogue_id = uuid4()
    out = VendorAnalyticsBundleOut(
        catalogue=VendorCatalogueAnalyticsOut(
            catalogue_id=catalogue_id,
            catalogue_name="Seed",
            product_count=2,
        ),
        mappings=VendorMappingAnalyticsOut(
            project_id=project_id,
            mapping_count=0,
        ),
    )
    client = TestClient(_app(user))

    with patch(
        "app.api.routes.v1_architectures.VendorAnalyticsService",
    ) as service_cls:
        service_cls.return_value.project_bundle.return_value = out
        response = client.get(f"/api/v1/projects/{project_id}/vendor-analytics")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["catalogue"]["product_count"] == 2
    assert data["mappings"]["project_id"] == str(project_id)
    service_cls.return_value.project_bundle.assert_called_once_with(
        project_id,
        user.id,
        architecture_id=None,
        catalogue_id=None,
    )
