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
            "business_objectives": _as_bullets(objectives),
            "functional_requirements": _as_bullets(functional),
            "non_functional_requirements": _as_bullets(non_functional),
            "assumptions": _as_bullets(assumptions),
            "risks": _as_bullets(risks),
            "provider": "local",
        }

    async def generate_clarifications(self, analysis: dict[str, Any]) -> list[str]:
        objectives = str(analysis.get("business_objectives") or "")
        functional = str(analysis.get("functional_requirements") or "")
        nfr = str(analysis.get("non_functional_requirements") or "")
        risks = str(analysis.get("risks") or "")

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

        # Stable, de-duplicated, 5–10 questions.
        deduped: list[str] = []
        for question in questions:
            if question not in deduped:
                deduped.append(question)
        return deduped[:10]


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
