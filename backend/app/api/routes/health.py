"""Health check route."""

from fastapi import APIRouter

from app.core.responses import success_response
from app.services.health_service import check_health

router = APIRouter(tags=["health"])


@router.get("/health")
def get_health() -> dict:
    """Public health endpoint including Postgres connectivity."""
    payload = check_health()
    return success_response(data=payload.model_dump())
