"""Stage D — deterministic gap analysis + clarification round-trip on Draft RKM."""

from __future__ import annotations

import copy
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.repositories.project_repository import ProjectRepository
from app.repositories.rkm_repository import RkmRepository
from app.schemas.gap import (
    ClarificationAnswerBatchIn,
    ClarificationAnswerResult,
    ClarificationOut,
    ConflictItem,
    GapAnalysisOut,
    GapItem,
    PublishBlocker,
)
from app.schemas.rkm import RkmDraftOut
from app.services.gap_scoring import (
    SECTION_WEIGHTS,
    compute_completeness_score,
    compute_confidence_score,
    compute_consistency_score,
    compute_evidence_coverage,
    overall_quality,
    quality_level,
    section_filled,
)

logger = logging.getLogger(__name__)

PUBLISH_THRESHOLD = 85.0
CLARIFICATION_MARKER = "Customer clarification:"
_SECTION_FROM_REASON = re.compile(r"Section '([a-z_]+)'")

_SECTION_CREATE_TITLES: dict[str, str] = {
    "business_objectives": "Business outcomes",
    "current_environment": "Current environment",
    "functional_requirements": "Functional requirement",
    "non_functional_requirements": "Non-functional requirement",
    "constraints": "Constraint",
    "dependencies": "Dependency",
    "risks": "Risk",
    "assumptions": "Assumption",
    "stakeholders": "Stakeholder",
}


class GapAnalysisService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = ProjectRepository(db)
        self.rkms = RkmRepository(db)

    def run_gap_analysis(self, project_id: UUID, user_id: UUID) -> GapAnalysisOut:
        self._require_project(project_id, user_id)
        row = self.rkms.ensure_active_draft(project_id)
        if row is None:
            raise NotFoundError("No Draft RKM found for this project")

        payload = copy.deepcopy(row.payload_json or {})
        report = self._build_report(project_id=project_id, rkm_id=row.id, version_label=row.version_label, payload=payload)

        # Persist scores + clarifications onto active Draft payload (same version).
        analysis = dict(payload.get("analysis") or {})
        analysis.update(
            {
                "confidence_score": report.confidence_score,
                "completeness_score": report.completeness_score,
                "consistency_score": report.consistency_score,
                "evidence_coverage": report.evidence_coverage,
                "reasoning_summary": (
                    str(analysis.get("reasoning_summary") or "").strip()
                    + " Gap analysis refreshed with deterministic scoring."
                ).strip(),
            },
        )
        payload["analysis"] = analysis
        # Preserve clarification IDs across re-runs (by question text) so in-progress
        # answers still match; keep previously answered items.
        previous = [
            item
            for item in (row.payload_json or {}).get("clarification_questions") or []
            if isinstance(item, dict)
        ]
        previous_by_question = {
            str(item.get("question") or "").strip().lower(): item
            for item in previous
            if str(item.get("question") or "").strip()
        }
        merged: list[dict[str, Any]] = []
        seen_questions: set[str] = set()
        for item in report.clarifications:
            data = item.model_dump(mode="json")
            key = str(data.get("question") or "").strip().lower()
            prior = previous_by_question.get(key)
            if prior is not None:
                # Reuse stable id; keep answered status/answer when present.
                data["id"] = str(prior.get("id") or data["id"])
                if prior.get("status") == "answered" and prior.get("answer"):
                    data["status"] = "answered"
                    data["answer"] = prior.get("answer")
            merged.append(data)
            if key:
                seen_questions.add(key)
        for item in previous:
            key = str(item.get("question") or "").strip().lower()
            if item.get("status") == "answered" and key and key not in seen_questions:
                merged.append(item)
                seen_questions.add(key)
        payload["clarification_questions"] = merged
        report.clarifications = [ClarificationOut.model_validate(item) for item in merged]

        row.payload_json = payload
        row.confidence_score = report.confidence_score
        row.completeness_score = report.completeness_score
        row.consistency_score = report.consistency_score
        row.evidence_coverage = report.evidence_coverage
        row.updated_at = datetime.now(timezone.utc)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)

        report.created_at = datetime.now(timezone.utc)
        return report

    def list_clarifications(self, project_id: UUID, user_id: UUID) -> list[ClarificationOut]:
        self._require_project(project_id, user_id)
        row = self.rkms.ensure_active_draft(project_id)
        if row is None:
            raise NotFoundError("No Draft RKM found for this project")
        items = (row.payload_json or {}).get("clarification_questions") or []
        return [ClarificationOut.model_validate(item) for item in items if isinstance(item, dict)]

    def generate_clarifications(self, project_id: UUID, user_id: UUID) -> list[ClarificationOut]:
        report = self.run_gap_analysis(project_id, user_id)
        return report.clarifications

    def answer_clarifications(
        self,
        project_id: UUID,
        user_id: UUID,
        body: ClarificationAnswerBatchIn,
    ) -> ClarificationAnswerResult:
        self._require_project(project_id, user_id)
        if not body.answers:
            raise ValidationAppError("At least one clarification answer is required")

        row = self.rkms.ensure_active_draft(project_id)
        if row is None:
            raise NotFoundError("No Draft RKM found for this project")

        payload = copy.deepcopy(row.payload_json or {})
        questions = list(payload.get("clarification_questions") or [])
        by_id = {
            str(item.get("id")): item
            for item in questions
            if isinstance(item, dict) and item.get("id")
        }

        answered = 0
        unknown_ids: list[str] = []
        new_evidence: list[dict[str, Any]] = list(payload.get("evidence") or [])
        for answer in body.answers:
            key = str(answer.clarification_id)
            item = by_id.get(key)
            if item is None:
                unknown_ids.append(key)
                continue
            text = (answer.answer or "").strip()
            if not text:
                raise ValidationAppError("Answer text is required")
            item["answer"] = text
            item["status"] = "answered"
            answered += 1

            evidence_id = uuid.uuid4()
            evidence_row = {
                "id": str(evidence_id),
                "source_type": "clarification_answer",
                "document_id": None,
                "page": None,
                "excerpt": text[:280],
                "field_name": None,
                "note": f"Answer to: {str(item.get('question') or '')[:120]}",
            }
            new_evidence.append(evidence_row)

            # Merge answer text into Draft RKM content + link clarification evidence.
            self._apply_clarification_answer(
                payload,
                clarification=item,
                answer_text=text,
                evidence_id=str(evidence_id),
            )

        if answered == 0:
            detail = ", ".join(unknown_ids[:3]) if unknown_ids else "none"
            raise ValidationAppError(
                "No matching clarification questions found for the submitted answers. "
                f"Run gap analysis again, then resubmit. Unknown ids: {detail}",
            )

        payload["evidence"] = new_evidence
        payload["clarification_questions"] = list(by_id.values())

        # Recalculate deterministic scores after answers.
        scores = {
            "completeness_score": compute_completeness_score(payload),
            "confidence_score": min(100.0, compute_confidence_score(payload) + (answered * 2)),
            "evidence_coverage": compute_evidence_coverage(payload),
        }
        conflicts = self._detect_conflicts(payload)
        scores["consistency_score"] = compute_consistency_score(payload, conflicts)
        analysis = dict(payload.get("analysis") or {})
        analysis.update(scores)
        analysis["reasoning_summary"] = (
            f"{str(analysis.get('reasoning_summary') or '').strip()} "
            f"Updated from {answered} clarification answer(s)."
        ).strip()
        payload["analysis"] = analysis

        major, minor, patch = self.rkms.next_draft_version(project_id)
        version_label = f"{major}.{minor}.{patch}"
        now = datetime.now(timezone.utc)
        payload["id"] = str(uuid.uuid4())  # temporary; replaced after create
        payload["version"] = {
            "number": version_label,
            "major": major,
            "minor": minor,
            "patch": patch,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "change_summary": f"Clarification answers applied ({answered})",
        }
        payload["approval"] = {
            "status": "ai_generated",
            "reviewed_by": None,
            "approved_by": None,
            "approved_at": None,
            "published_at": None,
        }

        # Requirement/evidence UUIDs must be unique across versions (PK). Remap
        # before persist so answer→minor-version never collides with the prior draft.
        payload = _remap_payload_entity_ids(payload)
        requirements, evidence_rows, links = _flatten_payload_for_persist(payload)
        validated = RkmDraftOut.model_validate(payload)

        created = self.rkms.create_draft(
            project_id=project_id,
            created_by=user_id,
            status="ai_generated",
            version_major=major,
            version_minor=minor,
            version_patch=patch,
            scores=scores,
            reasoning_summary=str(analysis.get("reasoning_summary") or ""),
            prompt_version=str(analysis.get("prompt_version") or "gap-analysis-1.0"),
            model=str(analysis.get("model") or "deterministic-gap"),
            payload_json=validated.model_dump(mode="json"),
            requirements=requirements,
            evidence=evidence_rows,
            links=links,
        )

        # Rewrite payload id/version timestamps to match persisted row.
        final_payload = copy.deepcopy(created.payload_json)
        final_payload["id"] = str(created.id)
        final_payload["version"]["created_at"] = created.created_at.isoformat()
        final_payload["version"]["updated_at"] = created.updated_at.isoformat()
        final_payload["version"]["number"] = created.version_label
        created.payload_json = final_payload
        self.db.add(created)
        self.db.commit()
        self.db.refresh(created)

        clarifications = [
            ClarificationOut.model_validate(item)
            for item in (final_payload.get("clarification_questions") or [])
            if isinstance(item, dict)
        ]
        return ClarificationAnswerResult(
            project_id=project_id,
            rkm_id=created.id,
            version_label=created.version_label,
            answered_count=answered,
            clarifications=clarifications,
            draft=final_payload,
        )

    def _build_report(
        self,
        *,
        project_id: UUID,
        rkm_id: UUID,
        version_label: str,
        payload: dict[str, Any],
    ) -> GapAnalysisOut:
        missing = [section for section in SECTION_WEIGHTS if not section_filled(payload, section)]
        gaps = self._detect_gaps(payload, missing)
        conflicts = self._detect_conflicts(payload)
        completeness = compute_completeness_score(payload)
        confidence = compute_confidence_score(payload)
        evidence_coverage = compute_evidence_coverage(payload)
        consistency = compute_consistency_score(payload, [c.model_dump() for c in conflicts])
        overall = overall_quality(completeness, confidence)
        blockers = self._publish_blockers(completeness, confidence, gaps, payload)
        clarifications = self._build_clarifications(payload, missing, gaps)

        return GapAnalysisOut(
            project_id=project_id,
            rkm_id=rkm_id,
            version_label=version_label,
            completeness_score=completeness,
            confidence_score=confidence,
            consistency_score=consistency,
            evidence_coverage=evidence_coverage,
            overall_quality=overall,
            quality_level=quality_level(overall),
            missing_sections=missing,
            gaps=gaps,
            conflicts=conflicts,
            publish_blockers=blockers,
            clarifications=clarifications,
        )

    def _detect_gaps(self, payload: dict[str, Any], missing: list[str]) -> list[GapItem]:
        gaps: list[GapItem] = []
        for section in missing:
            severity = "critical" if section in {
                "business_objectives",
                "functional_requirements",
                "non_functional_requirements",
            } else "high"
            gaps.append(
                GapItem(
                    code=f"missing_{section}",
                    section=section,
                    severity=severity,
                    message=f"Missing or empty section: {section.replace('_', ' ')}",
                ),
            )

        # Thin descriptions / missing evidence.
        for section in SECTION_WEIGHTS:
            if section == "current_environment":
                items = list((payload.get("current_environment") or {}).get("items") or [])
            else:
                items = list(payload.get(section) or [])
            for item in items:
                if not isinstance(item, dict):
                    continue
                item_id = item.get("id")
                affected = [UUID(str(item_id))] if item_id else []
                label = str(
                    item.get("title")
                    or item.get("name")
                    or item.get("role")
                    or "untitled",
                ).strip()
                description = str(
                    item.get("description")
                    or item.get("designation")
                    or item.get("role")
                    or "",
                ).strip()
                # Stakeholders often only have name/contact; don't treat as thin content.
                if section != "stakeholders" and len(description) < 20:
                    gaps.append(
                        GapItem(
                            code="thin_description",
                            section=section,
                            severity="medium",
                            message=f"Requirement needs more detail: {label}",
                            affected_requirement_ids=affected,
                        ),
                    )
                evidence_ids = item.get("evidence_ids") or []
                if not evidence_ids:
                    gaps.append(
                        GapItem(
                            code="missing_evidence",
                            section=section,
                            severity="high",
                            message=f"No evidence linked for: {label}",
                            affected_requirement_ids=affected,
                        ),
                    )
        return gaps

    def _detect_conflicts(self, payload: dict[str, Any]) -> list[ConflictItem]:
        conflicts: list[ConflictItem] = []
        functional = list(payload.get("functional_requirements") or [])
        constraints = list(payload.get("constraints") or [])
        # MVP heuristic: mention of "outdoor" vs "indoor only" style contradictions in titles/descriptions.
        texts = []
        for item in functional + constraints:
            if isinstance(item, dict):
                texts.append(
                    (
                        str(item.get("id") or ""),
                        f"{item.get('title') or ''} {item.get('description') or ''}".lower(),
                    ),
                )
        outdoor_ids = [UUID(i) for i, t in texts if i and "outdoor" in t]
        indoor_only_ids = [UUID(i) for i, t in texts if i and ("indoor only" in t or "no outdoor" in t)]
        if outdoor_ids and indoor_only_ids:
            conflicts.append(
                ConflictItem(
                    code="indoor_outdoor_conflict",
                    message="Possible conflict between outdoor coverage and indoor-only constraints.",
                    affected_requirement_ids=[*outdoor_ids[:3], *indoor_only_ids[:3]],
                ),
            )

        if functional and not payload.get("dependencies"):
            conflicts.append(
                ConflictItem(
                    code="missing_dependency_review",
                    message="Functional requirements exist but dependencies are empty — verify integrations/dependencies.",
                    affected_requirement_ids=[
                        UUID(str(item.get("id")))
                        for item in functional[:3]
                        if isinstance(item, dict) and item.get("id")
                    ],
                ),
            )
        return conflicts

    def _publish_blockers(
        self,
        completeness: float,
        confidence: float,
        gaps: list[GapItem],
        payload: dict[str, Any],
    ) -> list[PublishBlocker]:
        blockers: list[PublishBlocker] = []
        if completeness < PUBLISH_THRESHOLD:
            blockers.append(
                PublishBlocker(
                    code="completeness_below_threshold",
                    message=f"Completeness {completeness} is below publish threshold {PUBLISH_THRESHOLD}.",
                ),
            )
        if confidence < PUBLISH_THRESHOLD:
            blockers.append(
                PublishBlocker(
                    code="confidence_below_threshold",
                    message=f"Confidence {confidence} is below publish threshold {PUBLISH_THRESHOLD}.",
                ),
            )
        critical_gaps = [g for g in gaps if g.severity == "critical"]
        if critical_gaps:
            blockers.append(
                PublishBlocker(
                    code="critical_gaps_present",
                    message=f"{len(critical_gaps)} critical gap(s) must be resolved before publish.",
                ),
            )
        approval = (payload.get("approval") or {}).get("status")
        if approval not in {"approved", "published"}:
            blockers.append(
                PublishBlocker(
                    code="human_approval_required",
                    message="Human approval is required before publish (ATLAS-022).",
                ),
            )
        return blockers

    def _build_clarifications(
        self,
        payload: dict[str, Any],
        missing: list[str],
        gaps: list[GapItem],
    ) -> list[ClarificationOut]:
        questions: list[ClarificationOut] = []

        section_questions = {
            "business_objectives": (
                "critical",
                "Business",
                "What business outcomes and success metrics are mandatory for go-live?",
            ),
            "current_environment": (
                "high",
                "Infrastructure",
                "What is the as-is environment (sites, existing network/WiFi/security controls)?",
            ),
            "functional_requirements": (
                "critical",
                "Technical",
                "Which functional capabilities are must-have versus optional for phase 1?",
            ),
            "non_functional_requirements": (
                "critical",
                "Technical",
                "What availability, performance, and security targets are non-negotiable?",
            ),
            "constraints": (
                "high",
                "Business",
                "What budget, timeline, or technical constraints bound the solution?",
            ),
            "dependencies": (
                "high",
                "Technical",
                "Which systems, vendors, or teams must this solution integrate with or depend on?",
            ),
            "risks": (
                "medium",
                "Operations",
                "Which delivery or operational risks are already known and accepted?",
            ),
            "stakeholders": (
                "high",
                "Business",
                "Who are the decision-makers and technical contacts for requirements sign-off?",
            ),
            "assumptions": (
                "medium",
                "Business",
                "Which assumptions should be treated as confirmed facts versus open questions?",
            ),
        }

        for section in missing:
            if section not in section_questions:
                continue
            priority, category, question = section_questions[section]
            questions.append(
                ClarificationOut(
                    id=uuid.uuid4(),
                    question=question,
                    priority=priority,
                    category=category,
                    reason=f"Section '{section}' is missing or empty in the Draft RKM.",
                    section=section,
                    affected_requirement_ids=[],
                    status="open",
                    answer=None,
                    confidence_impact=8.0,
                ),
            )

        # Domain-aware extras from functional text — only tag matching requirements.
        def _ids_matching(*tokens: str) -> list[UUID]:
            matched: list[UUID] = []
            for item in payload.get("functional_requirements") or []:
                if not isinstance(item, dict) or not item.get("id"):
                    continue
                text = f"{item.get('title') or ''} {item.get('description') or ''}".lower()
                if any(token in text for token in tokens):
                    matched.append(UUID(str(item.get("id"))))
            return matched[:5]

        wifi_ids = _ids_matching("wifi", "wi-fi", "wireless", "wlan", "wap")
        if wifi_ids:
            questions.append(
                ClarificationOut(
                    id=uuid.uuid4(),
                    question="Which buildings/floors need WiFi coverage, and what concurrent user density is expected?",
                    priority="high",
                    category="Networking",
                    reason="Wireless/WiFi requirements are present but coverage scope/density is unclear.",
                    section="functional_requirements",
                    affected_requirement_ids=wifi_ids,
                    status="open",
                    confidence_impact=10.0,
                ),
            )
        security_ids = _ids_matching("firewall", "security")
        if security_ids:
            questions.append(
                ClarificationOut(
                    id=uuid.uuid4(),
                    question="What firewall throughput, HA model, and inspection scope are required?",
                    priority="high",
                    category="Security",
                    reason="Security controls are referenced without measurable targets.",
                    section="functional_requirements",
                    affected_requirement_ids=security_ids,
                    status="open",
                    confidence_impact=8.0,
                ),
            )

        # One question per thin/missing-evidence gap (cap).
        for gap in gaps:
            if gap.code not in {"thin_description", "missing_evidence"}:
                continue
            if len(questions) >= 12:
                break
            questions.append(
                ClarificationOut(
                    id=uuid.uuid4(),
                    question=f"Please clarify: {gap.message}",
                    priority=gap.severity if gap.severity in {"critical", "high", "medium", "low"} else "medium",
                    category=gap.section.replace("_", " ").title(),
                    reason=gap.message,
                    section=gap.section,
                    affected_requirement_ids=gap.affected_requirement_ids,
                    status="open",
                    confidence_impact=5.0,
                ),
            )

        # Deduplicate by question text.
        deduped: list[ClarificationOut] = []
        seen: set[str] = set()
        for item in questions:
            key = item.question.strip().lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped[:12]

    def _apply_clarification_answer(
        self,
        payload: dict[str, Any],
        *,
        clarification: dict[str, Any],
        answer_text: str,
        evidence_id: str,
    ) -> None:
        """Merge customer answer into Draft RKM content (not evidence-only)."""
        affected = [str(x) for x in (clarification.get("affected_requirement_ids") or [])]
        section = self._resolve_clarification_section(clarification)
        impact = 10.0
        try:
            impact = float(clarification.get("confidence_impact") or 10.0)
        except (TypeError, ValueError):
            impact = 10.0

        updated = self._enrich_items_with_answer(
            payload,
            requirement_ids=affected,
            answer_text=answer_text,
            evidence_id=evidence_id,
            question=str(clarification.get("question") or ""),
            confidence_bump=impact,
        )
        if updated:
            return

        # Missing-section / unmatched answers: create concrete RKM content.
        target_section = section or "assumptions"
        self._create_item_from_answer(
            payload,
            section=target_section,
            answer_text=answer_text,
            evidence_id=evidence_id,
            clarification=clarification,
            confidence=min(100.0, 55.0 + impact),
        )

    def _resolve_clarification_section(self, clarification: dict[str, Any]) -> str | None:
        section = clarification.get("section")
        if isinstance(section, str) and section in SECTION_WEIGHTS:
            return section

        reason = str(clarification.get("reason") or "")
        match = _SECTION_FROM_REASON.search(reason)
        if match and match.group(1) in SECTION_WEIGHTS:
            return match.group(1)

        category = str(clarification.get("category") or "").strip().lower()
        for key in SECTION_WEIGHTS:
            label = key.replace("_", " ")
            if category == key or category == label:
                return key

        category_map = {
            "networking": "functional_requirements",
            "security": "functional_requirements",
            "infrastructure": "current_environment",
            "business": "business_objectives",
            "technical": "functional_requirements",
            "operations": "risks",
        }
        return category_map.get(category)

    def _enrich_items_with_answer(
        self,
        payload: dict[str, Any],
        *,
        requirement_ids: list[str],
        answer_text: str,
        evidence_id: str,
        question: str,
        confidence_bump: float,
    ) -> int:
        if not requirement_ids:
            return 0
        targets = set(requirement_ids)
        updated = 0

        requirement_sections = [
            "business_objectives",
            "functional_requirements",
            "non_functional_requirements",
            "constraints",
            "dependencies",
            "risks",
            "assumptions",
        ]
        for section in requirement_sections:
            items = list(payload.get(section) or [])
            changed = False
            for item in items:
                if not isinstance(item, dict):
                    continue
                if str(item.get("id")) not in targets:
                    continue
                item["description"] = _merge_answer_into_text(
                    str(item.get("description") or ""),
                    answer_text,
                )
                self._link_evidence_and_bump(item, evidence_id, confidence_bump)
                updated += 1
                changed = True
            if changed:
                payload[section] = items

        env = dict(payload.get("current_environment") or {})
        env_items = list(env.get("items") or [])
        env_changed = False
        for item in env_items:
            if not isinstance(item, dict):
                continue
            if str(item.get("id")) not in targets:
                continue
            item["description"] = _merge_answer_into_text(
                str(item.get("description") or ""),
                answer_text,
            )
            self._link_evidence_and_bump(item, evidence_id, confidence_bump)
            updated += 1
            env_changed = True
        if env_changed:
            env["items"] = env_items
            if not str(env.get("summary") or "").strip():
                env["summary"] = answer_text[:500]
            payload["current_environment"] = env

        stakeholders = list(payload.get("stakeholders") or [])
        stake_changed = False
        for item in stakeholders:
            if not isinstance(item, dict):
                continue
            if str(item.get("id")) not in targets:
                continue
            designation = str(item.get("designation") or item.get("role") or "")
            merged = _merge_answer_into_text(designation, answer_text)
            item["designation"] = merged
            if not str(item.get("role") or "").strip():
                item["role"] = answer_text[:160]
            self._link_evidence_and_bump(item, evidence_id, confidence_bump)
            updated += 1
            stake_changed = True
        if stake_changed:
            payload["stakeholders"] = stakeholders

        # Fallback: if IDs were stale, still surface the answer somewhere readable.
        if updated == 0 and answer_text.strip():
            logger.info(
                "Clarification answer had affected ids but none matched; creating fallback content. question=%s",
                question[:80],
            )
        return updated

    def _create_item_from_answer(
        self,
        payload: dict[str, Any],
        *,
        section: str,
        answer_text: str,
        evidence_id: str,
        clarification: dict[str, Any],
        confidence: float,
    ) -> None:
        title = _title_from_clarification(clarification, section)
        item_id = str(uuid.uuid4())

        if section == "stakeholders":
            name, role = _parse_stakeholder_answer(answer_text)
            stakeholders = list(payload.get("stakeholders") or [])
            stakeholders.append(
                {
                    "id": item_id,
                    "name": name or title,
                    "role": role,
                    "contact": None,
                    "designation": answer_text.strip(),
                    "evidence_ids": [evidence_id],
                },
            )
            payload["stakeholders"] = stakeholders
            return

        if section == "current_environment":
            env = dict(payload.get("current_environment") or {})
            items = list(env.get("items") or [])
            items.append(
                {
                    "id": item_id,
                    "title": title,
                    "description": answer_text.strip(),
                    "evidence_ids": [evidence_id],
                    "confidence": confidence,
                    "priority": clarification.get("priority") or "high",
                    "status": "draft",
                    "category": "infrastructure",
                },
            )
            env["items"] = items
            if not str(env.get("summary") or "").strip():
                env["summary"] = answer_text.strip()[:500]
            else:
                summary = str(env.get("summary") or "").strip()
                if answer_text.strip() not in summary:
                    env["summary"] = f"{summary}\n\n{CLARIFICATION_MARKER} {answer_text.strip()}"[:1000]
            payload["current_environment"] = env
            return

        requirement = {
            "id": item_id,
            "title": title,
            "description": answer_text.strip(),
            "priority": clarification.get("priority") or "high",
            "status": "draft",
            "confidence": confidence,
            "evidence_ids": [evidence_id],
            "category": {
                "business_objectives": "business",
                "functional_requirements": "functional",
                "non_functional_requirements": "non_functional",
                "constraints": "business",
                "dependencies": "functional",
                "risks": "business",
                "assumptions": "business",
            }.get(section, "business"),
        }
        items = list(payload.get(section) or [])
        items.append(requirement)
        payload[section] = items

    @staticmethod
    def _link_evidence_and_bump(
        item: dict[str, Any],
        evidence_id: str,
        confidence_bump: float,
    ) -> None:
        evidence_ids = list(item.get("evidence_ids") or [])
        if evidence_id not in evidence_ids:
            evidence_ids.append(evidence_id)
        item["evidence_ids"] = evidence_ids
        try:
            current = float(item.get("confidence") or 50)
        except (TypeError, ValueError):
            current = 50.0
        item["confidence"] = min(100.0, current + max(5.0, confidence_bump))

    def _require_project(self, project_id: UUID, user_id: UUID):
        project = self.projects.get_for_user(project_id, user_id)
        if project is None:
            raise NotFoundError("Project not found")
        return project


def _merge_answer_into_text(existing: str, answer: str) -> str:
    existing = (existing or "").strip()
    answer = (answer or "").strip()
    if not answer:
        return existing
    if answer in existing:
        return existing
    if not existing or len(existing) < 20:
        if existing and existing.lower() not in answer.lower():
            return f"{answer}\n\n(Prior note: {existing})"
        return answer
    return f"{existing}\n\n{CLARIFICATION_MARKER} {answer}"


def _title_from_clarification(clarification: dict[str, Any], section: str) -> str:
    default = _SECTION_CREATE_TITLES.get(section, "Clarified requirement")
    question = str(clarification.get("question") or "").strip()
    if question.lower().startswith("please clarify:"):
        rest = question.split(":", 1)[-1].strip()
        # "Requirement needs more detail: Campus WiFi" → Campus WiFi
        if ":" in rest:
            rest = rest.split(":")[-1].strip()
        return (rest or default)[:80]
    return default


def _parse_stakeholder_answer(answer: str) -> tuple[str, str | None]:
    text = (answer or "").strip()
    if not text:
        return "Clarified stakeholder", None
    first_line = text.splitlines()[0].strip()
    if "," in first_line:
        parts = [part.strip() for part in first_line.split(",") if part.strip()]
        name = parts[0]
        role = ", ".join(parts[1:]) if len(parts) > 1 else None
        return name[:120], (role[:160] if role else None)
    if " - " in first_line:
        name, role = first_line.split(" - ", 1)
        return name.strip()[:120], role.strip()[:160] or None
    return first_line[:120], None


def _remap_payload_entity_ids(payload: dict[str, Any]) -> dict[str, Any]:
    """Assign fresh UUIDs to requirements/evidence so new versions can persist."""
    data = copy.deepcopy(payload)
    id_map: dict[str, str] = {}

    def map_id(old: Any) -> str | None:
        if old is None:
            return None
        key = str(old)
        if key not in id_map:
            id_map[key] = str(uuid.uuid4())
        return id_map[key]

    def remap_items(items: list[Any]) -> list[dict[str, Any]]:
        remapped: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            row = dict(item)
            if row.get("id") is not None:
                row["id"] = map_id(row.get("id"))
            evidence_ids = []
            for evidence_id in row.get("evidence_ids") or []:
                mapped = map_id(evidence_id)
                if mapped:
                    evidence_ids.append(mapped)
            row["evidence_ids"] = evidence_ids
            remapped.append(row)
        return remapped

    for section in (
        "business_objectives",
        "functional_requirements",
        "non_functional_requirements",
        "constraints",
        "dependencies",
        "risks",
        "assumptions",
    ):
        data[section] = remap_items(list(data.get(section) or []))

    env = dict(data.get("current_environment") or {})
    env["items"] = remap_items(list(env.get("items") or []))
    data["current_environment"] = env

    stakeholders = []
    for item in list(data.get("stakeholders") or []):
        if not isinstance(item, dict):
            continue
        row = dict(item)
        if row.get("id") is not None:
            row["id"] = map_id(row.get("id"))
        evidence_ids = []
        for evidence_id in row.get("evidence_ids") or []:
            mapped = map_id(evidence_id)
            if mapped:
                evidence_ids.append(mapped)
        row["evidence_ids"] = evidence_ids
        stakeholders.append(row)
    data["stakeholders"] = stakeholders

    evidence_rows = []
    for item in list(data.get("evidence") or []):
        if not isinstance(item, dict):
            continue
        row = dict(item)
        if row.get("id") is not None:
            row["id"] = map_id(row.get("id"))
        evidence_rows.append(row)
    data["evidence"] = evidence_rows

    clarifications = []
    for item in list(data.get("clarification_questions") or []):
        if not isinstance(item, dict):
            continue
        row = dict(item)
        affected = []
        for requirement_id in row.get("affected_requirement_ids") or []:
            key = str(requirement_id)
            affected.append(id_map.get(key, key))
        row["affected_requirement_ids"] = affected
        clarifications.append(row)
    data["clarification_questions"] = clarifications
    return data


def _flatten_payload_for_persist(
    payload: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[tuple[UUID, UUID]]]:
    """Convert RKM JSON payload into normalized rows for create_draft."""
    requirements: list[dict[str, Any]] = []
    links: list[tuple[UUID, UUID]] = []

    def add_section(section: str, items: list[Any], *, default_category: str | None = None) -> None:
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            try:
                item_id = UUID(str(item.get("id")))
            except (TypeError, ValueError):
                item_id = uuid.uuid4()
                item["id"] = str(item_id)
            requirements.append(
                {
                    "id": item_id,
                    "section": section,
                    "category": item.get("category") or default_category,
                    "subcategory": item.get("subcategory"),
                    "title": str(item.get("title") or item.get("name") or f"{section} {index + 1}"),
                    "description": str(item.get("description") or item.get("role") or ""),
                    "priority": item.get("priority") or "medium",
                    "status": item.get("status") or "draft",
                    "confidence": float(item.get("confidence") or 0),
                    "sort_order": index,
                },
            )
            for evidence_id in item.get("evidence_ids") or []:
                try:
                    links.append((item_id, UUID(str(evidence_id))))
                except (TypeError, ValueError):
                    continue

    add_section("business_objectives", list(payload.get("business_objectives") or []), default_category="business")
    add_section(
        "functional_requirements",
        list(payload.get("functional_requirements") or []),
        default_category="functional",
    )
    add_section(
        "non_functional_requirements",
        list(payload.get("non_functional_requirements") or []),
        default_category="non_functional",
    )
    add_section("constraints", list(payload.get("constraints") or []), default_category="business")
    add_section("dependencies", list(payload.get("dependencies") or []), default_category="functional")
    add_section("risks", list(payload.get("risks") or []), default_category="business")
    add_section("assumptions", list(payload.get("assumptions") or []), default_category="business")
    add_section(
        "current_environment",
        list((payload.get("current_environment") or {}).get("items") or []),
        default_category="infrastructure",
    )
    # Stakeholders stored with name instead of title.
    for index, item in enumerate(list(payload.get("stakeholders") or [])):
        if not isinstance(item, dict):
            continue
        try:
            item_id = UUID(str(item.get("id")))
        except (TypeError, ValueError):
            item_id = uuid.uuid4()
            item["id"] = str(item_id)
        requirements.append(
            {
                "id": item_id,
                "section": "stakeholders",
                "category": "business",
                "subcategory": None,
                "title": str(item.get("name") or f"Stakeholder {index + 1}"),
                "description": str(item.get("designation") or item.get("role") or ""),
                "priority": "high",
                "status": "draft",
                "confidence": 80,
                "sort_order": index,
            },
        )
        for evidence_id in item.get("evidence_ids") or []:
            try:
                links.append((item_id, UUID(str(evidence_id))))
            except (TypeError, ValueError):
                continue

    evidence_rows: list[dict[str, Any]] = []
    for item in list(payload.get("evidence") or []):
        if not isinstance(item, dict):
            continue
        try:
            evidence_id = UUID(str(item.get("id")))
        except (TypeError, ValueError):
            evidence_id = uuid.uuid4()
            item["id"] = str(evidence_id)
        document_id = item.get("document_id")
        evidence_rows.append(
            {
                "id": evidence_id,
                "source_type": item.get("source_type") or "workshop",
                "document_id": UUID(str(document_id)) if document_id else None,
                "page": item.get("page"),
                "excerpt": item.get("excerpt"),
                "field_name": item.get("field_name"),
                "note": item.get("note"),
            },
        )

    return requirements, evidence_rows, links
