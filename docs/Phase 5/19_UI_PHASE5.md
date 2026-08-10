# UI Phase 5

Screens (named routes for Phase 5 portable completion):

| Screen | Route |
|--------|--------|
| Enterprise Knowledge Library | `/knowledge` |
| Knowledge Upload/Review + Detail/Version | `/knowledge`, `/knowledge/[id]` |
| Retrieval Explorer | `/knowledge/retrieve` |
| Agent Workspace | Project panel `#agent-workspace-panel` |
| Solution Review | `/solutions` |
| Collaboration/Comments | Project panel `#collaboration-panel` |
| Approval Center | `/approvals` |
| Audit Viewer | `/governance` |
| Tenant Administration | `/tenants` |
| Usage Dashboard | `/usage` |

Always show evidence, confidence, source/version and AI-generated vs human-authored content where those signals exist in the API payload.
