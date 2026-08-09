# API Phase 4

Base: /api/v1

Generation:
- POST /projects/{projectId}/documents/generate
- POST /projects/{projectId}/documents/preview

Documents:
- GET /projects/{projectId}/documents
- GET /documents/{documentId}
- POST /documents/{documentId}/revise
- POST /documents/{documentId}/validate
- POST /documents/{documentId}/approve

Sections:
- GET /documents/{documentId}/sections
- PATCH /documents/{documentId}/sections/{sectionId}

Export:
- POST /documents/{documentId}/export
- GET /exports/{exportId}

Packages:
- POST /projects/{projectId}/packages/generate
- GET /projects/{projectId}/packages
