"""Sprint 3.2 Task 10 — requirement → domain → architecture/component traceability.

Pure helpers (no DB/AI). Extends the Sprint 3.1 domain matrix with architecture
option and component links (docs/Phase 3/07_REQUIREMENT_TRACEABILITY.md).
"""

from __future__ import annotations

from typing import Any


def build_requirement_architecture_traceability(
    *,
    requirements: list[dict[str, Any]],
    architectures: list[dict[str, Any]],
    domain_links: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Build architecture-stage traceability rows for persistence.

    ``architectures`` items::
        {
          "id": UUID,
          "candidate_key": str,
          "components": [
            {"id": UUID, "name": str, "maps_to_requirements": [str, ...]},
            ...
          ],
        }

    ``domain_links`` items (from prior domain analyze)::
        {"requirement_id": str, "domain_id": UUID|None, "domain_code": str|None, "status": str}

    Status rules (architecture stage):
    - component maps requirement + domain link exists → covered
    - component maps requirement without domain link → partially_covered
    - requirement with no component map on this candidate → not_covered
      (architecture_id set, component_id null)
    """
    domain_by_req = _index_domain_links(domain_links or [])
    rows: list[dict[str, Any]] = []

    for architecture in architectures:
        arch_id = architecture.get("id")
        if arch_id is None:
            continue
        candidate_key = str(architecture.get("candidate_key") or "standard").strip() or "standard"
        components = architecture.get("components") or []
        if not isinstance(components, list):
            components = []

        mapped_req_ids: set[str] = set()
        for component in components:
            if not isinstance(component, dict):
                continue
            component_id = component.get("id")
            if component_id is None:
                continue
            name = str(component.get("name") or "component").strip() or "component"
            for raw_req in component.get("maps_to_requirements") or []:
                req_id = str(raw_req or "").strip()
                if not req_id:
                    continue
                mapped_req_ids.add(req_id)
                domain = domain_by_req.get(req_id)
                if domain is not None:
                    status = "covered"
                    domain_id = domain.get("domain_id")
                    domain_code = domain.get("domain_code")
                    evidence = (
                        f"Mapped via architecture component {name!r} "
                        f"(candidate {candidate_key}) and domain "
                        f"{domain_code or domain_id}"
                    )
                else:
                    status = "partially_covered"
                    domain_id = None
                    domain_code = None
                    evidence = (
                        f"Mapped via architecture component {name!r} "
                        f"(candidate {candidate_key}); no domain link recorded"
                    )
                rows.append(
                    {
                        "requirement_id": req_id,
                        "domain_id": domain_id,
                        "domain_code": domain_code,
                        "architecture_id": arch_id,
                        "component_id": component_id,
                        "decision_id": None,
                        "status": status,
                        "evidence": evidence,
                    },
                )

        for req in requirements:
            req_id = str(req.get("id") or "").strip()
            if not req_id or req_id in mapped_req_ids:
                continue
            domain = domain_by_req.get(req_id)
            priority = str(req.get("priority") or "medium").strip().lower()
            title = str(req.get("title") or req_id).strip()
            critical_note = "critical/high " if priority in {"critical", "high"} else ""
            rows.append(
                {
                    "requirement_id": req_id,
                    "domain_id": domain.get("domain_id") if domain else None,
                    "domain_code": domain.get("domain_code") if domain else None,
                    "architecture_id": arch_id,
                    "component_id": None,
                    "decision_id": None,
                    "status": "not_covered",
                    "evidence": (
                        f"No architecture component on candidate {candidate_key} "
                        f"maps {critical_note}requirement {title!r} ({priority})"
                    ).strip(),
                },
            )

    rows.sort(
        key=lambda row: (
            str(row.get("architecture_id") or ""),
            str(row.get("requirement_id") or ""),
            str(row.get("component_id") or ""),
        ),
    )
    return rows


def count_architecture_uncovered_critical(
    traceability: list[dict[str, Any]],
    requirements: list[dict[str, Any]],
) -> int:
    """Count critical/high requirements with not_covered architecture-stage rows.

    Used as a soft signal for later approve gates (Sprint 3.3). Counts unique
    requirement_ids that are not_covered on at least one candidate.
    """
    priority_by_id = {
        str(req.get("id") or ""): str(req.get("priority") or "medium").lower()
        for req in requirements
    }
    uncovered: set[str] = set()
    for row in traceability:
        if row.get("status") != "not_covered":
            continue
        if row.get("architecture_id") is None:
            continue
        req_id = str(row.get("requirement_id") or "").strip()
        if not req_id:
            continue
        if priority_by_id.get(req_id, "medium") in {"critical", "high"}:
            uncovered.add(req_id)
    return len(uncovered)


def architectures_payload_for_traceability(
    options: list[Any],
    components_by_architecture_id: dict[Any, list[Any]],
) -> list[dict[str, Any]]:
    """Adapt ORM option/component rows into builder input dicts."""
    out: list[dict[str, Any]] = []
    for option in options:
        option_id = getattr(option, "id", None)
        if option_id is None:
            continue
        components = components_by_architecture_id.get(option_id) or []
        out.append(
            {
                "id": option_id,
                "candidate_key": getattr(option, "candidate_key", "standard"),
                "components": [
                    {
                        "id": getattr(component, "id", None),
                        "name": getattr(component, "name", ""),
                        "maps_to_requirements": list(
                            getattr(component, "maps_to_requirements", None) or [],
                        ),
                    }
                    for component in components
                    if getattr(component, "id", None) is not None
                ],
            },
        )
    return out


def domain_links_from_analysis(
    domain_rows: list[Any],
    requirement_links: list[Any],
) -> list[dict[str, Any]]:
    """Build domain_links from DomainRepository domain + requirement link rows."""
    code_by_id: dict[Any, str] = {
        row.id: row.domain_code for row in domain_rows if getattr(row, "id", None)
    }
    out: list[dict[str, Any]] = []
    for link in requirement_links:
        req_id = str(getattr(link, "requirement_id", "") or "").strip()
        domain_id = getattr(link, "domain_id", None)
        if not req_id or domain_id is None:
            continue
        out.append(
            {
                "requirement_id": req_id,
                "domain_id": domain_id,
                "domain_code": code_by_id.get(domain_id),
                "status": "covered",
            },
        )
    return out


def _index_domain_links(
    domain_links: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for item in domain_links:
        if not isinstance(item, dict):
            continue
        req_id = str(item.get("requirement_id") or "").strip()
        if not req_id:
            continue
        # Prefer first domain link; later ones ignored for architecture evidence text.
        indexed.setdefault(req_id, item)
    return indexed

