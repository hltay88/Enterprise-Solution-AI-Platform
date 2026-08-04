#!/usr/bin/env bash
# Stop Project Atlas Docker Compose stack (keeps DB volume / data).
# Usage:
#   ./stop-atlas.sh
# To also wipe the local Postgres volume:
#   ./stop-atlas.sh --wipe

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

COMPOSE_FILE="docker/docker-compose.yml"
ENV_FILE=".env"

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: Docker is not installed or not on PATH."
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Error: Docker daemon is not running."
  echo "Open Docker Desktop and wait until it is ready, then retry."
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Warning: $ENV_FILE not found; Compose will use defaults where possible."
  ENV_ARGS=()
else
  ENV_ARGS=(--env-file "$ENV_FILE")
fi

if [[ "${1:-}" == "--wipe" ]]; then
  echo "Stopping Project Atlas and removing volumes (DB data will be deleted)..."
  docker compose -f "$COMPOSE_FILE" "${ENV_ARGS[@]}" down -v
else
  echo "Stopping Project Atlas (DB data kept)..."
  docker compose -f "$COMPOSE_FILE" "${ENV_ARGS[@]}" down
fi

echo "Stopped. Start again with: ./start-atlas.sh"
