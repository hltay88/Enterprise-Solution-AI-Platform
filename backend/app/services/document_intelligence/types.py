"""Shared types for document extraction pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ExtractedPage:
    page_number: int
    text: str
    confidence: float | None = None
    ocr_engine: str | None = None
    processing_ms: int | None = None
    language: str | None = None


@dataclass
class ExtractionResult:
    pages: list[ExtractedPage] = field(default_factory=list)
    full_text: str = ""
    ocr_used: bool = False
    language: str | None = None
    needs_manual_review: bool = False
    metadata: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
