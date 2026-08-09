"""Sprint 3.1 Task 8 — requirement → domain traceability builder.

Pure helpers (no DB/AI). Builds the domain-stage coverage matrix from a
Published RKM payload and validated domain identification results.
"""

from __future__ import annotations

from typing import Any

from app.schemas.domain import SolutionDomainAI

RKM_REQUIREMENT_SECTIONS = (
    "business_objectives",
    "functional_requirements",
    "non_functional_requirements",
    "constraints",
    "dependencies",
    "risks",
    "assumptions",
)


def extract_rkm_requirements(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten Published RKM sections into requirement refs for traceability."""
    refs: list[dict[str, Any]] = []
    seen: set[str] = set()
    for section in RKM_REQUIREMENT_SECTIONS:
        for index, item in enumerate(payload.get(section) or []):
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            description = str(item.get("description") or "").strip()
            req_id = str(item.get("id") or item.get("requirement_id") or "").strip()
            if not req_id:
                req_id = f"{section}:{index + 1}" if not title else title[:80]
            if req_id in seen:
                continue
            seen.add(req_id)
            priority = str(item.get("priority") or "medium").strip().lower() or "medium"
            refs.append(
                {
                    "id": req_id,
                    "title": title,
                    "description": description,
                    "priority": priority,
                    "section": section,
                },
            )
    return refs


def build_requirement_domain_traceability(
    requirements: list[dict[str, Any]],
    domains: list[SolutionDomainAI] | list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build requirement→domain traceability rows for persistence.

    Status rules (domain stage):
    - linked + mandatory domain + requirement source → covered
    - linked + optional / optional_alternative → optional
    - linked + dependency source → partially_covered
    - RKM requirement with no domain link → not_covered
    """
    domain_models = [_as_domain(item) for item in domains]

    # requirement_id → list of (domain_code, status, evidence)
    linked: dict[str, list[tuple[str, str, str]]] = {}
    for domain in domain_models:
        status = _status_for_domain_link(domain)
        for req_id in domain.supporting_requirements:
            rid = str(req_id or "").strip()
            if not rid:
                continue
            evidence = (
                f"Mapped via domain {domain.domain_code} "
                f"({domain.selection_source}, {domain.mandatory_or_optional})"
            )
            linked.setdefault(rid, []).append((domain.domain_code, status, evidence))

    rows: list[dict[str, Any]] = []
    covered_ids: set[str] = set()

    for req_id, mappings in linked.items():
        covered_ids.add(req_id)
        # Dedupe by domain_code; keep strongest status if duplicates.
        by_code: dict[str, tuple[str, str]] = {}
        for domain_code, status, evidence in mappings:
            prior = by_code.get(domain_code)
            if prior is None or _status_rank(status) > _status_rank(prior[0]):
                by_code[domain_code] = (status, evidence)
        for domain_code, (status, evidence) in sorted(by_code.items()):
            rows.append(
                {
                    "requirement_id": req_id,
                    "domain_code": domain_code,
                    "status": status,
                    "evidence": evidence,
                },
            )

    for req in requirements:
        req_id = str(req.get("id") or "").strip()
        if not req_id or req_id in covered_ids:
            continue
        priority = str(req.get("priority") or "medium").strip().lower()
        title = str(req.get("title") or req_id).strip()
        critical_note = "critical/high " if priority in {"critical", "high"} else ""
        rows.append(
            {
                "requirement_id": req_id,
                "domain_code": None,
                "status": "not_covered",
                "evidence": (
                    f"No solution domain mapped for {critical_note}requirement "
                    f"{title!r} ({priority})"
                ).strip(),
            },
        )

    rows.sort(key=lambda row: (row["requirement_id"], row.get("domain_code") or ""))
    return rows


def count_uncovered_critical(traceability: list[dict[str, Any]], requirements: list[dict[str, Any]]) -> int:
    """Count critical/high requirements that remain not_covered."""
    priority_by_id = {
        str(req.get("id") or ""): str(req.get("priority") or "medium").lower()
        for req in requirements
    }
    count = 0
    for row in traceability:
        if row.get("status") != "not_covered":
            continue
        priority = priority_by_id.get(str(row.get("requirement_id") or ""), "medium")
        if priority in {"critical", "high"}:
            count += 1
    return count


def _as_domain(item: SolutionDomainAI | dict[str, Any]) -> SolutionDomainAI:
    if isinstance(item, SolutionDomainAI):
        return item
    return SolutionDomainAI.model_validate(item)


def _status_for_domain_link(domain: SolutionDomainAI) -> str:
    if (
        domain.mandatory_or_optional == "optional"
        or domain.selection_source == "optional_alternative"
    ):
        return "optional"
    if domain.selection_source == "dependency":
        return "partially_covered"
    return "covered"


def _status_rank(status: str) -> int:
    order = {
        "not_covered": 0,
        "conflict": 1,
        "optional": 2,
        "partially_covered": 3,
        "covered": 4,
    }
    return order.get(status, 0)
