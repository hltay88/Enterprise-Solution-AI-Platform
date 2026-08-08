# CHANGELOG_PHASE3.md

## Version 0.3.0 — Architecture Recommendation MVP (Stage G)

### Added
- `architecture_models` table + schema bootstrap
- `POST /api/v1/projects/{id}/architecture/generate` (Published RKM only)
- `GET /api/v1/projects/{id}/architecture`
- Local / Gemini / OpenAI `recommend_architecture` providers
- Frontend `ArchitecturePanel`
- Audit event `architecture.generate`
