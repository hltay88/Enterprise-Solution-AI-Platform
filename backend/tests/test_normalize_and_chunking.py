from app.services.document_intelligence.chunking import chunk_pages
from app.services.document_intelligence.normalize import detect_language_hint, normalize_text
from app.services.document_intelligence.types import ExtractedPage


def test_normalize_collapses_whitespace_and_control_chars():
    raw = "Hello\x00  world\r\n\r\n\r\nNext"
    assert normalize_text(raw) == "Hello world\n\nNext"


def test_detect_language_hint_ascii():
    assert detect_language_hint("Requirement for network firewall and VPN") == "en"


def test_chunk_pages_splits_long_text():
    page = ExtractedPage(page_number=1, text=("alpha " * 500).strip())
    chunks = chunk_pages([page], chunk_size=100, overlap=20)
    assert len(chunks) > 1
    assert chunks[0].page_number == 1
    assert all(chunk.char_count <= 100 for chunk in chunks)
