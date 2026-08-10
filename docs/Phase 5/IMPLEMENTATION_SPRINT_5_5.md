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
- OIDC adapter (`ATLAS_OIDC_ENABLED`, `ATLAS_OIDC_ISSUER=mock://local`) +
  `/api/auth/oidc/start|mock/authorize|exchange`
- Billing: `MeteredBillingProvider` (default) / `NoopBillingProvider`
  (`ATLAS_BILLING_PROVIDER`)
- Backup helper: `scripts/backup-atlas-db.sh`
- Schema: `docker/postgres/init/16_phase5_tenancy.sql` + `ensure_schema()`
- Security release-gate + golden eval tests (Phase 5 closeout)

## Guarantees

- Cross-tenant knowledge retrieval excluded by SQL filter
- Projects owned by other users remain inaccessible (existing owner model)
- Mac demo path: login auto-ensures demo tenant membership

## Tests

- `backend/tests/test_tenancy_sprint55.py`
- `backend/tests/test_phase5_security_gates.py`
- `backend/tests/test_phase5_golden_eval.py`
- Full suite must remain green

## Ops

```bash
./scripts/backup-atlas-db.sh backup
./scripts/backup-atlas-db.sh restore backups/atlas-YYYYMMDD-HHMMSS.sql.gz
```

## Portable completion notes

- Mock OIDC is sufficient for Phase 5 identity closeout; live token exchange
  against a real issuer remains optional ops work outside this pack.
- Metered billing estimates costs for observability; vendor settlement is out of scope.
