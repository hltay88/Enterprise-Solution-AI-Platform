# Database Phase 4

Entities:
- document_templates
- template_versions
- source_snapshots
- documents
- document_versions
- document_sections
- content_items
- document_source_refs
- document_comments
- document_approvals
- export_jobs
- generation_runs
- generation_artifacts
- document_packages

Integrity:
- Documents reference immutable source snapshots.
- Approved versions cannot be updated in place.
- Generation runs retain model, prompt, template and source metadata.
