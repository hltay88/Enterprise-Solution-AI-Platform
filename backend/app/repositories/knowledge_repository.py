"""Persistence for Sprint 5.1 knowledge tables."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.constants.knowledge_taxonomy import TAXONOMY_SEED
from app.models.knowledge import (
    KnowledgeAuditEvent,
    KnowledgeItem,
    KnowledgeSource,
    KnowledgeVersion,
    TaxonomyDomain,
)


class KnowledgeRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def ensure_taxonomy_seeded(self) -> None:
        existing = set(self.db.scalars(select(TaxonomyDomain.code)).all())
        for code, name, aliases in TAXONOMY_SEED:
            if code in existing:
                continue
            self.db.add(
                TaxonomyDomain(code=code, name=name, aliases=list(aliases), active=True),
            )
        self.db.commit()

    def list_taxonomy(self, *, active_only: bool = True) -> list[TaxonomyDomain]:
        self.ensure_taxonomy_seeded()
        statement: Select[tuple[TaxonomyDomain]] = select(TaxonomyDomain).order_by(
            TaxonomyDomain.name.asc(),
        )
        if active_only:
            statement = statement.where(TaxonomyDomain.active.is_(True))
        return list(self.db.scalars(statement).all())

    def create_item_with_version(
        self,
        *,
        item: KnowledgeItem,
        version: KnowledgeVersion,
        commit: bool = True,
    ) -> tuple[KnowledgeItem, KnowledgeVersion]:
        self.db.add(item)
        self.db.flush()
        version.knowledge_item_id = item.id
        self.db.add(version)
        self.db.flush()
        item.current_version_id = version.id
        if commit:
            self.db.commit()
            self.db.refresh(item)
            self.db.refresh(version)
        else:
            self.db.flush()
        return item, version

    def get_item(self, item_id: UUID) -> KnowledgeItem | None:
        statement = (
            select(KnowledgeItem)
            .where(KnowledgeItem.id == item_id)
            .options(
                selectinload(KnowledgeItem.versions).selectinload(KnowledgeVersion.sources),
            )
        )
        return self.db.scalars(statement).first()

    def get_version(self, version_id: UUID) -> KnowledgeVersion | None:
        statement = (
            select(KnowledgeVersion)
            .where(KnowledgeVersion.id == version_id)
            .options(selectinload(KnowledgeVersion.sources))
        )
        return self.db.scalars(statement).first()

    def get_current_version(self, item: KnowledgeItem) -> KnowledgeVersion | None:
        if item.current_version_id is None:
            return None
        return self.get_version(item.current_version_id)

    def list_items(
        self,
        *,
        tenant_id: UUID | None = None,
        status: str | None = None,
        domain_code: str | None = None,
        knowledge_type: str | None = None,
        project_id: UUID | None = None,
        q: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[tuple[KnowledgeItem, KnowledgeVersion | None]]:
        statement = (
            select(KnowledgeItem, KnowledgeVersion)
            .outerjoin(
                KnowledgeVersion,
                KnowledgeVersion.id == KnowledgeItem.current_version_id,
            )
            .order_by(KnowledgeItem.updated_at.desc())
            .limit(max(1, min(limit, 200)))
            .offset(max(0, offset))
        )
        # Platform knowledge (NULL tenant) is visible until Sprint 5.5 isolation.
        if tenant_id is not None:
            statement = statement.where(
                or_(KnowledgeItem.tenant_id.is_(None), KnowledgeItem.tenant_id == tenant_id),
            )
        if status:
            statement = statement.where(KnowledgeVersion.status == status)
        if domain_code:
            statement = statement.where(KnowledgeItem.domain_code == domain_code)
        if knowledge_type:
            statement = statement.where(KnowledgeItem.knowledge_type == knowledge_type)
        if project_id is not None:
            statement = statement.where(KnowledgeItem.project_id == project_id)
        if q:
            like = f"%{q.strip()}%"
            statement = statement.where(
                or_(
                    KnowledgeItem.title.ilike(like),
                    KnowledgeItem.description.ilike(like),
                    KnowledgeVersion.content_text.ilike(like),
                ),
            )
        rows = self.db.execute(statement).all()
        return [(item, version) for item, version in rows]

    def max_version_number(self, item_id: UUID) -> int:
        value = self.db.scalar(
            select(func.coalesce(func.max(KnowledgeVersion.version_number), 0)).where(
                KnowledgeVersion.knowledge_item_id == item_id,
            ),
        )
        return int(value or 0)

    def add_version(self, version: KnowledgeVersion, *, commit: bool = True) -> KnowledgeVersion:
        self.db.add(version)
        if commit:
            self.db.commit()
            self.db.refresh(version)
        else:
            self.db.flush()
        return version

    def add_source(self, source: KnowledgeSource, *, commit: bool = True) -> KnowledgeSource:
        self.db.add(source)
        if commit:
            self.db.commit()
            self.db.refresh(source)
        else:
            self.db.flush()
        return source

    def save(self, *, commit: bool = True) -> None:
        if commit:
            self.db.commit()
        else:
            self.db.flush()

    def record_audit(
        self,
        *,
        action: str,
        summary: str,
        user_id: UUID | None,
        knowledge_item_id: UUID | None = None,
        knowledge_version_id: UUID | None = None,
        tenant_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
        commit: bool = True,
    ) -> KnowledgeAuditEvent:
        event = KnowledgeAuditEvent(
            tenant_id=tenant_id,
            knowledge_item_id=knowledge_item_id,
            knowledge_version_id=knowledge_version_id,
            user_id=user_id,
            action=action,
            summary=summary,
            metadata_json=metadata or {},
        )
        self.db.add(event)
        if commit:
            self.db.commit()
            self.db.refresh(event)
        else:
            self.db.flush()
        return event
