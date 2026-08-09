"""Offline heuristic AI provider for local demo when OpenAI is unavailable."""

from __future__ import annotations

import re
from typing import Any

from app.ai.base import AIProvider

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
_BULLET_LINE = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+")


class LocalAIProvider(AIProvider):
    """Produce usable Sprint 1 analysis without calling an external LLM."""

    async def analyze_requirements(self, document_text: str) -> dict[str, Any]:
        buckets = _heuristic_buckets(document_text)
        return {
            "business_objectives": _as_bullets(buckets["objectives"]),
            "functional_requirements": _as_bullets(buckets["functional"]),
            "non_functional_requirements": _as_bullets(buckets["non_functional"]),
            "assumptions": _as_bullets(buckets["assumptions"]),
            "risks": _as_bullets(buckets["risks"]),
            "provider": "local",
        }

    async def extract_rkm_draft(self, source_text: str) -> dict[str, Any]:
        buckets = _heuristic_buckets(source_text)
        haystack = (source_text or "").lower()

        def _req_items(lines: list[str], *, category: str, priority: str = "medium") -> list[dict]:
            items = []
            for line in lines:
                items.append(
                    {
                        "title": line[:120],
                        "description": line,
                        "category": category,
                        "subcategory": None,
                        "priority": priority,
                        "confidence": 55,
                    },
                )
            return items

        env_items: list[dict[str, Any]] = []
        for token, title in (
            ("wifi", "Existing wireless footprint"),
            ("firewall", "Existing security controls"),
            ("server room", "Existing server room / core"),
            ("wap", "Wireless access points present in drawings"),
        ):
            if token in haystack:
                env_items.append(
                    {
                        "title": title,
                        "description": f"Source material references '{token}'.",
                        "confidence": 50,
                    },
                )

        return {
            "business_objectives": [
                {
                    "title": line[:120],
                    "description": line,
                    "priority": "high",
                    "confidence": 55,
                }
                for line in buckets["objectives"]
            ],
            "current_environment": {
                "summary": "Inferred from sales intake and uploaded drawings/documents.",
                "items": env_items
                or [
                    {
                        "title": "Current environment details incomplete",
                        "description": "Confirm as-is topology, sites, and constraints with the customer.",
                        "confidence": 40,
                    },
                ],
            },
            "functional_requirements": _req_items(
                buckets["functional"],
                category="infrastructure" if "wifi" in haystack or "network" in haystack else "functional",
            ),
            "non_functional_requirements": _req_items(
                buckets["non_functional"],
                category="non_functional",
            ),
            "constraints": [],
            "dependencies": [],
            "risks": _req_items(buckets["risks"], category="business", priority="high"),
            "assumptions": _req_items(buckets["assumptions"], category="business"),
            "reasoning_summary": (
                "Draft RKM generated locally from sales intake and document text heuristics. "
                "Validate with stakeholders before review/publish."
            ),
            "provider": "local",
            "model": "local-heuristics",
        }

    async def recommend_architecture(
        self,
        published_rkm: dict[str, Any],
        *,
        knowledge_pack_context: str = "",
    ) -> dict[str, Any]:
        return _local_architecture(published_rkm, knowledge_pack_context=knowledge_pack_context)

    async def recommend_architectures(
        self,
        published_rkm: dict[str, Any],
        *,
        domain_context: str = "",
        pattern_context: str = "",
    ) -> dict[str, Any]:
        from app.ai.common import normalize_architecture_candidates

        raw = _local_architecture_candidates(
            published_rkm,
            domain_context=domain_context,
            pattern_context=pattern_context,
        )
        result = normalize_architecture_candidates(raw)
        result["provider"] = "local"
        result["model"] = "local-architecture-candidates"
        return result

    async def identify_solution_domains(
        self,
        published_rkm: dict[str, Any],
        *,
        knowledge_pack_context: str = "",
    ) -> dict[str, Any]:
        return _local_domain_identification(
            published_rkm,
            knowledge_pack_context=knowledge_pack_context,
        )

    async def generate_proposal_content(
        self,
        snapshot: dict[str, Any],
        content_plan: dict[str, Any],
        *,
        prompt_version: str = "proposal_v1",
    ) -> dict[str, Any]:
        return _local_proposal_content(
            snapshot,
            content_plan,
            prompt_version=prompt_version,
        )

    async def generate_clarifications(
        self,
        analysis: dict[str, Any],
        *,
        document_text: str = "",
        checklist_context: str = "",
        detected_domains: list[str] | None = None,
        min_questions: int = 8,
        max_questions: int = 16,
    ) -> list[str]:
        objectives = str(analysis.get("business_objectives") or "")
        functional = str(analysis.get("functional_requirements") or "")
        nfr = str(analysis.get("non_functional_requirements") or "")
        risks = str(analysis.get("risks") or "")
        domains = set(detected_domains or [])
        # Ignore checklist_context text for heuristics (packs mention adjacent domains).
        haystack = " ".join([objectives, functional, nfr, document_text]).lower()

        questions = [
            "Which business outcomes are mandatory for go-live versus nice-to-have?",
            "Who are the primary users and decision-makers for this solution?",
            "What existing systems must be integrated in the first release?",
            "What data sources are in scope, and who owns data quality?",
            "What security, compliance, or residency constraints are non-negotiable?",
            "What availability and performance targets define success?",
            "What is the target timeline and any hard external deadlines?",
            "Which risks from the analysis are already accepted by the customer?",
        ]

        domain_seeds: list[str] = []
        if "wireless" in domains or any(
            token in haystack for token in ("wifi", "wi-fi", "wlan", "access point", "heatmap")
        ):
            domain_seeds.extend(
                [
                    "Is an accurate scaled floor plan available for the wireless design scope?",
                    "Which indoor and outdoor areas require wireless coverage, and which are out of scope?",
                    "What concurrent client density and peak-usage scenarios should drive capacity design?",
                    "Should the proposal include a predictive heatmap and estimated AP count/types?",
                ]
            )
        if "networking" in domains:
            domain_seeds.append(
                "What is the target campus LAN topology and which buildings/IDFs are in scope?",
            )
        if "data_centre" in domains:
            domain_seeds.append(
                "What rack count, kW/rack target, and power/cooling redundancy model are required?",
            )
        if "network_security" in domains:
            domain_seeds.append(
                "What throughput, HA model, and traffic inspection scope must the firewall/NAC design support?",
            )
        if "cybersecurity" in domains:
            domain_seeds.append(
                "Which endpoint, identity, and SOC/SIEM controls are mandatory for go-live evidence?",
            )
        if "storage" in domains:
            domain_seeds.append(
                "What capacity, performance, protocol, and RPO/RTO targets drive the storage design?",
            )
        if "hci" in domains:
            domain_seeds.append(
                "What HCI cluster size, failure tolerance, and backup/DR topology are required?",
            )
        if "servers" in domains:
            domain_seeds.append(
                "What server counts, form factors, and workload consolidation targets are in scope?",
            )
        if "led" in domains:
            domain_seeds.append(
                "What wall dimensions, viewing distance, pixel pitch, and content sources are required for the LED wall?",
            )
        if "av" in domains:
            domain_seeds.append(
                "Which rooms need AV/UC, and what audio, display, and control outcomes define success?",
            )
        if domain_seeds:
            questions = [*domain_seeds, *questions]

        if "integrat" in functional.lower():
            questions.insert(
                3,
                "For each required integration, what interface/API and ownership model exists today?",
            )
        if "security" in nfr.lower() or "compliance" in nfr.lower():
            questions.append(
                "Which security controls or compliance frameworks must be evidenced at go-live?",
            )
        if objectives.strip():
            questions.append(
                "How should success for the stated business objectives be measured after launch?",
            )
        if risks.strip():
            questions.append(
                "Which identified risks need mitigation before solution design begins?",
            )

        deduped: list[str] = []
        for question in questions:
            if question not in deduped:
                deduped.append(question)
        upper = max(min_questions, min(max_questions, len(deduped)))
        return deduped[:upper]


def _heuristic_buckets(document_text: str) -> dict[str, list[str]]:
    text = (document_text or "").strip()
    sentences = _extract_sentences(text)

    objectives = _pick(
        sentences,
        keywords=(
            "objective",
            "goal",
            "outcome",
            "business",
            "improve",
            "reduce",
            "increase",
            "enable",
            "transform",
        ),
        limit=6,
    )
    functional = _pick(
        sentences,
        keywords=(
            "must",
            "shall",
            "should",
            "need",
            "require",
            "system",
            "user",
            "workflow",
            "process",
            "feature",
            "function",
            "wifi",
            "network",
            "firewall",
            "server",
            "coverage",
        ),
        limit=8,
    )
    non_functional = _pick(
        sentences,
        keywords=(
            "performance",
            "latency",
            "availability",
            "security",
            "compliance",
            "scalability",
            "uptime",
            "sla",
            "privacy",
            "audit",
            "encryption",
            "10gbps",
            "redundant",
        ),
        limit=6,
    )
    assumptions = _pick(
        sentences,
        keywords=("assume", "assumption", "expected", "probably", "likely"),
        limit=4,
    )
    risks = _pick(
        sentences,
        keywords=("risk", "issue", "constraint", "blocker", "dependency", "concern"),
        limit=4,
    )

    if not objectives:
        objectives = [
            "Clarify primary business outcomes the solution must deliver.",
            "Identify measurable success criteria with the customer stakeholders.",
        ]
    if not functional:
        functional = sentences[:5] or [
            "Capture core user workflows that the solution must support.",
            "Define required integrations with existing enterprise systems.",
        ]
    if not non_functional:
        non_functional = [
            "Confirm availability, security, and performance expectations.",
            "Confirm compliance, audit, and data residency constraints.",
        ]
    if not assumptions:
        assumptions = [
            "Document text is representative of the current customer scope.",
            "Stakeholders will validate prioritized requirements in a follow-up workshop.",
        ]
    if not risks:
        risks = [
            "Scope may be incomplete until clarification questions are answered.",
            "Missing non-functional targets may delay solution design.",
        ]

    return {
        "objectives": objectives,
        "functional": functional,
        "non_functional": non_functional,
        "assumptions": assumptions,
        "risks": risks,
    }


def _extract_sentences(text: str) -> list[str]:
    chunks: list[str] = []
    for raw in _SENTENCE_SPLIT.split(text):
        line = _BULLET_LINE.sub("", raw).strip()
        line = re.sub(r"\s+", " ", line)
        if len(line) < 20:
            continue
        if line.lower().startswith("# document:"):
            continue
        chunks.append(line[:320])
    # Preserve order but unique
    seen: set[str] = set()
    unique: list[str] = []
    for item in chunks:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def _pick(sentences: list[str], keywords: tuple[str, ...], limit: int) -> list[str]:
    matched = [
        sentence
        for sentence in sentences
        if any(keyword in sentence.lower() for keyword in keywords)
    ]
    return matched[:limit]


def _as_bullets(items: list[str]) -> str:
    return "\n".join(f"- {item.rstrip('.')}" for item in items if item.strip())


def _local_architecture(
    published_rkm: dict[str, Any],
    *,
    knowledge_pack_context: str = "",
) -> dict[str, Any]:
    """Vendor-neutral architecture heuristic from Published RKM fields."""
    blob_parts: list[str] = []
    titles: list[str] = []
    for key in (
        "business_objectives",
        "functional_requirements",
        "non_functional_requirements",
        "constraints",
        "risks",
    ):
        for item in published_rkm.get(key) or []:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            desc = str(item.get("description") or "").strip()
            if title:
                titles.append(title)
            blob_parts.extend([title, desc])
    haystack = " ".join(blob_parts + [knowledge_pack_context]).lower()

    wants_wifi = any(token in haystack for token in ("wifi", "wi-fi", "wlan", "wireless", "access point"))
    wants_switching = any(token in haystack for token in ("switch", "switching", "10g", "uplink", "lan"))
    wants_security = any(token in haystack for token in ("802.1x", "nac", "firewall", "security", "ad "))
    wants_ops = any(token in haystack for token in ("nms", "monitor", "observability", "alerting"))

    domains: list[str] = []
    if wants_wifi:
        domains.append("campus wireless")
    if wants_switching:
        domains.append("campus LAN switching")
    if wants_security:
        domains.append("network access security")
    if wants_ops:
        domains.append("network operations")
    if not domains:
        domains.append("enterprise infrastructure")

    high_level = [
        f"Deliver a layered {', '.join(domains)} architecture aligned to published business outcomes.",
        "Separate access, distribution/core, and services/management planes.",
        "Keep design vendor-neutral; select products in a later BOM phase.",
    ]
    logical = [
        "User / device access layer for wired and/or wireless endpoints",
        "Aggregation / core layer for east-west and north-south traffic",
        "Identity and policy services for authentication and segmentation",
        "Management / observability plane for configuration and alerting",
    ]
    physical = [
        "Per-floor or per-IDF access infrastructure as required by coverage/density",
        "Redundant uplinks from access to distribution/core where HA is required",
        "Centralized or distributed controllers/services per site scale",
    ]
    stack: list[dict[str, str]] = []
    if wants_wifi:
        stack.append(
            {
                "layer": "Access",
                "category": "Enterprise Wi-Fi 6/6E WLAN",
                "rationale": "Satisfies wireless coverage and concurrent client requirements.",
            },
        )
    if wants_switching:
        stack.append(
            {
                "layer": "Campus LAN",
                "category": "Multi-gig / 10G capable access and aggregation switching",
                "rationale": "Supports uplink capacity and wired aggregation needs.",
            },
        )
    if wants_security:
        stack.append(
            {
                "layer": "Security",
                "category": "802.1X / NAC with directory integration",
                "rationale": "Enforces authenticated access aligned to identity requirements.",
            },
        )
    if wants_ops:
        stack.append(
            {
                "layer": "Operations",
                "category": "Centralized NMS / observability",
                "rationale": "Provides monitoring and alerting for day-2 operations.",
            },
        )
    if not stack:
        stack.append(
            {
                "layer": "Platform",
                "category": "Enterprise infrastructure platform",
                "rationale": "Baseline architecture pending richer published requirements.",
            },
        )

    components = [
        {
            "name": item,
            "purpose": f"Supports published requirement: {item}",
            "maps_to_requirements": [item],
        }
        for item in titles[:6]
    ] or [
        {
            "name": "Core solution fabric",
            "purpose": "Primary architecture backbone for published objectives",
            "maps_to_requirements": [],
        },
    ]

    assumptions = [
        "Published RKM is complete enough for high-level architecture.",
        "Detailed BOM and vendor selection occur in later phases.",
    ]
    if knowledge_pack_context.strip():
        assumptions.append("Vendor-neutral knowledge pack guidance was applied.")

    risks = [
        str(item.get("title") or item.get("description") or "Technical risk")
        for item in (published_rkm.get("risks") or [])
        if isinstance(item, dict)
    ][:5] or [
        "Incomplete site surveys may change access density and topology.",
        "Identity integration details may alter security control placement.",
    ]

    return {
        "summary": (
            f"Vendor-neutral architecture recommendation for {', '.join(domains)} "
            "derived from the Published Requirement Knowledge Model."
        ),
        "high_level_architecture": high_level,
        "logical_architecture": logical,
        "physical_architecture": physical,
        "technology_stack": stack,
        "solution_components": components,
        "design_assumptions": assumptions,
        "technical_risks": risks,
        "architecture_decisions": [
            {
                "decision": "Use layered campus architecture with separated management plane",
                "rationale": "Improves operability and limits blast radius of access changes.",
                "impact": "Guides switching, WLAN, and ops tool placement.",
            },
            {
                "decision": "Remain vendor-neutral in Phase 3 MVP",
                "rationale": "ATLAS phase separation defers product SKUs to BOM/vendor stages.",
                "impact": "Technology categories only; no OEM lock-in yet.",
            },
        ],
        "alternatives": [
            {
                "name": "Controller-light / distributed edge",
                "summary": "Push more policy to the access edge",
                "tradeoffs": "Simpler core, more complex edge operations.",
            },
            {
                "name": "Centralized services hub",
                "summary": "Concentrate identity and management centrally",
                "tradeoffs": "Stronger consistency; higher WAN/dependency risk for remote sites.",
            },
        ],
        "reasoning_summary": (
            "Generated with local architecture heuristics from Published RKM"
            + (" and knowledge pack stubs." if knowledge_pack_context.strip() else ".")
        ),
        "provider": "local",
        "model": "local-architecture-heuristics",
    }


def _local_architecture_candidates(
    published_rkm: dict[str, Any],
    *,
    domain_context: str = "",
    pattern_context: str = "",
) -> dict[str, Any]:
    """Multi-candidate architecture heuristic (Sprint 3.2 Task 5)."""
    from app.schemas.architecture_option import DEFAULT_SCORE_WEIGHTS
    from app.services.phase3_knowledge_packs import detect_phase3_domains
    from app.services.phase3_pattern_catalog import patterns_for_domains

    requirements = _rkm_requirement_refs(published_rkm)
    req_ids = [req["id"] for req in requirements[:6]]
    blob = " ".join(
        part
        for req in requirements
        for part in (req["id"], req["title"], req["description"])
    )
    blob = f"{blob} {domain_context} {pattern_context}".strip()
    haystack = blob.lower()

    domain_codes = detect_phase3_domains(blob)
    pattern_entries = patterns_for_domains(domain_codes) if domain_codes else []
    pattern_codes = [item.code for item in pattern_entries[:4]]

    wants_wifi = any(
        token in haystack for token in ("wifi", "wi-fi", "wlan", "wireless", "access point")
    ) or "wifi" in domain_codes
    wants_campus = any(
        token in haystack for token in ("campus", "switching", "lan", "idf")
    ) or "campus_lan" in domain_codes
    wants_security = any(
        token in haystack for token in ("802.1x", "nac", "firewall", "zero trust", "security")
    ) or bool({"identity", "cybersecurity", "security_edge"} & set(domain_codes))
    wants_ha = any(
        token in haystack for token in ("high availability", "ha ", "redundant", "resilien")
    )

    if wants_wifi and "wireless_enterprise" not in pattern_codes:
        pattern_codes.insert(0, "wireless_enterprise")
    if wants_campus and "two_tier_campus" not in pattern_codes:
        pattern_codes.append("two_tier_campus")
    if wants_security and "zero_trust" not in pattern_codes and "secure_internet_edge" not in pattern_codes:
        pattern_codes.append("zero_trust")
    if not pattern_codes:
        pattern_codes = ["two_tier_campus"]

    # Deduplicate while preserving order.
    seen_patterns: set[str] = set()
    ordered_patterns: list[str] = []
    for code in pattern_codes:
        if code not in seen_patterns:
            seen_patterns.add(code)
            ordered_patterns.append(code)
    pattern_codes = ordered_patterns[:4]

    maps = req_ids or ["published-rkm"]

    def _component(
        name: str,
        purpose: str,
        temp_id: str,
        *,
        kind: str = "logical",
    ) -> dict[str, Any]:
        return {
            "name": name,
            "purpose": purpose,
            "component_kind": kind,
            "maps_to_requirements": maps[:3],
            "temp_id": temp_id,
        }

    standard_components = [
        _component(
            "Access underlay",
            "Wired access for endpoints and wireless APs",
            "c_access",
            kind="physical",
        ),
        _component(
            "Aggregation / services",
            "Campus aggregation and shared services attachment",
            "c_agg",
        ),
        _component(
            "Identity & policy",
            "Authentication and access policy enforcement",
            "c_id",
            kind="technology",
        ),
    ]
    if wants_wifi:
        standard_components.insert(
            1,
            _component(
                "Enterprise WLAN",
                "Vendor-neutral Wi-Fi 6/6E coverage and RF management",
                "c_wlan",
                kind="technology",
            ),
        )

    relationships = [
        {
            "from_component": "c_access",
            "to_component": "c_agg",
            "relationship_kind": "connects_to",
            "description": "Access uplinks to aggregation",
        },
        {
            "from_component": "c_id",
            "to_component": "c_access",
            "relationship_kind": "depends_on",
            "description": "Policy applies at access edge",
        },
    ]
    if wants_wifi:
        relationships.append(
            {
                "from_component": "c_wlan",
                "to_component": "c_access",
                "relationship_kind": "depends_on",
                "description": "APs require wired underlay",
            },
        )

    score_dims = [
        ("requirement_coverage", 4.0, "Aligned to published functional outcomes"),
        ("technical_fit", 3.5, "Uses catalog patterns matching detected domains"),
        ("security", 3.0 if wants_security else 2.5, "Identity/policy plane included"),
        (
            "availability_resilience",
            2.5,
            "Standard candidate; HA deferred to alternate option",
        ),
    ]
    scores = [
        {
            "dimension": dim,
            "weight": DEFAULT_SCORE_WEIGHTS[dim],
            "score": score,
            "explanation": explanation,
        }
        for dim, score, explanation in score_dims
    ]

    capacity_notes: list[dict[str, Any]] = []
    if wants_wifi:
        capacity_notes.append(
            {
                "label": "AP count",
                "confidence": 0.2,
                "related_requirement_ids": maps[:2],
                "open_question": (
                    "What floor plans, wall materials, and concurrent client density "
                    "should drive AP count?"
                ),
            },
        )
    else:
        capacity_notes.append(
            {
                "label": "Access port density",
                "confidence": 0.2,
                "related_requirement_ids": maps[:2],
                "open_question": (
                    "How many wired ports / IDFs and what uplink capacity are required?"
                ),
            },
        )

    domain_label = ", ".join(domain_codes) if domain_codes else "enterprise infrastructure"
    standard = {
        "candidate_key": "standard",
        "title": f"Standard {domain_label} architecture",
        "summary": (
            "Vendor-neutral layered architecture derived from the Published RKM "
            "and latest domain signals."
        ),
        "reasoning_summary": (
            "Local heuristics selected catalog patterns from RKM + domain/pattern context."
        ),
        "pattern_codes": pattern_codes,
        "confidence": 0.72 if domain_codes else 0.45,
        "high_level_architecture": [
            f"Deliver layered design for {domain_label}.",
            "Keep product selection out of scope (ATLAS-035).",
        ],
        "logical_architecture": [
            "Access, aggregation/services, and identity/policy planes",
            "Centralized management/observability attachment point",
        ],
        "physical_architecture": [
            "Per-floor or per-IDF access as site scope requires",
            "Uplinks sized after capacity inputs are confirmed",
        ],
        "technology_stack": [
            {
                "layer": "Access",
                "category": (
                    "Enterprise Wi-Fi 6/6E WLAN" if wants_wifi else "Multi-gig access switching"
                ),
                "rationale": "Matches published access requirements without OEM lock-in.",
            },
            {
                "layer": "Security",
                "category": "802.1X / NAC with directory integration",
                "rationale": "Supports authenticated access and segmentation.",
            },
        ],
        "components": standard_components,
        "relationships": relationships,
        "decisions": [
            {
                "decision": "Remain vendor-neutral for candidate architectures",
                "rationale": "ATLAS-035 defers SKUs to later vendor/BOM work",
                "impact": "Technology categories and patterns only",
            },
            {
                "decision": f"Anchor design on patterns: {', '.join(pattern_codes)}",
                "rationale": "Pattern catalog intersected with domain signals",
                "impact": "Guides component placement and scoring",
            },
        ],
        "assumptions": [
            {
                "statement": "Published RKM plus domain context is sufficient for high-level candidates",
                "reason": "Architecture generate consumes Published RKM only",
                "affected_components": ["c_access", "c_agg"],
                "validation_required": True,
                "status": "unvalidated",
            },
        ],
        "risks": [
            {
                "description": (
                    str(
                        next(
                            (
                                item.get("title") or item.get("description")
                                for item in (published_rkm.get("risks") or [])
                                if isinstance(item, dict)
                                and (item.get("title") or item.get("description"))
                            ),
                            "Incomplete site inputs may change access density and topology",
                        ),
                    )
                ),
                "category": "capacity",
                "probability": "medium",
                "severity": "medium",
                "mitigation": "Capture survey / floor-plan inputs before BOM",
                "related_requirement_ids": maps[:2],
            },
        ],
        "scores": scores,
        "capacity_notes": capacity_notes,
        "advantages": [
            "Simple to review against Published RKM",
            "Uses frozen Phase 3 pattern codes",
        ],
        "disadvantages": [
            "Limited HA / redundancy compared with alternate candidate",
        ],
    }

    architectures = [standard]
    if wants_ha or wants_wifi or wants_campus:
        ha_components = [
            *standard_components,
            _component(
                "Redundant control / services path",
                "Secondary path for controller/services and critical uplinks",
                "c_ha",
                kind="physical",
            ),
        ]
        ha_scores = [
            {
                "dimension": dim,
                "weight": DEFAULT_SCORE_WEIGHTS[dim],
                "score": (
                    4.0
                    if dim == "availability_resilience"
                    else 3.5
                    if dim == "requirement_coverage"
                    else 3.0
                ),
                "explanation": (
                    "Adds redundancy for critical control/services"
                    if dim == "availability_resilience"
                    else "Same functional coverage with higher resilience cost"
                ),
            }
            for dim, _, _ in score_dims
        ]
        architectures.append(
            {
                "candidate_key": "high_availability",
                "title": f"HA {domain_label} architecture",
                "summary": (
                    "Same pattern base as standard with redundant control/services "
                    "and dual uplinks where HA is indicated."
                ),
                "reasoning_summary": (
                    "Local heuristics added an HA variant when resilience signals "
                    "or campus/wireless scope suggest review of redundancy."
                ),
                "pattern_codes": pattern_codes,
                "confidence": 0.68 if domain_codes else 0.4,
                "high_level_architecture": [
                    "Retain layered design with redundant critical paths.",
                    "Prefer dual uplinks and resilient identity/policy attachment.",
                ],
                "logical_architecture": standard["logical_architecture"],
                "physical_architecture": [
                    "Dual uplinks from access to aggregation where HA is required",
                    "Redundant controller/services placement pending site topology",
                ],
                "technology_stack": standard["technology_stack"],
                "components": ha_components,
                "relationships": [
                    *relationships,
                    {
                        "from_component": "c_ha",
                        "to_component": "c_agg",
                        "relationship_kind": "connects_to",
                        "description": "Secondary services path",
                    },
                ],
                "decisions": [
                    {
                        "decision": "Offer HA candidate separately from standard",
                        "rationale": "Lets reviewers compare resilience vs complexity",
                        "impact": "Scoring favors availability_resilience",
                    },
                    {
                        "decision": "Remain vendor-neutral",
                        "rationale": "ATLAS-035",
                        "impact": "No OEM SKUs",
                    },
                ],
                "assumptions": [
                    {
                        "statement": "Customer will accept higher complexity for HA",
                        "reason": "Resilience language present or campus wireless scope",
                        "affected_components": ["c_ha", "c_agg"],
                        "validation_required": True,
                        "status": "unvalidated",
                    },
                ],
                "risks": [
                    {
                        "description": "HA design may over-build if resilience targets are soft",
                        "category": "commercial",
                        "probability": "medium",
                        "severity": "low",
                        "mitigation": "Confirm RTO/RPO and dual-path requirements",
                        "related_requirement_ids": maps[:2],
                    },
                ],
                "scores": ha_scores,
                "capacity_notes": capacity_notes,
                "advantages": ["Better resilience for critical access services"],
                "disadvantages": ["Higher complexity and operational cost"],
            },
        )

    return {
        "summary": (
            f"Local architecture candidates for {domain_label} "
            f"using patterns {', '.join(pattern_codes)}."
        ),
        "reasoning_summary": (
            "Generated with local multi-candidate heuristics from Published RKM, "
            "domain context, and Phase 3 pattern catalog."
            + (" Domain context supplied." if domain_context.strip() else "")
            + (" Pattern context supplied." if pattern_context.strip() else "")
        ),
        "architectures": architectures,
        "provider": "local",
        "model": "local-architecture-candidates",
    }


def _local_domain_identification(
    published_rkm: dict[str, Any],
    *,
    knowledge_pack_context: str = "",
) -> dict[str, Any]:
    """Catalog-bound domain identification heuristic from Published RKM fields."""
    from app.services.phase3_domain_catalog import load_domain_catalog
    from app.services.phase3_knowledge_packs import detect_phase3_domains

    requirements = _rkm_requirement_refs(published_rkm)
    blob = " ".join(
        part
        for req in requirements
        for part in (req["id"], req["title"], req["description"])
    )
    blob = f"{blob} {knowledge_pack_context}".strip()
    detected = detect_phase3_domains(blob)
    catalog = load_domain_catalog()

    # Always consider typical deps of detected domains as dependency candidates.
    codes: list[str] = []
    seen: set[str] = set()
    for code in detected:
        if code not in seen:
            seen.add(code)
            codes.append(code)
        entry = catalog.get(code)
        if entry is None:
            continue
        for dep in entry.typical_dependencies:
            if dep not in seen:
                seen.add(dep)
                codes.append(dep)

    if not codes:
        # Fail soft with an open question rather than inventing domains.
        return {
            "summary": "No solution domains could be identified from the Published RKM.",
            "domains": [],
            "open_questions": [
                {
                    "question": (
                        "Which solution domains are in scope "
                        "(for example Wi-Fi, Campus LAN, Identity, Cybersecurity)?"
                    ),
                    "affects_selection": True,
                    "related_requirement_ids": [req["id"] for req in requirements[:5]],
                },
            ],
            "reasoning_summary": (
                "Local domain heuristics found no catalog domain signals in the Published RKM."
            ),
            "provider": "local",
            "model": "local-domain-heuristics",
        }

    domains_out: list[dict[str, Any]] = []
    open_questions: list[dict[str, Any]] = []
    for code in codes:
        entry = catalog.get(code)
        if entry is None:
            continue
        supporting = _matching_requirements(requirements, entry)
        is_primary = code in detected
        if is_primary and supporting:
            selection_source = "requirement"
            confidence = min(0.9, 0.55 + 0.05 * len(supporting))
        elif is_primary:
            selection_source = "requirement"
            # Use first requirement ids as weak evidence when keyword hit is global.
            supporting = [req["id"] for req in requirements[:3]]
            confidence = 0.45 if supporting else 0.35
            if not supporting:
                # Cannot emit requirement source without IDs — treat as dependency note.
                selection_source = "dependency"
                confidence = 0.4
        else:
            selection_source = "dependency"
            confidence = 0.5

        dependencies = [
            {
                "depends_on_domain_code": dep,
                "dependency_kind": "recommended",
                "reason": f"Typical dependency of {entry.name}",
            }
            for dep in entry.typical_dependencies
            if dep in seen
        ]

        reason = (
            f"Published RKM indicates {entry.name} scope."
            if is_primary
            else f"{entry.name} is a documented design dependency of identified domains."
        )
        if selection_source == "requirement" and not supporting:
            continue
        if selection_source == "dependency" and not dependencies and not reason:
            continue

        domain_questions: list[dict[str, Any]] = []
        if code == "wifi" and not any("survey" in req["description"].lower() for req in requirements):
            domain_questions.append(
                {
                    "question": "Is a predictive wireless survey / heatmap required before design?",
                    "affects_selection": True,
                    "related_requirement_ids": supporting[:3],
                },
            )
        if code in {"identity", "ztna_vpn"} and not any(
            token in blob.lower() for token in ("mfa", "multi-factor", "802.1x")
        ):
            domain_questions.append(
                {
                    "question": "Is MFA / 802.1X mandatory for the identified access domains?",
                    "affects_selection": True,
                    "related_requirement_ids": supporting[:3],
                },
            )

        domains_out.append(
            {
                "domain_code": code,
                "name": entry.name,
                "reason": reason,
                "supporting_requirements": supporting,
                "confidence": confidence,
                "mandatory_or_optional": "mandatory" if is_primary else "optional",
                "selection_source": selection_source,
                "dependencies": dependencies,
                "open_questions": domain_questions,
            },
        )
        open_questions.extend(
            {**question, "domain_code": code} for question in domain_questions
        )

    names = [str(item.get("name") or item.get("domain_code")) for item in domains_out]
    return {
        "summary": (
            "Solution domains identified from the Published RKM: " + ", ".join(names)
            if names
            else "No solution domains identified."
        ),
        "domains": domains_out,
        "open_questions": open_questions,
        "reasoning_summary": (
            "Generated with local domain heuristics from Published RKM"
            + (" and Phase 3 knowledge pack context." if knowledge_pack_context.strip() else ".")
        ),
        "provider": "local",
        "model": "local-domain-heuristics",
    }


def _rkm_requirement_refs(published_rkm: dict[str, Any]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    seen: set[str] = set()
    for section in (
        "business_objectives",
        "functional_requirements",
        "non_functional_requirements",
        "constraints",
        "dependencies",
        "risks",
        "assumptions",
    ):
        for index, item in enumerate(published_rkm.get(section) or []):
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            description = str(item.get("description") or "").strip()
            req_id = str(
                item.get("id") or item.get("requirement_id") or "",
            ).strip()
            if not req_id:
                req_id = f"{section}:{index + 1}" if not title else title[:80]
            if req_id in seen:
                continue
            seen.add(req_id)
            refs.append(
                {
                    "id": req_id,
                    "title": title,
                    "description": description,
                },
            )
    return refs


def _matching_requirements(
    requirements: list[dict[str, str]],
    entry: Any,
) -> list[str]:
    needles = {
        entry.code.replace("_", " "),
        entry.code,
        entry.name.lower(),
        *[alias.lower() for alias in entry.aliases],
    }
    matched: list[str] = []
    for req in requirements:
        hay = f"{req['title']} {req['description']}".lower()
        if any(needle and needle in hay for needle in needles):
            matched.append(req["id"])
    return matched


def _local_proposal_content(
    snapshot: dict[str, Any],
    content_plan: dict[str, Any],
    *,
    prompt_version: str = "proposal_v1",
) -> dict[str, Any]:
    """Deterministic proposal draft from snapshot — never invents prices/dates."""
    rkm = snapshot.get("rkm") or {}
    arch = snapshot.get("architecture") or {}
    bom = snapshot.get("bom") or {}
    bom_validated = bool(bom.get("validated") or content_plan.get("bom_validated"))
    customer = rkm.get("customer_name") or rkm.get("project_name") or "the customer"
    title = f"Proposal — {arch.get('title') or 'Solution Architecture'}"
    requirements = rkm.get("requirements") or []
    components = arch.get("components") or []
    risks = arch.get("risks") or []
    assumptions = arch.get("assumptions") or []
    decisions = arch.get("decisions") or []

    def _item(
        text: str,
        *,
        refs: list[dict[str, Any]] | None = None,
        review_required: bool = False,
        content_type: str = "paragraph",
        confidence: float = 0.75,
    ) -> dict[str, Any]:
        return {
            "content_type": content_type,
            "text": text,
            "structured_data": {},
            "confidence": confidence,
            "review_required": review_required,
            "source_refs": refs or [],
        }

    sections_out: list[dict[str, Any]] = []
    for planned in content_plan.get("sections") or []:
        section_type = str(planned.get("section_type") or "")
        section_title = str(planned.get("title") or section_type)
        sequence = int(planned.get("sequence") or 0)
        items: list[dict[str, Any]] = []
        section_assumptions: list[str] = []

        if section_type == "cover":
            items.append(_item(f"{title}\nPrepared for {customer}"))
        elif section_type == "executive_summary":
            items.append(
                _item(
                    (arch.get("summary") or f"This proposal outlines a solution for {customer} "
                     f"based on the approved architecture '{arch.get('title') or arch.get('candidate_key')}'.")
                )
            )
        elif section_type == "customer_understanding":
            items.append(
                _item(
                    str(rkm.get("summary") or f"Engagement for {customer} based on the Published RKM.")
                )
            )
        elif section_type == "challenges":
            if risks:
                for risk in risks[:8]:
                    items.append(
                        _item(
                            str(risk.get("title") or risk.get("description") or "Risk"),
                            refs=[{"ref_kind": "risk", "ref_id": str(risk.get("id") or ""), "label": "risk"}],
                            content_type="bullet_list",
                        )
                    )
            else:
                items.append(
                    _item(
                        "Challenges are inferred only from approved architecture risks; none recorded.",
                        review_required=True,
                        confidence=0.4,
                    )
                )
                section_assumptions.append("No explicit challenges recorded in source snapshot")
        elif section_type == "requirements":
            for req in requirements[:40]:
                req_id = str(req.get("id") or "")
                items.append(
                    _item(
                        str(req.get("statement") or ""),
                        refs=[{"ref_kind": "requirement", "ref_id": req_id, "label": req_id}],
                        content_type="bullet_list",
                    )
                )
            if not requirements:
                items.append(_item("No requirements present in snapshot.", review_required=True))
        elif section_type in {"proposed_solution", "architecture"}:
            items.append(
                _item(
                    arch.get("summary") or arch.get("title") or "Approved architecture",
                    refs=[{"ref_kind": "architecture", "ref_id": str(arch.get("id") or ""), "label": "architecture"}],
                )
            )
            for decision in decisions[:10]:
                items.append(
                    _item(
                        str(decision.get("decision") or ""),
                        refs=[{"ref_kind": "decision", "ref_id": str(decision.get("id") or ""), "label": "decision"}],
                        content_type="bullet_list",
                    )
                )
        elif section_type == "solution_components":
            for component in components:
                items.append(
                    _item(
                        f"{component.get('name')}: {component.get('purpose') or ''}".strip(": "),
                        refs=[
                            {
                                "ref_kind": "component",
                                "ref_id": str(component.get("id") or ""),
                                "label": str(component.get("name") or "component"),
                            }
                        ],
                        content_type="bullet_list",
                    )
                )
            if not components:
                items.append(_item("No components in approved architecture.", review_required=True))
        elif section_type == "benefits":
            items.append(
                _item(
                    "Benefits should be confirmed with stakeholders; derived only from approved scope.",
                    review_required=True,
                    confidence=0.45,
                )
            )
            section_assumptions.append("Benefits not explicitly present in snapshot")
        elif section_type == "implementation_approach":
            items.append(
                _item(
                    "Implementation approach will follow the approved architecture components and design decisions.",
                    refs=[{"ref_kind": "architecture", "ref_id": str(arch.get("id") or ""), "label": "architecture"}],
                )
            )
        elif section_type == "timeline":
            items.append(
                _item(
                    "No authoritative schedule is present in the source snapshot. Timeline requires customer confirmation.",
                    review_required=True,
                    confidence=0.3,
                )
            )
            section_assumptions.append("Schedule not authorized in snapshot")
        elif section_type == "assumptions":
            for assumption in assumptions:
                items.append(
                    _item(
                        str(assumption.get("statement") or ""),
                        refs=[{"ref_kind": "assumption", "ref_id": str(assumption.get("id") or ""), "label": "assumption"}],
                        content_type="bullet_list",
                    )
                )
            if not bom_validated:
                items.append(
                    _item(
                        "Validated BOM / approved pricing data is not available; commercial figures are excluded.",
                        review_required=True,
                        content_type="assumption",
                    )
                )
            if not assumptions:
                items.append(_item("No architecture assumptions recorded.", review_required=True))
        elif section_type == "risks":
            for risk in risks:
                items.append(
                    _item(
                        f"{risk.get('title') or risk.get('description')} "
                        f"(severity={risk.get('severity')})",
                        refs=[{"ref_kind": "risk", "ref_id": str(risk.get("id") or ""), "label": "risk"}],
                        content_type="bullet_list",
                    )
                )
            if not risks:
                items.append(_item("No risks recorded on the approved architecture.", review_required=True))
        elif section_type == "exclusions":
            items.append(
                _item(
                    "Items not covered by the Published RKM or approved architecture are excluded unless added via change control.",
                    review_required=True,
                )
            )
        elif section_type == "support_warranty":
            items.append(
                _item(
                    "Support and warranty terms are not present as authoritative approved data in the snapshot.",
                    review_required=True,
                    confidence=0.2,
                )
            )
            section_assumptions.append("Warranty/support require commercial approval")
        elif section_type == "next_steps":
            items.append(
                _item(
                    "1. Review this draft proposal\n2. Confirm open REVIEW REQUIRED items\n3. Approve for customer release"
                )
            )
        else:
            items.append(_item(f"Content for {section_title}", review_required=True, confidence=0.4))

        sections_out.append(
            {
                "section_type": section_type,
                "title": section_title,
                "sequence": sequence,
                "confidence": min((i.get("confidence") or 0.5) for i in items) if items else 0.5,
                "assumptions": section_assumptions,
                "content_items": items,
            }
        )

    return {
        "title": title,
        "sections": sections_out,
        "provider": "local",
        "model": "local-proposal",
        "prompt_version": prompt_version,
    }
