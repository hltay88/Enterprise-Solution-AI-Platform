from app.services.gap_analysis_service import GapAnalysisService


class _Dummy(GapAnalysisService):
    def __init__(self):
        self.db = None
        self.projects = None
        self.rkms = None


def test_stakeholder_without_long_description_is_not_thin_gap():
    service = _Dummy()
    payload = {
        "business_objectives": [
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "title": "Outcome",
                "description": "Deliver reliable campus connectivity for students",
                "evidence_ids": ["22222222-2222-2222-2222-222222222222"],
            }
        ],
        "current_environment": {"summary": "ok", "items": []},
        "functional_requirements": [
            {
                "id": "33333333-3333-3333-3333-333333333333",
                "title": "WiFi",
                "description": "Provide enterprise WiFi coverage across blocks",
                "evidence_ids": ["22222222-2222-2222-2222-222222222222"],
            }
        ],
        "non_functional_requirements": [
            {
                "id": "44444444-4444-4444-4444-444444444444",
                "title": "HA",
                "description": "High availability for core network services",
                "evidence_ids": ["22222222-2222-2222-2222-222222222222"],
            }
        ],
        "constraints": [],
        "dependencies": [],
        "risks": [],
        "assumptions": [],
        "stakeholders": [
            {
                "id": "55555555-5555-5555-5555-555555555555",
                "name": "Site PIC",
                "role": "PIC",
                "designation": "IT",
                "evidence_ids": ["22222222-2222-2222-2222-222222222222"],
            }
        ],
    }
    gaps = service._detect_gaps(payload, missing=[])
    assert not any(
        gap.section == "stakeholders" and gap.code == "thin_description" for gap in gaps
    )
    assert not any("untitled" in gap.message for gap in gaps)
