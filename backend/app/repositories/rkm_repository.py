"""Persistence for Draft Requirement Knowledge Models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.requirement_evidence import RequirementEvidence, RequirementEvidenceLink
from app.models.requirement_item import RequirementItem
from app.models.requirement_model import RequirementModel


class RkmRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_active_draft(self, project_id: UUID) -> RequirementModel | None:
        statement = (
            select(RequirementModel)
            .where(
                RequirementModel.project_id == project_id,
                RequirementModel.is_active_draft.is_(True),
            )
            .order_by(RequirementModel.updated_at.desc())
        )
        return self.db.scalars(statement).first()

    def get_by_id(self, rkm_id: UUID) -> RequirementModel | None:
        return self.db.scalars(
            select(RequirementModel).where(RequirementModel.id == rkm_id),
        ).first()

    def get_by_version_label(self, project_id: UUID, version_label: str) -> RequirementModel | None:
        return self.db.scalars(
            select(RequirementModel).where(
                RequirementModel.project_id == project_id,
                RequirementModel.version_label == version_label,
            ),
        ).first()

    def list_versions(self, project_id: UUID) -> list[RequirementModel]:
        statement = (
            select(RequirementModel)
            .where(RequirementModel.project_id == project_id)
            .order_by(
                RequirementModel.version_major.desc(),
                RequirementModel.version_minor.desc(),
                RequirementModel.version_patch.desc(),
                RequirementModel.created_at.desc(),
            )
        )
        return list(self.db.scalars(statement).all())

    def clear_active_drafts(self, project_id: UUID) -> None:
        self.db.execute(
            update(RequirementModel)
            .where(
                RequirementModel.project_id == project_id,
                RequirementModel.is_active_draft.is_(True),
            )
            .values(is_active_draft=False, updated_at=datetime.now(timezone.utc)),
        )
        self.db.commit()

    def create_draft(
        self,
        *,
        project_id: UUID,
        created_by: UUID | None,
        status: str,
        version_major: int,
        version_minor: int,
        version_patch: int,
        scores: dict[str, float],
        reasoning_summary: str | None,
        prompt_version: str | None,
        model: str | None,
        payload_json: dict[str, Any],
        requirements: list[dict[str, Any]],
        evidence: list[dict[str, Any]],
        links: list[tuple[UUID, UUID]],
    ) -> RequirementModel:
        self.clear_active_drafts(project_id)
        version_label = f"{version_major}.{version_minor}.{version_patch}"
        now = datetime.now(timezone.utc)

        rkm = RequirementModel(
            project_id=project_id,
            status=status,
            version_major=version_major,
            version_minor=version_minor,
            version_patch=version_patch,
            version_label=version_label,
            is_active_draft=True,
            confidence_score=scores.get("confidence_score", 0),
            completeness_score=scores.get("completeness_score", 0),
            consistency_score=scores.get("consistency_score", 0),
            evidence_coverage=scores.get("evidence_coverage", 0),
            reasoning_summary=reasoning_summary,
            prompt_version=prompt_version,
            model=model,
            payload_json=payload_json,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )
        self.db.add(rkm)
        self.db.flush()

        for item in requirements:
            self.db.add(
                RequirementItem(
                    id=item["id"],
                    rkm_id=rkm.id,
                    section=item["section"],
                    category=item.get("category"),
                    subcategory=item.get("subcategory"),
                    title=item["title"],
                    description=item.get("description") or "",
                    priority=item.get("priority") or "medium",
                    status=item.get("status") or "draft",
                    confidence=float(item.get("confidence") or 0),
                    sort_order=int(item.get("sort_order") or 0),
                ),
            )

        for evidence_row in evidence:
            self.db.add(
                RequirementEvidence(
                    id=evidence_row["id"],
                    rkm_id=rkm.id,
                    source_type=evidence_row["source_type"],
                    document_id=evidence_row.get("document_id"),
                    page=evidence_row.get("page"),
                    excerpt=evidence_row.get("excerpt"),
                    field_name=evidence_row.get("field_name"),
                    note=evidence_row.get("note"),
                ),
            )

        self.db.flush()
        for requirement_id, evidence_id in links:
            self.db.add(
                RequirementEvidenceLink(
                    requirement_id=requirement_id,
                    evidence_id=evidence_id,
                ),
            )

        self.db.commit()
        self.db.refresh(rkm)
        return rkm

    def next_draft_version(self, project_id: UUID) -> tuple[int, int, int]:
        versions = self.list_versions(project_id)
        if not versions:
            return 1, 0, 0
        latest = versions[0]
        # Stage C regenerates Active Draft as a new minor bump.
        return latest.version_major, latest.version_minor + 1, 0
