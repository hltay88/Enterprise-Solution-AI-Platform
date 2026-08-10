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
        "description": "Campus/WAN/LAN advisory assessments",
    },
    "wireless": {
        "name": "Wireless Specialist",
        "domain_code": "wireless",
        "query": "Wi-Fi wireless high density AP spacing RF design",
        "description": "Wi-Fi / WLAN high-density advisory",
    },
    "security": {
        "name": "Security Specialist",
        "domain_code": "cybersecurity",
        "query": "cybersecurity zero trust network segmentation firewall controls",
        "description": "Cybersecurity / zero-trust advisory",
    },
    "cloud": {
        "name": "Cloud Specialist",
        "domain_code": "cloud",
        "query": "cloud landing zone connectivity hybrid connectivity security baseline",
        "description": "Cloud landing-zone advisory",
    },
    "data_centre": {
        "name": "Data Centre Specialist",
        "domain_code": "data_centre",
        "query": "data centre facility power cooling rack density cabling availability tiers",
        "description": "Data centre facility and fabric advisory",
    },
    "storage": {
        "name": "Storage Specialist",
        "domain_code": "storage",
        "query": "storage SAN NAS object performance capacity tiering data services",
        "description": "Storage architecture advisory",
    },
    "backup": {
        "name": "Backup Specialist",
        "domain_code": "backup",
        "query": "backup recovery RPO RTO immutability ransomware protection DR",
        "description": "Backup and recovery advisory",
    },
    "av": {
        "name": "AV Specialist",
        "domain_code": "av",
        "query": "audio visual collaboration meeting room UC room systems conferencing",
        "description": "AV / collaboration room advisory",
    },
    "led_videowall": {
        "name": "LED / Digital Signage Specialist",
        "domain_code": "led_videowall",
        "query": "LED videowall digital signage pixel pitch controller content playback",
        "description": "LED videowall and digital signage advisory",
    },
    "smart_building": {
        "name": "Smart Building / IoT Specialist",
        "domain_code": "smart_building",
        "query": "smart building IoT BMS sensors OT network segmentation building systems",
        "description": "Smart building / IoT advisory",
    },
    "compute": {
        "name": "Compute Specialist",
        "domain_code": "compute",
        "query": "compute virtualization server hypervisor capacity HA clustering workload placement",
        "description": "Compute and virtualization advisory",
    },
    "hci": {
        "name": "HCI Specialist",
        "domain_code": "hci",
        "query": "HCI hyperconverged infrastructure cluster sizing storage compute networking",
        "description": "Hyperconverged infrastructure advisory",
    },
    "digital_signage": {
        "name": "Digital Signage Specialist",
        "domain_code": "digital_signage",
        "query": "digital signage CMS players displays content scheduling network",
        "description": "Digital signage platform advisory",
    },
    "billboard": {
        "name": "Billboard Specialist",
        "domain_code": "billboard",
        "query": "outdoor billboard LED DOOH structural power brightness compliance",
        "description": "Outdoor billboard / DOOH advisory",
    },
    "iot": {
        "name": "IoT Specialist",
        "domain_code": "iot",
        "query": "IoT sensors CCTV edge gateways telemetry OT security device management",
        "description": "IoT / CCTV / telemetry advisory",
    },
}


def run_specialist(agent_id: str, tools: AgentToolGateway, *, goal: str | None = None) -> SpecialistOutput:
    meta = RUNNABLE_AGENTS.get(agent_id)
    if meta is None:
        return SpecialistOutput(
            agent_id=agent_id,
            domain_code=agent_id,
            status="blocked",
            summary=f"Agent '{agent_id}' is not a registered runnable specialist.",
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

    conflicts.extend(_conflict_hints(agent_id, domain_codes))

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


def _conflict_hints(agent_id: str, domain_codes: set[str]) -> list[str]:
    hints: list[str] = []
    has_security = "cybersecurity" in domain_codes or "security" in domain_codes
    if agent_id == "security" and "cloud" in domain_codes:
        hints.append(
            "Security vs Cloud: confirm shared-responsibility and ingress/egress controls for hybrid cloud.",
        )
    if agent_id == "wireless" and has_security:
        hints.append(
            "Wireless vs Security: confirm guest/IoT SSID isolation and NAC posture requirements.",
        )
    if agent_id == "networking" and "cloud" in domain_codes:
        hints.append(
            "Networking vs Cloud: confirm overlay/underlay and cloud on-ramp path selection.",
        )
    if agent_id == "storage" and "backup" in domain_codes:
        hints.append(
            "Storage vs Backup: confirm snapshot/replication vs backup catalogue ownership and retention.",
        )
    if agent_id == "backup" and "cloud" in domain_codes:
        hints.append(
            "Backup vs Cloud: confirm offline/immutable copies and cross-region recovery paths.",
        )
    if agent_id == "data_centre" and "cloud" in domain_codes:
        hints.append(
            "Data Centre vs Cloud: confirm hybrid placement, interconnect capacity, and exit strategy.",
        )
    if agent_id == "smart_building" and has_security:
        hints.append(
            "Smart Building vs Security: confirm OT/IT segmentation and BMS remote-access controls.",
        )
    if agent_id == "av" and "networking" in domain_codes:
        hints.append(
            "AV vs Networking: confirm multicast/QoS and separate/shared VLAN design for media.",
        )
    if agent_id == "led_videowall" and "av" in domain_codes:
        hints.append(
            "LED vs AV: confirm control-system ownership, content workflow, and power/heat budgets.",
        )
    if agent_id == "compute" and "storage" in domain_codes:
        hints.append(
            "Compute vs Storage: confirm datastore attachment model, IOPS budget, and HA failover domains.",
        )
    if agent_id == "hci" and ("compute" in domain_codes or "storage" in domain_codes):
        hints.append(
            "HCI vs Compute/Storage: confirm whether HCI replaces or coexists with discrete compute/storage stacks.",
        )
    if agent_id == "hci" and "backup" in domain_codes:
        hints.append(
            "HCI vs Backup: confirm cluster-native snapshots vs external backup catalogue and RPO/RTO.",
        )
    if agent_id == "digital_signage" and "networking" in domain_codes:
        hints.append(
            "Digital Signage vs Networking: confirm bandwidth, VLAN isolation, and player connectivity model.",
        )
    if agent_id == "billboard" and ("led_videowall" in domain_codes or "digital_signage" in domain_codes):
        hints.append(
            "Billboard vs LED/Signage: confirm outdoor structural/power/brightness vs indoor display standards.",
        )
    if agent_id == "iot" and has_security:
        hints.append(
            "IoT vs Security: confirm device identity, certificate lifecycle, and OT/IT segmentation.",
        )
    if agent_id == "iot" and "smart_building" in domain_codes:
        hints.append(
            "IoT vs Smart Building: confirm shared BMS/edge platform ownership and data paths.",
        )
    return hints
