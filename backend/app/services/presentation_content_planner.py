"""Presentation storyline planner (Sprint 4.2)."""

from __future__ import annotations

from typing import Any


class PresentationContentPlanner:
    def build(self, snapshot_payload: dict[str, Any], template_sections: list[Any]) -> dict[str, Any]:
        bom = snapshot_payload.get("bom") or {}
        bom_validated = bool(bom.get("validated"))
        arch = snapshot_payload.get("architecture") or {}
        constraints: list[str] = []
        if not bom_validated:
            constraints.append("BOM not validated — never include pricing")
        if not (arch.get("capacity_notes") or []):
            constraints.append("No capacity inputs — do not invent timeline commitments")

        slides: list[dict[str, Any]] = []
        for index, raw in enumerate(template_sections or []):
            if isinstance(raw, dict):
                section_type = str(raw.get("section_type") or f"slide_{index}")
                title = str(raw.get("title") or section_type.replace("_", " ").title())
            else:
                section_type = str(raw)
                title = section_type.replace("_", " ").title()
            constrained = section_type in {"timeline", "benefits", "technical_highlights"}
            slides.append(
                {
                    "section_type": section_type,
                    "title": title,
                    "sequence": index,
                    "constrained": constrained,
                    "hints": self._hints(section_type, snapshot_payload),
                }
            )

        return {
            "document_type": "presentation",
            "constraints": constraints,
            "bom_validated": bom_validated,
            "sections": slides,
            "slides": slides,
        }

    def _hints(self, section_type: str, snapshot: dict[str, Any]) -> list[str]:
        rkm = snapshot.get("rkm") or {}
        arch = snapshot.get("architecture") or {}
        if section_type == "requirements":
            return [f"{len(rkm.get('requirements') or [])} requirements"]
        if section_type in {"proposed_architecture", "solution_overview"}:
            return [f"Architecture: {arch.get('title') or arch.get('candidate_key')}"]
        if section_type == "key_components":
            return [f"{len(arch.get('components') or [])} components"]
        if section_type == "risks_assumptions":
            return [
                f"{len(arch.get('risks') or [])} risks",
                f"{len(arch.get('assumptions') or [])} assumptions",
            ]
        if section_type == "timeline":
            return ["No authoritative schedule — REVIEW REQUIRED only"]
        return []
