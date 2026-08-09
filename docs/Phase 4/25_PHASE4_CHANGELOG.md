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

Planned later:
- SOW / Solution Design / PDF (4.3)
- Package + BOM commercial packaging (4.4)
