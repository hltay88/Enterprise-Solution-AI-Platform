# Phase 4 Implementation Guide

Sprint 4.1:
Build common document foundation first: source snapshots, document domain, templates, generation runs and validation, then Proposal Generator.

Sprint 4.2:
Reuse the common foundation for Presentation Generator.

Sprint 4.3:
Reuse source snapshot and traceability for SOW and Solution Design.
PDF exports convert DOCX via LibreOffice. Cross-document consistency is soft (findings only).

Sprint 4.4:
Assemble approved outputs into a package and add final BOM/export validation.
Hard gate: validated BOM + approved proposal/presentation/SOW/solution design.
ZIP export with manifest.json (ATLAS-050).

Principles:
- Reuse common document services.
- Separate content generation from rendering.
- Keep rendering independent from AI.
- Never bypass approval.
- Preserve Phase 1–3 behavior.
