"""Lightweight schema upgrades for local Sprint 1 development."""

from sqlalchemy import text

from app.db.session import engine


def ensure_schema() -> None:
    """Apply additive schema changes that init SQL may not have run yet."""
    statements = [
        """
        ALTER TABLE requirement_documents
        ADD COLUMN IF NOT EXISTS extracted_text TEXT
        """,
    ]
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
