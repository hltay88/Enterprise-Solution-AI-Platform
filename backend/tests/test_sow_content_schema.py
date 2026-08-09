"""SOW content schema tests."""

from app.schemas.deliverable import SowContentPayload


def test_sow_payload_requires_sections():
    payload = SowContentPayload.model_validate(
        {
            "title": "SOW",
            "sections": [
                {
                    "section_type": "purpose",
                    "title": "Purpose",
                    "sequence": 0,
                    "content_items": [
                        {
                            "text": "Scope from architecture",
                            "review_required": False,
                        }
                    ],
                }
            ],
        }
    )
    assert len(payload.sections) == 1
    assert payload.sections[0].section_type == "purpose"
