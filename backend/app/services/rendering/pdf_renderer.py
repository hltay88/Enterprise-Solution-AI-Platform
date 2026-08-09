"""PDF conversion via LibreOffice (DOCX → PDF), Sprint 4.3 ATLAS-049."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from app.core.config import get_settings
from app.core.exceptions import ValidationAppError


def resolve_soffice_path(explicit: str | None = None) -> str | None:
    settings = get_settings()
    candidate = (explicit or settings.libreoffice_path or "soffice").strip()
    found = shutil.which(candidate)
    if found:
        return found
    # macOS common app path
    mac = Path("/Applications/LibreOffice.app/Contents/MacOS/soffice")
    if mac.exists():
        return str(mac)
    return None


def convert_docx_bytes_to_pdf(
    docx_bytes: bytes,
    *,
    soffice_path: str | None = None,
    timeout_seconds: int = 120,
) -> bytes:
    """Render PDF bytes from DOCX via LibreOffice headless conversion."""
    binary = resolve_soffice_path(soffice_path)
    if not binary:
        raise ValidationAppError(
            "LibreOffice (soffice) is not available for PDF export. "
            "Install LibreOffice or set LIBREOFFICE_PATH."
        )

    with tempfile.TemporaryDirectory(prefix="atlas_pdf_") as tmp:
        tmp_path = Path(tmp)
        docx_path = tmp_path / "document.docx"
        docx_path.write_bytes(docx_bytes)
        try:
            completed = subprocess.run(
                [
                    binary,
                    "--headless",
                    "--norestore",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    str(tmp_path),
                    str(docx_path),
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise ValidationAppError("LibreOffice PDF conversion timed out") from exc

        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip()[:500]
            raise ValidationAppError(
                f"LibreOffice PDF conversion failed: {detail or completed.returncode}"
            )

        pdf_path = tmp_path / "document.pdf"
        if not pdf_path.exists():
            # LibreOffice may alter the stem; pick first PDF
            pdfs = list(tmp_path.glob("*.pdf"))
            if not pdfs:
                raise ValidationAppError("LibreOffice did not produce a PDF file")
            pdf_path = pdfs[0]
        data = pdf_path.read_bytes()
        if not data.startswith(b"%PDF"):
            raise ValidationAppError("Converted file is not a valid PDF")
        return data
