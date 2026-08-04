from pathlib import Path

import pytest

from app.core.exceptions import ValidationAppError
from app.services.document_ingest_service import _detect_phase2_type


def test_detect_phase2_types():
    assert _detect_phase2_type("a.PDF") == "pdf"
    assert _detect_phase2_type("sheet.XLSX") == "xlsx"
    assert _detect_phase2_type("scan.JPEG") == "jpeg"
    assert _detect_phase2_type("legacy.doc") == "doc"


def test_detect_phase2_rejects_zip():
    with pytest.raises(ValidationAppError):
        _detect_phase2_type("bundle.zip")


def test_sha256_stable_for_same_bytes(tmp_path: Path):
    import hashlib

    path = tmp_path / "same.txt"
    path.write_bytes(b"identical-content")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == hashlib.sha256(b"identical-content").hexdigest()
