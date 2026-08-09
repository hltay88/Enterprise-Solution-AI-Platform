# Document Generation Architecture

Flow:
Published RKM → Approved Architecture → Validated Solution → Document Data Model → Content Planning → AI Drafting → Validation → Human Review → Approval → Rendering → Export

Layers:
- Domain
- Application
- Infrastructure
- API
- UI

Rules:
- Domain logic must not depend directly on a specific AI provider.
- AI output must be schema validated.
- Source traceability must be retained.
- Draft and approved content are separate states.
- Rendering must use approved content and a versioned template.
