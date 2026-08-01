"""Shared FastAPI dependencies."""

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.db.session import get_db

# Re-export for route modules: `Depends(get_db)`
__all__ = ["get_db", "DbSession"]

DbSession = Generator[Session, None, None]
