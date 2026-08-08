import asyncio

from app.ai.local_provider import LocalAIProvider
from app.services.architecture_service import ArchitectureService
from app.core.exceptions import ValidationAppError
from types import SimpleNamespace
from uuid import uuid4
import pytest


def test_local_architecture_from_wifi_rkm():
    provider = LocalAIProvider()
    rkm = {
        "business_objectives": [
            {"title": "Improve coverage", "description": "Reliable campus WiFi"},
        ],
        "functional_requirements": [
            {
                "title": "WiFi 6 coverage",
                "description": "3 floors with seamless roaming and 802.1X",
            }
        ],
        "non_functional_requirements": [],
        "constraints": [],
        "risks": [{"title": "Survey delay", "description": "Floor plans late"}],
        "assumptions": [],
    }
    result = asyncio.run(
        provider.recommend_architecture(rkm, knowledge_pack_context="wireless pack"),
    )
    assert "Wi-Fi" in result["summary"] or "wireless" in result["summary"].lower()
    assert result["technology_stack"]
    assert result["high_level_architecture"]
    assert "vendor-neutral" in result["architecture_decisions"][1]["decision"].lower() or any(
        "vendor-neutral" in str(item).lower() for item in result["architecture_decisions"]
    )


def test_generate_requires_published_rkm():
    service = ArchitectureService.__new__(ArchitectureService)

    class Projects:
        def get_for_user(self, project_id, user_id):
            return SimpleNamespace(id=project_id)

    class Rkms:
        def get_published(self, _project_id):
            return None

    service.projects = Projects()
    service.rkms = Rkms()
    with pytest.raises(ValidationAppError) as exc:
        asyncio.run(service.generate(uuid4(), uuid4()))
    assert "Publish a Requirement Knowledge Model" in str(exc.value)
