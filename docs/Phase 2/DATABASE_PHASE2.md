# DATABASE_PHASE2.md
Phase 2 Database Design

---

## New Tables

```
projects
uploaded_documents
document_pages
document_chunks
document_metadata
requirement_models
requirement_versions
requirements
requirement_categories
requirement_relationships
requirement_evidence
clarification_questions
clarification_answers
analysis_sessions
analysis_results
gap_analysis
confidence_scores
approval_history
review_comments
audit_logs
```

### Deferred (ATLAS-030)
`document_embeddings` — not required for Sprint 2.1.

---

## Relationship

```
Project → Uploaded Documents → Requirement Knowledge Model
→ Requirement Version → Requirements → Evidence → Clarification → Approval
```

---

## Requirement Model Fields

| Field | Description |
|-------|-------------|
| id | Primary key |
| project_id | Parent project |
| version | Version number |
| status | Draft / Approved / Published |
| confidence_score | AI confidence |
| completeness_score | Completeness % |
| reasoning_summary | AI reasoning |
| created_by | Creator user |
| created_at | Creation timestamp |
| updated_at | Last update |
| approved_by | Approver |
| approved_at | Approval timestamp |

---

## Requirement Fields

| Field | Description |
|-------|-------------|
| id | Primary key |
| rkm_id | Parent RKM |
| category | Requirement category |
| subcategory | Sub-category |
| title | Short title |
| description | Full description |
| priority | Critical/High/Medium/Low |
| confidence | AI confidence score |
| status | Draft/Validated/Approved |
| source_document | Source doc reference |
| source_page | Source page reference |
| created_at | Timestamp |

---

## Evidence Rules
- Every requirement must reference one or more evidence records.
- No requirement may exist without traceability.

---

## Version Rules
- Each modification creates a new RKM version.
- Old versions remain immutable.
- Only one published RKM is active.
