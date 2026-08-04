#!/usr/bin/env bash
# Start Project Atlas locally via Docker Compose (Mac / Linux).
# Usage (from anywhere):
#   ./start-atlas.sh
# Optional: SKIP_BROWSER=1 ./start-atlas.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

COMPOSE_FILE="docker/docker-compose.yml"
ENV_FILE=".env"
ENV_EXAMPLE="env.example.md"

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: Docker is not installed or not on PATH."
  echo "Install/start Docker Desktop, then retry."
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Error: Docker daemon is not running."
  echo "Open Docker Desktop and wait until it is ready, then retry."
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  if [[ ! -f "$ENV_EXAMPLE" ]]; then
    echo "Error: missing $ENV_EXAMPLE; cannot create $ENV_FILE."
    exit 1
  fi
  # Strip Markdown heading / comment-only guidance lines that are not KEY=VALUE.
  # env.example.md is mostly already dotenv-compatible KEY=VALUE lines.
  grep -E '^[A-Za-z_][A-Za-z0-9_]*=' "$ENV_EXAMPLE" >"$ENV_FILE" || true
  if [[ ! -s "$ENV_FILE" ]]; then
    cp "$ENV_EXAMPLE" "$ENV_FILE"
  fi
  echo "Created $ENV_FILE from $ENV_EXAMPLE (edit secrets/AI keys as needed)."
fi

echo "Starting Project Atlas (db + backend + frontend)..."
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build

if [[ -x "./docker/postgres/check-ready.sh" ]]; then
  echo "Waiting for Postgres..."
  ./docker/postgres/check-ready.sh
fi

echo "Waiting for backend health..."
for _ in $(seq 1 60); do
  if curl -sf "http://localhost:8000/api/health" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

if ! curl -sf "http://localhost:8000/api/health" >/dev/null 2>&1; then
  echo "Warning: backend health check did not succeed yet."
  echo "Check: docker compose -f $COMPOSE_FILE --env-file $ENV_FILE logs backend"
else
  echo "Backend is healthy."
fi

echo "Waiting for frontend..."
for _ in $(seq 1 60); do
  if curl -sf "http://localhost:3000" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

echo
echo "Project Atlas is up:"
echo "  Frontend: http://localhost:3000"
echo "  API:      http://localhost:8000/api/health"
echo "  Login:    demo@example.com / changeme"
echo
echo "Stop later with: ./stop-atlas.sh"

if [[ "${SKIP_BROWSER:-0}" != "1" ]]; then
  if command -v open >/dev/null 2>&1; then
    open "http://localhost:3000"
  elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "http://localhost:3000" >/dev/null 2>&1 || true
  fi
fi
