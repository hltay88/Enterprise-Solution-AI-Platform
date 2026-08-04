# API_PHASE2.md
Base URL: `/api/v1`

---

## Document APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /documents/upload | Upload one or more customer documents. |
| GET | /documents/{id} | Retrieve uploaded document. |
| DELETE | /documents/{id} | Delete uploaded document. |

---

## Requirement APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /requirements/analyze | Analyze uploaded documents. |
| GET | /requirements/{projectId} | Retrieve active Requirement Knowledge Model. |
| POST | /requirements/review | Submit review changes. |
| POST | /requirements/publish | Publish approved Requirement Knowledge Model. |
| POST | /requirements/version | Create new requirement version. |
| POST | /requirements/gap-analysis | Generate missing information report. |

---

## Clarification APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /clarification/generate | Generate clarification questions. |
| POST | /clarification/answer | Submit customer answers. |

---

## Analysis APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /analysis/history | Retrieve previous AI analysis. |

---

## Future APIs
- Architecture Engine
- Proposal Engine
- Presentation Engine
- SOW Engine
- BOM Engine

> These APIs belong to later phases.
