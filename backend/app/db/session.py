"""SQLAlchemy engine and session factory."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def normalize_database_url(url: str) -> str:
    """Ensure SQLAlchemy uses the psycopg2 driver for PostgreSQL URLs."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    return url


def create_db_engine(database_url: str | None = None) -> Engine:
    return create_engine(
        normalize_database_url(database_url or settings.database_url),
        pool_pre_ping=True,
    )


engine = create_db_engine()
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
