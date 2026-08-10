# Sprint 5.5 — SaaS / Multi-tenant foundation (implementation notes)

Status: **implemented** (Mac-local development target).

## Scope delivered

- `tenants` + `tenant_memberships` tables; demo tenant `atlas-demo`
- JWT `tid` claim + `user.active_tenant_id` session context
- `projects.tenant_id` stamped on create; list/get filtered by active tenant
- Knowledge create stamps tenant; list + retrieval see platform (`NULL`) **or** active tenant
- Usage APIs scoped by tenant; agent/retrieval usage records stamp tenant
- Tenant APIs: `GET /tenants`, `/tenants/current`, members list/add
- UI: `/tenants` admin page; Tenant nav link
- Rate-limit middleware (`ATLAS_RATE_LIMIT_PER_MINUTE`, default off)
- OIDC config stubs (`ATLAS_OIDC_*`, disabled by default)
- Billing abstraction: `NoopBillingProvider`
- Backup helper: `scripts/backup-atlas-db.sh`
- Schema: `docker/postgres/init/16_phase5_tenancy.sql` + `ensure_schema()`

## Guarantees

- Cross-tenant knowledge retrieval excluded by SQL filter
- Projects owned by other users remain inaccessible (existing owner model)
- Mac demo path: login auto-ensures demo tenant membership

## Tests

- `backend/tests/test_tenancy_sprint55.py`
- Full suite must remain green

## Ops

```bash
./scripts/backup-atlas-db.sh backup
./scripts/backup-atlas-db.sh restore backups/atlas-YYYYMMDD-HHMMSS.sql.gz
```

## Out of scope / later

- Full OIDC/SAML IdP go-live
- Real billing provider
- Shared project membership across many users in a tenant
- Multi-region / WORM audit
