# Phase 4 Changelog

## 0.4.0 (Sprint 4.1 in progress)

### Sprint 4.0 — Design locks (2026-08-10)
- Accepted ATLAS-042…048 (deliverables namespace, snapshots, AI/render split, human approve, templates, no commercial fabrication, provider abstraction).
- Canonical docs path: `docs/Phase 4/`.

### Sprint 4.1 — Proposal foundation (implemented)
Added:
- Source snapshots (`source_snapshots`) with Published RKM + Complete architecture gate
- Document templates / template versions (default proposal seed)
- Generated documents, versions, sections, content items, source refs
- Generation runs + export jobs
- Proposal generation (`AIProvider.generate_proposal_content`) + local provider
- Review / approve / revise lifecycle
- DOCX export renderer
- API `/api/v1/projects/{id}/deliverables/...`
- UI `DeliverablesPanel`
- Unit tests + `scripts/verify_sprint_4_1.py`

Planned later (not shipped):
- Presentation / PPTX (4.2)
- SOW / Solution Design / PDF (4.3)
- Package + BOM commercial packaging (4.4)
