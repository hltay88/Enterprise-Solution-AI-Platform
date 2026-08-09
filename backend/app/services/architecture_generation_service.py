"""Phase 3 Sprint 3.2 Task 6 — multi-candidate architecture generation.

Published RKM + latest domain analysis → pattern packs → AI candidates →
validate → persist normalized tree → audit. MVP ``ArchitectureService``
(singular ``architecture_models``) is unchanged (ATLAS-034).
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.ai.common import normalize_architecture_candidates
from app.ai.factory import get_ai_provider
from app.core.exceptions import AppError, NotFoundError, ValidationAppError
from app.repositories.architecture_option_repository import ArchitectureOptionRepository
from app.repositories.domain_repository import DomainRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.rkm_repository import RkmRepository
from app.schemas.architecture_option import (
    ArchitectureAssumptionOut,
    ArchitectureComponentOut,
    ArchitectureGenerateOut,
    ArchitectureOptionOut,
    ArchitectureOptionSummaryOut,
    ArchitectureRelationshipOut,
    CapacityNoteOut,
    DesignDecisionOut,
    SolutionRiskOut,
    SolutionScoreOut,
    validate_architecture_ai_extraction,
)
from app.services.architecture_capacity import (
    enrich_architecture_capacity,
    preprocess_capacity_in_extraction,
)
from app.services.architecture_risks import (
    enrich_architecture_risks_assumptions,
    preprocess_risks_assumptions_in_extraction,
)
from app.services.audit_service import AuditService
from app.services.domain_traceability import extract_rkm_requirements
from app.services.phase3_domain_catalog import catalog_version
from app.services.phase3_pattern_catalog import build_pattern_pack_context

logger = logging.getLogger(__name__)
PROMPT_VERSION = "architecture-2.0"


class ArchitectureGenerationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = ProjectRepository(db)
        self.rkms = RkmRepository(db)
        self.domains = DomainRepository(db)
        self.architectures = ArchitectureOptionRepository(db)

    def list_options(
        self,
        project_id: UUID,
        user_id: UUID,
    ) -> list[ArchitectureOptionSummaryOut]:
        self._require_project(project_id, user_id)
        return [self._to_summary(row) for row in self.architectures.list_for_project(project_id)]

    def get_latest(self, project_id: UUID, user_id: UUID) -> ArchitectureOptionOut:
        self._require_project(project_id, user_id)
        row = self.architectures.get_latest(project_id)
        if row is None:
            raise NotFoundError("No architecture options found for this project")
        return self._to_out(row)

    def get_by_id(
        self,
        project_id: UUID,
        architecture_id: UUID,
        user_id: UUID,
    ) -> ArchitectureOptionOut:
        self._require_project(project_id, user_id)
        row = self.architectures.get_for_project(architecture_id, project_id)
        if row is None:
            raise NotFoundError("Architecture option not found")
        return self._to_out(row)

    def list_generation(
        self,
        project_id: UUID,
        generation_id: UUID,
        user_id: UUID,
    ) -> ArchitectureGenerateOut:
        self._require_project(project_id, user_id)
        rows = self.architectures.list_generation(project_id, generation_id)
        if not rows:
            raise NotFoundError("Architecture generation not found")
        outs = [self._to_out(row) for row in rows]
        return ArchitectureGenerateOut(
            generation_id=generation_id,
            version_label=outs[0].version_label,
            architectures=outs,
        )

    async def generate(self, project_id: UUID, user_id: UUID) -> ArchitectureGenerateOut:
        self._require_project(project_id, user_id)
        published = self.rkms.get_published(project_id)
        if published is None:
            raise ValidationAppError(
                "Publish a Requirement Knowledge Model before generating "
                "architecture candidates (Phase 3 consumes Published RKM only — ATLAS-023).",
            )

        domain_analysis = self.domains.get_latest(project_id)
        if domain_analysis is None:
            raise ValidationAppError(
                "Run solution domain identification before generating architecture "
                "candidates (hard gate — latest domain analysis required).",
            )

        rkm_payload = dict(published.payload_json or {})
        domain_rows = self.domains.list_domains(domain_analysis.id)
        domain_codes = [row.domain_code for row in domain_rows]
        domain_context = _build_domain_context(domain_analysis, domain_rows)
        pattern_context = build_pattern_pack_context(
            _rkm_text_blob(rkm_payload),
            domain_context,
            domain_codes=domain_codes,
        )
        knowledge_pack_version = catalog_version()

        provider = get_ai_provider()
        try:
            extraction = await provider.recommend_architectures(
                rkm_payload,
                domain_context=domain_context,
                pattern_context=pattern_context,
            )
        except AppError:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.exception("Architecture candidates AI call failed")
            raise ValidationAppError(
                f"Architecture candidate generation failed: {exc}",
            ) from exc

        if not isinstance(extraction, dict):
            raise ValidationAppError(
                "AI provider returned an invalid architecture candidates payload",
            )

        try:
            # Task 7/8: sanitize capacity + risks/assumptions before validation.
            requirements = extract_rkm_requirements(rkm_payload)
            preprocessed = preprocess_capacity_in_extraction(extraction)
            preprocessed = preprocess_risks_assumptions_in_extraction(preprocessed)
            normalized = normalize_architecture_candidates(preprocessed)
            validated = validate_architecture_ai_extraction(normalized)
            validated = enrich_architecture_capacity(
                validated,
                domain_codes=domain_codes,
                rkm_text=_rkm_text_blob(rkm_payload),
                requirements=requirements,
            )
            validated = enrich_architecture_risks_assumptions(
                validated,
                domain_codes=domain_codes,
                rkm_payload=rkm_payload,
                requirements=requirements,
            )
        except (ValidationError, ValueError, AppError) as exc:
            raise ValidationAppError(
                f"AI architecture candidates payload failed validation: {exc}",
            ) from exc

        major, minor, patch = self.architectures.next_version(project_id)
        model_name = str(
            normalized.get("model")
            or normalized.get("provider")
            or validated.model
            or validated.provider
            or "unknown",
        )

        tree_items: list[dict[str, Any]] = []
        for candidate in validated.architectures:
            item = candidate.model_dump(mode="json")
            scores = list(candidate.scores)
            overall = _weighted_overall_score(
                [
                    {"weight": score.weight, "score": score.score}
                    for score in scores
                ],
            )
            item["overall_score"] = overall
            item["status"] = "draft"
            item["payload_json"] = {
                "summary": candidate.summary,
                "reasoning_summary": candidate.reasoning_summary,
                "high_level_architecture": list(candidate.high_level_architecture),
                "logical_architecture": list(candidate.logical_architecture),
                "physical_architecture": list(candidate.physical_architecture),
                "technology_stack": list(candidate.technology_stack),
                "advantages": list(candidate.advantages),
                "disadvantages": list(candidate.disadvantages),
                "extraction_summary": validated.summary,
                "extraction_reasoning_summary": validated.reasoning_summary,
            }
            tree_items.append(item)

        try:
            options = self.architectures.create_generation_tree(
                project_id=project_id,
                rkm_id=published.id,
                rkm_version_label=published.version_label,
                domain_analysis_id=domain_analysis.id,
                created_by=user_id,
                version_major=major,
                version_minor=minor,
                version_patch=patch,
                model=model_name,
                prompt_version=PROMPT_VERSION,
                knowledge_pack_version=knowledge_pack_version,
                architectures=tree_items,
            )
        except ValueError as exc:
            raise ValidationAppError(str(exc)) from exc

        generation_id = options[0].generation_id
        version_label = options[0].version_label
        outs = [self._to_out(row) for row in options]

        AuditService(self.db).record(
            project_id=project_id,
            user_id=user_id,
            action="architectures.generate",
            summary=(
                f"Generated {len(options)} architecture candidate(s) v{version_label} "
                f"from Published RKM v{published.version_label} "
                f"and domain analysis v{domain_analysis.version_label}"
            ),
            resource_type="architecture_option",
            resource_id=options[0].id,
            metadata={
                "generation_id": str(generation_id),
                "version_label": version_label,
                "rkm_version_label": published.version_label,
                "domain_analysis_id": str(domain_analysis.id),
                "domain_analysis_version_label": domain_analysis.version_label,
                "model": model_name,
                "prompt_version": PROMPT_VERSION,
                "knowledge_pack_version": knowledge_pack_version,
                "candidate_count": len(options),
                "candidate_keys": [row.candidate_key for row in options],
            },
        )
        return ArchitectureGenerateOut(
            generation_id=generation_id,
            version_label=version_label,
            architectures=outs,
        )

    def _require_project(self, project_id: UUID, user_id: UUID):
        project = self.projects.get_for_user(project_id, user_id)
        if project is None:
            raise NotFoundError("Project not found")
        return project

    def _to_summary(self, row) -> ArchitectureOptionSummaryOut:
        return ArchitectureOptionSummaryOut(
            id=row.id,
            project_id=row.project_id,
            generation_id=row.generation_id,
            candidate_key=row.candidate_key,
            title=row.title or row.candidate_key,
            summary=str(row.summary or ""),
            status=row.status,
            confidence=float(row.confidence or 0),
            overall_score=row.overall_score,
            pattern_codes=[str(code) for code in (row.pattern_codes or [])],
            version_label=row.version_label,
            rkm_version_label=row.rkm_version_label,
            domain_analysis_id=row.domain_analysis_id,
            created_at=row.created_at,
        )

    def _to_out(self, row) -> ArchitectureOptionOut:
        payload = dict(row.payload_json or {})
        components = self.architectures.list_components(row.id)
        relationships = self.architectures.list_relationships(row.id)
        decisions = self.architectures.list_decisions(row.id)
        assumptions = self.architectures.list_assumptions(row.id)
        risks = self.architectures.list_risks(architecture_id=row.id)
        scores = self.architectures.list_scores(row.id)
        capacity_notes = self.architectures.list_capacity_notes(row.id)

        affected_ids = []
        for assumption in assumptions:
            raw_ids = assumption.affected_component_ids or []
            parsed: list[UUID] = []
            for item in raw_ids:
                try:
                    parsed.append(UUID(str(item)))
                except (TypeError, ValueError):
                    continue
            affected_ids.append(parsed)

        return ArchitectureOptionOut(
            id=row.id,
            project_id=row.project_id,
            rkm_id=row.rkm_id,
            rkm_version_label=row.rkm_version_label,
            domain_analysis_id=row.domain_analysis_id,
            generation_id=row.generation_id,
            candidate_key=row.candidate_key,
            title=row.title or row.candidate_key,
            summary=str(payload.get("summary") or row.summary or ""),
            reasoning_summary=str(
                payload.get("reasoning_summary") or row.reasoning_summary or "",
            ),
            status=row.status,
            confidence=float(row.confidence or 0),
            overall_score=row.overall_score,
            pattern_codes=[str(code) for code in (row.pattern_codes or [])],
            version_label=row.version_label,
            model=row.model,
            prompt_version=row.prompt_version,
            knowledge_pack_version=row.knowledge_pack_version,
            high_level_architecture=_str_list(payload.get("high_level_architecture")),
            logical_architecture=_str_list(payload.get("logical_architecture")),
            physical_architecture=_str_list(payload.get("physical_architecture")),
            technology_stack=_obj_list(payload.get("technology_stack")),
            components=[
                ArchitectureComponentOut(
                    id=item.id,
                    name=item.name,
                    purpose=item.purpose or "",
                    component_kind=item.component_kind,  # type: ignore[arg-type]
                    sort_order=item.sort_order,
                    maps_to_requirements=[
                        str(req) for req in (item.maps_to_requirements or [])
                    ],
                )
                for item in components
            ],
            relationships=[
                ArchitectureRelationshipOut(
                    id=item.id,
                    from_component_id=item.from_component_id,
                    to_component_id=item.to_component_id,
                    relationship_kind=item.relationship_kind,
                    description=item.description or "",
                )
                for item in relationships
            ],
            decisions=[
                DesignDecisionOut(
                    id=item.id,
                    decision=item.decision,
                    rationale=item.rationale or "",
                    impact=item.impact or "",
                )
                for item in decisions
            ],
            assumptions=[
                ArchitectureAssumptionOut(
                    id=item.id,
                    statement=item.statement,
                    reason=item.reason or "",
                    affected_component_ids=ids,
                    validation_required=bool(item.validation_required),
                    status=item.status,  # type: ignore[arg-type]
                )
                for item, ids in zip(assumptions, affected_ids, strict=True)
            ],
            risks=[
                SolutionRiskOut(
                    id=item.id,
                    description=item.description,
                    category=item.category or "technical",
                    cause=item.cause or "",
                    impact=item.impact or "",
                    probability=item.probability,  # type: ignore[arg-type]
                    severity=item.severity,  # type: ignore[arg-type]
                    mitigation=item.mitigation or "",
                    owner=item.owner,
                    related_requirement_ids=[
                        str(req) for req in (item.related_requirement_ids or [])
                    ],
                )
                for item in risks
            ],
            scores=[
                SolutionScoreOut(
                    id=item.id,
                    dimension=item.dimension,
                    weight=float(item.weight or 0),
                    score=float(item.score or 0),
                    explanation=item.explanation or "",
                )
                for item in scores
            ],
            capacity_notes=[
                CapacityNoteOut(
                    id=item.id,
                    label=item.label,
                    input_value=item.input_value,
                    unit=item.unit,
                    method=item.method,
                    assumption=item.assumption,
                    result=item.result,
                    confidence=float(item.confidence or 0),
                    related_requirement_ids=[
                        str(req) for req in (item.related_requirement_ids or [])
                    ],
                    open_question=item.open_question,
                )
                for item in capacity_notes
            ],
            advantages=_str_list(payload.get("advantages")),
            disadvantages=_str_list(payload.get("disadvantages")),
            created_at=row.created_at,
            updated_at=row.updated_at,
            payload=payload,
        )


def _weighted_overall_score(scores: list[dict[str, Any]]) -> float | None:
    total_weight = 0.0
    weighted = 0.0
    for item in scores:
        try:
            weight = float(item.get("weight") or 0)
            score = float(item.get("score") or 0)
        except (TypeError, ValueError):
            continue
        if weight <= 0:
            continue
        total_weight += weight
        weighted += weight * score
    if total_weight <= 0:
        return None
    return round(weighted / total_weight, 2)


def _build_domain_context(analysis: Any, domain_rows: list[Any]) -> str:
    lines = [
        "Latest solution domain analysis (required input for architecture generate)",
        f"domain_analysis_id: {analysis.id}",
        f"domain_analysis_version: {analysis.version_label}",
        f"rkm_version_label: {analysis.rkm_version_label or ''}",
        f"summary: {analysis.summary or ''}",
        "domains:",
    ]
    if not domain_rows:
        lines.append("- (none persisted)")
    for row in domain_rows:
        lines.append(
            f"- {row.domain_code} ({row.name}): confidence={row.confidence}; "
            f"source={row.selection_source}; "
            f"mandatory_or_optional={row.mandatory_or_optional}; "
            f"reason={row.reason or ''}",
        )
    return "\n".join(lines)


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


def _str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _obj_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]
