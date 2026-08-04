"""Persist pages, chunks, and metadata for a document."""

from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk
from app.models.document_metadata import DocumentMetadata
from app.models.document_page import DocumentPage
from app.services.document_intelligence.chunking import TextChunk
from app.services.document_intelligence.normalize import word_count
from app.services.document_intelligence.types import ExtractedPage


class DocumentIntelligenceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def replace_extraction(
        self,
        *,
        document_id: UUID,
        pages: list[ExtractedPage],
        chunks: list[TextChunk],
        metadata: dict[str, str],
    ) -> None:
        self.db.execute(delete(DocumentPage).where(DocumentPage.document_id == document_id))
        self.db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
        self.db.execute(delete(DocumentMetadata).where(DocumentMetadata.document_id == document_id))

        for page in pages:
            self.db.add(
                DocumentPage(
                    document_id=document_id,
                    page_number=page.page_number,
                    text=page.text,
                    language=page.language,
                    confidence=page.confidence,
                    char_count=len(page.text or ""),
                    word_count=word_count(page.text or ""),
                    ocr_engine=page.ocr_engine,
                    processing_ms=page.processing_ms,
                ),
            )

        for chunk in chunks:
            self.db.add(
                DocumentChunk(
                    document_id=document_id,
                    page_number=chunk.page_number,
                    chunk_index=chunk.chunk_index,
                    text=chunk.text,
                    char_count=chunk.char_count,
                ),
            )

        for key, value in metadata.items():
            self.db.add(
                DocumentMetadata(
                    document_id=document_id,
                    key=key,
                    value=value,
                ),
            )

        self.db.commit()

    def list_pages(self, document_id: UUID) -> list[DocumentPage]:
        from sqlalchemy import select

        statement = (
            select(DocumentPage)
            .where(DocumentPage.document_id == document_id)
            .order_by(DocumentPage.page_number.asc())
        )
        return list(self.db.scalars(statement).all())

    def list_chunks(self, document_id: UUID) -> list[DocumentChunk]:
        from sqlalchemy import select

        statement = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc())
        )
        return list(self.db.scalars(statement).all())

    def metadata_map(self, document_id: UUID) -> dict[str, str | None]:
        from sqlalchemy import select

        statement = select(DocumentMetadata).where(DocumentMetadata.document_id == document_id)
        rows = list(self.db.scalars(statement).all())
        return {row.key: row.value for row in rows}
