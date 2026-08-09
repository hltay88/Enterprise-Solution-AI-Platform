"""Deterministic proposal content plan from template + snapshot."""

from __future__ import annotations

from typing import Any


class ProposalContentPlanner:
    def build(self, snapshot_payload: dict[str, Any], template_sections: list[Any]) -> dict[str, Any]:
        bom = snapshot_payload.get("bom") or {}
        bom_validated = bool(bom.get("validated"))
        arch = snapshot_payload.get("architecture") or {}
        constraints: list[str] = []
        if not bom_validated:
            constraints.append(
                "BOM not validated — do not include pricing; mark commercial gaps REVIEW REQUIRED"
            )
        if not (arch.get("capacity_notes") or []):
            constraints.append("No capacity inputs — do not invent timeline durations")

        sections: list[dict[str, Any]] = []
        for index, raw in enumerate(template_sections or []):
            if isinstance(raw, dict):
                section_type = str(raw.get("section_type") or f"section_{index}")
                title = str(raw.get("title") or section_type.replace("_", " ").title())
            else:
                section_type = str(raw)
                title = section_type.replace("_", " ").title()
            constrained = section_type in {
                "timeline",
                "support_warranty",
                "benefits",
            } or section_type.endswith("pricing")
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
            "document_type": "proposal",
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
        if section_type == "requirements":
            return [f"{len(rkm.get('requirements') or [])} requirements in snapshot"]
        if section_type == "architecture":
            return [f"Architecture: {arch.get('title') or arch.get('candidate_key')}"]
        if section_type == "solution_components":
            return [f"{len(arch.get('components') or [])} components"]
        if section_type == "risks":
            return [f"{len(arch.get('risks') or [])} risks recorded"]
        if section_type == "assumptions":
            return [f"{len(arch.get('assumptions') or [])} assumptions recorded"]
        if section_type in {"timeline", "support_warranty"}:
            return [
                "No authoritative schedule/warranty data — emit REVIEW REQUIRED assumptions only"
            ]
        if section_type == "proposed_solution" and not bom_validated:
            return ["BOM not validated — omit pricing"]
        return []
