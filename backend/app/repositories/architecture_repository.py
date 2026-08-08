"""Persistence for architecture_models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.architecture_model import ArchitectureModel


class ArchitectureRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_latest(self, project_id: UUID) -> ArchitectureModel | None:
        statement = (
            select(ArchitectureModel)
            .where(ArchitectureModel.project_id == project_id)
            .order_by(
                ArchitectureModel.version_major.desc(),
                ArchitectureModel.version_minor.desc(),
                ArchitectureModel.version_patch.desc(),
                ArchitectureModel.created_at.desc(),
            )
        )
        return self.db.scalars(statement).first()

    def next_version(self, project_id: UUID) -> tuple[int, int, int]:
        latest = self.get_latest(project_id)
        if latest is None:
            return 1, 0, 0
        return latest.version_major, latest.version_minor + 1, 0

    def create(
        self,
        *,
        project_id: UUID,
        rkm_id: UUID | None,
        rkm_version_label: str | None,
        created_by: UUID | None,
        status: str,
        version_major: int,
        version_minor: int,
        version_patch: int,
        summary: str | None,
        reasoning_summary: str | None,
        model: str | None,
        prompt_version: str | None,
        payload_json: dict[str, Any],
    ) -> ArchitectureModel:
        now = datetime.now(timezone.utc)
        version_label = f"{version_major}.{version_minor}.{version_patch}"
        row = ArchitectureModel(
            project_id=project_id,
            rkm_id=rkm_id,
            rkm_version_label=rkm_version_label,
            status=status,
            version_label=version_label,
            version_major=version_major,
            version_minor=version_minor,
            version_patch=version_patch,
            summary=summary,
            reasoning_summary=reasoning_summary,
            model=model,
            prompt_version=prompt_version,
            payload_json=payload_json,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row
