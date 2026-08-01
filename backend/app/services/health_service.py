"""Health check business logic."""

from sqlalchemy import text

from app.db.session import SessionLocal
from app.schemas.common import HealthData


def check_health() -> HealthData:
    """Return API and database readiness."""
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return HealthData(status="ok", database="ok")
    except Exception:
        return HealthData(status="degraded", database="error")
