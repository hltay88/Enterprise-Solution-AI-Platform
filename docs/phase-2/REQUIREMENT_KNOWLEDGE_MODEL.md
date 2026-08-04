# REQUIREMENT_KNOWLEDGE_MODEL.md

**Requirement Knowledge Model**  
**Abbreviation:** RKM  
**Version:** 1.0  
**Status:** Enterprise Standard

---

# Definition

The Requirement Knowledge Model (RKM) is the canonical business representation of customer requirements.

The RKM is NOT a document.

The RKM is NOT AI output.

The RKM is the official business object owned by Project Atlas.

Uploaded customer documents become supporting evidence only.

---

# Purpose

The RKM provides a consistent, version-controlled representation of customer requirements for every downstream AI engine.

Every AI module must consume the RKM.

No downstream AI should parse uploaded documents directly.

---

# Aggregate Root

Requirement Knowledge Model contains:

- Project
- Business Objectives
- Current Environment
- Functional Requirements
- Non Functional Requirements
- Constraints
- Dependencies
- Risks
- Assumptions
- Stakeholders
- Clarification Questions
- Evidence
- Versions
- Approvals

---

# Lifecycle

```text
Draft
  ↓
AI Generated
  ↓
AI Validation
  ↓
Human Review
  ↓
Approved
  ↓
Published
  ↓
Archived
```

---

# Rules

- One project owns one active RKM.
- Every modification creates a new version.
- Old versions remain immutable.
- Only approved RKMs can be consumed by downstream engines.
- AI cannot publish RKMs automatically.
- Human approval is mandatory.

---

# Consumers

- Architecture Recommendation Engine
- Proposal Generator
- Presentation Generator
- SOW Generator
- BOM Intelligence
- Knowledge Engine
- Analytics Engine
- RAG Engine
