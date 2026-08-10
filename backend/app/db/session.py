"""SQLAlchemy engine and session factory."""

from collections.abc import Generator

from sqlalchemy import create_engine, event
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
    eng = create_engine(
        normalize_database_url(database_url or settings.database_url),
        pool_pre_ping=True,
    )

    @event.listens_for(eng, "connect")
    def _register_vector(dbapi_connection, connection_record) -> None:  # noqa: ARG001
        try:
            from pgvector.psycopg2 import register_vector

            register_vector(dbapi_connection)
        except Exception:
            # Unit tests / non-pgvector environments still import the app.
            pass

    return eng


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
