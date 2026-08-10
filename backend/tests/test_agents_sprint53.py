"""Sprint 5.3 — multi-agent tools, contracts, and orchestration (no DB)."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.constants.knowledge_taxonomy import TAXONOMY_CODES
from app.core.exceptions import ForbiddenError
from app.schemas.agent import AgentRunRequest, SpecialistOutput
from app.services.agent_tools import WRITE_TOOLS_DENIED, AgentToolGateway
from app.services.orchestrator_service import OrchestratorService
from app.services.specialist_agents import RUNNABLE_AGENTS, run_specialist


def test_write_tools_are_denied():
    gateway = AgentToolGateway(
        db=SimpleNamespace(),  # type: ignore[arg-type]
        project_id=uuid4(),
        user=SimpleNamespace(id=uuid4()),  # type: ignore[arg-type]
        run_id=uuid4(),
        agent_id="networking",
    )
    for tool in sorted(WRITE_TOOLS_DENIED):
        with pytest.raises(ForbiddenError):
            gateway.call(tool, {})


def test_runnable_agents_cover_full_taxonomy():
    expected = {
        "networking",
        "wireless",
        "security",
        "cloud",
        "data_centre",
        "storage",
        "backup",
        "av",
        "led_videowall",
        "smart_building",
        "compute",
        "hci",
        "digital_signage",
        "billboard",
        "iot",
    }
    assert set(RUNNABLE_AGENTS) == expected
    assert RUNNABLE_AGENTS["security"]["domain_code"] == "cybersecurity"
    covered_domains = {meta["domain_code"] for meta in RUNNABLE_AGENTS.values()}
    assert TAXONOMY_CODES <= covered_domains
    assert all("query" in meta and "name" in meta for meta in RUNNABLE_AGENTS.values())


def test_select_agents_by_include_and_focus():
    body = AgentRunRequest(include_agents=["networking", "unknown_xyz", "compute", "iot"])
    assert OrchestratorService._select_agents(body) == ["networking", "compute", "iot"]

    body2 = AgentRunRequest(focus_domains=["hci", "cybersecurity", "billboard"])
    selected = OrchestratorService._select_agents(body2)
    assert set(selected) == {"hci", "security", "billboard"}


def test_merge_conflicts_detects_cross_domain():
    specialists = [
        SpecialistOutput(agent_id="security", domain_code="cybersecurity", summary="ok"),
        SpecialistOutput(agent_id="cloud", domain_code="cloud", summary="ok"),
        SpecialistOutput(agent_id="hci", domain_code="hci", summary="ok"),
        SpecialistOutput(agent_id="compute", domain_code="compute", summary="ok"),
        SpecialistOutput(agent_id="iot", domain_code="iot", summary="ok"),
    ]
    conflicts = OrchestratorService._merge_conflicts(specialists)
    codes = {c.code for c in conflicts}
    assert "security_cloud" in codes
    assert "hci_compute" in codes
    assert "iot_security" in codes


class _FakeGateway:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def for_agent(self, agent_id: str) -> "_FakeGateway":
        _ = agent_id
        return self

    def call(self, tool_name: str, request: dict | None = None) -> dict:
        _ = request
        self.calls.append(tool_name)
        if tool_name == "get_published_rkm":
            return {"found": True, "summary": "Campus Wi-Fi and cloud connectivity refresh"}
        if tool_name == "get_domain_analysis":
            return {
                "found": True,
                "domains": [
                    {"code": "wireless", "name": "Wireless"},
                    {"code": "cybersecurity", "name": "Security"},
                    {"code": "cloud", "name": "Cloud"},
                    {"code": "storage", "name": "Storage"},
                    {"code": "compute", "name": "Compute"},
                    {"code": "hci", "name": "HCI"},
                    {"code": "iot", "name": "IoT"},
                    {"code": "smart_building", "name": "Smart Building"},
                ],
            }
        if tool_name == "get_architectures":
            return {"count": 0, "architectures": []}
        if tool_name == "knowledge_search":
            return {
                "insufficient_evidence": False,
                "hits": [
                    {
                        "chunk_id": str(uuid4()),
                        "content": "Segment guest SSID and enforce NAC posture checks.",
                        "citation": {
                            "title": "Wireless Security Guide",
                            "domain_code": "wireless",
                            "excerpt": "Segment guest SSID",
                        },
                    },
                ],
            }
        return {}


def test_specialist_heuristic_local_assessment():
    tools = _FakeGateway()
    out = run_specialist("wireless", tools, goal="Assess high-density Wi-Fi")  # type: ignore[arg-type]
    assert out.agent_id == "wireless"
    assert out.status == "ok"
    assert out.confidence > 0.5
    assert "knowledge_search" in out.tools_used
    assert any(f.code == "knowledge_grounded" for f in out.findings)
    assert out.citations
    assert out.conflicts  # wireless vs security hint


def test_all_runnable_specialists_execute():
    tools = _FakeGateway()
    for agent_id in RUNNABLE_AGENTS:
        out = run_specialist(agent_id, tools)  # type: ignore[arg-type]
        assert out.status == "ok", agent_id
        assert out.agent_id == agent_id
        assert out.confidence > 0


def test_specialist_unknown_is_blocked():
    out = run_specialist("not_a_real_agent", _FakeGateway())  # type: ignore[arg-type]
    assert out.status == "blocked"
