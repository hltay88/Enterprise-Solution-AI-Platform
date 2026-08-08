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
