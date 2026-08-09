# Test Plan Phase 4

## Covered in Foundation 0.4

Unit / verify (in repo):
- content schemas (proposal, presentation, SOW, solution design, package)
- source snapshot input gate
- deliverable / presentation / SOW validation (incl. ATLAS-047 pricing guards)
- cross-document consistency helpers
- DOCX / PDF (mocked soffice) / PPTX / XLSX renderers
- BOM package helpers
- `scripts/verify_sprint_4_{1,2,3,4}.py`

Live smoke (manual / session):
- generate → validate → review → approve narrative docs
- BOM deliverable → package assemble / validate / approve → ZIP

## Deferred (not required to freeze 0.4)

Integration tests (CI):
- RKM + architecture → proposal
- architecture + BOM → SOW
- solution → presentation
- approved documents → package

Golden projects:
- network
- cybersecurity
- cloud
- data centre
- AV/LED
- digital signage
- smart building

## Acceptance checklist (product)

- required sections present
- architecture consistency
- requirement traceability (source refs)
- no fabricated technical / commercial claims (ATLAS-047)
- successful exports
- correct version/audit metadata
