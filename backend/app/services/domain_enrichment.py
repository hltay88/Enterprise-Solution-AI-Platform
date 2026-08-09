"""Sprint 3.1 Task 9 — domain dependency validation and open-question enrichment.

Pure helpers (no DB/AI). Ensures dependency codes stay inside the Phase 3
catalog, surfaces missing selection inputs, and never fabricates capacity facts.
"""

from __future__ import annotations

from typing import Any

from app.schemas.domain import (
    DomainAIExtraction,
    DomainDependencyAI,
    DomainOpenQuestionAI,
    SolutionDomainAI,
)
from app.services.phase3_domain_catalog import resolve_domain_code

# Lightweight signals that affect domain selection / sizing (doc 06 style).
# Absence → open question; values are never invented.
_DOMAIN_SELECTION_SIGNALS: dict[str, tuple[str, ...]] = {
    "wifi": ("survey", "heatmap", "density", "concurrent", "ssid", "floor"),
    "campus_lan": ("port", "uplink", "idf", "building", "vlan"),
    "wan_sdwan": ("site", "branch", "bandwidth", "circuit"),
    "storage": ("capacity", "tb", "iops", "retention"),
    "backup_dr": ("rpo", "rto", "backup window", "retention"),
    "cctv": ("camera", "retention", "fps"),
    "led_video_wall": ("pixel", "pitch", "viewing distance", "dimension"),
    "digital_signage": ("screen", "display count", "cms"),
    "ztna_vpn": ("mfa", "remote user", "concurrent"),
    "identity": ("mfa", "directory", "sso", "802.1x"),
}


def preprocess_domain_extraction(payload: dict[str, Any]) -> dict[str, Any]:
    """Drop non-catalog dependency codes before schema validation; add questions."""
    if not isinstance(payload, dict):
        return payload
    domains_raw = payload.get("domains") or []
    if not isinstance(domains_raw, list):
        return payload

    domains_out: list[dict[str, Any]] = []
    for item in domains_raw:
        if not isinstance(item, dict):
            continue
        row = dict(item)
        code = str(row.get("domain_code") or row.get("domain_id") or row.get("code") or "")
        deps_in = row.get("dependencies") or []
        clean_deps: list[dict[str, Any]] = []
        questions = list(row.get("open_questions") or [])
        supporting = row.get("supporting_requirements") or []
        if not isinstance(deps_in, list):
            deps_in = []
        if not isinstance(questions, list):
            questions = []
        for dep in deps_in:
            if not isinstance(dep, dict):
                continue
            raw_code = str(dep.get("depends_on_domain_code") or "").strip()
            resolved = resolve_domain_code(raw_code)
            if resolved is None:
                questions.append(
                    {
                        "question": (
                            f"Dependency '{raw_code}' for domain {code or '(unknown)'} "
                            "is not a catalog code. Should it be remapped or removed?"
                        ),
                        "affects_selection": True,
                        "related_requirement_ids": [
                            str(item).strip()
                            for item in supporting[:5]
                            if str(item).strip()
                        ],
                        "domain_code": code or None,
                    },
                )
                continue
            clean_deps.append(
                {
                    "depends_on_domain_code": resolved,
                    "dependency_kind": dep.get("dependency_kind") or "required",
                    "reason": str(dep.get("reason") or "").strip()
                    or f"Declared dependency of {code or resolved}",
                },
            )
        row["dependencies"] = clean_deps
        row["open_questions"] = questions
        domains_out.append(row)

    out = dict(payload)
    out["domains"] = domains_out
    return out


def enrich_domains_and_questions(
    extraction: DomainAIExtraction,
    *,
    requirements: list[dict[str, Any]],
    traceability: list[dict[str, Any]],
    rkm_text: str = "",
) -> DomainAIExtraction:
    """Return a refined extraction with validated deps + selection open questions."""
    identified = {domain.domain_code for domain in extraction.domains}
    blob = (rkm_text or "").lower()
    req_blob = " ".join(
        f"{req.get('title', '')} {req.get('description', '')}" for req in requirements
    ).lower()
    haystack = f"{blob} {req_blob}"

    refined_domains: list[SolutionDomainAI] = []
    extra_questions: list[DomainOpenQuestionAI] = []

    for domain in extraction.domains:
        clean_deps: list[DomainDependencyAI] = []
        domain_questions = list(domain.open_questions)

        for dep in domain.dependencies:
            resolved = dep.depends_on_domain_code
            reason = (dep.reason or "").strip() or (
                f"Declared dependency of {domain.domain_code}"
            )
            clean_deps.append(
                DomainDependencyAI(
                    depends_on_domain_code=resolved,
                    dependency_kind=dep.dependency_kind,
                    reason=reason,
                ),
            )
            if resolved not in identified:
                domain_questions.append(
                    DomainOpenQuestionAI(
                        question=(
                            f"Domain {domain.domain_code} depends on {resolved}, "
                            f"which was not selected. Should {resolved} be included "
                            "in the Solution Domain Model?"
                        ),
                        affects_selection=True,
                        related_requirement_ids=list(domain.supporting_requirements[:5]),
                        domain_code=domain.domain_code,
                    ),
                )

        for signal_question in _missing_signal_questions(domain, haystack):
            domain_questions.append(signal_question)

        refined_domains.append(
            domain.model_copy(
                update={
                    "dependencies": clean_deps,
                    "open_questions": _dedupe_questions(domain_questions),
                },
            ),
        )

    for cycle in _find_dependency_cycles(refined_domains):
        extra_questions.append(
            DomainOpenQuestionAI(
                question=(
                    "Circular domain dependency detected: "
                    + " → ".join(cycle)
                    + ". Confirm the intended dependency direction."
                ),
                affects_selection=True,
                related_requirement_ids=[],
                domain_code=cycle[0] if cycle else None,
            ),
        )

    for row in traceability:
        if row.get("status") != "not_covered":
            continue
        req_id = str(row.get("requirement_id") or "")
        req = next((item for item in requirements if item.get("id") == req_id), None)
        priority = str((req or {}).get("priority") or "medium").lower()
        if priority not in {"critical", "high"}:
            continue
        title = str((req or {}).get("title") or req_id)
        extra_questions.append(
            DomainOpenQuestionAI(
                question=(
                    f"Which solution domain should cover {priority} requirement "
                    f"{title!r} ({req_id})?"
                ),
                affects_selection=True,
                related_requirement_ids=[req_id] if req_id else [],
                domain_code=None,
            ),
        )

    analysis_questions = _dedupe_questions(
        list(extraction.open_questions) + extra_questions,
    )

    return extraction.model_copy(
        update={
            "domains": refined_domains,
            "open_questions": analysis_questions,
        },
    )


def _missing_signal_questions(
    domain: SolutionDomainAI,
    haystack: str,
) -> list[DomainOpenQuestionAI]:
    signals = _DOMAIN_SELECTION_SIGNALS.get(domain.domain_code)
    if not signals:
        return []
    if any(token in haystack for token in signals):
        return []
    label = ", ".join(signals[:3])
    return [
        DomainOpenQuestionAI(
            question=(
                f"For domain {domain.domain_code}, key selection inputs "
                f"({label}) are not evident in the Published RKM. "
                "Provide the missing inputs rather than assuming values."
            ),
            affects_selection=True,
            related_requirement_ids=list(domain.supporting_requirements[:5]),
            domain_code=domain.domain_code,
        ),
    ]


def _find_dependency_cycles(domains: list[SolutionDomainAI]) -> list[list[str]]:
    graph: dict[str, list[str]] = {
        domain.domain_code: [dep.depends_on_domain_code for dep in domain.dependencies]
        for domain in domains
    }
    cycles: list[list[str]] = []
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def dfs(node: str) -> None:
        if node in visited:
            return
        if node in visiting:
            if node in stack:
                idx = stack.index(node)
                cycles.append([*stack[idx:], node])
            return
        visiting.add(node)
        stack.append(node)
        for nxt in graph.get(node, []):
            if nxt in graph:
                dfs(nxt)
        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for code in graph:
        dfs(code)
    # Deduplicate cycles by frozenset of nodes (ignore rotation)
    unique: list[list[str]] = []
    seen: set[frozenset[str]] = set()
    for cycle in cycles:
        key = frozenset(cycle)
        if key in seen:
            continue
        seen.add(key)
        unique.append(cycle)
    return unique


def _dedupe_questions(questions: list[DomainOpenQuestionAI]) -> list[DomainOpenQuestionAI]:
    out: list[DomainOpenQuestionAI] = []
    seen: set[str] = set()
    for question in questions:
        key = question.question.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(question)
    return out
