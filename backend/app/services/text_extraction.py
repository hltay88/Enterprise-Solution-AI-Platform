"""Extract plain text from uploaded requirement documents."""

from pathlib import Path

from docx import Document
from pypdf import PdfReader

from app.core.exceptions import ValidationAppError

ALLOWED_EXTENSIONS = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".txt": "txt",
}


def detect_file_type(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    file_type = ALLOWED_EXTENSIONS.get(suffix)
    if file_type is None:
        raise ValidationAppError("Only PDF, DOCX, and TXT files are supported")
    return file_type


def extract_text(file_path: Path, file_type: str) -> str:
    if file_type == "pdf":
        return _extract_pdf(file_path)
    if file_type == "docx":
        return _extract_docx(file_path)
    if file_type == "txt":
        return _extract_txt(file_path)
    raise ValidationAppError(f"Unsupported file type: {file_type}")


def _extract_pdf(file_path: Path) -> str:
    reader = PdfReader(str(file_path))
    parts: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            parts.append(text.strip())
    return "\n\n".join(parts).strip()


def _extract_docx(file_path: Path) -> str:
    document = Document(str(file_path))
    parts = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
    return "\n".join(parts).strip()


def _extract_txt(file_path: Path) -> str:
    raw = file_path.read_bytes()
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return raw.decode(encoding).strip()
        except UnicodeDecodeError:
            continue
    raise ValidationAppError("Unable to decode TXT file")
