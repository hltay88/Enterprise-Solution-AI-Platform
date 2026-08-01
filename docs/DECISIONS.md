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
  
# Future Decision Log  
  
The following areas are expected to require future decisions:  
  
- Authentication Provider  
- Multi-tenancy  
- RAG Architecture  
- Vector Database  
- Knowledge Synchronisation  
- Cloud Deployment Strategy  
- Licensing Model  
- Pricing Model  
- AI Cost Optimisation  
- Offline Mode  
- Enterprise Security  
- Plugin Framework  
- Marketplace  
- Mobile Application  
  
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
