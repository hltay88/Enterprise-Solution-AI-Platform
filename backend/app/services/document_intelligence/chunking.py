"""Split extracted text into persistence-friendly chunks."""

from __future__ import annotations

from dataclasses import dataclass

from app.services.document_intelligence.types import ExtractedPage


@dataclass
class TextChunk:
    chunk_index: int
    text: str
    page_number: int | None
    char_count: int


DEFAULT_CHUNK_SIZE = 2000
DEFAULT_CHUNK_OVERLAP = 200


def chunk_pages(
    pages: list[ExtractedPage],
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[TextChunk]:
    """Chunk page text with overlap; falls back to full-text chunking if empty pages."""
    chunks: list[TextChunk] = []
    index = 0

    for page in pages:
        text = (page.text or "").strip()
        if not text:
            continue
        if len(text) <= chunk_size:
            chunks.append(
                TextChunk(
                    chunk_index=index,
                    text=text,
                    page_number=page.page_number,
                    char_count=len(text),
                ),
            )
            index += 1
            continue

        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            piece = text[start:end].strip()
            if piece:
                chunks.append(
                    TextChunk(
                        chunk_index=index,
                        text=piece,
                        page_number=page.page_number,
                        char_count=len(piece),
                    ),
                )
                index += 1
            if end >= len(text):
                break
            start = max(0, end - overlap)

    return chunks
