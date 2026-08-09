# Database Phase 4

Sprint 4.1 entities (see `docker/postgres/init/10_phase4_deliverables.sql`):

- `document_templates`
- `template_versions`
- `source_snapshots`
- `generation_runs`
- `generated_documents` (product language: deliverable / document)
- `document_versions`
- `document_sections`
- `content_items`
- `document_source_refs`
- `document_approvals`
- `export_jobs`

Deferred to later sprints:
- `document_packages`
- `generation_artifacts` (optional; raw payload stored on `generation_runs`)
- `document_comments`

Integrity:
- Documents reference immutable source snapshots.
- Approved versions cannot be updated in place (revise creates a new version).
- Generation runs retain model, prompt, template and source metadata.
