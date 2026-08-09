# Document Domain Model

Document fields:
- document_id
- project_id
- document_type
- title
- status
- version
- template_id
- source_snapshot_id
- created_by
- approved_by
- timestamps

Document types:
- Proposal
- Presentation
- Solution Design
- SOW
- Document Package

Section fields:
- section_id
- document_id
- section_type
- title
- sequence
- content
- status
- source_refs
- assumptions
- confidence

Lifecycle:
Draft → In Review → Changes Requested → Approved → Superseded

Approved versions are immutable.
