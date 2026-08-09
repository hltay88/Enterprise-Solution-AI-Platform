"""Soft cross-document consistency checks (Sprint 4.3, backlog #17)."""

from __future__ import annotations

import re
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.repositories.deliverable_repository import DeliverableRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.deliverable import ConsistencyFinding, ConsistencyOut


def _normalize(text: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9][a-z0-9_-]{2,}", (text or "").lower())
    stop = {
        "the",
        "and",
        "for",
        "with",
        "from",
        "this",
        "that",
        "are",
        "was",
        "will",
        "review",
        "required",
        "approved",
        "architecture",
        "solution",
        "design",
        "customer",
        "requirement",
        "requirements",
        "section",
        "content",
        "statement",
        "work",
        "based",
        "present",
        "snapshot",
        "source",
        "must",
        "not",
        "only",
    }
    return {t for t in tokens if t not in stop}


class CrossDocumentConsistencyService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = ProjectRepository(db)
        self.repo = DeliverableRepository(db)

    def check(self, project_id: UUID, user_id: UUID) -> ConsistencyOut:
        if self.projects.get_for_user(project_id, user_id) is None:
            raise NotFoundError("Project not found")

        documents = self.repo.list_documents(project_id)
        if not documents:
            return ConsistencyOut(ok=True, findings=[])

        # Prefer latest per type
        by_type: dict[str, object] = {}
        for doc in documents:
            if doc.document_type not in by_type:
                by_type[doc.document_type] = doc

        findings: list[ConsistencyFinding] = []

        # Load texts + snapshot component names
        doc_texts: dict[UUID, str] = {}
        doc_snapshots: dict[UUID, dict] = {}
        for doc in by_type.values():
            texts: list[str] = []
            if doc.current_version_id:
                for section in self.repo.list_sections(doc.current_version_id):
                    for item in self.repo.list_content_items(section.id):
                        texts.append(item.text or "")
            doc_texts[doc.id] = "\n".join(texts)
            snapshot = self.repo.get_snapshot(doc.source_snapshot_id, project_id)
            doc_snapshots[doc.id] = (
                (snapshot.payload_json or {}) if snapshot is not None else {}
            )

        # Architecture component coverage for technical docs
        for doc_type in ("sow", "solution_design", "proposal", "presentation"):
            doc = by_type.get(doc_type)
            if doc is None:
                continue
            arch = (doc_snapshots.get(doc.id) or {}).get("architecture") or {}
            components = arch.get("components") or []
            text_lower = doc_texts.get(doc.id, "").lower()
            missing = []
            for component in components[:20]:
                name = str(component.get("name") or "").strip()
                if name and name.lower() not in text_lower:
                    missing.append(name)
            if missing and doc_type in {"sow", "solution_design"}:
                findings.append(
                    ConsistencyFinding(
                        severity="warning",
                        code="missing_architecture_components",
                        message=(
                            f"{doc_type} may omit architecture component(s): "
                            + ", ".join(missing[:8])
                        ),
                        document_ids=[doc.id],
                        review_required=True,
                    )
                )

        # Pairwise SOW vs solution_design / proposal exclusion overlap sanity
        pairs = [
            ("sow", "solution_design"),
            ("sow", "proposal"),
            ("solution_design", "proposal"),
        ]
        for left_type, right_type in pairs:
            left = by_type.get(left_type)
            right = by_type.get(right_type)
            if left is None or right is None:
                continue
            left_arch = (doc_snapshots.get(left.id) or {}).get("architecture") or {}
            right_arch = (doc_snapshots.get(right.id) or {}).get("architecture") or {}
            left_id = str(left_arch.get("id") or left_arch.get("candidate_key") or "")
            right_id = str(right_arch.get("id") or right_arch.get("candidate_key") or "")
            if left_id and right_id and left_id != right_id:
                findings.append(
                    ConsistencyFinding(
                        severity="warning",
                        code="snapshot_architecture_mismatch",
                        message=(
                            f"{left_type} and {right_type} appear pinned to different "
                            "architecture snapshots"
                        ),
                        document_ids=[left.id, right.id],
                        review_required=True,
                    )
                )

            left_tokens = _normalize(doc_texts.get(left.id, ""))
            right_tokens = _normalize(doc_texts.get(right.id, ""))
            if left_tokens and right_tokens:
                overlap = len(left_tokens & right_tokens) / max(
                    1, min(len(left_tokens), len(right_tokens))
                )
                if overlap < 0.02:
                    findings.append(
                        ConsistencyFinding(
                            severity="info",
                            code="low_lexical_overlap",
                            message=(
                                f"Low shared terminology between {left_type} and "
                                f"{right_type}; confirm they describe the same solution"
                            ),
                            document_ids=[left.id, right.id],
                            review_required=True,
                        )
                    )

        # Soft only — never blocking
        return ConsistencyOut(ok=True, findings=findings)
