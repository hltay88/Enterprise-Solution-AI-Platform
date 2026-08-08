"""Stage C — Draft RKM generation, evidence mapping, and persistence."""

from __future__ import annotations

import logging
import uuid
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.factory import get_ai_provider
from app.constants.rkm import PROMPT_VERSION, normalize_category, normalize_priority
from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.project import Project
from app.repositories.document_repository import DocumentRepository
from app.repositories.job_repository import JobRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.rkm_repository import RkmRepository
from app.schemas.rkm import (
    RkmAnalyzeAccepted,
    RkmDraftOut,
    RkmVersionSummary,
)
from app.services.analysis_service import AnalysisService

logger = logging.getLogger(__name__)

EXCERPT_CHARS = 280


class RkmGenerationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = ProjectRepository(db)
        self.documents = DocumentRepository(db)
        self.jobs = JobRepository(db)
        self.rkms = RkmRepository(db)
        self.analysis = AnalysisService(db)

    def get_active_draft(self, project_id: UUID, user_id: UUID) -> RkmDraftOut:
        self._require_project(project_id, user_id)
        row = self.rkms.ensure_active_draft(project_id)
        if row is None:
            raise NotFoundError("No Draft RKM found for this project")
        return RkmDraftOut.model_validate(row.payload_json)

    def list_versions(self, project_id: UUID, user_id: UUID) -> list[RkmVersionSummary]:
        self._require_project(project_id, user_id)
        rows = self.rkms.list_versions(project_id)
        return [
            RkmVersionSummary(
                id=row.id,
                project_id=row.project_id,
                status=row.status,
                version_label=row.version_label,
                is_active_draft=row.is_active_draft,
                confidence_score=row.confidence_score,
                completeness_score=row.completeness_score,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            for row in rows
        ]

    def get_version(self, project_id: UUID, version_label: str, user_id: UUID) -> RkmDraftOut:
        self._require_project(project_id, user_id)
        row = self.rkms.get_by_version_label(project_id, version_label)
        if row is None:
            raise NotFoundError("RKM version not found")
        return RkmDraftOut.model_validate(row.payload_json)

    def start_analyze(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
    ) -> tuple[RkmAnalyzeAccepted, UUID]:
        project = self._require_project(project_id, user_id)
        source = self.analysis.build_source_text(project)
        if not source.strip():
            raise ValidationAppError(
                "Add sales intake requirement details and/or upload documents "
                "with extractable text before generating a Draft RKM",
            )

        job = self.jobs.create(
            project_id=project_id,
            document_id=None,
            job_type="rkm_generate",
            status="queued",
        )
        accepted = RkmAnalyzeAccepted(
            project_id=project_id,
            job_id=job.id,
            status="queued",
            message="RKM generation job accepted",
        )
        return accepted, job.id

    async def process_generate_job(self, job_id: UUID, user_id: UUID | None = None) -> None:
        job = self.jobs.get(job_id)
        if job is None:
            logger.error("RKM job %s not found", job_id)
            return

        project = self.projects.get_for_user(job.project_id, user_id) if user_id else None
        if project is None:
            # Background worker: load project without user filter via repo list/get.
            from sqlalchemy import select
            from app.models.project import Project as ProjectModel

            project = self.db.scalars(
                select(ProjectModel).where(ProjectModel.id == job.project_id),
            ).first()
        if project is None:
            self.jobs.mark_failed(job, "Project not found")
            return

        self.jobs.mark_started(job)
        try:
            self.jobs.mark_progress(job, 25)
            source = self.analysis.build_source_text(project)
            if not source.strip():
                raise ValidationAppError("No source text available for RKM generation")

            from app.services.knowledge_packs import build_knowledge_pack_context

            pack_context = build_knowledge_pack_context(source)
            if pack_context:
                source = (
                    f"{source}\n\n--- Vendor-neutral knowledge pack guidance ---\n"
                    f"{pack_context}"
                )

            provider = get_ai_provider()
            extraction = await provider.extract_rkm_draft(source)
            if pack_context and isinstance(extraction, dict):
                prior = str(extraction.get("reasoning_summary") or "").strip()
                extraction["reasoning_summary"] = (
                    f"{prior} Knowledge pack stub context applied (vendor-neutral)."
                ).strip()
            self.jobs.mark_progress(job, 60)

            built = self._assemble_draft(
                project=project,
                extraction=extraction,
                created_by=user_id or project.user_id,
            )
            self.jobs.mark_progress(job, 90)

            self.jobs.mark_completed(
                job,
                result={
                    "rkm_id": str(built["rkm_id"]),
                    "version": built["version_label"],
                    "requirement_count": built["requirement_count"],
                    "evidence_count": built["evidence_count"],
                },
            )
        except Exception as exc:
            logger.exception("RKM generation job %s failed", job_id)
            job = self.jobs.get(job_id) or job
            self.jobs.mark_failed(job, str(exc) or "RKM generation failed")

    def _assemble_draft(
        self,
        *,
        project: Project,
        extraction: dict[str, Any],
        created_by: UUID,
    ) -> dict[str, Any]:
        major, minor, patch = self.rkms.next_draft_version(project.id)
        version_label = f"{major}.{minor}.{patch}"

        evidence_rows, evidence_by_key = self._build_evidence(project)
        evidence_ids_all = [row["id"] for row in evidence_rows]
        intake_ids = [
            row["id"] for row in evidence_rows if row["source_type"] == "sales_intake"
        ]
        document_ids = [
            row["id"] for row in evidence_rows if row["source_type"] == "document"
        ]
        default_evidence = evidence_ids_all[:3] or intake_ids or document_ids
        if not default_evidence:
            # Guaranteed evidence so ATLAS-021 holds even with thin sources.
            fallback_id = uuid.uuid4()
            evidence_rows.append(
                {
                    "id": fallback_id,
                    "source_type": "sales_intake",
                    "document_id": None,
                    "page": None,
                    "excerpt": project.requirement_details or project.project_name,
                    "field_name": "requirement_details",
                    "note": "Fallback evidence from project intake",
                },
            )
            default_evidence = [fallback_id]
            intake_ids = [fallback_id]

        requirements_rows: list[dict[str, Any]] = []
        links: list[tuple[UUID, UUID]] = []

        def add_items(
            section: str,
            items: list[dict[str, Any]],
            *,
            default_category: str,
            evidence_pool: list[UUID],
        ) -> list[dict[str, Any]]:
            out: list[dict[str, Any]] = []
            for index, raw in enumerate(items):
                item_id = uuid.uuid4()
                title = str(raw.get("title") or "").strip() or f"{section} item {index + 1}"
                description = str(raw.get("description") or title).strip()
                category = normalize_category(
                    raw.get("category"),
                    default=default_category,
                )
                priority = normalize_priority(raw.get("priority"))
                confidence = _confidence(raw.get("confidence"), default=55)
                chosen = list(evidence_pool) if evidence_pool else list(default_evidence)
                if not chosen:
                    chosen = list(default_evidence)
                for evidence_id in chosen[:2]:
                    links.append((item_id, evidence_id))
                requirements_rows.append(
                    {
                        "id": item_id,
                        "section": section,
                        "category": category,
                        "subcategory": raw.get("subcategory"),
                        "title": title,
                        "description": description,
                        "priority": priority,
                        "status": "draft",
                        "confidence": confidence,
                        "sort_order": index,
                    },
                )
                out.append(
                    {
                        "id": item_id,
                        "category": category,
                        "subcategory": raw.get("subcategory"),
                        "title": title,
                        "description": description,
                        "priority": priority,
                        "status": "draft",
                        "confidence": confidence,
                        "evidence_ids": chosen[:2],
                    },
                )
            return out

        business = add_items(
            "business_objectives",
            list(extraction.get("business_objectives") or []),
            default_category="business",
            evidence_pool=intake_ids or default_evidence,
        )
        functional = add_items(
            "functional_requirements",
            list(extraction.get("functional_requirements") or []),
            default_category="functional",
            evidence_pool=document_ids or default_evidence,
        )
        non_functional = add_items(
            "non_functional_requirements",
            list(extraction.get("non_functional_requirements") or []),
            default_category="non_functional",
            evidence_pool=document_ids or intake_ids or default_evidence,
        )
        constraints = add_items(
            "constraints",
            list(extraction.get("constraints") or []),
            default_category="business",
            evidence_pool=intake_ids or default_evidence,
        )
        dependencies = add_items(
            "dependencies",
            list(extraction.get("dependencies") or []),
            default_category="functional",
            evidence_pool=document_ids or default_evidence,
        )
        risks = add_items(
            "risks",
            list(extraction.get("risks") or []),
            default_category="business",
            evidence_pool=default_evidence,
        )
        assumptions = add_items(
            "assumptions",
            list(extraction.get("assumptions") or []),
            default_category="business",
            evidence_pool=intake_ids or default_evidence,
        )

        env_raw = extraction.get("current_environment") or {}
        env_summary = str(env_raw.get("summary") or "").strip()
        env_items_out: list[dict[str, Any]] = []
        for index, raw in enumerate(list(env_raw.get("items") or [])):
            item_id = uuid.uuid4()
            title = str(raw.get("title") or f"Environment item {index + 1}").strip()
            description = str(raw.get("description") or title).strip()
            chosen = (document_ids or default_evidence)[:2]
            for evidence_id in chosen:
                links.append((item_id, evidence_id))
            requirements_rows.append(
                {
                    "id": item_id,
                    "section": "current_environment",
                    "category": "infrastructure",
                    "subcategory": None,
                    "title": title,
                    "description": description,
                    "priority": "medium",
                    "status": "draft",
                    "confidence": _confidence(raw.get("confidence"), default=50),
                    "sort_order": index,
                },
            )
            env_items_out.append(
                {
                    "id": item_id,
                    "title": title,
                    "description": description,
                    "evidence_ids": chosen,
                },
            )

        stakeholders_out: list[dict[str, Any]] = []
        if project.pic_name and project.pic_name.strip():
            stakeholder_id = uuid.uuid4()
            pic_evidence = [
                evidence_by_key[key]
                for key in ("pic_name", "pic_contact", "pic_designation")
                if key in evidence_by_key
            ] or intake_ids[:1] or default_evidence[:1]
            for evidence_id in pic_evidence:
                links.append((stakeholder_id, evidence_id))
            requirements_rows.append(
                {
                    "id": stakeholder_id,
                    "section": "stakeholders",
                    "category": "business",
                    "subcategory": None,
                    "title": project.pic_name.strip(),
                    "description": project.pic_designation or "Customer PIC",
                    "priority": "high",
                    "status": "draft",
                    "confidence": 80,
                    "sort_order": 0,
                },
            )
            stakeholders_out.append(
                {
                    "id": stakeholder_id,
                    "name": project.pic_name.strip(),
                    "role": "PIC",
                    "contact": project.pic_contact,
                    "designation": project.pic_designation,
                    "evidence_ids": pic_evidence,
                },
            )

        scores = _compute_scores(
            business=business,
            functional=functional,
            non_functional=non_functional,
            evidence_count=len(evidence_rows),
            linked_count=len(links),
            has_intake=bool(intake_ids),
            has_docs=bool(document_ids),
        )
        reasoning = str(extraction.get("reasoning_summary") or "").strip() or (
            "Draft RKM assembled from sales intake and uploaded document evidence."
        )
        model_name = extraction.get("model") or extraction.get("provider")

        # Persist first to obtain timestamps, then embed them in payload.
        # We'll build payload after create using returned row timestamps.
        placeholder_payload: dict[str, Any] = {"pending": True}

        rkm = self.rkms.create_draft(
            project_id=project.id,
            created_by=created_by,
            status="ai_generated",
            version_major=major,
            version_minor=minor,
            version_patch=patch,
            scores=scores,
            reasoning_summary=reasoning,
            prompt_version=PROMPT_VERSION,
            model=str(model_name) if model_name else None,
            payload_json=placeholder_payload,
            requirements=requirements_rows,
            evidence=evidence_rows,
            links=links,
        )

        payload = {
            "id": str(rkm.id),
            "project_id": str(project.id),
            "project": {
                "project_name": project.project_name,
                "customer": project.customer,
                "industry": project.industry,
                "account_manager": project.account_manager,
                "deal_id": project.deal_id,
                "deal_name": project.deal_name,
                "request_type": project.request_type,
                "required_completion_date": (
                    project.required_completion_date.isoformat()
                    if project.required_completion_date
                    else None
                ),
                "budget_information": project.budget_information,
                "winning_probability": project.winning_probability,
            },
            "business_objectives": [_req_payload(item) for item in business],
            "current_environment": {
                "summary": env_summary,
                "items": [
                    {
                        "id": str(item["id"]),
                        "title": item["title"],
                        "description": item["description"],
                        "evidence_ids": [str(eid) for eid in item["evidence_ids"]],
                    }
                    for item in env_items_out
                ],
            },
            "functional_requirements": [_req_payload(item) for item in functional],
            "non_functional_requirements": [_req_payload(item) for item in non_functional],
            "constraints": [_req_payload(item) for item in constraints],
            "dependencies": [_req_payload(item) for item in dependencies],
            "risks": [_req_payload(item) for item in risks],
            "assumptions": [_req_payload(item) for item in assumptions],
            "stakeholders": [
                {
                    "id": str(item["id"]),
                    "name": item["name"],
                    "role": item.get("role"),
                    "contact": item.get("contact"),
                    "designation": item.get("designation"),
                    "evidence_ids": [str(eid) for eid in item["evidence_ids"]],
                }
                for item in stakeholders_out
            ],
            "clarification_questions": [],
            "evidence": [
                {
                    "id": str(row["id"]),
                    "source_type": row["source_type"],
                    "document_id": str(row["document_id"]) if row.get("document_id") else None,
                    "page": row.get("page"),
                    "excerpt": row.get("excerpt"),
                    "field_name": row.get("field_name"),
                    "note": row.get("note"),
                }
                for row in evidence_rows
            ],
            "analysis": {
                "confidence_score": scores["confidence_score"],
                "completeness_score": scores["completeness_score"],
                "consistency_score": scores["consistency_score"],
                "evidence_coverage": scores["evidence_coverage"],
                "reasoning_summary": reasoning,
                "prompt_version": PROMPT_VERSION,
                "model": str(model_name) if model_name else None,
            },
            "approval": {
                "status": "ai_generated",
                "reviewed_by": None,
                "approved_by": None,
                "approved_at": None,
                "published_at": None,
            },
            "version": {
                "number": version_label,
                "major": major,
                "minor": minor,
                "patch": patch,
                "created_at": rkm.created_at.isoformat(),
                "updated_at": rkm.updated_at.isoformat(),
                "change_summary": "AI-generated Draft RKM from intake + documents",
            },
        }

        # Validate against response schema, then persist canonical payload.
        validated = RkmDraftOut.model_validate(payload)
        rkm.payload_json = validated.model_dump(mode="json")
        self.db.add(rkm)
        self.db.commit()
        self.db.refresh(rkm)

        return {
            "rkm_id": rkm.id,
            "version_label": version_label,
            "requirement_count": len(requirements_rows),
            "evidence_count": len(evidence_rows),
        }

    def _build_evidence(
        self,
        project: Project,
    ) -> tuple[list[dict[str, Any]], dict[str, UUID]]:
        rows: list[dict[str, Any]] = []
        by_key: dict[str, UUID] = {}

        intake_fields = [
            ("project_name", project.project_name),
            ("customer", project.customer),
            ("deal_id", project.deal_id),
            ("deal_name", project.deal_name),
            ("request_type", project.request_type),
            ("pic_name", project.pic_name),
            ("pic_contact", project.pic_contact),
            ("pic_designation", project.pic_designation),
            ("budget_information", project.budget_information),
            ("requirement_details", project.requirement_details),
        ]
        for field_name, value in intake_fields:
            if value is None or not str(value).strip():
                continue
            evidence_id = uuid.uuid4()
            by_key[field_name] = evidence_id
            excerpt = str(value).strip()
            if len(excerpt) > EXCERPT_CHARS:
                excerpt = excerpt[: EXCERPT_CHARS - 1].rstrip() + "…"
            rows.append(
                {
                    "id": evidence_id,
                    "source_type": "sales_intake",
                    "document_id": None,
                    "page": None,
                    "excerpt": excerpt,
                    "field_name": field_name,
                    "note": f"Sales intake field: {field_name}",
                },
            )

        for document in self.documents.list_for_project(project.id):
            text = (document.extracted_text or "").strip()
            if not text:
                continue
            excerpt = text if len(text) <= EXCERPT_CHARS else text[: EXCERPT_CHARS - 1].rstrip() + "…"
            evidence_id = uuid.uuid4()
            rows.append(
                {
                    "id": evidence_id,
                    "source_type": "document",
                    "document_id": document.id,
                    "page": 1,
                    "excerpt": excerpt,
                    "field_name": None,
                    "note": f"Extracted from {document.filename}",
                },
            )

        return rows, by_key

    def _require_project(self, project_id: UUID, user_id: UUID) -> Project:
        project = self.projects.get_for_user(project_id, user_id)
        if project is None:
            raise NotFoundError("Project not found")
        return project


def _confidence(value: Any, *, default: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if number > 1:
        number = number  # already 0-100
    else:
        number = number * 100
    return max(0.0, min(100.0, number))


def _req_payload(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(item["id"]),
        "category": item.get("category"),
        "subcategory": item.get("subcategory"),
        "title": item["title"],
        "description": item["description"],
        "priority": item.get("priority") or "medium",
        "status": item.get("status") or "draft",
        "confidence": float(item.get("confidence") or 0),
        "evidence_ids": [str(eid) for eid in item.get("evidence_ids") or []],
    }


def _compute_scores(
    *,
    business: list,
    functional: list,
    non_functional: list,
    evidence_count: int,
    linked_count: int,
    has_intake: bool,
    has_docs: bool,
) -> dict[str, float]:
    item_count = len(business) + len(functional) + len(non_functional)
    completeness = 20.0
    if has_intake:
        completeness += 25.0
    if has_docs:
        completeness += 25.0
    if business:
        completeness += 10.0
    if functional:
        completeness += 10.0
    if non_functional:
        completeness += 10.0
    completeness = min(100.0, completeness)

    if item_count == 0:
        confidence = 20.0
    else:
        avg = sum(float(i.get("confidence") or 50) for i in [*business, *functional, *non_functional])
        confidence = avg / item_count

    evidence_coverage = 0.0
    if item_count > 0 and evidence_count > 0:
        evidence_coverage = min(100.0, (linked_count / max(item_count, 1)) * 50 + (30 if has_docs else 0) + (20 if has_intake else 0))

    consistency = 70.0 if item_count >= 3 else 45.0
    return {
        "confidence_score": round(confidence, 1),
        "completeness_score": round(completeness, 1),
        "consistency_score": round(consistency, 1),
        "evidence_coverage": round(evidence_coverage, 1),
    }


async def run_rkm_generate_job(job_id: UUID, user_id: UUID | None = None) -> None:
    """Background task entrypoint with its own DB session."""
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        await RkmGenerationService(db).process_generate_job(job_id, user_id=user_id)
    finally:
        db.close()
