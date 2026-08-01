#!/usr/bin/env sh
# Quick check that the backend container has usable AI keys.
# Run from the repo root:
#   ./docker/verify-ai.sh

set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
COMPOSE="docker compose -f ${ROOT_DIR}/docker/docker-compose.yml --env-file ${ROOT_DIR}/.env"

echo "== backend AI env (key metadata only) =="
$COMPOSE exec -T backend sh -c '
echo "ATLAS_AI_PROVIDER=${ATLAS_AI_PROVIDER:-unset}"
echo "GEMINI_MODEL=${GEMINI_MODEL:-unset}"
echo "OPENAI_MODEL=${OPENAI_MODEL:-unset}"
if [ -n "${GEMINI_API_KEY:-}" ]; then
  echo "GEMINI_KEY_PREFIX=${GEMINI_API_KEY%${GEMINI_API_KEY#????}}"
  echo "GEMINI_KEY_LENGTH=${#GEMINI_API_KEY}"
else
  echo "GEMINI_KEY_MISSING"
fi
if [ -n "${OPENAI_API_KEY:-}" ]; then
  echo "OPENAI_KEY_PREFIX=${OPENAI_API_KEY%${OPENAI_API_KEY#???????}}"
  echo "OPENAI_KEY_LENGTH=${#OPENAI_API_KEY}"
else
  echo "OPENAI_KEY_MISSING"
fi
'

echo "== recent backend logs =="
docker logs atlas-backend --tail 50
