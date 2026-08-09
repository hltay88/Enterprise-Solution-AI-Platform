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
