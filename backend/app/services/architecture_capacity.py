"""Sprint 3.2 Task 7 — capacity notes helper (no fabricate).

Pure helpers (no DB/AI). Aligns with docs/Phase 3/06_CAPACITY_PLANNING.md:
every sizing result needs input + unit + method + assumption; missing inputs
become open questions — never invent numbers.
"""

from __future__ import annotations

from typing import Any

from app.schemas.architecture_option import (
    ArchitectureAIExtraction,
    ArchitectureCandidateAI,
    CapacityNoteAI,
)

# Domain → expected capacity dimensions (labels + clarifying questions).
# Signals in RKM text suppress the auto-added open question (evidence present).
_CAPACITY_BY_DOMAIN: dict[str, tuple[dict[str, Any], ...]] = {
    "wifi": (
        {
            "label": "AP count",
            "unit": "APs",
            "open_question": (
                "What floor plans, wall materials, and concurrent client density "
                "should drive AP count?"
            ),
            "signals": ("access point", "ap count", "heatmap", "density", "floor plan"),
        },
        {
            "label": "Concurrent wireless clients",
            "unit": "clients",
            "open_question": "What peak concurrent wireless client count is required?",
            "signals": ("concurrent", "client density", "devices per"),
        },
    ),
    "campus_lan": (
        {
            "label": "Access port density",
            "unit": "ports",
            "open_question": (
                "How many wired access ports / IDFs and what uplink capacity are required?"
            ),
            "signals": ("port count", "access port", "idf", "uplink"),
        },
    ),
    "wan_sdwan": (
        {
            "label": "WAN / site bandwidth",
            "unit": "Mbps",
            "open_question": "What per-site WAN bandwidth and dual-circuit targets apply?",
            "signals": ("bandwidth", "mbps", "circuit", "wan"),
        },
    ),
    "internet": (
        {
            "label": "Internet egress bandwidth",
            "unit": "Mbps",
            "open_question": "What peak internet egress Mbps is required?",
            "signals": ("internet bandwidth", "egress", "mbps"),
        },
    ),
    "storage": (
        {
            "label": "Storage capacity",
            "unit": "TB",
            "open_question": "What usable capacity, growth, and performance (IOPS) targets apply?",
            "signals": ("tb", "storage capacity", "iops", "usable capacity"),
        },
    ),
    "backup_dr": (
        {
            "label": "Backup / DR retention",
            "unit": "days",
            "open_question": "What RPO/RTO and backup retention window are mandatory?",
            "signals": ("rpo", "rto", "retention", "backup window"),
        },
    ),
    "cctv": (
        {
            "label": "Camera count / retention",
            "unit": "cameras",
            "open_question": "How many cameras and what retention/FPS drive storage sizing?",
            "signals": ("camera", "fps", "retention"),
        },
    ),
    "led_video_wall": (
        {
            "label": "LED wall sizing",
            "unit": "mm pitch",
            "open_question": (
                "What wall dimensions, viewing distance, and pixel pitch are required?"
            ),
            "signals": ("pixel pitch", "viewing distance", "wall dimension"),
        },
    ),
    "ztna_vpn": (
        {
            "label": "Concurrent remote sessions",
            "unit": "sessions",
            "open_question": "How many concurrent remote / ZTNA sessions must be supported?",
            "signals": ("concurrent", "remote user", "session"),
        },
    ),
}


def preprocess_capacity_in_extraction(payload: dict[str, Any]) -> dict[str, Any]:
    """Sanitize capacity notes before schema validation.

    Fabricated ``result`` values (no input+method and no assumption) are cleared
    and converted to ``open_question`` entries with low confidence.
    """
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
        notes_in = row.get("capacity_notes") or []
        if not isinstance(notes_in, list):
            notes_in = []
        row["capacity_notes"] = [
            sanitize_capacity_note_dict(note) for note in notes_in if isinstance(note, dict)
        ]
        out_arch.append(row)

    result = dict(payload)
    result["architectures"] = out_arch
    if "architecture" in result and not isinstance(result.get("architecture"), list):
        # Keep singular key consistent if present.
        result["architecture"] = out_arch[0] if out_arch else result["architecture"]
    return result


def sanitize_capacity_note_dict(note: dict[str, Any]) -> dict[str, Any]:
    """Return a capacity note dict that does not fabricate sizing results."""
    row = dict(note)
    label = str(row.get("label") or "Capacity").strip() or "Capacity"
    row["label"] = label

    result = str(row.get("result") or "").strip() or None
    input_value = str(row.get("input_value") or "").strip() or None
    method = str(row.get("method") or "").strip() or None
    assumption = str(row.get("assumption") or "").strip() or None
    open_question = str(row.get("open_question") or "").strip() or None
    unit = str(row.get("unit") or "").strip() or None

    has_inputs = bool(input_value and method)
    fabricated = bool(result) and not has_inputs and not assumption

    if fabricated:
        # Never keep invented numbers — ask instead.
        if not open_question:
            open_question = (
                f"What verified inputs and method should be used to size {label}? "
                f"(AI suggested {result!r} without evidence — do not treat as fact.)"
            )
        result = None
        try:
            confidence = float(row.get("confidence") or 0)
        except (TypeError, ValueError):
            confidence = 0.0
        if confidence > 1.0:
            confidence = confidence / 100.0
        row["confidence"] = min(confidence, 0.25)

    if not result and not open_question and not has_inputs:
        open_question = f"What inputs and method should drive sizing for {label}?"
        row["confidence"] = float(row.get("confidence") or 0.2) or 0.2

    row["result"] = result
    row["input_value"] = input_value
    row["method"] = method
    row["assumption"] = assumption
    row["open_question"] = open_question
    row["unit"] = unit
    return row


def enrich_architecture_capacity(
    extraction: ArchitectureAIExtraction,
    *,
    domain_codes: list[str] | None = None,
    rkm_text: str = "",
    requirements: list[dict[str, Any]] | None = None,
) -> ArchitectureAIExtraction:
    """Ensure domain-relevant capacity open questions exist when evidence is thin.

    Never invents numeric results. Existing notes are re-validated via CapacityNoteAI.
    """
    codes = {
        str(code or "").strip().lower()
        for code in (domain_codes or [])
        if str(code or "").strip()
    }
    haystack = _haystack(rkm_text, requirements)
    refined: list[ArchitectureCandidateAI] = []

    for candidate in extraction.architectures:
        notes = [
            CapacityNoteAI.model_validate(sanitize_capacity_note_dict(note.model_dump()))
            for note in candidate.capacity_notes
        ]
        existing_labels = {_normalize_label(note.label) for note in notes}

        for code in sorted(codes):
            for spec in _CAPACITY_BY_DOMAIN.get(code, ()):
                label_key = _normalize_label(str(spec["label"]))
                if label_key in existing_labels:
                    continue
                if _signals_present(haystack, tuple(spec["signals"])):
                    # Evidence exists in RKM — leave sizing to AI/human; do not invent.
                    continue
                notes.append(
                    CapacityNoteAI(
                        label=str(spec["label"]),
                        unit=spec.get("unit"),
                        open_question=str(spec["open_question"]),
                        confidence=0.2,
                        related_requirement_ids=_related_requirement_ids(
                            requirements,
                            tuple(spec["signals"]),
                        ),
                    ),
                )
                existing_labels.add(label_key)

        refined.append(candidate.model_copy(update={"capacity_notes": notes}))

    return extraction.model_copy(update={"architectures": refined})


def expected_capacity_labels_for_domains(domain_codes: list[str] | None) -> list[str]:
    """Test/helper: labels the enricher may add for the given domains."""
    labels: list[str] = []
    seen: set[str] = set()
    for code in domain_codes or []:
        for spec in _CAPACITY_BY_DOMAIN.get(str(code).strip().lower(), ()):
            label = str(spec["label"])
            key = _normalize_label(label)
            if key not in seen:
                seen.add(key)
                labels.append(label)
    return labels


def _haystack(rkm_text: str, requirements: list[dict[str, Any]] | None) -> str:
    parts = [rkm_text or ""]
    for req in requirements or []:
        parts.append(str(req.get("title") or ""))
        parts.append(str(req.get("description") or ""))
    return " ".join(parts).lower()


def _signals_present(haystack: str, signals: tuple[str, ...]) -> bool:
    return any(signal and signal in haystack for signal in signals)


def _normalize_label(label: str) -> str:
    return " ".join(label.lower().split())


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
            req_id = str(req.get("id") or req.get("requirement_id") or "").strip()
            if req_id and req_id not in matched:
                matched.append(req_id)
    return matched[:5]
