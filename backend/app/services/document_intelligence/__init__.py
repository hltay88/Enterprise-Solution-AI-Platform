"""Document Intelligence package (Phase 2 Stage B)."""

from app.services.document_intelligence.parsers import extract_document
from app.services.document_intelligence.types import ExtractionResult, ExtractedPage

__all__ = ["extract_document", "ExtractionResult", "ExtractedPage"]
