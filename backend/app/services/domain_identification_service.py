"""Phase 3 Sprint 3.1 Task 7 — Solution Domain Identification orchestration.

Published RKM → Phase 3 packs → AI → validate → persist → audit (ATLAS-023).
Traceability coverage matrix is Task 8; this service persists the domain model
tree (domains, requirement links, dependencies, open questions).
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.ai.common import normalize_domain_identification
from app.ai.factory import get_ai_provider
from app.core.exceptions import AppError, NotFoundError, ValidationAppError
from app.repositories.domain_repository import DomainRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.rkm_repository import RkmRepository
from app.schemas.domain import (
    DomainAnalysisOut,
    DomainAnalysisVersionOut,
    DomainDependencyOut,
    DomainOpenQuestionOut,
    SolutionDomainOut,
    TraceabilityOut,
    validate_domain_ai_extraction,
)
from app.services.audit_service import AuditService
from app.services.domain_confidence import apply_confidence_to_extraction
from app.services.domain_enrichment import (
    enrich_domains_and_questions,
    preprocess_domain_extraction,
)
from app.services.domain_traceability import (
    build_requirement_domain_traceability,
    count_uncovered_critical,
    extract_rkm_requirements,
)
from app.services.phase3_knowledge_packs import build_domain_pack_context, pack_version

logger = logging.getLogger(__name__)
PROMPT_VERSION = "domain-1.0"


class DomainIdentificationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = ProjectRepository(db)
        self.rkms = RkmRepository(db)
        self.domains = DomainRepository(db)

    def get_latest(self, project_id: UUID, user_id: UUID) -> DomainAnalysisOut:
        self._require_project(project_id, user_id)
        row = self.domains.get_latest(project_id)
        if row is None:
            raise NotFoundError("No solution domain analysis found for this project")
        return self._to_out(row)

    def get_by_id(
        self,
        project_id: UUID,
        analysis_id: UUID,
        user_id: UUID,
    ) -> DomainAnalysisOut:
        self._require_project(project_id, user_id)
        row = self.domains.get_for_project(analysis_id, project_id)
        if row is None:
            raise NotFoundError("Solution domain analysis not found")
        return self._to_out(row)

    def list_versions(
        self,
        project_id: UUID,
        user_id: UUID,
    ) -> list[DomainAnalysisVersionOut]:
        self._require_project(project_id, user_id)
        rows = self.domains.list_versions(project_id)
        return [
            DomainAnalysisVersionOut(
                id=row.id,
                version_label=row.version_label,
                status=row.status,
                rkm_id=row.rkm_id,
                rkm_version_label=row.rkm_version_label,
                created_at=row.created_at,
                domain_count=self.domains.count_domains(row.id),
            )
            for row in rows
        ]

    def get_traceability(
        self,
        project_id: UUID,
        user_id: UUID,
        analysis_id: UUID | None = None,
    ) -> list[TraceabilityOut]:
        """Return domain-stage traceability for latest or a specific analysis."""
        self._require_project(project_id, user_id)
        if analysis_id is not None:
            row = self.domains.get_for_project(analysis_id, project_id)
            if row is None:
                raise NotFoundError("Solution domain analysis not found")
        else:
            row = self.domains.get_latest(project_id)
            if row is None:
                raise NotFoundError("No solution domain analysis found for this project")

        domain_rows = self.domains.list_domains(row.id)
        code_by_id = {item.id: item.domain_code for item in domain_rows}
        return [
            TraceabilityOut(
                id=item.id,
                project_id=item.project_id,
                analysis_id=item.analysis_id,
                requirement_id=item.requirement_id,
                domain_id=item.domain_id,
                domain_code=code_by_id.get(item.domain_id) if item.domain_id else None,
                architecture_id=item.architecture_id,
                component_id=item.component_id,
                decision_id=item.decision_id,
                evidence=item.evidence,
                status=item.status,  # type: ignore[arg-type]
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
            for item in self.domains.list_traceability(analysis_id=row.id)
        ]

    async def analyze(self, project_id: UUID, user_id: UUID) -> DomainAnalysisOut:
        self._require_project(project_id, user_id)
        published = self.rkms.get_published(project_id)
        if published is None:
            raise ValidationAppError(
                "Publish a Requirement Knowledge Model before analyzing solution "
                "domains (Phase 3 consumes Published RKM only — ATLAS-023).",
            )

        rkm_payload = dict(published.payload_json or {})
        if not _rkm_has_requirements(rkm_payload):
            raise ValidationAppError(
                "Published RKM has no requirements to analyze for solution domains.",
            )

        pack_context = build_domain_pack_context(_rkm_text_blob(rkm_payload))
        knowledge_pack_version = pack_version()
        provider = get_ai_provider()
        try:
            extraction = await provider.identify_solution_domains(
                rkm_payload,
                knowledge_pack_context=pack_context,
            )
        except AppError:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.exception("Domain identification AI call failed")
            raise ValidationAppError(
                f"Domain identification failed: {exc}",
            ) from exc

        if not isinstance(extraction, dict):
            raise ValidationAppError("AI provider returned an invalid domain payload")

        try:
            # Drop unknown dependency codes before strict schema validation.
            preprocessed = preprocess_domain_extraction(extraction)
            normalized = normalize_domain_identification(preprocessed)
            validated = validate_domain_ai_extraction(normalized)
        except (ValidationError, ValueError, AppError) as exc:
            raise ValidationAppError(
                f"AI domain identification payload failed validation: {exc}",
            ) from exc

        rkm_requirements = extract_rkm_requirements(rkm_payload)
        # Draft coverage first so enrichment can ask about uncovered criticals.
        draft_traceability = build_requirement_domain_traceability(
            rkm_requirements,
            list(validated.domains),
        )
        validated = enrich_domains_and_questions(
            validated,
            requirements=rkm_requirements,
            traceability=draft_traceability,
            rkm_text=_rkm_text_blob(rkm_payload),
        )
        validated = apply_confidence_to_extraction(validated)
        # Rebuild coverage after dependency sanitization / domain refinements.
        traceability_rows = build_requirement_domain_traceability(
            rkm_requirements,
            list(validated.domains),
        )
        uncovered_critical = count_uncovered_critical(traceability_rows, rkm_requirements)

        major, minor, patch = self.domains.next_version(project_id)
        model_name = str(
            normalized.get("model")
            or normalized.get("provider")
            or validated.model
            or validated.provider
            or "unknown",
        )
        payload = {
            **validated.model_dump(mode="json"),
            "project_id": str(project_id),
            "rkm_id": str(published.id),
            "rkm_version_label": published.version_label,
            "prompt_version": PROMPT_VERSION,
            "knowledge_pack_version": knowledge_pack_version,
            "traceability_summary": {
                "row_count": len(traceability_rows),
                "uncovered_critical_or_high": uncovered_critical,
            },
        }

        domain_rows = [_domain_tree_item(item, index) for index, item in enumerate(validated.domains)]
        analysis_questions = [
            {
                "question": question.question,
                "affects_selection": question.affects_selection,
                "related_requirement_ids": list(question.related_requirement_ids),
                "domain_code": question.domain_code,
            }
            for question in validated.open_questions
        ]

        try:
            row = self.domains.create_analysis_tree(
                project_id=project_id,
                rkm_id=published.id,
                rkm_version_label=published.version_label,
                created_by=user_id,
                status="draft",
                version_major=major,
                version_minor=minor,
                version_patch=patch,
                summary=validated.summary or None,
                model=model_name,
                prompt_version=PROMPT_VERSION,
                knowledge_pack_version=knowledge_pack_version,
                payload_json=payload,
                domains=domain_rows,
                analysis_open_questions=analysis_questions,
                traceability=traceability_rows,
            )
        except ValueError as exc:
            raise ValidationAppError(str(exc)) from exc

        AuditService(self.db).record(
            project_id=project_id,
            user_id=user_id,
            action="domain.analyze",
            summary=(
                f"Analyzed solution domains v{row.version_label} "
                f"from Published RKM v{published.version_label}"
            ),
            resource_type="domain_analysis",
            resource_id=row.id,
            metadata={
                "version_label": row.version_label,
                "rkm_version_label": published.version_label,
                "model": model_name,
                "prompt_version": PROMPT_VERSION,
                "knowledge_pack_version": knowledge_pack_version,
                "domain_count": len(domain_rows),
                "traceability_count": len(traceability_rows),
                "uncovered_critical_or_high": uncovered_critical,
            },
        )
        return self._to_out(row)

    def _require_project(self, project_id: UUID, user_id: UUID):
        project = self.projects.get_for_user(project_id, user_id)
        if project is None:
            raise NotFoundError("Project not found")
        return project

    def _to_out(self, row) -> DomainAnalysisOut:
        domain_rows = self.domains.list_domains(row.id)
        domain_ids = [item.id for item in domain_rows]
        links = self.domains.list_requirement_links(domain_ids)
        deps = self.domains.list_dependencies(domain_ids)
        questions = self.domains.list_open_questions(row.id)
        trace_rows = self.domains.list_traceability(analysis_id=row.id)

        links_by_domain: dict[UUID, list[str]] = {}
        for link in links:
            links_by_domain.setdefault(link.domain_id, []).append(link.requirement_id)

        deps_by_domain: dict[UUID, list[DomainDependencyOut]] = {}
        for dep in deps:
            deps_by_domain.setdefault(dep.domain_id, []).append(
                DomainDependencyOut(
                    id=dep.id,
                    depends_on_domain_code=dep.depends_on_domain_code,
                    dependency_kind=dep.dependency_kind,  # type: ignore[arg-type]
                    reason=dep.reason or "",
                ),
            )

        code_by_id = {item.id: item.domain_code for item in domain_rows}
        questions_by_domain: dict[UUID, list[DomainOpenQuestionOut]] = {}
        analysis_questions: list[DomainOpenQuestionOut] = []
        for question in questions:
            out = DomainOpenQuestionOut(
                id=question.id,
                domain_id=question.domain_id,
                domain_code=(
                    code_by_id.get(question.domain_id) if question.domain_id else None
                ),
                question=question.question,
                affects_selection=question.affects_selection,
                related_requirement_ids=[
                    str(item) for item in (question.related_requirement_ids or [])
                ],
            )
            if question.domain_id is None:
                analysis_questions.append(out)
            else:
                questions_by_domain.setdefault(question.domain_id, []).append(out)

        domains_out = [
            SolutionDomainOut(
                id=item.id,
                domain_code=item.domain_code,
                name=item.name,
                reason=item.reason or "",
                confidence=float(item.confidence or 0),
                mandatory_or_optional=item.mandatory_or_optional,  # type: ignore[arg-type]
                selection_source=item.selection_source,  # type: ignore[arg-type]
                sort_order=item.sort_order,
                supporting_requirements=links_by_domain.get(item.id, []),
                dependencies=deps_by_domain.get(item.id, []),
                open_questions=questions_by_domain.get(item.id, []),
            )
            for item in domain_rows
        ]

        payload = dict(row.payload_json or {})
        return DomainAnalysisOut(
            id=row.id,
            project_id=row.project_id,
            rkm_id=row.rkm_id,
            rkm_version_label=row.rkm_version_label,
            status=row.status,
            version_label=row.version_label,
            summary=str(payload.get("summary") or row.summary or ""),
            reasoning_summary=str(payload.get("reasoning_summary") or ""),
            model=row.model,
            prompt_version=row.prompt_version,
            knowledge_pack_version=row.knowledge_pack_version,
            domains=domains_out,
            open_questions=analysis_questions,
            traceability=[
                TraceabilityOut(
                    id=item.id,
                    project_id=item.project_id,
                    analysis_id=item.analysis_id,
                    requirement_id=item.requirement_id,
                    domain_id=item.domain_id,
                    domain_code=code_by_id.get(item.domain_id) if item.domain_id else None,
                    architecture_id=item.architecture_id,
                    component_id=item.component_id,
                    decision_id=item.decision_id,
                    evidence=item.evidence,
                    status=item.status,  # type: ignore[arg-type]
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                )
                for item in trace_rows
            ],
            created_at=row.created_at,
            updated_at=row.updated_at,
            payload=payload,
        )


def _domain_tree_item(item: Any, index: int) -> dict[str, Any]:
    return {
        "domain_code": item.domain_code,
        "name": item.name or item.domain_code,
        "reason": item.reason,
        "confidence": item.confidence,
        "mandatory_or_optional": item.mandatory_or_optional,
        "selection_source": item.selection_source,
        "sort_order": index,
        "supporting_requirements": list(item.supporting_requirements),
        "dependencies": [
            {
                "depends_on_domain_code": dep.depends_on_domain_code,
                "dependency_kind": dep.dependency_kind,
                "reason": dep.reason,
            }
            for dep in item.dependencies
        ],
        "open_questions": [
            {
                "question": question.question,
                "affects_selection": question.affects_selection,
                "related_requirement_ids": list(question.related_requirement_ids),
            }
            for question in item.open_questions
        ],
    }


def _rkm_has_requirements(payload: dict[str, Any]) -> bool:
    for key in (
        "business_objectives",
        "functional_requirements",
        "non_functional_requirements",
        "constraints",
        "dependencies",
        "risks",
        "assumptions",
    ):
        items = payload.get(key) or []
        if isinstance(items, list) and any(isinstance(item, dict) for item in items):
            return True
    return False


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
