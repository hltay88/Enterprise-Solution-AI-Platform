"""Presentation validation — key_message rule."""

from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from app.schemas.deliverable import PRESENTATION_SECTION_TYPES
from app.services.deliverable_validation_service import DeliverableValidationService


def test_missing_key_message_blocks_presentation():
    service = DeliverableValidationService(MagicMock())
    sections = []
    body_section_id = uuid4()
    for code, title in PRESENTATION_SECTION_TYPES:
        sid = body_section_id if code == "title" else uuid4()
        sections.append(SimpleNamespace(id=sid, section_type=code, title=title))

    def list_content(sid):
        if sid == body_section_id:
            return [
                SimpleNamespace(
                    id=uuid4(),
                    text="Welcome",
                    review_required=False,
                    content_type="paragraph",
                    structured_data={"slide": {"key_message": ""}},
                )
            ]
        return [
            SimpleNamespace(
                id=uuid4(),
                text="ok",
                review_required=False,
                content_type="paragraph",
                structured_data={"slide": {"key_message": "Message"}},
            )
        ]

    service.repo.list_content_items = MagicMock(side_effect=list_content)
    service.repo.list_source_refs = MagicMock(return_value=[object()])
    result = service.validate_sections(
        sections, bom_validated=True, document_type="presentation"
    )
    assert result.ok is False
    assert any(i.code == "missing_key_message" for i in result.issues)
