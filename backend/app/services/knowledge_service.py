"""Sprint 5.1 — Enterprise Knowledge Engine service (CRUD, classify, lifecycle, ingest)."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.constants.file_limits import KNOWLEDGE_ALLOWED_EXTENSIONS, MIME_BY_TYPE
from app.constants.knowledge_lifecycle import (
    STATUS_APPROVED,
    STATUS_ARCHIVED,
    STATUS_DEPRECATED,
    STATUS_DRAFT,
    STATUS_PUBLISHED,
    STATUS_REVIEW,
    can_transition,
    normalize_status,
)
from app.constants.knowledge_taxonomy import (
    DEFAULT_DOMAIN_CODE,
    TAXONOMY_SEED,
    resolve_domain_code,
)
from app.constants.knowledge_types import (
    DEFAULT_KNOWLEDGE_TYPE,
    knowledge_type_choices,
    normalize_knowledge_type,
)
from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models.knowledge import KnowledgeItem, KnowledgeSource, KnowledgeVersion
from app.models.user import User
from app.repositories.knowledge_repository import KnowledgeRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.knowledge import (
    KnowledgeCreateIn,
    KnowledgeItemDetail,
    KnowledgeItemSummary,
    KnowledgeNewVersionIn,
    KnowledgeSourceOut,
    KnowledgeTypeOut,
    KnowledgeUpdateIn,
    KnowledgeVersionOut,
    TaxonomyDomainOut,
)
from app.services.document_intelligence.parsers import extract_document
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)


class KnowledgeService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = KnowledgeRepository(db)
        self.projects = ProjectRepository(db)
        self.storage = StorageService()

    # ------------------------------------------------------------------ taxonomy
    def list_domains(self) -> list[TaxonomyDomainOut]:
        rows = self.repo.list_taxonomy(active_only=True)
        return [TaxonomyDomainOut.model_validate(row) for row in rows]

    def list_types(self) -> list[KnowledgeTypeOut]:
        return [KnowledgeTypeOut(**item) for item in knowledge_type_choices()]

    # ------------------------------------------------------------------ queries
    def list_items(
        self,
        *,
        status: str | None = None,
        domain_code: str | None = None,
        knowledge_type: str | None = None,
        project_id: UUID | None = None,
        q: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[KnowledgeItemSummary]:
        rows = self.repo.list_items(
            status=status,
            domain_code=domain_code,
            knowledge_type=knowledge_type,
            project_id=project_id,
            q=q,
            limit=limit,
            offset=offset,
        )
        return [self._to_summary(item, version) for item, version in rows]

    def get_item(self, item_id: UUID, *, include_versions: bool = True) -> KnowledgeItemDetail:
        item = self.repo.get_item(item_id)
        if item is None:
            raise NotFoundError("Knowledge item not found")
        current = self.repo.get_current_version(item)
        versions = item.versions if include_versions else []
        summary = self._to_summary(item, current)
        return KnowledgeItemDetail(
            **summary.model_dump(),
            current_version=self._to_version_out(current) if current else None,
            versions=[self._to_version_out(v) for v in versions],
        )

    # ------------------------------------------------------------------ create / update
    async def create(
        self,
        body: KnowledgeCreateIn,
        actor: User,
        *,
        upload: UploadFile | None = None,
    ) -> KnowledgeItemDetail:
        knowledge_type = self._safe_type(body.knowledge_type)
        domain_code = self._resolve_domain(body.domain_code, body.title, body.description, body.content_text)
        if body.project_id is not None:
            if self.projects.get_for_user(body.project_id, actor.id) is None:
                raise NotFoundError("Project not found")

        item = KnowledgeItem(
            tenant_id=None,
            project_id=body.project_id,
            title=body.title.strip(),
            description=(body.description or "").strip() or None,
            knowledge_type=knowledge_type,
            domain_code=domain_code,
            owner_user_id=actor.id,
            sensitivity=(body.sensitivity or "internal").strip().lower() or "internal",
        )
        version = KnowledgeVersion(
            version_number=1,
            version_label="1",
            status=STATUS_DRAFT,
            content_text=body.content_text,
            change_summary=body.change_summary or "Initial draft",
            metadata_json=dict(body.metadata or {}),
            tags=list(body.tags or []),
            created_by=actor.id,
        )
        item, version = self.repo.create_item_with_version(item=item, version=version, commit=False)

        if upload is not None:
            await self._ingest_into_version(item, version, upload, commit=False)

        if not body.domain_code:
            version_refreshed = self.repo.get_version(version.id) or version
            classified = self.classify_domain(
                item.title,
                item.description,
                version_refreshed.content_text,
                version_refreshed.source_document_name,
            )
            item.domain_code = classified

        self.repo.record_audit(
            action="knowledge.create",
            summary=f"Created knowledge draft '{item.title}' v1",
            user_id=actor.id,
            knowledge_item_id=item.id,
            knowledge_version_id=version.id,
            tenant_id=item.tenant_id,
            metadata={"domain_code": item.domain_code, "knowledge_type": item.knowledge_type},
            commit=True,
        )
        return self.get_item(item.id)

    def update_draft(self, item_id: UUID, body: KnowledgeUpdateIn, actor: User) -> KnowledgeItemDetail:
        item = self._require_item(item_id)
        version = self._require_current_version(item)
        if version.status != STATUS_DRAFT:
            raise ConflictError(
                "Only Draft knowledge can be edited in place. Create a new version from published knowledge.",
            )

        if body.title is not None:
            item.title = body.title.strip()
        if body.description is not None:
            item.description = body.description.strip() or None
        if body.knowledge_type is not None:
            item.knowledge_type = self._safe_type(body.knowledge_type)
        if body.domain_code is not None:
            item.domain_code = self._resolve_domain(body.domain_code)
        if body.sensitivity is not None:
            item.sensitivity = body.sensitivity.strip().lower() or item.sensitivity
        if body.tags is not None:
            version.tags = list(body.tags)
        if body.content_text is not None:
            version.content_text = body.content_text
        if body.metadata is not None:
            version.metadata_json = dict(body.metadata)
        if body.change_summary is not None:
            version.change_summary = body.change_summary
        if body.effective_date is not None:
            version.effective_date = body.effective_date
        if body.expiry_date is not None:
            version.expiry_date = body.expiry_date
        if body.next_review_date is not None:
            version.next_review_date = body.next_review_date

        item.updated_at = datetime.now(timezone.utc)
        version.updated_at = datetime.now(timezone.utc)
        self.repo.record_audit(
            action="knowledge.update",
            summary=f"Updated draft knowledge '{item.title}' v{version.version_label}",
            user_id=actor.id,
            knowledge_item_id=item.id,
            knowledge_version_id=version.id,
            tenant_id=item.tenant_id,
            commit=True,
        )
        return self.get_item(item.id)

    # ------------------------------------------------------------------ lifecycle
    def submit_review(self, item_id: UUID, actor: User) -> KnowledgeItemDetail:
        return self._transition(item_id, STATUS_REVIEW, actor, action="knowledge.submit_review")

    def approve(self, item_id: UUID, actor: User) -> KnowledgeItemDetail:
        return self._transition(item_id, STATUS_APPROVED, actor, action="knowledge.approve")

    def publish(self, item_id: UUID, actor: User) -> KnowledgeItemDetail:
        return self._transition(item_id, STATUS_PUBLISHED, actor, action="knowledge.publish")

    def deprecate(self, item_id: UUID, actor: User) -> KnowledgeItemDetail:
        return self._transition(item_id, STATUS_DEPRECATED, actor, action="knowledge.deprecate")

    def archive(self, item_id: UUID, actor: User) -> KnowledgeItemDetail:
        return self._transition(item_id, STATUS_ARCHIVED, actor, action="knowledge.archive")

    def return_to_draft(self, item_id: UUID, actor: User) -> KnowledgeItemDetail:
        """Approver/editor bounce from review back to draft."""
        return self._transition(item_id, STATUS_DRAFT, actor, action="knowledge.return_draft")

    def new_version(
        self,
        item_id: UUID,
        actor: User,
        body: KnowledgeNewVersionIn | None = None,
    ) -> KnowledgeItemDetail:
        item = self._require_item(item_id)
        current = self._require_current_version(item)
        if current.status == STATUS_DRAFT:
            raise ConflictError("An active Draft already exists. Edit it or publish before forking.")
        if current.status not in {STATUS_PUBLISHED, STATUS_DEPRECATED, STATUS_APPROVED}:
            raise ConflictError(
                f"New version requires published, deprecated, or approved knowledge "
                f"(current status: '{current.status}')",
            )

        body = body or KnowledgeNewVersionIn()
        next_number = self.repo.max_version_number(item.id) + 1
        now = datetime.now(timezone.utc)
        forked = KnowledgeVersion(
            id=uuid4(),
            knowledge_item_id=item.id,
            version_number=next_number,
            version_label=str(next_number),
            status=STATUS_DRAFT,
            content_text=body.content_text if body.content_text is not None else current.content_text,
            content_location=current.content_location,
            change_summary=body.change_summary or f"New draft from v{current.version_label}",
            metadata_json=dict(current.metadata_json or {}),
            tags=list(current.tags or []),
            effective_date=current.effective_date,
            expiry_date=current.expiry_date,
            next_review_date=current.next_review_date,
            source_document_name=current.source_document_name,
            created_by=actor.id,
            created_at=now,
            updated_at=now,
        )
        self.repo.add_version(forked, commit=False)
        item.current_version_id = forked.id
        item.updated_at = datetime.now(timezone.utc)
        self.repo.record_audit(
            action="knowledge.new_version",
            summary=f"Forked '{item.title}' → v{forked.version_label} (draft)",
            user_id=actor.id,
            knowledge_item_id=item.id,
            knowledge_version_id=forked.id,
            tenant_id=item.tenant_id,
            metadata={"from_version": current.version_number, "from_status": current.status},
            commit=True,
        )
        return self.get_item(item.id)

    # ------------------------------------------------------------------ ingest
    async def ingest_file(
        self,
        item_id: UUID,
        actor: User,
        upload: UploadFile,
    ) -> KnowledgeItemDetail:
        item = self._require_item(item_id)
        version = self._require_current_version(item)
        if version.status != STATUS_DRAFT:
            raise ConflictError("Ingestion is only allowed on Draft knowledge versions")
        await self._ingest_into_version(item, version, upload, commit=False)
        classified = self.classify_domain(
            item.title,
            item.description,
            version.content_text,
            version.source_document_name,
        )
        item.domain_code = classified
        item.updated_at = datetime.now(timezone.utc)
        self.repo.record_audit(
            action="knowledge.ingest",
            summary=f"Ingested source into '{item.title}' v{version.version_label}",
            user_id=actor.id,
            knowledge_item_id=item.id,
            knowledge_version_id=version.id,
            tenant_id=item.tenant_id,
            metadata={"filename": version.source_document_name, "domain_code": item.domain_code},
            commit=True,
        )
        return self.get_item(item.id)

    # ------------------------------------------------------------------ classify
    def classify_domain(self, *text_blobs: str | None) -> str:
        blob = " ".join(t for t in text_blobs if t).lower()
        if not blob:
            return DEFAULT_DOMAIN_CODE

        # Prefer longer alias / name matches.
        scored: list[tuple[int, str]] = []
        normalized_blob = re.sub(r"[\s_\-]+", " ", blob)
        for code, name, aliases in TAXONOMY_SEED:
            tokens = [code, name.lower(), *aliases]
            best = 0
            for token in tokens:
                token_n = token.lower().replace("-", "_").replace(" ", "_")
                if not token_n:
                    continue
                parts = [re.escape(p) for p in token_n.split("_") if p]
                if not parts:
                    continue
                pattern = r"(?<![a-z0-9])" + r"[\s_\-]+".join(parts) + r"(?![a-z0-9])"
                if re.search(pattern, normalized_blob):
                    best = max(best, len(token_n))
            if best:
                scored.append((best, code))
        if not scored:
            return DEFAULT_DOMAIN_CODE
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return scored[0][1]

    # ------------------------------------------------------------------ internals
    def _transition(
        self,
        item_id: UUID,
        target: str,
        actor: User,
        *,
        action: str,
    ) -> KnowledgeItemDetail:
        item = self._require_item(item_id)
        version = self._require_current_version(item)
        current = normalize_status(version.status)
        target = normalize_status(target)
        if not can_transition(current, target):
            raise ConflictError(f"Cannot transition knowledge from '{current}' to '{target}'")

        now = datetime.now(timezone.utc)
        version.status = target
        if target == STATUS_REVIEW:
            version.reviewed_by = actor.id
            version.reviewed_at = now
        elif target == STATUS_APPROVED:
            version.approved_by = actor.id
            version.approved_at = now
        elif target == STATUS_PUBLISHED:
            version.published_by = actor.id
            version.published_at = now
        item.updated_at = now
        version.updated_at = now

        self.repo.record_audit(
            action=action,
            summary=f"{action.split('.')[-1].replace('_', ' ').title()} '{item.title}' v{version.version_label}",
            user_id=actor.id,
            knowledge_item_id=item.id,
            knowledge_version_id=version.id,
            tenant_id=item.tenant_id,
            metadata={"from": current, "to": target},
            commit=True,
        )
        return self.get_item(item.id)

    async def _ingest_into_version(
        self,
        item: KnowledgeItem,
        version: KnowledgeVersion,
        upload: UploadFile,
        *,
        commit: bool,
    ) -> KnowledgeSource:
        file_type = self._detect_knowledge_type(upload.filename or "")
        relative_path, size, checksum = await self.storage.save_knowledge_upload(
            knowledge_item_id=item.id,
            upload=upload,
        )
        absolute = self.storage.absolute_path(relative_path)
        extraction = extract_document(absolute, file_type)
        section_hints = self._section_hints(extraction.pages, extraction.metadata)

        version.content_text = extraction.full_text
        version.content_location = relative_path
        version.source_document_name = Path(upload.filename or "upload").name
        meta = dict(version.metadata_json or {})
        meta["extract"] = {
            "parser": extraction.metadata.get("parser"),
            "page_count": len(extraction.pages),
            "ocr_used": extraction.ocr_used,
            "language": extraction.language,
            "warnings": extraction.warnings,
        }
        version.metadata_json = meta

        source = KnowledgeSource(
            knowledge_version_id=version.id,
            original_filename=version.source_document_name,
            file_type=file_type,
            mime_type=MIME_BY_TYPE.get(file_type),
            storage_path=relative_path,
            size_bytes=size,
            checksum_sha256=checksum,
            page_count=len(extraction.pages),
            extract_warnings=list(extraction.warnings or []),
            section_hints=section_hints,
        )
        self.repo.add_source(source, commit=commit)
        return source

    def _detect_knowledge_type(self, filename: str) -> str:
        suffix = Path(filename).suffix.lower()
        file_type = KNOWLEDGE_ALLOWED_EXTENSIONS.get(suffix)
        if file_type is None:
            allowed = ", ".join(sorted({ext.lstrip(".").upper() for ext in KNOWLEDGE_ALLOWED_EXTENSIONS}))
            raise ValidationAppError(f"Unsupported knowledge file type. Allowed: {allowed}")
        return file_type

    @staticmethod
    def _section_hints(pages: list[Any], metadata: dict[str, str]) -> list[dict[str, Any]]:
        hints: list[dict[str, Any]] = []
        for page in pages:
            if getattr(page, "text", None):
                hints.append(
                    {
                        "page": page.page_number,
                        "preview": (page.text or "")[:240],
                    },
                )
        for key, value in metadata.items():
            if key.startswith("heading_"):
                hints.append({"section": value})
        return hints[:50]

    def _require_item(self, item_id: UUID) -> KnowledgeItem:
        item = self.repo.get_item(item_id)
        if item is None:
            raise NotFoundError("Knowledge item not found")
        return item

    def _require_current_version(self, item: KnowledgeItem) -> KnowledgeVersion:
        version = self.repo.get_current_version(item)
        if version is None:
            raise ConflictError("Knowledge item has no current version")
        return version

    def _safe_type(self, value: str | None) -> str:
        try:
            return normalize_knowledge_type(value)
        except ValueError as exc:
            raise ValidationAppError(str(exc)) from exc

    def _resolve_domain(self, explicit: str | None, *blobs: str | None) -> str:
        if explicit:
            resolved = resolve_domain_code(explicit) or (
                explicit.strip().lower().replace(" ", "_").replace("-", "_")
            )
            # Accept seeded codes; unknown free-form rejected unless classified
            from app.constants.knowledge_taxonomy import TAXONOMY_CODES

            if resolved in TAXONOMY_CODES:
                return resolved
            raise ValidationAppError(f"Unknown domain_code: {explicit}")
        return self.classify_domain(*blobs)

    @staticmethod
    def _to_summary(item: KnowledgeItem, version: KnowledgeVersion | None) -> KnowledgeItemSummary:
        return KnowledgeItemSummary(
            id=item.id,
            tenant_id=item.tenant_id,
            project_id=item.project_id,
            title=item.title,
            description=item.description,
            knowledge_type=item.knowledge_type,
            domain_code=item.domain_code,
            owner_user_id=item.owner_user_id,
            sensitivity=item.sensitivity,
            current_version_id=item.current_version_id,
            status=version.status if version else None,
            version_label=version.version_label if version else None,
            version_number=version.version_number if version else None,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    @staticmethod
    def _to_version_out(version: KnowledgeVersion) -> KnowledgeVersionOut:
        sources: list[Any] = []
        try:
            sources = list(version.sources or [])
        except Exception:
            sources = []
        now = datetime.now(timezone.utc)
        return KnowledgeVersionOut(
            id=version.id,
            knowledge_item_id=version.knowledge_item_id,
            version_number=version.version_number,
            version_label=version.version_label,
            status=version.status,
            content_text=version.content_text,
            content_location=version.content_location,
            change_summary=version.change_summary,
            metadata=dict(version.metadata_json or {}),
            tags=list(version.tags or []),
            effective_date=version.effective_date,
            expiry_date=version.expiry_date,
            next_review_date=version.next_review_date,
            source_document_name=version.source_document_name,
            created_by=version.created_by,
            reviewed_by=version.reviewed_by,
            approved_by=version.approved_by,
            published_by=version.published_by,
            reviewed_at=version.reviewed_at,
            approved_at=version.approved_at,
            published_at=version.published_at,
            created_at=version.created_at or now,
            updated_at=version.updated_at or now,
            sources=[KnowledgeSourceOut.model_validate(s) for s in sources],
        )
