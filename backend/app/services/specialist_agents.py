"""Sprint 5.3 — specialist agent runners (advise-only, local-heuristic friendly)."""

from __future__ import annotations

from typing import Any

from app.schemas.agent import AgentCitation, SpecialistFinding, SpecialistOutput
from app.services.agent_tools import AgentToolGateway

RUNNABLE_AGENTS: dict[str, dict[str, str]] = {
    "networking": {
        "name": "Networking Specialist",
        "domain_code": "networking",
        "query": "campus LAN WAN SD-WAN routing switching design best practices",
    },
    "wireless": {
        "name": "Wireless Specialist",
        "domain_code": "wireless",
        "query": "Wi-Fi wireless high density AP spacing RF design",
    },
    "security": {
        "name": "Security Specialist",
        "domain_code": "cybersecurity",
        "query": "cybersecurity zero trust network segmentation firewall controls",
    },
    "cloud": {
        "name": "Cloud Specialist",
        "domain_code": "cloud",
        "query": "cloud landing zone connectivity hybrid connectivity security baseline",
    },
}


def run_specialist(agent_id: str, tools: AgentToolGateway, *, goal: str | None = None) -> SpecialistOutput:
    meta = RUNNABLE_AGENTS.get(agent_id)
    if meta is None:
        return SpecialistOutput(
            agent_id=agent_id,
            domain_code=agent_id,
            status="blocked",
            summary=f"Agent '{agent_id}' is not runnable in Sprint 5.3.",
            confidence=0.0,
        )

    gateway = tools.for_agent(agent_id)
    tools_used: list[str] = []
    citations: list[AgentCitation] = []

    rkm = gateway.call("get_published_rkm", {})
    tools_used.append("get_published_rkm")
    domains = gateway.call("get_domain_analysis", {})
    tools_used.append("get_domain_analysis")
    arch = gateway.call("get_architectures", {})
    tools_used.append("get_architectures")

    query = meta["query"]
    if goal:
        query = f"{goal} {query}"
    if rkm.get("found") and rkm.get("summary"):
        query = f"{query} {str(rkm.get('summary'))[:240]}"

    knowledge = gateway.call(
        "knowledge_search",
        {"query": query, "domain_code": meta["domain_code"], "top_k": 5, "min_score": 0.0},
    )
    tools_used.append("knowledge_search")

    hits = knowledge.get("hits") or []
    for hit in hits[:5]:
        cite = hit.get("citation") or {}
        citations.append(
            AgentCitation(
                source_kind="knowledge",
                title=cite.get("title") or "Knowledge",
                knowledge_id=cite.get("knowledge_id"),
                knowledge_version_id=cite.get("knowledge_version_id"),
                chunk_id=cite.get("chunk_id") or hit.get("chunk_id"),
                domain_code=cite.get("domain_code") or meta["domain_code"],
                excerpt=(cite.get("excerpt") or hit.get("content") or "")[:400],
            ),
        )

    return _heuristic_assess(
        agent_id=agent_id,
        domain_code=meta["domain_code"],
        goal=goal,
        rkm=rkm,
        domains=domains,
        arch=arch,
        hits=hits,
        citations=citations,
        tools_used=tools_used,
        insufficient=bool(knowledge.get("insufficient_evidence")),
    )


def _heuristic_assess(
    *,
    agent_id: str,
    domain_code: str,
    goal: str | None,
    rkm: dict[str, Any],
    domains: dict[str, Any],
    arch: dict[str, Any],
    hits: list[dict[str, Any]],
    citations: list[AgentCitation],
    tools_used: list[str],
    insufficient: bool,
) -> SpecialistOutput:
    domain_codes = {
        str(d.get("code") or "").lower()
        for d in (domains.get("domains") or [])
        if d.get("code")
    }
    has_rkm = bool(rkm.get("found"))
    has_knowledge = len(hits) > 0
    mentioned = domain_code in domain_codes or any(
        domain_code in str(d.get("code") or "").lower() for d in (domains.get("domains") or [])
    )

    findings: list[SpecialistFinding] = []
    assumptions: list[str] = []
    risks: list[str] = []
    recommendations: list[str] = []
    conflicts: list[str] = []

    if not has_rkm:
        findings.append(
            SpecialistFinding(
                code="missing_rkm",
                statement="No published RKM found; assessment limited to available knowledge.",
                severity="warning",
            ),
        )
        assumptions.append("Published RKM will be provided before firm design decisions.")

    if mentioned:
        findings.append(
            SpecialistFinding(
                code="domain_present",
                statement=f"Solution domain analysis includes '{domain_code}'.",
                severity="info",
            ),
        )
    elif has_rkm:
        findings.append(
            SpecialistFinding(
                code="domain_not_selected",
                statement=f"Domain '{domain_code}' not clearly selected in latest domain analysis.",
                severity="warning",
            ),
        )
        recommendations.append(f"Confirm whether {domain_code} is in scope for this opportunity.")

    if has_knowledge:
        top = hits[0]
        excerpt = (top.get("content") or "")[:220]
        findings.append(
            SpecialistFinding(
                code="knowledge_grounded",
                statement=f"Grounded on enterprise knowledge: {excerpt}",
                severity="info",
                evidence=[str(top.get("chunk_id") or "")],
            ),
        )
        recommendations.append(
            f"Apply {domain_code} guidance from cited knowledge when shaping architecture.",
        )
    else:
        findings.append(
            SpecialistFinding(
                code="no_knowledge_hits",
                statement="No eligible enterprise knowledge chunks retrieved for this domain.",
                severity="warning",
            ),
        )
        recommendations.append(
            "Publish approved domain knowledge to the Enterprise Knowledge Library.",
        )

    if int(arch.get("count") or 0) == 0:
        assumptions.append("Architecture options are not yet generated for this project.")
    else:
        findings.append(
            SpecialistFinding(
                code="architecture_present",
                statement=f"Found {arch.get('count')} architecture option(s) for cross-check.",
                severity="info",
            ),
        )

    # Lightweight cross-domain conflict hints used by orchestrator merge.
    if agent_id == "security" and "cloud" in domain_codes:
        conflicts.append(
            "Security vs Cloud: confirm shared-responsibility and ingress/egress controls for hybrid cloud.",
        )
    if agent_id == "wireless" and ("cybersecurity" in domain_codes or "security" in domain_codes):
        conflicts.append(
            "Wireless vs Security: confirm guest/IoT SSID isolation and NAC posture requirements.",
        )
    if agent_id == "networking" and "cloud" in domain_codes:
        conflicts.append(
            "Networking vs Cloud: confirm overlay/underlay and cloud on-ramp path selection.",
        )

    if goal:
        recommendations.append(f"Align {domain_code} recommendations to goal: {goal[:200]}")

    if insufficient or (not has_knowledge and not has_rkm):
        status = "insufficient_evidence"
        confidence = 0.25
        summary = (
            f"{domain_code} specialist: insufficient grounded evidence — REVIEW REQUIRED."
        )
    elif not has_knowledge:
        status = "partial"
        confidence = 0.45
        summary = f"{domain_code} specialist: partial assessment from project context only."
    else:
        status = "ok"
        confidence = 0.72 if mentioned else 0.6
        summary = f"{domain_code} specialist: advisory assessment grounded on retrieved knowledge."

    risks.append(f"Advisory-only output — do not treat as approved {domain_code} design.")

    return SpecialistOutput(
        agent_id=agent_id,
        domain_code=domain_code,
        status=status,
        summary=summary,
        findings=findings,
        assumptions=assumptions,
        risks=risks,
        recommendations=recommendations,
        conflicts=conflicts,
        confidence=confidence,
        citations=citations,
        tools_used=tools_used,
    )
