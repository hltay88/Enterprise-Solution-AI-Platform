# API Phase 4

Base: `/api/v1`

**Namespace (ATLAS-042):** Generated deliverables live under
`/projects/{projectId}/deliverables/...`.

Phase 2 requirement-file ingest retains `/documents` and
`/projects/{projectId}/documents` — do not overload those paths.

## Snapshots

- `POST /projects/{projectId}/deliverables/snapshots`
- `GET /projects/{projectId}/deliverables/snapshots/{snapshotId}`

## Generation

- `POST /projects/{projectId}/deliverables/generate`
  - body: `{ document_type: "proposal" | "presentation" | "sow" | "solution_design" | "bom", snapshot_id?, architecture_id? }`
- `POST /projects/{projectId}/deliverables/preview` (optional dry-run)

## Deliverables

- `GET /projects/{projectId}/deliverables`
- `GET /projects/{projectId}/deliverables/{documentId}`
- `POST /projects/{projectId}/deliverables/{documentId}/revise`
- `POST /projects/{projectId}/deliverables/{documentId}/validate`
- `POST /projects/{projectId}/deliverables/{documentId}/review`
- `POST /projects/{projectId}/deliverables/{documentId}/approve`

## Sections

- `GET /projects/{projectId}/deliverables/{documentId}/sections`
- `PATCH /projects/{projectId}/deliverables/{documentId}/sections/{sectionId}`

## Export

- `POST /projects/{projectId}/deliverables/{documentId}/export`
  - proposal / sow / solution_design → `{ format: "docx" | "pdf" }`
  - presentation → `{ format: "pptx" }`
  - bom → `{ format: "xlsx" }`
- `GET /projects/{projectId}/deliverables/exports/{exportId}`

## Packages (Sprint 4.4)

- `POST /projects/{projectId}/packages/assemble` (alias: `/packages/generate`)
- `GET /projects/{projectId}/packages`
- `GET /projects/{projectId}/packages/{packageId}`
- `POST /projects/{projectId}/packages/{packageId}/validate`
- `POST /projects/{projectId}/packages/{packageId}/approve`
- `POST /projects/{projectId}/packages/{packageId}/export` → ZIP + manifest
