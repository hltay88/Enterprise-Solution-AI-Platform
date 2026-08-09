# DECISIONS.md  
  
> Project: Project Atlas  
>  
> Commercial Product: Enterprise Solution AI Platform  
>  
> Foundation Version: Atlas Foundation 0.1  
>  
> Sprint: Sprint 1  
>  
> Status: Active  
>  
> Last Updated: 2026-08-01  
  
---  
  
# Purpose  
  
This document records significant architectural, technical and product decisions made during the development of Project Atlas.  
  
The objective is to preserve the reasoning behind important decisions so future developers, architects and AI coding assistants understand why the project evolved in a particular direction.  
  
This document serves as the project's Architecture Decision Log.  
  
---  
  
# Decision Record Format  
  
Every decision should follow the same format.  
  
Decision ID  
  
Status  
  
Date  
  
Context  
  
Decision  
  
Reason  
  
Alternatives Considered  
  
Impact  
  
Future Review  
  
---  
  
# Decision 001  
  
Decision ID  
  
ATLAS-001  
  
Status  
  
Accepted  
  
Date  
  
2026-08-01  
  
## Context  
  
The platform requires a modern backend framework that is fast, modular and AI-friendly.  
  
## Decision  
  
Use FastAPI as the backend framework.  
  
## Reason  
  
FastAPI provides:  
  
- Excellent performance  
- Automatic OpenAPI documentation  
- Strong typing  
- Modern async support  
- Easy AI integration  
- Excellent developer productivity  
  
## Alternatives Considered  
  
- Django  
- Flask  
- ASP.NET  
- Spring Boot  
  
## Impact  
  
Backend services will follow REST API principles using FastAPI.  
  
Future migration cost is expected to be low.  
  
Review  
  
Review only if business requirements change significantly.  
  
---  
  
# Decision 002  
  
Decision ID  
  
ATLAS-002  
  
Status  
  
Accepted  
  
Date  
  
2026-08-01  
  
## Context  
  
A frontend framework is required.  
  
## Decision  
  
Use Next.js with TypeScript.  
  
## Reason  
  
- Modern React ecosystem  
- Server Components  
- Excellent routing  
- Strong community  
- Easy deployment  
- Good developer experience  
  
## Alternatives  
  
- React SPA  
- Angular  
- Vue  
  
## Impact  
  
Frontend standards will follow the Next.js ecosystem.  
  
---  
  
# Decision 003  
  
Decision ID  
  
ATLAS-003  
  
Status  
  
Accepted  
  
## Context  
  
A relational database is required.  
  
## Decision  
  
Use PostgreSQL.  
  
## Reason  
  
- Enterprise ready  
- Open source  
- Strong ecosystem  
- JSON support  
- pgvector support  
- Excellent scalability  
  
## Alternatives  
  
- MySQL  
- SQL Server  
- MongoDB  
  
---  
  
# Decision 004  
  
Decision ID  
  
ATLAS-004  
  
Status  
  
Accepted  
  
## Context  
  
The AI platform should remain flexible.  
  
## Decision  
  
Do not lock Project Atlas to a single AI provider.  
  
## Decision  
  
Introduce an AI abstraction layer.  
  
```  
AI Service  
  
↓  
  
OpenAI  
  
Anthropic  
  
Azure OpenAI  
  
Future Providers  
```  
  
## Reason  
  
Future AI providers may become better or more cost-effective.  
  
Changing providers should not require rewriting business logic.  
  
---  
  
# Decision 005  
  
Decision ID  
  
ATLAS-005  
  
Status  
  
Accepted  
  
## Context  
  
The product will support multiple technology vendors.  
  
## Decision  
  
Adopt a Solution-First strategy.  
  
Solutions are recommended before vendors.  
  
## Example  
  
Customer Requirement  
  
↓  
  
Networking  
  
↓  
  
Recommended Vendors  
  
Cisco  
  
Aruba  
  
Huawei  
  
Juniper  
  
HPE  
  
Instead of  
  
Cisco  
  
↓  
  
Networking  
  
---  
  
# Decision 006  
  
Decision ID  
  
ATLAS-006  
  
Status  
  
Accepted  
  
## Context  
  
The product roadmap originally focused only on IT infrastructure.  
  
## Decision  
  
Expand Project Atlas into a complete Enterprise Solution Platform.  
  
Supported solution domains include:  
  
- Networking  
- Cybersecurity  
- Cloud  
- Data Centre  
- Storage  
- Microsoft  
- AI  
- IoT  
- Smart Building  
- Audio Visual  
- LED Video Wall  
- Digital Signage  
- CCTV  
- Access Control  
- UPS  
- Structured Cabling  
  
## Impact  
  
The platform is no longer limited to traditional IT presales.  
  
---  
  
# Decision 007  
  
Decision ID  
  
ATLAS-007  
  
Status  
  
Accepted  
  
## Context  
  
The project requires long-term maintainability.  
  
## Decision  
  
Adopt a Modular Architecture.  
  
Major capabilities become independent modules.  
  
Examples:  
  
- Requirement Intelligence  
- Architecture Recommendation  
- Proposal Generation  
- Presentation Generation  
- SOW Generation  
- BOM Intelligence  
- Knowledge Management  
  
## Reason  
  
Modules can evolve independently.  
  
Testing becomes easier.  
  
Future SaaS deployment becomes simpler.  
  
---  
  
# Decision 008  
  
Decision ID  
  
ATLAS-008  
  
Status  
  
Accepted  
  
## Context  
  
The first release should deliver value quickly.  
  
## Decision  
  
Build a working MVP before implementing advanced features.  
  
Sprint 1 includes:  
  
- Login  
- Project Management  
- Requirement Upload  
- AI Requirement Analysis  
- Clarification Questions  
- Project Storage  
  
Future functionality will be delivered incrementally.  
  
---  
  
# Decision 009  
  
Decision ID  
  
ATLAS-009  
  
Status  
  
Accepted  
  
## Context  
  
Documentation should remain usable regardless of AI coding tools.  
  
## Decision  
  
Keep project documentation AI-vendor neutral.  
  
Only adapter files may contain tool-specific guidance.  
  
Supported coding assistants include:  
  
- Cursor  
- Claude Code  
- Codex  
- Grok  
- GitHub Copilot  
- Gemini  
- Windsurf  
  
Future assistants can be added without modifying the core documentation.  
  
---  
  
# Decision 010  
  
Decision ID  
  
ATLAS-010  
  
Status  
  
Accepted  
  
## Context  
  
Project Atlas is intended to become a commercial SaaS product.  
  
## Decision  
  
Develop locally on a MacBook using Docker Compose while designing the architecture to support future SaaS deployment.  
  
## Benefits  
  
- Faster development  
- Lower cost  
- Easier debugging  
- Smooth transition to cloud deployment  
  
---  
  
# Decision 011  
  
Decision ID  
  
ATLAS-011  
  
Status  
  
Accepted  
  
Date  
  
2026-08-01  
  
## Context  
  
Sprint 1 requires user login and protected project APIs. A full SSO/OAuth provider is not required for the local MVP.  
  
## Decision  
  
Use email/password authentication with bcrypt password hashes and JWT Bearer tokens.  
  
Sprint 1 details:  
  
- `POST /api/auth/login` returns a signed JWT.  
- Protected endpoints require `Authorization: Bearer <token>`.  
- Passwords stored only as `password_hash` (bcrypt).  
- Seed a local demo user via environment variables (no public registration in Sprint 1).  
- `GET /api/auth/me` returns the current user.  
  
## Reason  
  
JWT is simple for a split Next.js + FastAPI Docker setup, avoids session sticky-state, and is easy to replace later with SSO.  
  
## Alternatives Considered  
  
- Server sessions + HTTP-only cookies  
- OAuth / OIDC (Auth0, Azure AD, Keycloak)  
- NextAuth-only with BFF pattern  
  
## Impact  
  
Backend owns auth issuance and validation. Frontend stores the access token for API calls. OAuth/SSO remains a future decision.  
  
## Future Review  
  
Revisit before multi-user collaboration, SaaS multi-tenancy, or enterprise SSO requirements.  
  
---  
  
# Decision 012  
  
Decision ID  
  
ATLAS-012  
  
Status  
  
Accepted  
  
Date  
  
2026-08-01  
  
## Context  
  
Sprint 1 needs a working AI requirement analysis path while remaining provider-independent.  
  
## Decision  
  
Default AI provider for Sprint 1 is OpenAI.  
  
- Env: `OPENAI_API_KEY`, `OPENAI_MODEL` (default `gpt-4o-mini`).  
- All business logic calls an AI abstraction interface (`AIProvider`).  
- OpenAI is the first concrete adapter; Anthropic/Azure/local adapters may be added later without changing services.  
  
## Reason  
  
OpenAI is already referenced in env examples, has strong document-analysis quality for MVP cost, and is the fastest path to a working demo.  
  
## Alternatives Considered  
  
- Anthropic as default  
- Azure OpenAI as default  
- Local LLM only  
  
## Impact  
  
Local development requires an OpenAI key. The abstraction layer remains mandatory.  
  
## Future Review  
  
Revisit when cost, data residency, or customer-preferred providers require a different default.  
  
---  
  
# Decision 013  
  
Decision ID  
  
ATLAS-013  
  
Status  
  
Accepted  
  
Date  
  
2026-08-01  
  
## Context  
  
Requirement uploads (PDF, DOCX, TXT) need durable storage for the local Docker MVP. Object storage is unnecessary for Sprint 1.  
  
## Decision  
  
Store uploaded files on the local filesystem.  
  
- Path: `storage/uploads/` (repo root), mounted into the backend container.  
- DB table `RequirementDocuments.storage_path` stores the relative path.  
- Allowed types: `pdf`, `docx`, `txt`.  
- Max upload size: 10 MB per file.  
  
## Reason  
  
Matches Docker Compose local development, keeps ops simple, and can later swap to S3/Blob behind the same repository interface.  
  
## Alternatives Considered  
  
- PostgreSQL bytea  
- S3 / MinIO from day one  
- Netlify Blobs / cloud object storage  
  
## Impact  
  
Compose must mount a persistent volume or bind mount for `storage/`. Cloud object storage becomes a future decision.  
  
## Future Review  
  
Revisit before SaaS multi-instance deployment or shared storage requirements.  
  
---  
  
# Decision 014  
  
Decision ID  
  
ATLAS-014  
  
Status  
  
Accepted  
  
Date  
  
2026-08-01  
  
## Context  
  
API_STANDARD.md listed write endpoints but omitted reads needed for dashboard/history, and did not define a response envelope.  
  
## Decision  
  
### Response envelope  
  
Success:  
  
```json  
{  
  "success": true,  
  "data": {},  
  "message": null  
}  
```  
  
Error:  
  
```json  
{  
  "success": false,  
  "data": null,  
  "error": {  
    "code": "NOT_FOUND",  
    "message": "Project not found"  
  }  
}  
```  
  
### Additional Sprint 1 endpoints  
  
- `GET /api/auth/me`  
- `GET /api/projects/{id}`  
- `GET /api/projects/{id}/documents`  
- `GET /api/projects/{id}/analysis`  
- `GET /api/projects/{id}/clarifications`  
  
List endpoints return arrays in `data`. Resource endpoints return a single object in `data`.  
  
### Clarification naming  
  
Use plural path `clarifications` for collection GET; keep `POST /api/projects/{id}/clarification` to generate questions.  
  
## Reason  
  
A uniform envelope simplifies frontend handling. Explicit GET routes unblock dashboard and project history without over-fetching.  
  
## Alternatives Considered  
  
- Nested project detail payload only (no separate analysis/clarification GETs)  
- JSON:API  
- Problem Details (RFC 7807) only  
  
## Impact  
  
All FastAPI routes and the Next.js client must follow this envelope. API_STANDARD.md is the source of truth.  
  
## Future Review  
  
Revisit if public partner APIs require JSON:API or RFC 7807 exclusively.  
  
---  
  
## Decision ID: ATLAS-015  
  
## Title  
  
Domain checklist packs for clarification generation  
  
## Status  
  
Accepted  
  
## Date  
  
2026-08-02  
  
## Context  
  
Generic 5–10 clarification questions based only on structured analysis missed Presales-critical Wireless items (floor plan, coverage zones, heatmap/AP sizing) on real opportunities such as SEGI WLAN.  
  
## Decision  
  
1. Store domain checklist packs under `knowledge/checklists/` (e.g. `wireless.md`, `networking.md`).  
2. Detect domains from sales intake + extracted document text + analysis.  
3. Inject matching checklists into the clarification prompt.  
4. Pass original source text (not analysis alone) into clarification generation.  
5. Raise question budget for wireless / multi-domain opportunities (up to ~20).  
6. Mount `knowledge/` into the backend container via `KNOWLEDGE_PATH`.  
  
## Reason  
  
Presales quality depends on domain playbooks. Checklists keep prompts focused while remaining editable without code changes for every question.  
  
## Alternatives Considered  
  
- Hard-code wireless questions only in the prompt (harder to extend)  
- Vector RAG over all knowledge docs in Sprint 1 (deferred)  
- Keep analysis-only clarification input (rejected — loses source facts)  
  
## Impact  
  
ClarificationService, AIProvider adapters, Docker Compose knowledge mount, and `knowledge/checklists/*`.  
  
## Future Review  
  
Optional RAG retrieval when the knowledge corpus grows beyond curated checklist packs.  
  
---  
  
## Decision ID: ATLAS-015a  
  
## Title  
  
Expand domain checklist coverage across Project Atlas solution domains  
  
## Status  
  
Accepted  
  
## Date  
  
2026-08-02  
  
## Context  
  
ATLAS-015 shipped Wireless + basic Networking packs. Presales quality still depended on generic questions for Data Centre, security, storage/HCI/servers, LED/AV, and other domains listed in PROJECT.md.  
  
## Decision  
  
1. Ship curated checklist packs under `knowledge/checklists/` for the program domains, including: Wireless, Networking, Data Centre, Network Security, Cybersecurity, Storage, HCI, Servers, LED, AV, Backup, Virtualization, Cloud, Collaboration, Microsoft, CCTV, Access Control, Structured Cabling, UPS, Digital Signage, and IoT/Smart Building.  
2. Keep keyword detection specific enough to avoid false positives (e.g. avoid bare `led` / `floor plan` triggers).  
3. Inject at most four full checklist packs per clarification run (priority-ordered); list remaining detected domains as light-touch probes.  
4. Scale clarification question budget with detected domain count (up to 18–24 for broad multi-domain deals).  
  
## Impact  
  
Clarification quality improves for multi-domain opportunities without requiring code changes to add new question text — editors can update markdown packs.  
  
---  
  
---  
  
# Phase 2 Decisions (ATLAS-020+)  
  
Full text: [`docs/Phase 2/DECISIONS_PHASE2.md`](../Phase%202/DECISIONS_PHASE2.md) and [`docs/Phase 2/PHASE2_ROADMAP.md`](../Phase%202/PHASE2_ROADMAP.md).  
  
| ID | Title | Status |
|----|-------|--------|
| ATLAS-020 | RKM is canonical business object | Accepted |
| ATLAS-021 | Evidence required; source_type includes document / sales_intake / workshop / clarification_answer | Accepted |
| ATLAS-022 | Human approval required to publish | Accepted |
| ATLAS-023 | Downstream consumes Published RKM only | Accepted |
| ATLAS-024 | Published RKM immutable; Active Draft + Published model | Accepted |
| ATLAS-025 | Phase separation (no architecture/vendors in Phase 2) | Accepted |
| ATLAS-026 | Sprint 1 `/api/*` kept; Phase 2 APIs under `/api/v1/*` | Accepted |
| ATLAS-027 | Phase 2.1 file limits 50MB/file, 200MB/batch; type allow-list | Accepted |
| ATLAS-028 | Phase 2 decision IDs use ATLAS-020+ (retire Decision 011–016) | Accepted |
| ATLAS-029 | OCR / RKM generation are async jobs | Accepted |
| ATLAS-030 | Embeddings / vector DB deferred past Sprint 2.1 | Accepted |

---

# Phase 3 Decisions (ATLAS-031+)

Full text: [`docs/Phase 3/21_PHASE3_DECISIONS.md`](../Phase%203/21_PHASE3_DECISIONS.md).

| ID | Title | Status |
|----|-------|--------|
| ATLAS-031 | Phase 3 APIs under `/api/v1/projects/{id}/…` | Accepted |
| ATLAS-032 | Normalized Phase 3 tables; reuse `projects` (no `solution_projects`) | Accepted |
| ATLAS-033 | Phase 3 decision IDs use ATLAS-031+ (retire ADR-017…024) | Accepted |
| ATLAS-034 | Keep thin architecture MVP until Sprint 3.2 refactor | Accepted |
| ATLAS-035 | Vendor neutrality first | Accepted |
| ATLAS-036 | Requirement / evidence traceability mandatory | Accepted |
| ATLAS-037 | AI cannot approve architecture (human Approver) | Accepted |
| ATLAS-038 | Vendor catalogue data is versioned | Accepted |
| ATLAS-039 | External BOM is evidence, not truth | Accepted |
| ATLAS-040 | Multi-domain support (IT + AV/LED/signage/smart building) | Accepted |
| ATLAS-041 | AI provider independence via abstraction | Accepted |

---  
  
# Future Decision Log  
  
The following areas are expected to require future decisions:  
  
- Enterprise SSO / OAuth provider  
- Multi-tenancy  
- RAG Architecture  
- Vector Database (deferred by ATLAS-030 for Sprint 2.1)  
- Knowledge Synchronisation  
- Cloud object storage (S3/Blob)  
- Cloud Deployment Strategy  
- Licensing Model  
- Pricing Model  
- AI Cost Optimisation  
- Offline Mode  
- Enterprise Security  
- Plugin Framework  
- Marketplace  
- Mobile Application  
- Virus scan product choice (required by Phase 2 pipeline)  
- Queue / worker implementation for ATLAS-029  

---  
  
# Decision Governance  
  
Every significant architectural or product decision should be recorded before implementation.  
  
Each decision should include:  
  
- Business context  
- Technical context  
- Decision  
- Rationale  
- Alternatives  
- Impact  
- Review trigger  
  
This document should be updated whenever a decision materially affects the platform's architecture, scalability, maintainability or product direction.  
