"""Proposal content schema tests."""

from app.schemas.deliverable import ProposalContentPayload


def test_proposal_payload_requires_sections():
    payload = ProposalContentPayload.model_validate(
        {
            "title": "Demo",
            "sections": [
                {
                    "section_type": "cover",
                    "title": "Cover",
                    "sequence": 0,
                    "content_items": [
                        {
                            "text": "Hello",
                            "source_refs": [],
                        }
                    ],
                }
            ],
        }
    )
    assert payload.title == "Demo"
    assert payload.sections[0].content_items[0].text == "Hello"
