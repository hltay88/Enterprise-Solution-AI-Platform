"""Stage F audit trail helpers."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.audit_repository import AuditRepository
from app.repositories.project_repository import ProjectRepository
from app.core.exceptions import NotFoundError
from app.schemas.audit import AuditLogOut


class AuditService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audits = AuditRepository(db)
        self.projects = ProjectRepository(db)

    def record(
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
    ) -> AuditLogOut:
        row = self.audits.create(
            project_id=project_id,
            user_id=user_id,
            action=action,
            summary=summary,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata=metadata,
            commit=commit,
        )
        return AuditLogOut.model_validate(row)

    def list_for_project(
        self,
        project_id: UUID,
        user_id: UUID,
        *,
        limit: int = 100,
    ) -> list[AuditLogOut]:
        if self.projects.get_for_user(project_id, user_id) is None:
            raise NotFoundError("Project not found")
        rows = self.audits.list_for_project(project_id, limit=limit)
        return [AuditLogOut.model_validate(row) for row in rows]
