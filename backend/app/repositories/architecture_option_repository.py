"""Persistence for normalized architecture candidates (Sprint 3.2 Task 4).

Data access only — no AI, no HTTP. MVP ``ArchitectureRepository``
(``architecture_models``) is unchanged (ATLAS-034).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.architecture_option import (
    ArchitectureAssumption,
    ArchitectureComponent,
    ArchitectureOption,
    ArchitectureRelationship,
    CapacityNote,
    DesignDecision,
    SolutionRisk,
    SolutionScore,
)
from app.models.domain_analysis import RequirementTraceability


def compute_next_architecture_version(
    latest: ArchitectureOption | None,
) -> tuple[int, int, int]:
    """Return next major/minor/patch for a project's architecture options."""
    if latest is None:
        return 1, 0, 0
    return latest.version_major, latest.version_minor + 1, 0


class ArchitectureOptionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_latest(self, project_id: UUID) -> ArchitectureOption | None:
        """Latest option by version, preferring ``recommended`` then newest created."""
        statement = (
            select(ArchitectureOption)
            .where(ArchitectureOption.project_id == project_id)
            .order_by(
                ArchitectureOption.version_major.desc(),
                ArchitectureOption.version_minor.desc(),
                ArchitectureOption.version_patch.desc(),
                ArchitectureOption.created_at.desc(),
            )
        )
        return self.db.scalars(statement).first()

    def get_by_id(self, architecture_id: UUID) -> ArchitectureOption | None:
        return self.db.scalars(
            select(ArchitectureOption).where(ArchitectureOption.id == architecture_id),
        ).first()

    def get_for_project(
        self,
        architecture_id: UUID,
        project_id: UUID,
    ) -> ArchitectureOption | None:
        return self.db.scalars(
            select(ArchitectureOption).where(
                ArchitectureOption.id == architecture_id,
                ArchitectureOption.project_id == project_id,
            ),
        ).first()

    def list_traceability_for_architecture(
        self,
        architecture_id: UUID,
    ) -> list[RequirementTraceability]:
        statement = (
            select(RequirementTraceability)
            .where(RequirementTraceability.architecture_id == architecture_id)
            .order_by(
                RequirementTraceability.requirement_id.asc(),
                RequirementTraceability.created_at.asc(),
            )
        )
        return list(self.db.scalars(statement).all())

    def mark_under_review(
        self,
        architecture_id: UUID,
        *,
        reviewed_by: UUID,
        review_note: str | None,
        commit: bool = True,
    ) -> ArchitectureOption:
        """Stamp human review (ATLAS-037). Does not approve."""
        row = self.get_by_id(architecture_id)
        if row is None:
            raise ValueError("Architecture option not found")
        now = datetime.now(timezone.utc)
        note = (str(review_note).strip() if review_note else "") or None
        row.status = "under_review"
        row.reviewed_at = now
        row.reviewed_by = reviewed_by
        row.review_note = note
        row.updated_at = now
        if commit:
            self.db.commit()
            self.db.refresh(row)
        else:
            self.db.flush()
        return row

    def mark_complete(
        self,
        architecture_id: UUID,
        *,
        approved_by: UUID,
        approval_note: str | None,
        commit: bool = True,
    ) -> ArchitectureOption:
        """Stamp Approver Complete (ATLAS-036/037). Caller enforces uncovered gate."""
        row = self.get_by_id(architecture_id)
        if row is None:
            raise ValueError("Architecture option not found")
        now = datetime.now(timezone.utc)
        note = (str(approval_note).strip() if approval_note else "") or None
        row.status = "complete"
        row.approved_at = now
        row.approved_by = approved_by
        row.approval_note = note
        if row.reviewed_at is None:
            row.reviewed_at = now
            row.reviewed_by = row.reviewed_by or approved_by
        row.updated_at = now
        if commit:
            self.db.commit()
            self.db.refresh(row)
        else:
            self.db.flush()
        return row

    def list_for_project(self, project_id: UUID) -> list[ArchitectureOption]:
        statement = (
            select(ArchitectureOption)
            .where(ArchitectureOption.project_id == project_id)
            .order_by(
                ArchitectureOption.version_major.desc(),
                ArchitectureOption.version_minor.desc(),
                ArchitectureOption.version_patch.desc(),
                ArchitectureOption.candidate_key.asc(),
                ArchitectureOption.created_at.desc(),
            )
        )
        return list(self.db.scalars(statement).all())

    def list_generation(
        self,
        project_id: UUID,
        generation_id: UUID,
    ) -> list[ArchitectureOption]:
        statement = (
            select(ArchitectureOption)
            .where(
                ArchitectureOption.project_id == project_id,
                ArchitectureOption.generation_id == generation_id,
            )
            .order_by(ArchitectureOption.candidate_key.asc())
        )
        return list(self.db.scalars(statement).all())

    def next_version(self, project_id: UUID) -> tuple[int, int, int]:
        return compute_next_architecture_version(self.get_latest(project_id))

    def list_components(self, architecture_id: UUID) -> list[ArchitectureComponent]:
        statement = (
            select(ArchitectureComponent)
            .where(ArchitectureComponent.architecture_id == architecture_id)
            .order_by(
                ArchitectureComponent.sort_order.asc(),
                ArchitectureComponent.created_at.asc(),
            )
        )
        return list(self.db.scalars(statement).all())

    def list_relationships(self, architecture_id: UUID) -> list[ArchitectureRelationship]:
        statement = select(ArchitectureRelationship).where(
            ArchitectureRelationship.architecture_id == architecture_id,
        )
        return list(self.db.scalars(statement).all())

    def list_decisions(self, architecture_id: UUID) -> list[DesignDecision]:
        statement = (
            select(DesignDecision)
            .where(DesignDecision.architecture_id == architecture_id)
            .order_by(DesignDecision.created_at.asc())
        )
        return list(self.db.scalars(statement).all())

    def list_assumptions(self, architecture_id: UUID) -> list[ArchitectureAssumption]:
        statement = (
            select(ArchitectureAssumption)
            .where(ArchitectureAssumption.architecture_id == architecture_id)
            .order_by(ArchitectureAssumption.created_at.asc())
        )
        return list(self.db.scalars(statement).all())

    def list_risks(
        self,
        *,
        architecture_id: UUID | None = None,
        project_id: UUID | None = None,
    ) -> list[SolutionRisk]:
        if architecture_id is None and project_id is None:
            raise ValueError("list_risks requires architecture_id or project_id")
        statement = select(SolutionRisk)
        if architecture_id is not None:
            statement = statement.where(SolutionRisk.architecture_id == architecture_id)
        if project_id is not None:
            statement = statement.where(SolutionRisk.project_id == project_id)
        statement = statement.order_by(SolutionRisk.created_at.asc())
        return list(self.db.scalars(statement).all())

    def list_assumptions_for_project(self, project_id: UUID) -> list[ArchitectureAssumption]:
        statement = (
            select(ArchitectureAssumption)
            .where(ArchitectureAssumption.project_id == project_id)
            .order_by(ArchitectureAssumption.created_at.asc())
        )
        return list(self.db.scalars(statement).all())

    def list_scores(self, architecture_id: UUID) -> list[SolutionScore]:
        statement = (
            select(SolutionScore)
            .where(SolutionScore.architecture_id == architecture_id)
            .order_by(SolutionScore.dimension.asc())
        )
        return list(self.db.scalars(statement).all())

    def list_capacity_notes(self, architecture_id: UUID) -> list[CapacityNote]:
        statement = (
            select(CapacityNote)
            .where(CapacityNote.architecture_id == architecture_id)
            .order_by(CapacityNote.created_at.asc())
        )
        return list(self.db.scalars(statement).all())

    def count_components(self, architecture_id: UUID) -> int:
        statement = (
            select(func.count())
            .select_from(ArchitectureComponent)
            .where(ArchitectureComponent.architecture_id == architecture_id)
        )
        return int(self.db.scalar(statement) or 0)

    def add_traceability_rows(
        self,
        *,
        project_id: UUID,
        analysis_id: UUID,
        rows: list[dict[str, Any]],
        commit: bool = True,
    ) -> int:
        """Persist architecture-stage requirement_traceability rows.

        Each row may include requirement_id, domain_id, architecture_id,
        component_id, decision_id, status, evidence. Domain analyze rows are
        left untouched; this only inserts new architecture-linked rows.
        """
        if not rows:
            return 0
        now = datetime.now(timezone.utc)
        added = 0
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                raise ValueError(f"traceability[{index}] must be an object")
            requirement_id = str(row.get("requirement_id") or "").strip()
            if not requirement_id:
                raise ValueError(f"traceability[{index}].requirement_id is required")
            architecture_id = row.get("architecture_id")
            if architecture_id is None:
                raise ValueError(
                    f"traceability[{index}].architecture_id is required for "
                    "architecture-stage rows",
                )
            self.db.add(
                RequirementTraceability(
                    id=uuid4(),
                    project_id=project_id,
                    analysis_id=analysis_id,
                    requirement_id=requirement_id,
                    domain_id=row.get("domain_id"),
                    architecture_id=architecture_id,
                    component_id=row.get("component_id"),
                    decision_id=row.get("decision_id"),
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
            added += 1
        if commit:
            self.db.commit()
        else:
            self.db.flush()
        return added

    def create_generation_tree(
        self,
        *,
        project_id: UUID,
        rkm_id: UUID | None,
        rkm_version_label: str | None,
        domain_analysis_id: UUID | None,
        created_by: UUID | None,
        version_major: int,
        version_minor: int,
        version_patch: int,
        model: str | None,
        prompt_version: str | None,
        knowledge_pack_version: str | None,
        architectures: list[dict[str, Any]],
        generation_id: UUID | None = None,
    ) -> list[ArchitectureOption]:
        """Persist one generate batch (shared version + generation_id).

        Each architecture dict may include:
        - candidate_key, title, summary, reasoning_summary, status, confidence,
          overall_score, pattern_codes, payload_json
        - components: [{name, purpose, component_kind, maps_to_requirements, temp_id}]
        - relationships: [{from_component, to_component, relationship_kind, description}]
          (endpoints are temp_id or component name)
        - decisions, assumptions, risks, scores, capacity_notes
        """
        if not architectures:
            raise ValueError("architectures must be a non-empty list")

        now = datetime.now(timezone.utc)
        version_label = f"{version_major}.{version_minor}.{version_patch}"
        batch_id = generation_id or uuid4()
        seen_keys: set[str] = set()
        options: list[ArchitectureOption] = []
        pending: list[tuple[ArchitectureOption, dict[str, Any]]] = []

        for index, item in enumerate(architectures):
            if not isinstance(item, dict):
                raise ValueError(f"architectures[{index}] must be an object")
            candidate_key = (
                str(item.get("candidate_key") or "standard").strip().lower().replace(" ", "_")
                or "standard"
            )
            if candidate_key in seen_keys:
                raise ValueError(f"duplicate candidate_key in generation: {candidate_key}")
            seen_keys.add(candidate_key)

            title = str(item.get("title") or candidate_key).strip() or candidate_key
            option = ArchitectureOption(
                id=uuid4(),
                project_id=project_id,
                rkm_id=rkm_id,
                rkm_version_label=rkm_version_label,
                domain_analysis_id=domain_analysis_id,
                generation_id=batch_id,
                candidate_key=candidate_key,
                title=title,
                summary=str(item.get("summary") or "").strip() or None,
                reasoning_summary=str(item.get("reasoning_summary") or "").strip() or None,
                status=str(item.get("status") or "draft").strip() or "draft",
                confidence=float(item.get("confidence") or 0),
                overall_score=(
                    float(item["overall_score"])
                    if item.get("overall_score") is not None
                    else None
                ),
                pattern_codes=list(item.get("pattern_codes") or []),
                version_label=version_label,
                version_major=version_major,
                version_minor=version_minor,
                version_patch=version_patch,
                model=model,
                prompt_version=prompt_version,
                knowledge_pack_version=knowledge_pack_version,
                payload_json=dict(item.get("payload_json") or {}),
                created_by=created_by,
                created_at=now,
                updated_at=now,
            )
            # Keep narrative lists in payload for API mapping until dedicated columns exist.
            payload = dict(option.payload_json)
            for key in (
                "high_level_architecture",
                "logical_architecture",
                "physical_architecture",
                "technology_stack",
                "advantages",
                "disadvantages",
            ):
                if key in item and key not in payload:
                    payload[key] = item[key]
            option.payload_json = payload
            self.db.add(option)
            options.append(option)
            pending.append((option, item))

        self.db.flush()

        for option, item in pending:
            temp_to_id = self._add_components(option, item.get("components") or [], now)
            self.db.flush()
            self._add_relationships(
                option,
                item.get("relationships") or [],
                temp_to_id,
                now,
            )
            self._add_decisions(option, item.get("decisions") or [], now)
            self._add_assumptions(
                option,
                item.get("assumptions") or [],
                temp_to_id,
                now,
            )
            self._add_risks(option, item.get("risks") or [], now)
            self._add_scores(option, item.get("scores") or [], now)
            self._add_capacity_notes(option, item.get("capacity_notes") or [], now)

        self.db.commit()
        for option in options:
            self.db.refresh(option)
        return options

    def _add_components(
        self,
        option: ArchitectureOption,
        components: list[Any],
        now: datetime,
    ) -> dict[str, UUID]:
        temp_to_id: dict[str, UUID] = {}
        name_to_id: dict[str, UUID] = {}
        for index, raw in enumerate(components):
            if not isinstance(raw, dict):
                raise ValueError(f"components[{index}] must be an object")
            name = str(raw.get("name") or "").strip()
            if not name:
                raise ValueError(f"components[{index}].name is required")
            component = ArchitectureComponent(
                id=uuid4(),
                architecture_id=option.id,
                name=name,
                purpose=str(raw.get("purpose") or "").strip(),
                component_kind=str(raw.get("component_kind") or "logical").strip()
                or "logical",
                sort_order=int(
                    raw.get("sort_order") if raw.get("sort_order") is not None else index,
                ),
                maps_to_requirements=list(raw.get("maps_to_requirements") or []),
                created_at=now,
            )
            self.db.add(component)
            temp_id = str(raw.get("temp_id") or "").strip()
            if temp_id:
                temp_to_id[temp_id] = component.id
            temp_to_id[name] = component.id
            name_to_id[name.lower()] = component.id
        # Also allow lookup by lowercased name.
        temp_to_id.update({f"name:{key}": value for key, value in name_to_id.items()})
        return temp_to_id

    def _resolve_component_ref(
        self,
        ref: Any,
        temp_to_id: dict[str, UUID],
        *,
        field: str,
    ) -> UUID:
        text = str(ref or "").strip()
        if not text:
            raise ValueError(f"{field} is required")
        if text in temp_to_id:
            return temp_to_id[text]
        lower = text.lower()
        if f"name:{lower}" in temp_to_id:
            return temp_to_id[f"name:{lower}"]
        raise ValueError(f"Unknown component reference for {field}: {text!r}")

    def _add_relationships(
        self,
        option: ArchitectureOption,
        relationships: list[Any],
        temp_to_id: dict[str, UUID],
        now: datetime,
    ) -> None:
        for index, raw in enumerate(relationships):
            if not isinstance(raw, dict):
                raise ValueError(f"relationships[{index}] must be an object")
            from_id = self._resolve_component_ref(
                raw.get("from_component") or raw.get("from_component_id"),
                temp_to_id,
                field=f"relationships[{index}].from_component",
            )
            to_id = self._resolve_component_ref(
                raw.get("to_component") or raw.get("to_component_id"),
                temp_to_id,
                field=f"relationships[{index}].to_component",
            )
            self.db.add(
                ArchitectureRelationship(
                    id=uuid4(),
                    architecture_id=option.id,
                    from_component_id=from_id,
                    to_component_id=to_id,
                    relationship_kind=str(raw.get("relationship_kind") or "connects_to").strip()
                    or "connects_to",
                    description=str(raw.get("description") or "").strip(),
                    created_at=now,
                ),
            )

    def _add_decisions(
        self,
        option: ArchitectureOption,
        decisions: list[Any],
        now: datetime,
    ) -> None:
        for index, raw in enumerate(decisions):
            if not isinstance(raw, dict):
                raise ValueError(f"decisions[{index}] must be an object")
            decision = str(raw.get("decision") or "").strip()
            if not decision:
                raise ValueError(f"decisions[{index}].decision is required")
            self.db.add(
                DesignDecision(
                    id=uuid4(),
                    architecture_id=option.id,
                    decision=decision,
                    rationale=str(raw.get("rationale") or "").strip(),
                    impact=str(raw.get("impact") or "").strip(),
                    created_at=now,
                ),
            )

    def _add_assumptions(
        self,
        option: ArchitectureOption,
        assumptions: list[Any],
        temp_to_id: dict[str, UUID],
        now: datetime,
    ) -> None:
        for index, raw in enumerate(assumptions):
            if not isinstance(raw, dict):
                raise ValueError(f"assumptions[{index}] must be an object")
            statement = str(raw.get("statement") or "").strip()
            if not statement:
                raise ValueError(f"assumptions[{index}].statement is required")
            affected: list[str] = []
            for ref in raw.get("affected_components") or raw.get("affected_component_ids") or []:
                try:
                    affected.append(
                        str(
                            self._resolve_component_ref(
                                ref,
                                temp_to_id,
                                field=f"assumptions[{index}].affected_components",
                            ),
                        ),
                    )
                except ValueError:
                    # Allow unresolved names to be dropped; service layer validates earlier.
                    text = str(ref or "").strip()
                    if text:
                        affected.append(text)
            self.db.add(
                ArchitectureAssumption(
                    id=uuid4(),
                    architecture_id=option.id,
                    project_id=option.project_id,
                    statement=statement,
                    reason=str(raw.get("reason") or "").strip(),
                    affected_component_ids=affected,
                    validation_required=bool(
                        raw.get("validation_required")
                        if raw.get("validation_required") is not None
                        else True,
                    ),
                    status=str(raw.get("status") or "unvalidated").strip() or "unvalidated",
                    created_at=now,
                ),
            )

    def _add_risks(
        self,
        option: ArchitectureOption,
        risks: list[Any],
        now: datetime,
    ) -> None:
        for index, raw in enumerate(risks):
            if not isinstance(raw, dict):
                raise ValueError(f"risks[{index}] must be an object")
            description = str(raw.get("description") or "").strip()
            if not description:
                raise ValueError(f"risks[{index}].description is required")
            self.db.add(
                SolutionRisk(
                    id=uuid4(),
                    architecture_id=option.id,
                    project_id=option.project_id,
                    description=description,
                    category=str(raw.get("category") or "technical").strip() or "technical",
                    cause=str(raw.get("cause") or "").strip(),
                    impact=str(raw.get("impact") or "").strip(),
                    probability=str(raw.get("probability") or "medium").strip() or "medium",
                    severity=str(raw.get("severity") or "medium").strip() or "medium",
                    mitigation=str(raw.get("mitigation") or "").strip(),
                    owner=(str(raw.get("owner")).strip() if raw.get("owner") else None),
                    related_requirement_ids=list(raw.get("related_requirement_ids") or []),
                    created_at=now,
                ),
            )

    def _add_scores(
        self,
        option: ArchitectureOption,
        scores: list[Any],
        now: datetime,
    ) -> None:
        for index, raw in enumerate(scores):
            if not isinstance(raw, dict):
                raise ValueError(f"scores[{index}] must be an object")
            dimension = str(raw.get("dimension") or "").strip()
            if not dimension:
                raise ValueError(f"scores[{index}].dimension is required")
            self.db.add(
                SolutionScore(
                    id=uuid4(),
                    architecture_id=option.id,
                    dimension=dimension,
                    weight=float(raw.get("weight") or 0),
                    score=float(raw.get("score") or 0),
                    explanation=str(raw.get("explanation") or "").strip(),
                    created_at=now,
                ),
            )

    def _add_capacity_notes(
        self,
        option: ArchitectureOption,
        notes: list[Any],
        now: datetime,
    ) -> None:
        for index, raw in enumerate(notes):
            if not isinstance(raw, dict):
                raise ValueError(f"capacity_notes[{index}] must be an object")
            label = str(raw.get("label") or "").strip()
            if not label:
                raise ValueError(f"capacity_notes[{index}].label is required")
            self.db.add(
                CapacityNote(
                    id=uuid4(),
                    architecture_id=option.id,
                    project_id=option.project_id,
                    label=label,
                    input_value=(
                        str(raw.get("input_value")).strip()
                        if raw.get("input_value") is not None
                        else None
                    )
                    or None,
                    unit=(str(raw.get("unit")).strip() if raw.get("unit") is not None else None)
                    or None,
                    method=(
                        str(raw.get("method")).strip() if raw.get("method") is not None else None
                    )
                    or None,
                    assumption=(
                        str(raw.get("assumption")).strip()
                        if raw.get("assumption") is not None
                        else None
                    )
                    or None,
                    result=(
                        str(raw.get("result")).strip() if raw.get("result") is not None else None
                    )
                    or None,
                    confidence=float(raw.get("confidence") or 0),
                    related_requirement_ids=list(raw.get("related_requirement_ids") or []),
                    open_question=(
                        str(raw.get("open_question")).strip()
                        if raw.get("open_question") is not None
                        else None
                    )
                    or None,
                    created_at=now,
                ),
            )
