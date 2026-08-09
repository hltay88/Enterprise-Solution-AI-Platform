"""Presentation content schema tests."""

from app.schemas.deliverable import PresentationContentPayload


def test_presentation_payload_requires_slides():
    payload = PresentationContentPayload.model_validate(
        {
            "title": "Deck",
            "slides": [
                {
                    "section_type": "title",
                    "title": "Title",
                    "sequence": 0,
                    "key_message": "Hello",
                    "body_content": "Body",
                    "speaker_notes": "Notes",
                }
            ],
        }
    )
    assert len(payload.slides) == 1
    assert payload.slides[0].key_message == "Hello"
