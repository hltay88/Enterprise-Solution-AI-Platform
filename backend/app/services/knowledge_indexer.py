"""Sprint 5.2 — index eligible knowledge versions into pgvector chunks."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.ai.embeddings.factory import get_embedding_provider
from app.constants.knowledge_lifecycle import RETRIEVAL_ELIGIBLE_STATUSES
from app.core.exceptions import ConflictError, NotFoundError
from app.models.knowledge import KnowledgeChunk, KnowledgeItem, KnowledgeSource, KnowledgeVersion
from app.services.knowledge_chunking import chunk_knowledge_text

logger = logging.getLogger(__name__)


class KnowledgeIndexer:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.embedder = get_embedding_provider()

    def index_version(self, version_id: UUID) -> dict:
        version = self.db.get(KnowledgeVersion, version_id)
        if version is None:
            raise NotFoundError("Knowledge version not found")
        if version.status not in RETRIEVAL_ELIGIBLE_STATUSES:
            raise ConflictError(
                f"Only approved/published knowledge can be indexed (status={version.status})",
            )
        text = (version.content_text or "").strip()
        if not text:
            # Clear any prior chunks and skip.
            self._delete_chunks(version_id)
            self.db.commit()
            return {"version_id": str(version_id), "chunk_count": 0, "skipped": "empty_content"}

        sources = list(
            self.db.scalars(
                select(KnowledgeSource).where(KnowledgeSource.knowledge_version_id == version_id),
            ).all(),
        )
        hints: list = []
        for src in sources:
            hints.extend(src.section_hints or [])

        pieces = chunk_knowledge_text(text, section_hints=hints)
        vectors = self.embedder.embed_documents([p.text for p in pieces])

        self._delete_chunks(version_id)
        for piece, vector in zip(pieces, vectors, strict=False):
            self.db.add(
                KnowledgeChunk(
                    knowledge_item_id=version.knowledge_item_id,
                    knowledge_version_id=version.id,
                    chunk_index=piece.chunk_index,
                    content=piece.text,
                    page_number=piece.page_number,
                    section_label=piece.section_label,
                    embedding=vector,
                    embedding_provider=self.embedder.name,
                    embedding_model=self.embedder.model,
                    metadata_json={
                        "char_count": len(piece.text),
                        "dims": self.embedder.dimensions,
                    },
                ),
            )
        self.db.commit()
        logger.info(
            "Indexed knowledge version %s (%s chunks, provider=%s)",
            version_id,
            len(pieces),
            self.embedder.name,
        )
        return {
            "version_id": str(version_id),
            "chunk_count": len(pieces),
            "embedding_provider": self.embedder.name,
            "embedding_model": self.embedder.model,
        }

    def index_item_current_if_eligible(self, item_id: UUID) -> dict | None:
        item = self.db.get(KnowledgeItem, item_id)
        if item is None or item.current_version_id is None:
            return None
        version = self.db.get(KnowledgeVersion, item.current_version_id)
        if version is None or version.status not in RETRIEVAL_ELIGIBLE_STATUSES:
            return None
        try:
            return self.index_version(version.id)
        except Exception:
            logger.exception("Failed to index knowledge item %s", item_id)
            return {"version_id": str(version.id), "error": "index_failed"}

    def _delete_chunks(self, version_id: UUID) -> None:
        self.db.execute(
            delete(KnowledgeChunk).where(KnowledgeChunk.knowledge_version_id == version_id),
        )
