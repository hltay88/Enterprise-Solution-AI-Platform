"""Persistence for Phase 3 domain analyses and requirement→domain traceability.

Sprint 3.1 Task 4 — data access only (no AI, no HTTP).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.domain_analysis import (
    DomainAnalysis,
    DomainDependency,
    DomainOpenQuestion,
    DomainRequirementLink,
    RequirementTraceability,
    SolutionDomain,
)


def compute_next_domain_version(
    latest: DomainAnalysis | None,
) -> tuple[int, int, int]:
    """Return next major/minor/patch for a project's domain analyses."""
    if latest is None:
        return 1, 0, 0
    return latest.version_major, latest.version_minor + 1, 0


class DomainRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_latest(self, project_id: UUID) -> DomainAnalysis | None:
        statement = (
            select(DomainAnalysis)
            .where(DomainAnalysis.project_id == project_id)
            .order_by(
                DomainAnalysis.version_major.desc(),
                DomainAnalysis.version_minor.desc(),
                DomainAnalysis.version_patch.desc(),
                DomainAnalysis.created_at.desc(),
            )
        )
        return self.db.scalars(statement).first()

    def get_by_id(self, analysis_id: UUID) -> DomainAnalysis | None:
        return self.db.scalars(
            select(DomainAnalysis).where(DomainAnalysis.id == analysis_id),
        ).first()

    def get_for_project(self, analysis_id: UUID, project_id: UUID) -> DomainAnalysis | None:
        return self.db.scalars(
            select(DomainAnalysis).where(
                DomainAnalysis.id == analysis_id,
                DomainAnalysis.project_id == project_id,
            ),
        ).first()

    def list_versions(self, project_id: UUID) -> list[DomainAnalysis]:
        statement = (
            select(DomainAnalysis)
            .where(DomainAnalysis.project_id == project_id)
            .order_by(
                DomainAnalysis.version_major.desc(),
                DomainAnalysis.version_minor.desc(),
                DomainAnalysis.version_patch.desc(),
                DomainAnalysis.created_at.desc(),
            )
        )
        return list(self.db.scalars(statement).all())

    def next_version(self, project_id: UUID) -> tuple[int, int, int]:
        return compute_next_domain_version(self.get_latest(project_id))

    def count_domains(self, analysis_id: UUID) -> int:
        statement = (
            select(func.count())
            .select_from(SolutionDomain)
            .where(SolutionDomain.analysis_id == analysis_id)
        )
        return int(self.db.scalar(statement) or 0)

    def list_domains(self, analysis_id: UUID) -> list[SolutionDomain]:
        statement = (
            select(SolutionDomain)
            .where(SolutionDomain.analysis_id == analysis_id)
            .order_by(SolutionDomain.sort_order.asc(), SolutionDomain.created_at.asc())
        )
        return list(self.db.scalars(statement).all())

    def list_requirement_links(self, domain_ids: list[UUID]) -> list[DomainRequirementLink]:
        if not domain_ids:
            return []
        statement = select(DomainRequirementLink).where(
            DomainRequirementLink.domain_id.in_(domain_ids),
        )
        return list(self.db.scalars(statement).all())

    def list_dependencies(self, domain_ids: list[UUID]) -> list[DomainDependency]:
        if not domain_ids:
            return []
        statement = select(DomainDependency).where(
            DomainDependency.domain_id.in_(domain_ids),
        )
        return list(self.db.scalars(statement).all())

    def list_open_questions(self, analysis_id: UUID) -> list[DomainOpenQuestion]:
        statement = (
            select(DomainOpenQuestion)
            .where(DomainOpenQuestion.analysis_id == analysis_id)
            .order_by(DomainOpenQuestion.created_at.asc())
        )
        return list(self.db.scalars(statement).all())

    def list_traceability(
        self,
        *,
        analysis_id: UUID | None = None,
        project_id: UUID | None = None,
    ) -> list[RequirementTraceability]:
        if analysis_id is None and project_id is None:
            raise ValueError("list_traceability requires analysis_id or project_id")
        statement = select(RequirementTraceability)
        if analysis_id is not None:
            statement = statement.where(RequirementTraceability.analysis_id == analysis_id)
        if project_id is not None:
            statement = statement.where(RequirementTraceability.project_id == project_id)
        statement = statement.order_by(
            RequirementTraceability.requirement_id.asc(),
            RequirementTraceability.created_at.asc(),
        )
        return list(self.db.scalars(statement).all())

    def create_analysis_tree(
        self,
        *,
        project_id: UUID,
        rkm_id: UUID | None,
        rkm_version_label: str | None,
        created_by: UUID | None,
        status: str = "draft",
        version_major: int,
        version_minor: int,
        version_patch: int,
        summary: str | None,
        model: str | None,
        prompt_version: str | None,
        knowledge_pack_version: str | None,
        payload_json: dict[str, Any] | None,
        domains: list[dict[str, Any]],
        analysis_open_questions: list[dict[str, Any]] | None = None,
        traceability: list[dict[str, Any]] | None = None,
    ) -> DomainAnalysis:
        """Persist one domain analysis version with nested rows (single transaction).

        Each ``domains`` item may include:
        - domain_code (required), name, reason, confidence, mandatory_or_optional,
          selection_source, sort_order
        - supporting_requirements: list[str] or list[{requirement_id, evidence}]
        - dependencies: list[{depends_on_domain_code, dependency_kind, reason}]
        - open_questions: list[{question, affects_selection, related_requirement_ids}]

        ``traceability`` items:
        - requirement_id (required), status, evidence, domain_code (optional)
        """
        now = datetime.now(timezone.utc)
        version_label = f"{version_major}.{version_minor}.{version_patch}"
        analysis = DomainAnalysis(
            id=uuid4(),
            project_id=project_id,
            rkm_id=rkm_id,
            rkm_version_label=rkm_version_label,
            status=status,
            version_label=version_label,
            version_major=version_major,
            version_minor=version_minor,
            version_patch=version_patch,
            summary=summary,
            model=model,
            prompt_version=prompt_version,
            knowledge_pack_version=knowledge_pack_version,
            payload_json=dict(payload_json or {}),
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )
        self.db.add(analysis)
        # Flush parent before children — ORM has no relationship() graph, so
        # insertmany can otherwise write domain_dependencies before solution_domains.
        self.db.flush()

        code_to_domain: dict[str, SolutionDomain] = {}
        seen_codes: set[str] = set()
        pending_children: list[tuple[SolutionDomain, dict[str, Any]]] = []

        for index, item in enumerate(domains or []):
            if not isinstance(item, dict):
                raise ValueError(f"domains[{index}] must be an object")
            code = str(item.get("domain_code") or "").strip().lower()
            if not code:
                raise ValueError(f"domains[{index}].domain_code is required")
            if code in seen_codes:
                raise ValueError(f"duplicate domain_code in analysis tree: {code}")
            seen_codes.add(code)

            name = str(item.get("name") or code).strip() or code
            domain = SolutionDomain(
                id=uuid4(),
                analysis_id=analysis.id,
                project_id=project_id,
                domain_code=code,
                name=name,
                reason=str(item.get("reason") or "").strip(),
                confidence=float(item.get("confidence") or 0),
                mandatory_or_optional=str(
                    item.get("mandatory_or_optional") or "mandatory",
                ).strip()
                or "mandatory",
                selection_source=str(item.get("selection_source") or "requirement").strip()
                or "requirement",
                sort_order=int(item.get("sort_order") if item.get("sort_order") is not None else index),
                created_at=now,
            )
            self.db.add(domain)
            code_to_domain[code] = domain
            pending_children.append((domain, item))

        self.db.flush()

        for domain, item in pending_children:
            code = domain.domain_code
            for req in item.get("supporting_requirements") or []:
                requirement_id, evidence = _parse_requirement_ref(req)
                if not requirement_id:
                    continue
                self.db.add(
                    DomainRequirementLink(
                        id=uuid4(),
                        domain_id=domain.id,
                        requirement_id=requirement_id,
                        evidence=evidence,
                        created_at=now,
                    ),
                )

            for dep in item.get("dependencies") or []:
                if not isinstance(dep, dict):
                    raise ValueError(f"dependencies for {code} must be objects")
                dep_code = str(dep.get("depends_on_domain_code") or "").strip().lower()
                if not dep_code:
                    raise ValueError(f"dependency for {code} missing depends_on_domain_code")
                self.db.add(
                    DomainDependency(
                        id=uuid4(),
                        domain_id=domain.id,
                        depends_on_domain_code=dep_code,
                        dependency_kind=str(dep.get("dependency_kind") or "required").strip()
                        or "required",
                        reason=str(dep.get("reason") or "").strip(),
                        created_at=now,
                    ),
                )

            for question in item.get("open_questions") or []:
                self.db.add(
                    _build_open_question(
                        question,
                        analysis_id=analysis.id,
                        domain_id=domain.id,
                        now=now,
                    ),
                )

        for question in analysis_open_questions or []:
            self.db.add(
                _build_open_question(
                    question,
                    analysis_id=analysis.id,
                    domain_id=_domain_id_for_question(question, code_to_domain),
                    now=now,
                ),
            )

        for row in traceability or []:
            if not isinstance(row, dict):
                raise ValueError("traceability rows must be objects")
            requirement_id = str(row.get("requirement_id") or "").strip()
            if not requirement_id:
                raise ValueError("traceability.requirement_id is required")
            domain_code = str(row.get("domain_code") or "").strip().lower()
            domain_id = code_to_domain[domain_code].id if domain_code in code_to_domain else None
            if row.get("domain_id") is not None and domain_id is None:
                try:
                    domain_id = UUID(str(row["domain_id"]))
                except (TypeError, ValueError) as exc:
                    raise ValueError("traceability.domain_id is not a valid UUID") from exc
            self.db.add(
                RequirementTraceability(
                    id=uuid4(),
                    project_id=project_id,
                    analysis_id=analysis.id,
                    requirement_id=requirement_id,
                    domain_id=domain_id,
                    architecture_id=None,
                    component_id=None,
                    decision_id=None,
                    evidence=(
                        str(row["evidence"]).strip()
                        if row.get("evidence") is not None
                        else None
                    ),
                    status=str(row.get("status") or "not_covered").strip() or "not_covered",
                    created_at=now,
                    updated_at=now,
                ),
            )

        self.db.commit()
        self.db.refresh(analysis)
        return analysis


def _parse_requirement_ref(value: Any) -> tuple[str, str | None]:
    if isinstance(value, dict):
        requirement_id = str(
            value.get("requirement_id") or value.get("id") or "",
        ).strip()
        evidence_raw = value.get("evidence")
        evidence = str(evidence_raw).strip() if evidence_raw is not None else None
        return requirement_id, evidence or None
    return str(value or "").strip(), None


def _domain_id_for_question(
    question: Any,
    code_to_domain: dict[str, SolutionDomain],
) -> UUID | None:
    if not isinstance(question, dict):
        return None
    code = str(question.get("domain_code") or "").strip().lower()
    if code and code in code_to_domain:
        return code_to_domain[code].id
    if question.get("domain_id") is not None:
        try:
            return UUID(str(question["domain_id"]))
        except (TypeError, ValueError):
            return None
    return None


def _build_open_question(
    question: Any,
    *,
    analysis_id: UUID,
    domain_id: UUID | None,
    now: datetime,
) -> DomainOpenQuestion:
    if isinstance(question, str):
        text = question.strip()
        related: list[Any] = []
        affects = True
    elif isinstance(question, dict):
        text = str(question.get("question") or "").strip()
        affects = bool(question.get("affects_selection", True))
        related_raw = question.get("related_requirement_ids") or []
        if isinstance(related_raw, list):
            related = [str(item).strip() for item in related_raw if str(item).strip()]
        else:
            related = []
    else:
        raise ValueError("open_questions entries must be strings or objects")
    if not text:
        raise ValueError("open question text is required")
    return DomainOpenQuestion(
        id=uuid4(),
        analysis_id=analysis_id,
        domain_id=domain_id,
        question=text,
        affects_selection=affects,
        related_requirement_ids=related,
        created_at=now,
    )
