# API_PHASE3.md

Base path: `/api/v1` (same envelope as Phase 2)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/projects/{projectId}/architecture/generate` | Generate architecture from **Published** RKM. |
| GET | `/projects/{projectId}/architecture` | Get latest architecture recommendation (404 if none). |

Generation fails with validation error if the project has no Published RKM.
