#!/usr/bin/env bash
# Verify Atlas Postgres is healthy and Sprint 1 schema is present.
# Usage (repo root, Docker Desktop running):
#   ./docker/postgres/check-ready.sh
# Optional env: POSTGRES_USER POSTGRES_DB (defaults: atlas)

set -euo pipefail

CONTAINER_NAME="${CONTAINER_NAME:-atlas-db}"
POSTGRES_USER="${POSTGRES_USER:-atlas}"
POSTGRES_DB="${POSTGRES_DB:-atlas}"
RETRIES="${RETRIES:-30}"
SLEEP_SECONDS="${SLEEP_SECONDS:-2}"

REQUIRED_TABLES=(
  users
  projects
  requirement_documents
  requirement_analysis
  clarification_questions
)

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker CLI not found. Start Docker Desktop and retry."
  exit 1
fi

if ! docker inspect "$CONTAINER_NAME" >/dev/null 2>&1; then
  echo "ERROR: container '$CONTAINER_NAME' not found."
  echo "Start it with:"
  echo "  docker compose -f docker/docker-compose.yml --env-file .env up -d"
  exit 1
fi

echo "Waiting for Postgres readiness in '$CONTAINER_NAME'..."

for ((i = 1; i <= RETRIES; i++)); do
  if docker exec "$CONTAINER_NAME" pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; then
    echo "pg_isready: OK"
    break
  fi
  if ((i == RETRIES)); then
    echo "ERROR: Postgres did not become ready within $((RETRIES * SLEEP_SECONDS))s."
    exit 1
  fi
  sleep "$SLEEP_SECONDS"
done

echo "Checking Sprint 1 tables..."

missing=0
for table in "${REQUIRED_TABLES[@]}"; do
  exists="$(
    docker exec -e PGPASSWORD="${POSTGRES_PASSWORD:-atlas}" "$CONTAINER_NAME" \
      psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc \
      "SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '${table}';"
  )"
  if [[ "$exists" == "1" ]]; then
    echo "  OK  $table"
  else
    echo "  MISSING  $table"
    missing=1
  fi
done

if ((missing != 0)); then
  echo
  echo "ERROR: Schema incomplete."
  echo "Init scripts run only on first volume create. Reset with:"
  echo "  docker compose -f docker/docker-compose.yml --env-file .env down -v"
  echo "  docker compose -f docker/docker-compose.yml --env-file .env up -d"
  exit 1
fi

echo
echo "PostgreSQL configured and ready."
