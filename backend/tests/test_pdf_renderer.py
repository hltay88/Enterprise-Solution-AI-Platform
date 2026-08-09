"""PDF conversion helpers (LibreOffice mocked)."""

from pathlib import Path

import pytest

from app.core.exceptions import ValidationAppError
from app.services.rendering import pdf_renderer


def test_convert_docx_requires_soffice(monkeypatch):
    monkeypatch.setattr(pdf_renderer, "resolve_soffice_path", lambda explicit=None: None)
    with pytest.raises(ValidationAppError, match="LibreOffice"):
        pdf_renderer.convert_docx_bytes_to_pdf(b"PK fake")


def test_convert_docx_success(monkeypatch, tmp_path):
    monkeypatch.setattr(
        pdf_renderer, "resolve_soffice_path", lambda explicit=None: "/usr/bin/soffice"
    )

    class Result:
        returncode = 0
        stderr = ""
        stdout = ""

    def fake_run(cmd, **kwargs):
        # Write a minimal PDF into outdir
        outdir = Path(cmd[cmd.index("--outdir") + 1])
        (outdir / "document.pdf").write_bytes(b"%PDF-1.4 mock")
        return Result()

    monkeypatch.setattr(pdf_renderer.subprocess, "run", fake_run)
    data = pdf_renderer.convert_docx_bytes_to_pdf(b"PK fake docx")
    assert data.startswith(b"%PDF")
