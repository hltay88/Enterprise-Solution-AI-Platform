"""BOM / package unit tests (Sprint 4.4)."""

from app.schemas.deliverable import BOM_SECTION_TYPES
from app.services.bom_generation_service import _classify
from app.services.rendering.xlsx_renderer import render_bom_xlsx


def test_bom_section_types():
    assert len(BOM_SECTION_TYPES) == 5
    assert BOM_SECTION_TYPES[0][0] == "cover"


def test_classify_optional_and_recommended():
    assert _classify("optional accessory", None) == "optional"
    assert _classify("recommended uplink", "") == "recommended"
    assert _classify("core switching", None) == "mandatory"
    assert _classify("", None) == "review_required"


def test_xlsx_renderer_produces_workbook():
    data = render_bom_xlsx(
        title="BOM Test",
        status="draft",
        sections=[
            {
                "section_type": "cover",
                "title": "Cover",
                "content_items": [{"text": "Hello", "review_required": False}],
            },
            {
                "section_type": "line_items",
                "title": "Line Items",
                "content_items": [
                    {
                        "text": "Acme | AP-1",
                        "review_required": False,
                        "structured_data": {
                            "bom_item": {
                                "vendor": "Acme",
                                "product_model": "AP-1",
                                "quantity": 10,
                                "unit": "ea",
                                "category": "wireless",
                                "description": "AP",
                                "sku": "AP1",
                            }
                        },
                    }
                ],
            },
            {
                "section_type": "classification",
                "title": "Classification",
                "content_items": [
                    {
                        "text": "AP-1: mandatory",
                        "structured_data": {
                            "classification": "mandatory",
                            "bom_item": {"product_model": "AP-1", "sku": "AP1"},
                        },
                    }
                ],
            },
            {
                "section_type": "issues",
                "title": "Issues",
                "content_items": [{"text": "None", "review_required": False}],
            },
            {
                "section_type": "sources",
                "title": "Sources",
                "content_items": [{"text": "snapshot", "review_required": False}],
            },
        ],
    )
    assert isinstance(data, (bytes, bytearray))
    assert len(data) > 100
    assert data[:2] == b"PK"
