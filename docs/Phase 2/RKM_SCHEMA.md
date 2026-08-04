# RKM_SCHEMA.md

Requirement Knowledge Model Schema — **Version 1.0 (frozen for Stage A)**  
Status: Contract for Stages B–F implementation  
Related: ATLAS-020, ATLAS-021, ATLAS-024, `REQUIREMENT_CLASSIFICATION.md`

---

## Serialization

The RKM is a business object. JSON is the primary interchange format for APIs.

---

## Enums

### `rkm_status`
`draft` | `ai_generated` | `in_review` | `approved` | `published` | `archived`

### `requirement_category`
`business` | `functional` | `non_functional` | `infrastructure` | `security` | `collaboration` | `audio_visual` | `smart_building`

### `priority`
`critical` | `high` | `medium` | `low`

### `requirement_status`
`draft` | `validated` | `approved` | `implemented` | `verified` | `retired`

### `evidence_source_type` (ATLAS-021)
`document` | `sales_intake` | `workshop` | `clarification_answer`

---

## Canonical JSON (typed)

```json
{
  "id": "uuid",
  "project_id": "uuid",
  "project": {
    "project_name": "string",
    "customer": "string|null",
    "industry": "string|null",
    "account_manager": "string|null",
    "deal_id": "string|null",
    "deal_name": "string|null",
    "request_type": "string|null",
    "required_completion_date": "YYYY-MM-DD|null",
    "budget_information": "string|null",
    "winning_probability": "0-100|null"
  },
  "business_objectives": [
    {
      "id": "uuid",
      "title": "string",
      "description": "string",
      "priority": "critical|high|medium|low",
      "status": "draft|validated|approved|implemented|verified|retired",
      "confidence": 0,
      "evidence_ids": ["uuid"]
    }
  ],
  "current_environment": {
    "summary": "string",
    "items": [
      {
        "id": "uuid",
        "title": "string",
        "description": "string",
        "evidence_ids": ["uuid"]
      }
    ]
  },
  "functional_requirements": [
    {
      "id": "uuid",
      "category": "functional",
      "subcategory": "string|null",
      "title": "string",
      "description": "string",
      "priority": "critical|high|medium|low",
      "status": "draft|validated|approved|implemented|verified|retired",
      "confidence": 0,
      "evidence_ids": ["uuid"]
    }
  ],
  "non_functional_requirements": [],
  "constraints": [],
  "dependencies": [],
  "risks": [],
  "assumptions": [],
  "stakeholders": [
    {
      "id": "uuid",
      "name": "string",
      "role": "string|null",
      "contact": "string|null",
      "designation": "string|null",
      "evidence_ids": ["uuid"]
    }
  ],
  "clarification_questions": [
    {
      "id": "uuid",
      "question": "string",
      "priority": "critical|high|medium|low",
      "category": "string",
      "reason": "string",
      "affected_requirement_ids": ["uuid"],
      "status": "open|answered|dismissed",
      "answer": "string|null"
    }
  ],
  "evidence": [
    {
      "id": "uuid",
      "source_type": "document|sales_intake|workshop|clarification_answer",
      "document_id": "uuid|null",
      "page": "number|null",
      "excerpt": "string|null",
      "field_name": "string|null",
      "note": "string|null"
    }
  ],
  "analysis": {
    "confidence_score": 0,
    "completeness_score": 0,
    "consistency_score": 0,
    "evidence_coverage": 0,
    "reasoning_summary": "string",
    "prompt_version": "string",
    "model": "string|null"
  },
  "approval": {
    "status": "draft|ai_generated|in_review|approved|published|archived",
    "reviewed_by": "string|null",
    "approved_by": "string|null",
    "approved_at": "ISO-8601|null",
    "published_at": "ISO-8601|null"
  },
  "version": {
    "number": "1.0.0",
    "major": 1,
    "minor": 0,
    "patch": 0,
    "created_at": "ISO-8601",
    "updated_at": "ISO-8601",
    "change_summary": "string|null"
  }
}
```

Notes:
- `functional_requirements`, `non_functional_requirements`, `constraints`, `dependencies`, `risks`, and `assumptions` share the same item shape as `functional_requirements` above (with `category` set appropriately).
- `business_objectives` use the lighter objective shape shown.
- Every requirement-like item MUST have `evidence_ids.length >= 1` (ATLAS-021).

---

## Publish rules (product gate)

May publish only when:
- Human approval recorded (ATLAS-022)
- `analysis.completeness_score >= 85`
- `analysis.confidence_score >= 85`
- No critical validation errors (missing evidence, invalid relationships)

---

## Immutability (ATLAS-024)

- `approval.status == published` ⇒ payload immutable
- Changes require a new version number per `VERSIONING.md`
