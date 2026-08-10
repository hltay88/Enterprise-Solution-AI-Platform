"""Sprint 5.2 — chunk plain knowledge text for indexing."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings
from app.services.document_intelligence.chunking import TextChunk


@dataclass
class KnowledgeTextChunk:
    chunk_index: int
    text: str
    page_number: int | None = None
    section_label: str | None = None


def chunk_knowledge_text(
    text: str,
    *,
    chunk_size: int | None = None,
    overlap: int | None = None,
    section_hints: list | None = None,
) -> list[KnowledgeTextChunk]:
    """Char-window chunking with optional section labels from ingest hints."""
    size = int(chunk_size or settings.atlas_knowledge_chunk_size or 1000)
    ov = int(overlap or settings.atlas_knowledge_chunk_overlap or 150)
    body = (text or "").strip()
    if not body:
        return []

    # Map page previews from section_hints when present.
    page_by_preview: dict[str, int] = {}
    sections: list[str] = []
    for hint in section_hints or []:
        if not isinstance(hint, dict):
            continue
        if "section" in hint and hint["section"]:
            sections.append(str(hint["section"]))
        if "page" in hint and hint.get("preview"):
            page_by_preview[str(hint["preview"])[:80]] = int(hint["page"])

    raw_chunks: list[TextChunk] = []
    index = 0
    if len(body) <= size:
        raw_chunks.append(
            TextChunk(chunk_index=0, text=body, page_number=None, char_count=len(body)),
        )
    else:
        start = 0
        while start < len(body):
            end = min(start + size, len(body))
            piece = body[start:end].strip()
            if piece:
                raw_chunks.append(
                    TextChunk(
                        chunk_index=index,
                        text=piece,
                        page_number=None,
                        char_count=len(piece),
                    ),
                )
                index += 1
            if end >= len(body):
                break
            start = max(0, end - ov)

    out: list[KnowledgeTextChunk] = []
    for i, chunk in enumerate(raw_chunks):
        page = None
        for preview, page_no in page_by_preview.items():
            if preview and preview in chunk.text:
                page = page_no
                break
        section = sections[i] if i < len(sections) else (sections[0] if sections else None)
        out.append(
            KnowledgeTextChunk(
                chunk_index=i,
                text=chunk.text,
                page_number=page,
                section_label=section,
            ),
        )
    return out
