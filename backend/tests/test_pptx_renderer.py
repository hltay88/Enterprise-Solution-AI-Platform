"""PPTX renderer smoke test."""

from app.services.rendering.pptx_renderer import render_presentation_pptx


def test_pptx_renderer_produces_bytes():
    data = render_presentation_pptx(
        title="Test Deck",
        status="draft",
        slides=[
            {
                "title": "Title",
                "section_type": "title",
                "content_items": [
                    {
                        "text": "Hello",
                        "content_type": "paragraph",
                        "review_required": False,
                        "structured_data": {
                            "slide": {
                                "key_message": "Hello customer",
                                "speaker_notes": "Welcome them",
                            }
                        },
                    },
                    {
                        "text": "Welcome them",
                        "content_type": "speaker_notes",
                        "review_required": False,
                        "structured_data": {},
                    },
                ],
            }
        ],
    )
    assert isinstance(data, (bytes, bytearray))
    assert len(data) > 100
    assert data[:2] == b"PK"
