# DATABASE_PHASE2.md

Phase 2 Database Design

---

## New Tables

- projects
- uploaded_documents
- document_pages
- document_chunks
- document_metadata
- document_embeddings
- requirement_models
- requirement_versions
- requirements
- requirement_categories
- requirement_relationships
- requirement_evidence
- clarification_questions
- clarification_answers
- analysis_sessions
- analysis_results
- gap_analysis
- confidence_scores
- approval_history
- review_comments
- audit_logs

---

## Relationship

```text
Project
  ↓
Uploaded Documents
  ↓
Requirement Knowledge Model
  ↓
Requirement Version
  ↓
Requirements
  ↓
Evidence
  ↓
Clarification
  ↓
Approval
```

---

## Requirement Model

**Fields:**

- id
- project_id
- version
- status
- confidence_score
- completeness_score
- reasoning_summary
- created_by
- created_at
- updated_at
- approved_by
- approved_at

---

## Requirement

- id
- rkm_id
- category
- subcategory
- title
- description
- priority
- confidence
- status
- source_document
- source_page
- created_at

---

## Evidence

Every requirement must reference one or more evidence records.

No requirement may exist without traceability.

---

## Version Rules

- Each modification creates a new RKM version.
- Old versions remain immutable.
- Only one published RKM is active.
