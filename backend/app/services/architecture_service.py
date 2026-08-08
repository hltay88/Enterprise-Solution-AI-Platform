"""Phase 3 — Architecture Recommendation from Published RKM only (ATLAS-023)."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.factory import get_ai_provider
from app.core.exceptions import NotFoundError, ValidationAppError
from app.repositories.architecture_repository import ArchitectureRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.rkm_repository import RkmRepository
from app.schemas.architecture import ArchitectureOut
from app.services.audit_service import AuditService
from app.services.knowledge_packs import build_knowledge_pack_context

logger = logging.getLogger(__name__)
PROMPT_VERSION = "architecture-1.0"


class ArchitectureService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = ProjectRepository(db)
        self.rkms = RkmRepository(db)
        self.architectures = ArchitectureRepository(db)

    def get_latest(self, project_id: UUID, user_id: UUID) -> ArchitectureOut:
        self._require_project(project_id, user_id)
        row = self.architectures.get_latest(project_id)
        if row is None:
            raise NotFoundError("No architecture recommendation found for this project")
        return self._to_out(row)

    async def generate(self, project_id: UUID, user_id: UUID) -> ArchitectureOut:
        self._require_project(project_id, user_id)
        published = self.rkms.get_published(project_id)
        if published is None:
            raise ValidationAppError(
                "Publish a Requirement Knowledge Model before generating architecture "
                "(Phase 3 consumes Published RKM only — ATLAS-023).",
            )

        rkm_payload = dict(published.payload_json or {})
        pack_context = build_knowledge_pack_context(
            _rkm_text_blob(rkm_payload),
        )
        provider = get_ai_provider()
        extraction = await provider.recommend_architecture(
            rkm_payload,
            knowledge_pack_context=pack_context,
        )
        if not isinstance(extraction, dict):
            raise ValidationAppError("AI provider returned an invalid architecture payload")

        major, minor, patch = self.architectures.next_version(project_id)
        version_label = f"{major}.{minor}.{patch}"
        summary = str(extraction.get("summary") or "").strip()
        reasoning = str(extraction.get("reasoning_summary") or "").strip()
        model = str(extraction.get("model") or extraction.get("provider") or "unknown")

        payload = {
            **extraction,
            "project_id": str(project_id),
            "rkm_id": str(published.id),
            "rkm_version_label": published.version_label,
            "version_label": version_label,
            "prompt_version": PROMPT_VERSION,
        }
        row = self.architectures.create(
            project_id=project_id,
            rkm_id=published.id,
            rkm_version_label=published.version_label,
            created_by=user_id,
            status="draft",
            version_major=major,
            version_minor=minor,
            version_patch=patch,
            summary=summary,
            reasoning_summary=reasoning,
            model=model,
            prompt_version=PROMPT_VERSION,
            payload_json=payload,
        )
        AuditService(self.db).record(
            project_id=project_id,
            user_id=user_id,
            action="architecture.generate",
            summary=f"Generated architecture v{row.version_label} from Published RKM v{published.version_label}",
            resource_type="architecture_model",
            resource_id=row.id,
            metadata={
                "version_label": row.version_label,
                "rkm_version_label": published.version_label,
                "model": model,
            },
        )
        return self._to_out(row)

    def _require_project(self, project_id: UUID, user_id: UUID):
        project = self.projects.get_for_user(project_id, user_id)
        if project is None:
            raise NotFoundError("Project not found")
        return project

    @staticmethod
    def _to_out(row) -> ArchitectureOut:
        payload = dict(row.payload_json or {})
        return ArchitectureOut(
            id=row.id,
            project_id=row.project_id,
            rkm_id=row.rkm_id,
            rkm_version_label=row.rkm_version_label,
            status=row.status,
            version_label=row.version_label,
            summary=str(payload.get("summary") or row.summary or ""),
            high_level_architecture=_str_list(payload.get("high_level_architecture")),
            logical_architecture=_str_list(payload.get("logical_architecture")),
            physical_architecture=_str_list(payload.get("physical_architecture")),
            technology_stack=_obj_list(payload.get("technology_stack")),
            solution_components=_obj_list(payload.get("solution_components")),
            design_assumptions=_str_list(payload.get("design_assumptions")),
            technical_risks=_str_list(payload.get("technical_risks")),
            architecture_decisions=_obj_list(payload.get("architecture_decisions")),
            alternatives=_obj_list(payload.get("alternatives")),
            reasoning_summary=str(
                payload.get("reasoning_summary") or row.reasoning_summary or "",
            ),
            model=row.model,
            prompt_version=row.prompt_version,
            created_at=row.created_at,
            updated_at=row.updated_at,
            payload=payload,
        )


def _str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _obj_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _rkm_text_blob(payload: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in (
        "business_objectives",
        "functional_requirements",
        "non_functional_requirements",
        "constraints",
        "dependencies",
        "risks",
        "assumptions",
    ):
        for item in payload.get(key) or []:
            if isinstance(item, dict):
                parts.append(str(item.get("title") or ""))
                parts.append(str(item.get("description") or ""))
    env = payload.get("current_environment") or {}
    if isinstance(env, dict):
        parts.append(str(env.get("summary") or ""))
    return "\n".join(parts)
