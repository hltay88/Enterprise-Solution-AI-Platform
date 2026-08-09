"""Deliverable validation rules."""

from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from app.services.deliverable_validation_service import DeliverableValidationService


def test_pricing_without_bom_flagged():
    db = MagicMock()
    service = DeliverableValidationService(db)
    section_id = uuid4()
    item_id = uuid4()
    sections = [
        SimpleNamespace(id=section_id, section_type="proposed_solution", title="Solution")
    ]
    # Make all required sections present by faking list via validate_sections only
    # Directly test content scan:
    service.repo.list_content_items = MagicMock(
        return_value=[
            SimpleNamespace(
                id=item_id,
                text="Unit price is $1200 per AP",
                review_required=False,
            )
        ]
    )
    service.repo.list_source_refs = MagicMock(return_value=[object()])

    # Inject required section types with one priced section + stubs for others
    from app.schemas.deliverable import PROPOSAL_SECTION_TYPES

    all_sections = []
    for code, title in PROPOSAL_SECTION_TYPES:
        sid = section_id if code == "proposed_solution" else uuid4()
        all_sections.append(
            SimpleNamespace(id=sid, section_type=code, title=title)
        )

    def list_content(sid):
        if sid == section_id:
            return [
                SimpleNamespace(
                    id=item_id,
                    text="Unit price is $1200 per AP",
                    review_required=False,
                )
            ]
        return [
            SimpleNamespace(
                id=uuid4(),
                text="ok",
                review_required=False,
            )
        ]

    service.repo.list_content_items = MagicMock(side_effect=list_content)
    result = service.validate_sections(all_sections, bom_validated=False)
    assert result.ok is False
    assert any(i.code == "pricing_without_authority" for i in result.issues)


def test_pricing_disclaimer_not_flagged():
    """ATLAS-047: 'pricing omitted' is compliant without a validated BOM."""
    db = MagicMock()
    service = DeliverableValidationService(db)
    section_id = uuid4()

    from app.schemas.deliverable import PROPOSAL_SECTION_TYPES

    all_sections = []
    for code, title in PROPOSAL_SECTION_TYPES:
        sid = section_id if code == "proposed_solution" else uuid4()
        all_sections.append(
            SimpleNamespace(id=sid, section_type=code, title=title)
        )

    disclaimer = (
        "Commercial pricing is omitted until a validated BOM is available. "
        "Do not invent unit prices."
    )

    def list_content(sid):
        if sid == section_id:
            return [
                SimpleNamespace(
                    id=uuid4(),
                    text=disclaimer,
                    review_required=False,
                )
            ]
        return [
            SimpleNamespace(id=uuid4(), text="ok", review_required=False)
        ]

    service.repo.list_content_items = MagicMock(side_effect=list_content)
    service.repo.list_source_refs = MagicMock(return_value=[object()])
    result = service.validate_sections(all_sections, bom_validated=False)
    assert not any(i.code == "pricing_without_authority" for i in result.issues)
