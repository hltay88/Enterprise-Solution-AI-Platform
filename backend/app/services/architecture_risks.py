"""Sprint 3.2 Task 8 — risk and assumption builder.

Pure helpers (no DB/AI). Aligns with docs/Phase 3/12_RISK_AND_ASSUMPTION_ENGINE.md:
structured risks/assumptions, assumptions never silently become requirements.
Tables already exist (Task 2); this builds/normalizes records for persist.
"""

from __future__ import annotations

from typing import Any

from app.schemas.architecture_option import (
    ArchitectureAIExtraction,
    ArchitectureAssumptionAI,
    ArchitectureCandidateAI,
    SolutionRiskAI,
)

ALLOWED_RISK_CATEGORIES: frozenset[str] = frozenset(
    {
        "technical",
        "security",
        "integration",
        "capacity",
        "availability",
        "operational",
        "vendor",
        "lifecycle",
        "commercial",
        "implementation",
    },
)

_CATEGORY_ALIASES: dict[str, str] = {
    "tech": "technical",
    "ops": "operational",
    "operation": "operational",
    "avail": "availability",
    "ha": "availability",
    "resilience": "availability",
    "cost": "commercial",
    "commercial_suitability": "commercial",
    "sku": "vendor",
    "product": "vendor",
    "schedule": "implementation",
    "delivery": "implementation",
}

# Baseline assumptions always surfaced (must stay unvalidated until confirmed).
_BASELINE_ASSUMPTIONS: tuple[dict[str, Any], ...] = (
    {
        "statement": (
            "Published RKM plus latest domain analysis are sufficient for "
            "high-level architecture candidates"
        ),
        "reason": "Phase 3 generate consumes Published RKM only (ATLAS-023)",
        "validation_required": True,
    },
    {
        "statement": "Product SKUs and vendor selection remain out of scope for this stage",
        "reason": "ATLAS-035 vendor-neutral architecture candidates",
        "validation_required": True,
    },
)

# Domain → starter risks when AI/RKM omit them (still explicit, not silent requirements).
_DOMAIN_RISKS: dict[str, tuple[dict[str, Any], ...]] = {
    "wifi": (
        {
            "description": "Incomplete RF/site survey may change AP density and placement",
            "category": "capacity",
            "cause": "Missing floor plans or wall-material data",
            "impact": "Coverage/capacity redesign and schedule slip",
            "probability": "medium",
            "severity": "medium",
            "mitigation": "Schedule survey before BOM; keep AP count as open capacity note",
            "signals": ("survey", "heatmap", "floor plan"),
        },
    ),
    "campus_lan": (
        {
            "description": "Unknown IDF/uplink constraints may force topology changes",
            "category": "technical",
            "cause": "Incomplete campus inventory",
            "impact": "Rework of access/aggregation design",
            "probability": "medium",
            "severity": "medium",
            "mitigation": "Confirm IDF counts, uplink capacity, and PoE budget",
            "signals": ("idf", "uplink", "poe"),
        },
    ),
    "identity": (
        {
            "description": "Identity integration details may alter security control placement",
            "category": "security",
            "cause": "Directory/MFA/NAC specifics not fully specified",
            "impact": "Delayed access policy design",
            "probability": "medium",
            "severity": "medium",
            "mitigation": "Validate IdP, 802.1X, and MFA requirements early",
            "signals": ("802.1x", "mfa", "directory", "nac"),
        },
    ),
    "backup_dr": (
        {
            "description": "Unclear RPO/RTO targets may invalidate DR topology",
            "category": "availability",
            "cause": "Missing recovery objectives",
            "impact": "Incorrect DR sizing or site design",
            "probability": "medium",
            "severity": "high",
            "mitigation": "Confirm RPO/RTO and retention before finalizing pattern",
            "signals": ("rpo", "rto"),
        },
    ),
}


def preprocess_risks_assumptions_in_extraction(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Normalize legacy risk/assumption shapes before schema validation."""
    if not isinstance(payload, dict):
        return payload
    architectures = payload.get("architectures")
    if architectures is None and "architecture" in payload:
        architectures = payload.get("architecture")
    if isinstance(architectures, dict):
        architectures = [architectures]
    if not isinstance(architectures, list):
        return payload

    out_arch: list[Any] = []
    for item in architectures:
        if not isinstance(item, dict):
            out_arch.append(item)
            continue
        row = dict(item)

        risks_in = row.get("risks")
        if risks_in is None and "technical_risks" in row:
            risks_in = row.get("technical_risks")
        row["risks"] = [
            sanitize_risk_dict(note)
            for note in _coerce_risk_list(risks_in)
        ]

        assumptions_in = row.get("assumptions")
        if assumptions_in is None and "design_assumptions" in row:
            assumptions_in = row.get("design_assumptions")
        row["assumptions"] = [
            sanitize_assumption_dict(note)
            for note in _coerce_assumption_list(assumptions_in)
        ]
        out_arch.append(row)

    result = dict(payload)
    result["architectures"] = out_arch
    if "architecture" in result and not isinstance(result.get("architecture"), list):
        result["architecture"] = out_arch[0] if out_arch else result["architecture"]
    return result


def sanitize_risk_dict(note: dict[str, Any]) -> dict[str, Any]:
    """Normalize a single risk record (category aliases, required description)."""
    row = dict(note)
    description = str(
        row.get("description") or row.get("title") or row.get("risk") or "",
    ).strip()
    row["description"] = description or "Unspecified technical risk"
    row["category"] = _normalize_category(row.get("category"))
    row["cause"] = str(row.get("cause") or "").strip()
    row["impact"] = str(row.get("impact") or "").strip()
    row["mitigation"] = str(row.get("mitigation") or "").strip()
    row["probability"] = _normalize_probability(row.get("probability"))
    row["severity"] = _normalize_severity(row.get("severity"))
    owner = str(row.get("owner") or "").strip()
    row["owner"] = owner or None
    reqs = row.get("related_requirement_ids") or row.get("related_requirement") or []
    if isinstance(reqs, str):
        reqs = [reqs]
    if not isinstance(reqs, list):
        reqs = []
    row["related_requirement_ids"] = [
        str(item).strip() for item in reqs if str(item).strip()
    ]
    return row


def sanitize_assumption_dict(note: dict[str, Any]) -> dict[str, Any]:
    """Normalize assumption; force unvalidated + validation_required (never silent req)."""
    row = dict(note)
    statement = str(
        row.get("statement") or row.get("assumption") or row.get("text") or "",
    ).strip()
    row["statement"] = statement or "Unspecified design assumption"
    row["reason"] = str(row.get("reason") or "").strip()
    affected = row.get("affected_components") or row.get("affected_component_ids") or []
    if isinstance(affected, str):
        affected = [affected]
    if not isinstance(affected, list):
        affected = []
    row["affected_components"] = [
        str(item).strip() for item in affected if str(item).strip()
    ]
    # Rule: assumption must never silently become a requirement.
    row["validation_required"] = True
    status = str(row.get("status") or "unvalidated").strip().lower()
    if status not in {"unvalidated", "validated", "rejected"}:
        status = "unvalidated"
    # Builder never auto-validates.
    if status == "validated" and not row.get("allow_validated"):
        status = "unvalidated"
    row["status"] = status
    row.pop("allow_validated", None)
    return row


def enrich_architecture_risks_assumptions(
    extraction: ArchitectureAIExtraction,
    *,
    domain_codes: list[str] | None = None,
    rkm_payload: dict[str, Any] | None = None,
    requirements: list[dict[str, Any]] | None = None,
) -> ArchitectureAIExtraction:
    """Merge RKM risks, baseline assumptions, and domain starter risks."""
    codes = {
        str(code or "").strip().lower()
        for code in (domain_codes or [])
        if str(code or "").strip()
    }
    rkm = rkm_payload or {}
    rkm_risks = _rkm_risks(rkm, requirements)
    haystack = _haystack(rkm, requirements)
    refined: list[ArchitectureCandidateAI] = []

    for candidate in extraction.architectures:
        risks = [
            SolutionRiskAI.model_validate(sanitize_risk_dict(item.model_dump()))
            for item in candidate.risks
        ]
        assumptions = [
            ArchitectureAssumptionAI.model_validate(
                sanitize_assumption_dict(item.model_dump()),
            )
            for item in candidate.assumptions
        ]

        risk_keys = {_risk_key(item.description) for item in risks}
        for rkm_risk in rkm_risks:
            key = _risk_key(rkm_risk["description"])
            if key in risk_keys:
                continue
            risks.append(SolutionRiskAI.model_validate(rkm_risk))
            risk_keys.add(key)

        for code in sorted(codes):
            for spec in _DOMAIN_RISKS.get(code, ()):
                if _signals_present(haystack, tuple(spec.get("signals") or ())):
                    # Evidence already discusses the concern; skip starter risk.
                    continue
                key = _risk_key(str(spec["description"]))
                if key in risk_keys:
                    continue
                risks.append(
                    SolutionRiskAI.model_validate(
                        {
                            "description": spec["description"],
                            "category": spec["category"],
                            "cause": spec.get("cause") or "",
                            "impact": spec.get("impact") or "",
                            "probability": spec.get("probability") or "medium",
                            "severity": spec.get("severity") or "medium",
                            "mitigation": spec.get("mitigation") or "",
                            "related_requirement_ids": _related_requirement_ids(
                                requirements,
                                tuple(spec.get("signals") or ()),
                            ),
                        },
                    ),
                )
                risk_keys.add(key)

        assumption_keys = {_assumption_key(item.statement) for item in assumptions}
        for baseline in _BASELINE_ASSUMPTIONS:
            key = _assumption_key(str(baseline["statement"]))
            if key in assumption_keys:
                continue
            assumptions.append(
                ArchitectureAssumptionAI.model_validate(
                    sanitize_assumption_dict(baseline),
                ),
            )
            assumption_keys.add(key)

        # Capacity open questions imply an explicit assumption that sizing is pending.
        if candidate.capacity_notes and any(
            note.open_question and not note.result for note in candidate.capacity_notes
        ):
            pending = (
                "Capacity sizing remains preliminary until open capacity questions "
                "are answered; do not treat provisional figures as requirements"
            )
            key = _assumption_key(pending)
            if key not in assumption_keys:
                assumptions.append(
                    ArchitectureAssumptionAI.model_validate(
                        sanitize_assumption_dict(
                            {
                                "statement": pending,
                                "reason": "Capacity planning standard (doc 06) — no fabricate",
                                "validation_required": True,
                            },
                        ),
                    ),
                )

        refined.append(
            candidate.model_copy(
                update={"risks": risks, "assumptions": assumptions},
            ),
        )

    return extraction.model_copy(update={"architectures": refined})


def _coerce_risk_list(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [{"description": text}] if text else []
    if not isinstance(value, list):
        return []
    out: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            out.append({"description": item.strip()})
        elif isinstance(item, dict):
            out.append(item)
    return out


def _coerce_assumption_list(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [{"statement": text}] if text else []
    if not isinstance(value, list):
        return []
    out: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            out.append({"statement": item.strip()})
        elif isinstance(item, dict):
            out.append(item)
    return out


def _normalize_category(value: Any) -> str:
    text = str(value or "technical").strip().lower().replace(" ", "_").replace("-", "_")
    text = _CATEGORY_ALIASES.get(text, text)
    if text not in ALLOWED_RISK_CATEGORIES:
        return "technical"
    return text


def _normalize_probability(value: Any) -> str:
    text = str(value or "medium").strip().lower()
    if text not in {"low", "medium", "high"}:
        return "medium"
    return text


def _normalize_severity(value: Any) -> str:
    text = str(value or "medium").strip().lower()
    if text not in {"low", "medium", "high", "critical"}:
        return "medium"
    return text


def _rkm_risks(
    rkm: dict[str, Any],
    requirements: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in rkm.get("risks") or []:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        description = str(item.get("description") or "").strip()
        text = description or title
        if not text:
            continue
        req_id = str(item.get("id") or item.get("requirement_id") or title or "").strip()
        related = [req_id] if req_id else []
        out.append(
            {
                "description": text if not title or title in text else f"{title}: {text}",
                "category": "technical",
                "cause": "Captured in Published RKM risks",
                "impact": description or title,
                "probability": "medium",
                "severity": "medium",
                "mitigation": "Track through architecture review; validate with stakeholders",
                "related_requirement_ids": related[:5],
            },
        )
    # Also surface high-priority requirements that mention risk language.
    for req in requirements or []:
        blob = f"{req.get('title', '')} {req.get('description', '')}".lower()
        if "risk" not in blob and "single point" not in blob:
            continue
        req_id = str(req.get("id") or "").strip()
        desc = str(req.get("title") or req.get("description") or "").strip()
        if not desc:
            continue
        out.append(
            {
                "description": f"Requirement-linked risk signal: {desc}",
                "category": "technical",
                "cause": "Language in Published RKM requirement",
                "impact": "May constrain architecture choices",
                "probability": "medium",
                "severity": "medium",
                "mitigation": "Confirm acceptance criteria during review",
                "related_requirement_ids": [req_id] if req_id else [],
            },
        )
    return out


def _haystack(
    rkm: dict[str, Any],
    requirements: list[dict[str, Any]] | None,
) -> str:
    parts: list[str] = []
    for key in (
        "business_objectives",
        "functional_requirements",
        "non_functional_requirements",
        "constraints",
        "risks",
        "assumptions",
    ):
        for item in rkm.get(key) or []:
            if isinstance(item, dict):
                parts.append(str(item.get("title") or ""))
                parts.append(str(item.get("description") or ""))
    for req in requirements or []:
        parts.append(str(req.get("title") or ""))
        parts.append(str(req.get("description") or ""))
    return " ".join(parts).lower()


def _signals_present(haystack: str, signals: tuple[str, ...]) -> bool:
    return any(signal and signal in haystack for signal in signals)


def _related_requirement_ids(
    requirements: list[dict[str, Any]] | None,
    signals: tuple[str, ...],
) -> list[str]:
    if not requirements:
        return []
    matched: list[str] = []
    for req in requirements:
        blob = f"{req.get('title', '')} {req.get('description', '')}".lower()
        if any(signal in blob for signal in signals):
            req_id = str(req.get("id") or "").strip()
            if req_id and req_id not in matched:
                matched.append(req_id)
    return matched[:5]


def _risk_key(text: str) -> str:
    return " ".join(text.lower().split())


def _assumption_key(text: str) -> str:
    return " ".join(text.lower().split())
