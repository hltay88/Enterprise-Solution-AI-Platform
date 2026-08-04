# IMPLEMENTATION_GUIDE.md
Phase: Atlas Foundation 0.2

---

## Objective
Implement the Requirement Intelligence Engine incrementally.

Follow **`PHASE2_ROADMAP.md` stages A→F**. Do not start Stage B application code until Stage A locks are accepted (complete).

---

## Stage mapping

| Guide step | Roadmap stage | Focus |
|------------|---------------|--------|
| Contracts / decisions | A | Schema, API, limits, evidence policy |
| Step 1–2 Document upload + OCR | B (2.1a) | Ingest, extract, jobs |
| Step 3–4 Extraction + classification | C (2.1b) | Draft RKM |
| Step 5–6 Gap + clarifications | D (2.2) | Scores + questions |
| Step 7–8 Review + publish | E (2.3) | Governance |
| Hardening | F | Perf, security, tests |

---

## Step 1 — Document Upload
**Deliverable:** Multiple file upload with validation (ATLAS-027 limits).

## Step 2 — OCR & Text Extraction
**Deliverable:** Extract searchable text (async jobs — ATLAS-029).

## Step 3 — Requirement Extraction
**Deliverable:** Generate draft Requirement Knowledge Model (schema v1.0).

## Step 4 — Requirement Classification
**Deliverable:** Categorize requirements.

## Step 5 — Gap Analysis
**Deliverable:** Identify missing information.

## Step 6 — Clarification Engine
**Deliverable:** Generate structured clarification questions.

## Step 7 — Review & Approval
**Deliverable:** Human review, comments, approval.

## Step 8 — Publish RKM
**Deliverable:** Publish approved Requirement Knowledge Model for downstream engines.

---

## Development Principles
- Keep domain logic independent of AI providers.
- Separate business rules from persistence.
- Use interfaces for OCR and AI services to enable provider changes.
- Respect ATLAS-021 evidence source types (including `sales_intake`).
- Never mark tasks complete without tests or a recorded demo.
