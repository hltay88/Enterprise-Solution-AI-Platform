# DATABASE.md  
  
Sprint 1 Database  
  
Related: `docker/postgres/init/`, ATLAS-003  
  
---  
  
## Conventions  
  
- Table names: `snake_case`  
- Primary keys: `UUID` (`gen_random_uuid()` via `pgcrypto`)  
- Timestamps: `TIMESTAMPTZ`  
  
Schema is applied on first Postgres container init via:  
  
`docker/postgres/init/*.sql`  
  
---  
  
## users  
  
| Column | Type | Notes |  
|--------|------|-------|  
| id | UUID PK | default `gen_random_uuid()` |  
| name | TEXT | required |  
| email | TEXT | required, unique |  
| password_hash | TEXT | bcrypt hash |  
| created_at | TIMESTAMPTZ | default `NOW()` |  
  
---  
  
## projects  
  
| Column | Type | Notes |  
|--------|------|-------|  
| id | UUID PK | |  
| user_id | UUID FK → users | ON DELETE CASCADE |  
| project_name | TEXT | required |  
| customer | TEXT | |  
| industry | TEXT | |  
| status | TEXT | default `draft` |  
| created_at | TIMESTAMPTZ | |  
| updated_at | TIMESTAMPTZ | |  
  
---  
  
## requirement_documents  
  
| Column | Type | Notes |  
|--------|------|-------|  
| id | UUID PK | |  
| project_id | UUID FK → projects | ON DELETE CASCADE |  
| filename | TEXT | |  
| file_type | TEXT | `pdf` / `docx` / `txt` |  
| storage_path | TEXT | relative path under storage |  
| extracted_text | TEXT | plain text extracted on upload |  
| uploaded_at | TIMESTAMPTZ | |  
  
---  
  
## requirement_analysis  
  
| Column | Type | Notes |  
|--------|------|-------|  
| id | UUID PK | |  
| project_id | UUID FK → projects | ON DELETE CASCADE |  
| business_objectives | TEXT | |  
| functional_requirements | TEXT | |  
| non_functional_requirements | TEXT | |  
| assumptions | TEXT | |  
| risks | TEXT | |  
| analysis_json | JSONB | full structured analysis |  
| created_at | TIMESTAMPTZ | |  
  
---  
  
## clarification_questions  
  
| Column | Type | Notes |  
|--------|------|-------|  
| id | UUID PK | |  
| project_id | UUID FK → projects | ON DELETE CASCADE |  
| question | TEXT | |  
| status | TEXT | default `open` |  
| created_at | TIMESTAMPTZ | |  
  
---  
  
## Local verification  
  
```bash  
docker compose -f docker/docker-compose.yml --env-file .env up -d  
./docker/postgres/check-ready.sh  
```  
  
Init SQL runs only when the `atlas-postgres-data` volume is first created.  
To re-apply schema from scratch:  
  
```bash  
docker compose -f docker/docker-compose.yml --env-file .env down -v  
docker compose -f docker/docker-compose.yml --env-file .env up -d  
```  
