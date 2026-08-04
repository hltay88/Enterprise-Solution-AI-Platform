# RKM_SCHEMA.md

**Requirement Knowledge Model Schema**  
**Version:** 1.0

---

The Requirement Knowledge Model is a business object.

JSON is only one serialization format.

Future serialization may include:

- JSON
- YAML
- XML
- Graph Database
- Relational Database
- Protocol Buffers

---

# Canonical JSON Representation

```json
{
  "project": {},
  "business_objectives": [],
  "current_environment": {},
  "functional_requirements": [],
  "non_functional_requirements": [],
  "constraints": [],
  "dependencies": [],
  "risks": [],
  "assumptions": [],
  "stakeholders": [],
  "clarification_questions": [],
  "evidence": [],
  "analysis": {
    "confidence_score": 0,
    "completeness_score": 0,
    "reasoning_summary": ""
  },
  "approval": {
    "status": "Draft",
    "reviewed_by": "",
    "approved_by": "",
    "approved_at": ""
  },
  "version": {
    "number": 1,
    "created_at": "",
    "updated_at": ""
  }
}
```

---

# Rules

- The RKM is immutable after publication.
- Every update creates a new version.
- Downstream AI engines consume only approved RKMs.
- Uploaded documents remain evidence and are never modified.
- Business logic operates on the RKM, not on uploaded documents.
