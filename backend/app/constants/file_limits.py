"""Phase 2.1 file limits (ATLAS-027)."""

from __future__ import annotations

# Per-file and per-batch ceilings for /api/v1 document ingest.
MAX_UPLOAD_MB_PHASE2 = 50
MAX_BATCH_UPLOAD_MB_PHASE2 = 200

PHASE2_ALLOWED_EXTENSIONS: dict[str, str] = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".doc": "doc",
    ".xlsx": "xlsx",
    ".csv": "csv",
    ".txt": "txt",
    ".png": "png",
    ".jpg": "jpg",
    ".jpeg": "jpeg",
}

# Sprint 1 sync upload remains narrower for backward compatibility.
SPRINT1_ALLOWED_EXTENSIONS: dict[str, str] = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".txt": "txt",
}

MIME_BY_TYPE: dict[str, str] = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "doc": "application/msword",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "csv": "text/csv",
    "txt": "text/plain",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
}
