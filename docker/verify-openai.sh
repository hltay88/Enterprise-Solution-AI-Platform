#!/usr/bin/env sh
# Quick check that the backend container has a usable OpenAI key.
# Run from the repo root:
#   ./docker/verify-openai.sh

set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)

compose() {
  docker compose \
    -f "$ROOT_DIR/docker/docker-compose.yml" \
    --env-file "$ROOT_DIR/.env" \
    "$@"
}

echo "== backend env (key metadata only) =="
compose exec -T backend sh -c '
if [ -z "${OPENAI_API_KEY:-}" ]; then
  echo "KEY_MISSING"
  exit 1
fi
echo "KEY_PREFIX=${OPENAI_API_KEY%${OPENAI_API_KEY#???????}}"
echo "KEY_LENGTH=${#OPENAI_API_KEY}"
echo "MODEL=${OPENAI_MODEL:-unset}"
'

echo "== recent backend logs =="
docker logs atlas-backend --tail 40
