"""Solution design content plan from template + snapshot (Sprint 4.3)."""

from __future__ import annotations

from typing import Any


class SolutionDesignContentPlanner:
    def build(self, snapshot_payload: dict[str, Any], template_sections: list[Any]) -> dict[str, Any]:
        bom = snapshot_payload.get("bom") or {}
        bom_validated = bool(bom.get("validated"))
        arch = snapshot_payload.get("architecture") or {}
        constraints: list[str] = [
            "Remain consistent with the approved architecture in the source snapshot",
            "Do not introduce new technical claims without REVIEW REQUIRED",
        ]
        if not bom_validated:
            constraints.append("BOM not validated — omit commercial/SKU invention")
        if not (arch.get("capacity_notes") or []):
            constraints.append("No capacity inputs — mark capacity section REVIEW REQUIRED")

        sections: list[dict[str, Any]] = []
        for index, raw in enumerate(template_sections or []):
            if isinstance(raw, dict):
                section_type = str(raw.get("section_type") or f"section_{index}")
                title = str(raw.get("title") or section_type.replace("_", " ").title())
            else:
                section_type = str(raw)
                title = section_type.replace("_", " ").title()
            constrained = section_type in {"capacity", "availability", "security"}
            sections.append(
                {
                    "section_type": section_type,
                    "title": title,
                    "sequence": index,
                    "constrained": constrained,
                    "hints": self._hints(section_type, snapshot_payload),
                }
            )

        return {
            "document_type": "solution_design",
            "constraints": constraints,
            "bom_validated": bom_validated,
            "sections": sections,
        }

    def _hints(self, section_type: str, snapshot: dict[str, Any]) -> list[str]:
        rkm = snapshot.get("rkm") or {}
        arch = snapshot.get("architecture") or {}
        if section_type == "requirements_traceability":
            return [f"{len(rkm.get('requirements') or [])} requirements"]
        if section_type in {
            "high_level_architecture",
            "logical_design",
            "physical_component_design",
        }:
            return [
                f"Architecture: {arch.get('title') or arch.get('candidate_key')}",
                f"{len(arch.get('components') or [])} components",
            ]
        if section_type == "design_decisions":
            return [f"{len(arch.get('decisions') or [])} decisions"]
        if section_type == "risks":
            return [f"{len(arch.get('risks') or [])} risks"]
        if section_type == "assumptions":
            return [f"{len(arch.get('assumptions') or [])} assumptions"]
        if section_type == "capacity":
            notes = arch.get("capacity_notes") or []
            if notes:
                return [f"{len(notes)} capacity notes"]
            return ["No capacity notes — REVIEW REQUIRED"]
        return []
