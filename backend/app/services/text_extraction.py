"""Extract plain text from uploaded requirement documents (Sprint 1 sync path)."""

from pathlib import Path

from app.constants.file_limits import SPRINT1_ALLOWED_EXTENSIONS
from app.core.exceptions import ValidationAppError
from app.services.document_intelligence import extract_document


def detect_file_type(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    file_type = SPRINT1_ALLOWED_EXTENSIONS.get(suffix)
    if file_type is None:
        raise ValidationAppError("Only PDF, DOCX, and TXT files are supported")
    return file_type


def extract_text(file_path: Path, file_type: str) -> str:
    result = extract_document(file_path, file_type)
    return result.full_text
