"""Health check route."""

from fastapi import APIRouter

from app.core.responses import success_response
from app.schemas.common import HealthData

router = APIRouter(tags=["health"])


@router.get("/health")
def get_health() -> dict:
    """Public health endpoint. Database status is wired in the next Phase B task."""
    payload = HealthData(status="ok", database="not_configured")
    return success_response(data=payload.model_dump())
