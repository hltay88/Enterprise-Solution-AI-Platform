# Phase 4 Changelog

## 0.4.0 (in progress)

### Sprint 4.0 — Design locks (2026-08-10)
- Accepted ATLAS-042…048.

### Sprint 4.1 — Proposal foundation
- Source snapshots, proposal generation/review/approve, DOCX export, deliverables API/UI.

### Sprint 4.2 — Presentation Generator (implemented)
Added:
- Presentation template seed (14-slide storyline)
- `AIProvider.generate_presentation_content` (+ local provider)
- Presentation planner, generation service, validation (key_message rule)
- PPTX rendering via `python-pptx`
- Export `format=pptx` for presentations
- UI: Generate presentation + Export PPTX in Deliverables panel
- `scripts/verify_sprint_4_2.py`

### Sprint 4.3 — SOW + Solution Design + PDF (implemented)
Added:
- SOW + Solution Design templates, planners, generation services
- `AIProvider.generate_sow_content` / `generate_solution_design_content`
- Soft cross-document consistency (`GET .../deliverables/consistency`)
- Generalized DOCX renderer; PDF via LibreOffice DOCX→PDF (`format=pdf`)
- UI: Generate SOW / solution design; Export DOCX + Export PDF
- `scripts/verify_sprint_4_3.py`
- ATLAS-049 PDF conversion path

### Sprint 4.4 — Package + BOM (implemented)
Added:
- Deterministic BOM deliverable (`document_type=bom`) + XLSX via openpyxl
- `document_packages` / members; assemble hard gate (validated BOM + 4 approved docs)
- Package validate / approve / ZIP export with `manifest.json`
- UI: Generate BOM, Package panel
- `scripts/verify_sprint_4_4.py`
- ATLAS-050 package gate + ZIP final export

## Atlas Foundation 0.4
Phase 4 exit criteria covered for implemented deliverable generators, package assembly, and export stack (DOCX/PDF/PPTX/XLSX).
