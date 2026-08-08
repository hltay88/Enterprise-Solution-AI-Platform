"""Persistence for audit_logs."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        project_id: UUID,
        user_id: UUID | None,
        action: str,
        summary: str,
        resource_type: str | None = None,
        resource_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
        commit: bool = True,
    ) -> AuditLog:
        row = AuditLog(
            project_id=project_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            summary=summary,
            metadata_json=metadata or {},
        )
        self.db.add(row)
        if commit:
            self.db.commit()
            self.db.refresh(row)
        else:
            self.db.flush()
        return row

    def list_for_project(self, project_id: UUID, *, limit: int = 100) -> list[AuditLog]:
        statement = (
            select(AuditLog)
            .where(AuditLog.project_id == project_id)
            .order_by(AuditLog.created_at.desc())
            .limit(max(1, min(limit, 500)))
        )
        return list(self.db.scalars(statement).all())
