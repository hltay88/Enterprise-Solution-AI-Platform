"""Phase 5 closeout — golden-set RAG / re-rank / specialist / agent eval gates."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.ai.specialist_completion import enrich_specialist_output
from app.core.exceptions import ForbiddenError
from app.schemas.agent import SpecialistFinding, SpecialistOutput
from app.services.agent_tools import AgentToolGateway
from app.services.orchestrator_service import OrchestratorService
from app.services.rerank import lexical_overlap_score, rerank_hits
from app.services.retrieval_service import RetrievalService

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _load_json(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_golden_set_lexical_overlap_gate():
    """Each golden query must lexically match its expected evidence corpus."""
    data = _load_json("rag_golden_set.json")
    min_ratio = float(data["min_overlap_ratio"])
    # Portable synthetic corpora per domain (offline stand-in for indexed chunks)
    corpora = {
        "wireless": "High-density Wi-Fi AP spacing and RF design for wireless capacity planning.",
        "networking": "Campus LAN and WAN with SD-WAN routing best practices for enterprise networks.",
        "cybersecurity": "Zero trust segmentation with firewall cybersecurity controls and policy.",
        "hci": "Hyperconverged infrastructure HCI compute cluster design and virtualization.",
        "backup": "Backup disaster recovery with RPO RTO retention policies and restore drills.",
    }
    for case in data["cases"]:
        corpus = corpora[case["domain_hint"]]
        score = lexical_overlap_score(case["query"], corpus)
        assert score >= min_ratio, f"{case['id']}: overlap {score} < {min_ratio}"
        content_l = corpus.lower()
        assert any(tok in content_l for tok in case["must_contain_any"]), case["id"]


def test_rerank_boosts_lexical_match_over_weak_rrf():
    query = "high density wifi wireless AP spacing"
    hits = [
        {
            "chunk_id": "weak",
            "content": "unrelated invoice payment terms",
            "fused_score": 0.05,
            "knowledge_item_id": "i1",
        },
        {
            "chunk_id": "strong",
            "content": "high density wifi AP spacing wireless RF design guidance",
            "fused_score": 0.02,
            "knowledge_item_id": "i2",
        },
    ]
    ranked = rerank_hits(query, hits, top_k=2)
    assert ranked[0]["chunk_id"] == "strong"
    assert ranked[0]["rerank_score"] > ranked[1]["rerank_score"]


def test_rrf_plus_rerank_pipeline_orders_overlap_first():
    v = [
        {"chunk_id": "a", "content": "campus WAN SD-WAN routing", "knowledge_item_id": "i1", "vector_score": 0.9},
        {"chunk_id": "b", "content": "misc notes", "knowledge_item_id": "i2", "vector_score": 0.85},
    ]
    k = [
        {"chunk_id": "a", "content": "campus WAN SD-WAN routing", "knowledge_item_id": "i1", "keyword_score": 0.8},
        {"chunk_id": "c", "content": "other", "knowledge_item_id": "i3", "keyword_score": 0.5},
    ]
    fused = RetrievalService._rrf_fuse(v, k, top_k=6)
    ranked = rerank_hits("campus LAN WAN SD-WAN routing", fused, top_k=3)
    assert ranked[0]["chunk_id"] == "a"


def test_specialist_local_enrich_adds_evidence_and_goal():
    base = SpecialistOutput(
        agent_id="networking",
        domain_code="networking",
        summary="Baseline assessment.",
        findings=[SpecialistFinding(code="ok", statement="fine", severity="info")],
        confidence=0.5,
        tools_used=["retrieve_knowledge"],
    )
    out = enrich_specialist_output(
        base,
        context={"goal": "Assess campus WAN", "rkm_summary": "Customer needs SD-WAN", "hit_count": 3},
    )
    codes = {f.code for f in out.findings}
    assert "evidence_density" in codes
    assert "goal_aligned" in codes
    assert "local_refine" in out.tools_used
    assert out.confidence >= base.confidence


def test_agent_eval_denied_tools_fixture():
    data = _load_json("agent_eval_set.json")
    gateway = AgentToolGateway(
        db=SimpleNamespace(),  # type: ignore[arg-type]
        project_id=uuid4(),
        user=SimpleNamespace(id=uuid4()),  # type: ignore[arg-type]
        run_id=uuid4(),
        agent_id="networking",
    )
    for tool in data["denied_tools"]:
        with pytest.raises(ForbiddenError):
            gateway.call(tool, {})


def test_agent_eval_conflict_pairs_fixture():
    data = _load_json("agent_eval_set.json")
    specialists = [
        SpecialistOutput(agent_id="security", domain_code="cybersecurity", summary="ok"),
        SpecialistOutput(agent_id="cloud", domain_code="cloud", summary="ok"),
        SpecialistOutput(agent_id="hci", domain_code="hci", summary="ok"),
        SpecialistOutput(agent_id="compute", domain_code="compute", summary="ok"),
        SpecialistOutput(agent_id="iot", domain_code="iot", summary="ok"),
    ]
    conflicts = OrchestratorService._merge_conflicts(specialists)
    codes = {c.code for c in conflicts}
    for _a, _b, expected in data["conflict_pairs"]:
        assert expected in codes
