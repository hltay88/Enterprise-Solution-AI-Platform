"""Deterministic SOW content plan from template + snapshot (Sprint 4.3)."""

from __future__ import annotations

from typing import Any


class SowContentPlanner:
    def build(self, snapshot_payload: dict[str, Any], template_sections: list[Any]) -> dict[str, Any]:
        bom = snapshot_payload.get("bom") or {}
        bom_validated = bool(bom.get("validated"))
        arch = snapshot_payload.get("architecture") or {}
        constraints: list[str] = [
            "Never invent legal obligations, warranties, SLAs, penalties, dates, or acceptance commitments",
            "Mark missing contractual facts as REVIEW REQUIRED",
        ]
        if not bom_validated:
            constraints.append("BOM not validated — omit commercial figures")
        if not (arch.get("capacity_notes") or []):
            constraints.append("No capacity/schedule inputs — do not invent schedule dates")

        sections: list[dict[str, Any]] = []
        for index, raw in enumerate(template_sections or []):
            if isinstance(raw, dict):
                section_type = str(raw.get("section_type") or f"section_{index}")
                title = str(raw.get("title") or section_type.replace("_", " ").title())
            else:
                section_type = str(raw)
                title = section_type.replace("_", " ").title()
            constrained = section_type in {
                "schedule",
                "support_warranty",
                "acceptance_criteria",
                "testing",
            }
            sections.append(
                {
                    "section_type": section_type,
                    "title": title,
                    "sequence": index,
                    "constrained": constrained,
                    "hints": self._hints(section_type, snapshot_payload, bom_validated),
                }
            )

        return {
            "document_type": "sow",
            "constraints": constraints,
            "bom_validated": bom_validated,
            "sections": sections,
        }

    def _hints(
        self,
        section_type: str,
        snapshot: dict[str, Any],
        bom_validated: bool,
    ) -> list[str]:
        rkm = snapshot.get("rkm") or {}
        arch = snapshot.get("architecture") or {}
        if section_type in {"scope", "solution_overview", "deliverables"}:
            return [
                f"Architecture: {arch.get('title') or arch.get('candidate_key')}",
                f"{len(arch.get('components') or [])} components",
            ]
        if section_type == "assumptions":
            return [f"{len(arch.get('assumptions') or [])} assumptions recorded"]
        if section_type in {"schedule", "support_warranty", "acceptance_criteria"}:
            return ["No authoritative contractual terms — REVIEW REQUIRED only"]
        if section_type == "purpose" and not bom_validated:
            return ["BOM not validated — omit pricing"]
        if section_type == "deliverables":
            return [f"{len(rkm.get('requirements') or [])} requirements in snapshot"]
        return []
