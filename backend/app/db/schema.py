"""Lightweight schema upgrades for local Sprint 1 / 1.1 development."""

from sqlalchemy import text

from app.db.session import engine


def ensure_schema() -> None:
    """Apply additive schema changes that init SQL may not have run yet."""
    statements = [
        """
        ALTER TABLE requirement_documents
        ADD COLUMN IF NOT EXISTS extracted_text TEXT
        """,
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS account_manager TEXT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS deal_id TEXT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS deal_name TEXT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS pic_name TEXT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS pic_contact TEXT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS pic_designation TEXT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS budget_information TEXT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS request_type TEXT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS required_completion_date DATE",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS requirement_details TEXT",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS winning_probability INTEGER",
        """
        CREATE INDEX IF NOT EXISTS idx_projects_request_type
        ON projects (request_type)
        """,
    ]
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
