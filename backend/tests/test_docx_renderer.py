"""DOCX renderer smoke test."""

from app.services.rendering.docx_renderer import render_proposal_docx


def test_docx_renderer_produces_bytes():
    data = render_proposal_docx(
        title="Test Proposal",
        status="draft",
        sections=[
            {
                "title": "Executive Summary",
                "section_type": "executive_summary",
                "assumptions": [],
                "content_items": [
                    {
                        "text": "Hello world",
                        "content_type": "paragraph",
                        "review_required": False,
                    }
                ],
            }
        ],
    )
    assert isinstance(data, (bytes, bytearray))
    assert len(data) > 100
    assert data[:2] == b"PK"  # zip/docx
