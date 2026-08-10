# API Phase 5

Base: /api/v1

Knowledge: POST /knowledge; GET /knowledge; GET /knowledge/{id}; POST /knowledge/{id}/publish; POST /knowledge/{id}/new-version.

Retrieval: POST /retrieval/search; POST /retrieval/context.

Agents: GET /agents; POST /agents/{id}/run; GET /agent-runs/{id}.

Collaboration: POST /projects/{id}/comments; POST /projects/{id}/review-requests; POST /projects/{id}/approval-requests.

Administration: GET /tenants; GET /usage; GET /audit-events.

Every endpoint must enforce authorization and tenant scoping.
