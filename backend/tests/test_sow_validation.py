"""SOW / solution design validation tests."""

from types import SimpleNamespace

from app.schemas.deliverable import SOW_SECTION_TYPES, SOLUTION_DESIGN_SECTION_TYPES
from app.services.deliverable_validation_service import DeliverableValidationService


class _FakeRepo:
    def list_content_items(self, section_id):
        return []

    def list_source_refs(self, content_item_id):
        return []


def test_sow_missing_sections_are_errors():
    svc = DeliverableValidationService.__new__(DeliverableValidationService)
    svc.repo = _FakeRepo()
    # Only first section present
    code, title = SOW_SECTION_TYPES[0]
    sections = [
        SimpleNamespace(id="s1", section_type=code, title=title, assumptions_json=[])
    ]
    result = svc.validate_sections(
        sections, bom_validated=False, document_type="sow", load_content=False
    )
    assert result.ok is False
    assert any(i.code == "missing_section" for i in result.issues)


def test_solution_design_full_sections_ok_without_content_load():
    svc = DeliverableValidationService.__new__(DeliverableValidationService)
    svc.repo = _FakeRepo()
    sections = [
        SimpleNamespace(id=f"s{i}", section_type=code, title=title, assumptions_json=[])
        for i, (code, title) in enumerate(SOLUTION_DESIGN_SECTION_TYPES)
    ]
    result = svc.validate_sections(
        sections,
        bom_validated=True,
        document_type="solution_design",
        load_content=False,
    )
    assert result.ok is True


def test_sow_contractual_language_warning():
    svc = DeliverableValidationService.__new__(DeliverableValidationService)

    class Repo:
        def list_content_items(self, section_id):
            return [
                SimpleNamespace(
                    id="c1",
                    text="Provider shall warrant SLA of 99.99% with penalties.",
                    content_type="paragraph",
                    review_required=False,
                    structured_data={},
                )
            ]

        def list_source_refs(self, content_item_id):
            return []

    svc.repo = Repo()
    sections = [
        SimpleNamespace(
            id="s1",
            section_type=code,
            title=title,
            assumptions_json=[],
        )
        for code, title in SOW_SECTION_TYPES
    ]
    result = svc.validate_sections(
        sections, bom_validated=True, document_type="sow", load_content=True
    )
    assert any(i.code == "sow_contractual_invention" for i in result.issues)
