"""Stage E — Draft review, approve, publish gate, version compare."""

from __future__ import annotations

import copy
import uuid
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models.requirement_model import RequirementModel
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.repositories.rkm_repository import RkmRepository
from app.schemas.gap import PublishBlocker
from app.schemas.governance import (
    ApproveIn,
    ApproveResult,
    PublishIn,
    PublishResult,
    RequirementEditIn,
    ReviewIn,
    ReviewResult,
    VersionCompareOut,
    VersionDiffItem,
    VersionForkIn,
)
from app.schemas.rkm import RkmDraftOut
from app.services.gap_analysis_service import (
    GapAnalysisService,
    _flatten_payload_for_persist,
    _remap_payload_entity_ids,
)

_EDITABLE_SECTIONS = (
    "business_objectives",
    "functional_requirements",
    "non_functional_requirements",
    "constraints",
    "dependencies",
    "risks",
    "assumptions",
)


class RkmGovernanceService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = ProjectRepository(db)
        self.rkms = RkmRepository(db)
        self.gap = GapAnalysisService(db)

    def get_by_status(self, project_id: UUID, user_id: UUID, status: str | None) -> RkmDraftOut:
        self._require_project(project_id, user_id)
        normalized = (status or "draft").strip().lower()
        if normalized in {"published"}:
            row = self.rkms.get_published(project_id)
            if row is None:
                raise NotFoundError("No Published RKM found for this project")
            return RkmDraftOut.model_validate(row.payload_json)
        if normalized in {"draft", "ai_generated", "active", "under_review", "approved", "reviewed"}:
            row = self.rkms.ensure_active_draft(project_id)
            if row is None:
                raise NotFoundError("No Draft RKM found for this project")
            return RkmDraftOut.model_validate(row.payload_json)
        raise ValidationAppError(
            "status must be one of: draft, published, under_review, approved",
        )

    def review(
        self,
        project_id: UUID,
        user_id: UUID,
        body: ReviewIn,
        actor: User,
    ) -> ReviewResult:
        self._require_project(project_id, user_id)
        row = self._require_mutable_draft(project_id)
        if not body.edits and not (body.reasoning_note or "").strip():
            raise ValidationAppError("Provide at least one requirement edit or a reasoning note")

        payload = copy.deepcopy(row.payload_json or {})
        edited = self._apply_edits(payload, body.edits)
        if body.edits and edited == 0:
            raise ValidationAppError("No matching requirement ids found for the submitted edits")

        analysis = dict(payload.get("analysis") or {})
        note = (body.reasoning_note or "").strip()
        if note:
            prior = str(analysis.get("reasoning_summary") or "").strip()
            analysis["reasoning_summary"] = f"{prior} Review note: {note}".strip()
        payload["analysis"] = analysis

        change_summary = (body.change_summary or "").strip() or (
            f"Human review edits ({edited})" if edited else "Human review note"
        )
        created = self._persist_new_version(
            project_id=project_id,
            user_id=user_id,
            payload=payload,
            version_parts=self.rkms.next_patch_version(project_id),
            status="under_review",
            change_summary=change_summary,
            approval_status="under_review",
            actor_email=actor.email,
            as_reviewed_by=True,
        )
        return ReviewResult(
            project_id=project_id,
            rkm_id=created.id,
            version_label=created.version_label,
            edited_count=edited,
            draft=RkmDraftOut.model_validate(created.payload_json),
        )

    def approve(
        self,
        project_id: UUID,
        user_id: UUID,
        body: ApproveIn,
        actor: User,
    ) -> ApproveResult:
        self._require_project(project_id, user_id)
        row = self._require_mutable_draft(project_id)
        payload = copy.deepcopy(row.payload_json or {})

        # Soft gate: warn via blockers but allow approve so human can acknowledge.
        # Publish still enforces hard blockers.
        now = datetime.now(timezone.utc)
        approval = dict(payload.get("approval") or {})
        approval.update(
            {
                "status": "approved",
                "approved_by": actor.email,
                "approved_at": now.isoformat(),
                "reviewed_by": approval.get("reviewed_by") or actor.email,
            },
        )
        payload["approval"] = approval
        analysis = dict(payload.get("analysis") or {})
        note = (body.note or "").strip()
        if note:
            prior = str(analysis.get("reasoning_summary") or "").strip()
            analysis["reasoning_summary"] = f"{prior} Approval note: {note}".strip()
            payload["analysis"] = analysis

        # Approval is a governance stamp on the same version (no content change).
        validated = RkmDraftOut.model_validate(payload)
        row.payload_json = validated.model_dump(mode="json")
        row.status = "approved"
        row.updated_at = now
        if note:
            row.reasoning_summary = str(analysis.get("reasoning_summary") or row.reasoning_summary)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)

        draft = RkmDraftOut.model_validate(row.payload_json)
        return ApproveResult(
            project_id=project_id,
            rkm_id=row.id,
            version_label=row.version_label,
            status="approved",
            approved_by=actor.email,
            approved_at=now,
            draft=draft,
        )

    def publish(
        self,
        project_id: UUID,
        user_id: UUID,
        body: PublishIn,
        actor: User,
    ) -> PublishResult:
        self._require_project(project_id, user_id)
        row = self._require_mutable_draft(project_id)
        payload = copy.deepcopy(row.payload_json or {})

        blockers = self._evaluate_publish_blockers(row, payload)
        if blockers:
            codes = ", ".join(item.code for item in blockers)
            raise ValidationAppError(
                f"Publish blocked ({len(blockers)}): {codes}. "
                "Resolve gap scores, critical gaps, and human approval first.",
            )

        now = datetime.now(timezone.utc)
        approval = dict(payload.get("approval") or {})
        approval.update(
            {
                "status": "published",
                "approved_by": approval.get("approved_by") or actor.email,
                "approved_at": approval.get("approved_at") or now.isoformat(),
                "published_at": now.isoformat(),
                "reviewed_by": approval.get("reviewed_by") or actor.email,
            },
        )
        payload["approval"] = approval
        analysis = dict(payload.get("analysis") or {})
        note = (body.note or "").strip()
        if note:
            prior = str(analysis.get("reasoning_summary") or "").strip()
            analysis["reasoning_summary"] = f"{prior} Publish note: {note}".strip()
            payload["analysis"] = analysis
            row.reasoning_summary = str(analysis.get("reasoning_summary") or "")

        version = dict(payload.get("version") or {})
        version["updated_at"] = now.isoformat()
        version["change_summary"] = (
            str(version.get("change_summary") or "").strip() or "Published for Phase 3 consumption"
        )
        payload["version"] = version

        validated = RkmDraftOut.model_validate(payload)
        self.rkms.archive_published(project_id, except_id=row.id)
        row.payload_json = validated.model_dump(mode="json")
        row.status = "published"
        row.is_active_draft = False
        row.updated_at = now
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)

        return PublishResult(
            project_id=project_id,
            rkm_id=row.id,
            version_label=row.version_label,
            status="published",
            published_at=now,
            draft=RkmDraftOut.model_validate(row.payload_json),
            publish_blockers=[],
        )

    def fork_version(
        self,
        project_id: UUID,
        user_id: UUID,
        body: VersionForkIn,
        actor: User,
    ) -> ReviewResult:
        """Create a new active Draft from a published (or specified) immutable snapshot."""
        self._require_project(project_id, user_id)
        source: RequirementModel | None
        if body.from_version:
            source = self.rkms.get_by_version_label(project_id, body.from_version.strip())
            if source is None:
                raise NotFoundError("Source RKM version not found")
        else:
            source = self.rkms.get_published(project_id)
            if source is None:
                source = self.rkms.ensure_active_draft(project_id)
            if source is None:
                raise NotFoundError("No RKM version available to fork")

        active = self.rkms.get_active_draft(project_id)
        if active is not None:
            raise ConflictError(
                "An active Draft already exists. Publish or continue editing it before forking.",
            )

        payload = copy.deepcopy(source.payload_json or {})
        change_summary = (body.change_summary or "").strip() or (
            f"Forked from v{source.version_label} for continued review"
        )
        created = self._persist_new_version(
            project_id=project_id,
            user_id=user_id,
            payload=payload,
            version_parts=self.rkms.next_draft_version(project_id),
            status="under_review",
            change_summary=change_summary,
            approval_status="under_review",
            actor_email=actor.email,
            as_reviewed_by=True,
        )
        return ReviewResult(
            project_id=project_id,
            rkm_id=created.id,
            version_label=created.version_label,
            edited_count=0,
            draft=RkmDraftOut.model_validate(created.payload_json),
        )

    def compare(
        self,
        project_id: UUID,
        user_id: UUID,
        from_version: str,
        to_version: str,
    ) -> VersionCompareOut:
        self._require_project(project_id, user_id)
        left = self.rkms.get_by_version_label(project_id, from_version.strip())
        right = self.rkms.get_by_version_label(project_id, to_version.strip())
        if left is None or right is None:
            raise NotFoundError("One or both RKM versions were not found")

        left_payload = left.payload_json or {}
        right_payload = right.payload_json or {}
        diffs = self._diff_payloads(left_payload, right_payload)
        left_reasoning = str((left_payload.get("analysis") or {}).get("reasoning_summary") or "")
        right_reasoning = str((right_payload.get("analysis") or {}).get("reasoning_summary") or "")
        return VersionCompareOut(
            project_id=project_id,
            from_version=left.version_label,
            to_version=right.version_label,
            from_status=left.status,
            to_status=right.status,
            from_reasoning=left_reasoning,
            to_reasoning=right_reasoning,
            diffs=diffs,
            summary={
                "added": sum(1 for d in diffs if d.change_type == "added"),
                "removed": sum(1 for d in diffs if d.change_type == "removed"),
                "modified": sum(1 for d in diffs if d.change_type == "modified"),
                "reasoning_changed": left_reasoning.strip() != right_reasoning.strip(),
            },
        )

    def _evaluate_publish_blockers(
        self,
        row: RequirementModel,
        payload: dict[str, Any],
    ) -> list[PublishBlocker]:
        report = self.gap._build_report(
            project_id=row.project_id,
            rkm_id=row.id,
            version_label=row.version_label,
            payload=payload,
        )
        return list(report.publish_blockers)

    def _apply_edits(self, payload: dict[str, Any], edits: list[RequirementEditIn]) -> int:
        if not edits:
            return 0
        by_id: dict[str, dict[str, Any]] = {}
        for section in _EDITABLE_SECTIONS:
            for item in list(payload.get(section) or []):
                if isinstance(item, dict) and item.get("id"):
                    by_id[str(item["id"])] = item
        env = dict(payload.get("current_environment") or {})
        for item in list(env.get("items") or []):
            if isinstance(item, dict) and item.get("id"):
                by_id[str(item["id"])] = item
        payload["current_environment"] = env
        for item in list(payload.get("stakeholders") or []):
            if isinstance(item, dict) and item.get("id"):
                by_id[str(item["id"])] = item

        edited = 0
        for edit in edits:
            target = by_id.get(str(edit.id))
            if target is None:
                continue
            if edit.title is not None:
                if "name" in target and "title" not in target:
                    target["name"] = edit.title.strip()
                else:
                    target["title"] = edit.title.strip()
            if edit.description is not None:
                if "role" in target and "description" not in target and "name" in target:
                    target["role"] = edit.description.strip()
                else:
                    target["description"] = edit.description.strip()
            if edit.priority is not None and "name" not in target:
                target["priority"] = edit.priority.strip().lower()
            edited += 1
        return edited

    def _persist_new_version(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        payload: dict[str, Any],
        version_parts: tuple[int, int, int],
        status: str,
        change_summary: str,
        approval_status: str,
        actor_email: str,
        as_reviewed_by: bool,
    ) -> RequirementModel:
        major, minor, patch = version_parts
        version_label = f"{major}.{minor}.{patch}"
        now = datetime.now(timezone.utc)
        payload = copy.deepcopy(payload)
        payload["id"] = str(uuid.uuid4())
        payload["project_id"] = str(project_id)
        payload["version"] = {
            "number": version_label,
            "major": major,
            "minor": minor,
            "patch": patch,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "change_summary": change_summary,
        }
        approval = {
            "status": approval_status,
            "reviewed_by": actor_email if as_reviewed_by else None,
            "approved_by": None,
            "approved_at": None,
            "published_at": None,
        }
        payload["approval"] = approval

        payload = _remap_payload_entity_ids(payload)
        requirements, evidence_rows, links = _flatten_payload_for_persist(payload)
        validated = RkmDraftOut.model_validate(payload)
        analysis = validated.analysis
        scores = {
            "confidence_score": float(analysis.confidence_score or 0),
            "completeness_score": float(analysis.completeness_score or 0),
            "consistency_score": float(analysis.consistency_score or 0),
            "evidence_coverage": float(analysis.evidence_coverage or 0),
        }
        created = self.rkms.create_draft(
            project_id=project_id,
            created_by=user_id,
            status=status,
            version_major=major,
            version_minor=minor,
            version_patch=patch,
            scores=scores,
            reasoning_summary=analysis.reasoning_summary,
            prompt_version=analysis.prompt_version,
            model=analysis.model,
            payload_json=validated.model_dump(mode="json"),
            requirements=requirements,
            evidence=evidence_rows,
            links=links,
        )
        final_payload = copy.deepcopy(created.payload_json)
        final_payload["id"] = str(created.id)
        final_payload["version"]["created_at"] = created.created_at.isoformat()
        final_payload["version"]["updated_at"] = created.updated_at.isoformat()
        final_payload["version"]["number"] = created.version_label
        created.payload_json = final_payload
        self.db.add(created)
        self.db.commit()
        self.db.refresh(created)
        return created

    def _diff_payloads(
        self,
        left: dict[str, Any],
        right: dict[str, Any],
    ) -> list[VersionDiffItem]:
        diffs: list[VersionDiffItem] = []
        for section in _EDITABLE_SECTIONS:
            left_map = self._section_map(left.get(section) or [])
            right_map = self._section_map(right.get(section) or [])
            for item_id in sorted(set(left_map) | set(right_map)):
                before = left_map.get(item_id)
                after = right_map.get(item_id)
                if before is None and after is not None:
                    diffs.append(
                        VersionDiffItem(
                            section=section,
                            change_type="added",
                            item_id=item_id,
                            title=after.get("title") or after.get("name"),
                            after=str(after.get("description") or after.get("role") or ""),
                        ),
                    )
                elif before is not None and after is None:
                    diffs.append(
                        VersionDiffItem(
                            section=section,
                            change_type="removed",
                            item_id=item_id,
                            title=before.get("title") or before.get("name"),
                            before=str(before.get("description") or before.get("role") or ""),
                        ),
                    )
                elif before is not None and after is not None:
                    before_text = (
                        f"{before.get('title') or before.get('name')}|{before.get('description') or before.get('role')}"
                    )
                    after_text = (
                        f"{after.get('title') or after.get('name')}|{after.get('description') or after.get('role')}"
                    )
                    if before_text != after_text:
                        diffs.append(
                            VersionDiffItem(
                                section=section,
                                change_type="modified",
                                item_id=item_id,
                                title=after.get("title") or after.get("name"),
                                before=str(before.get("description") or before.get("role") or ""),
                                after=str(after.get("description") or after.get("role") or ""),
                            ),
                        )
        return diffs

    @staticmethod
    def _section_map(items: list[Any]) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            # Prefer stable title/description fingerprint when ids remapped across versions.
            key = str(item.get("id") or "")
            title = str(item.get("title") or item.get("name") or "").strip().lower()
            if title:
                key = f"title:{title}"
            elif key:
                key = f"id:{key}"
            else:
                continue
            result[key] = item
        return result

    def _require_project(self, project_id: UUID, user_id: UUID):
        project = self.projects.get_for_user(project_id, user_id)
        if project is None:
            raise NotFoundError("Project not found")
        return project

    def _require_mutable_draft(self, project_id: UUID) -> RequirementModel:
        row = self.rkms.ensure_active_draft(project_id)
        if row is None:
            raise NotFoundError("No Draft RKM found for this project")
        if row.status == "published" or not row.is_active_draft:
            raise ConflictError("Published RKM is immutable. Fork a new Draft version to edit.")
        approval = ((row.payload_json or {}).get("approval") or {}).get("status")
        if approval == "published":
            raise ConflictError("Published RKM is immutable. Fork a new Draft version to edit.")
        return row
