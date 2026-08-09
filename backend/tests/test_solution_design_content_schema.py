"""Solution design content schema tests."""

from app.schemas.deliverable import SolutionDesignContentPayload


def test_solution_design_payload_requires_sections():
    payload = SolutionDesignContentPayload.model_validate(
        {
            "title": "Solution Design",
            "sections": [
                {
                    "section_type": "design_objectives",
                    "title": "Design Objectives",
                    "sequence": 0,
                    "content_items": [{"text": "Align to architecture"}],
                }
            ],
        }
    )
    assert payload.sections[0].section_type == "design_objectives"
