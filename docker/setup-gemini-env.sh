#!/usr/bin/env sh
# Configure repo-root .env for Gemini and recreate backend/frontend.
# Usage (from repo root):
#   GEMINI_API_KEY='your_key' ./docker/setup-gemini-env.sh
# or:
#   ./docker/setup-gemini-env.sh   # prompts for the key

set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

if [ ! -f .env ]; then
  cp env.example.md .env
  echo "Created .env from env.example.md"
fi

if [ -z "${GEMINI_API_KEY:-}" ]; then
  printf "Paste your GEMINI_API_KEY (input hidden): "
  stty -echo
  read -r GEMINI_API_KEY
  stty echo
  printf "\n"
fi

if [ -z "${GEMINI_API_KEY:-}" ]; then
  echo "GEMINI_API_KEY is empty. Stopping."
  exit 1
fi

# Upsert values without quotes / spaces
if grep -q '^GEMINI_API_KEY=' .env; then
  sed -i.bak "s|^GEMINI_API_KEY=.*|GEMINI_API_KEY=${GEMINI_API_KEY}|" .env
else
  printf '\nGEMINI_API_KEY=%s\n' "$GEMINI_API_KEY" >> .env
fi

if grep -q '^GEMINI_MODEL=' .env; then
  sed -i.bak 's|^GEMINI_MODEL=.*|GEMINI_MODEL=gemini-flash-latest|' .env
else
  echo 'GEMINI_MODEL=gemini-flash-latest' >> .env
fi

if grep -q '^ATLAS_AI_PROVIDER=' .env; then
  sed -i.bak 's|^ATLAS_AI_PROVIDER=.*|ATLAS_AI_PROVIDER=auto|' .env
else
  echo 'ATLAS_AI_PROVIDER=auto' >> .env
fi

# Avoid empty GEMINI_MODEL= wiping Compose defaults via env_file
sed -i.bak '/^GEMINI_MODEL=$/d' .env || true

rm -f .env.bak

KEY_LEN=${#GEMINI_API_KEY}
unset GEMINI_API_KEY
echo "Wrote GEMINI_API_KEY to .env (length=${KEY_LEN})"
echo "Set GEMINI_MODEL=gemini-flash-latest and ATLAS_AI_PROVIDER=auto"

echo "Pulling latest main..."
git pull origin main

echo "Recreating backend/frontend with Gemini config..."
docker compose \
  -f "$ROOT_DIR/docker/docker-compose.yml" \
  --env-file "$ROOT_DIR/.env" \
  up -d --build --force-recreate backend frontend

echo "Verifying AI env inside container..."
"$ROOT_DIR/docker/verify-ai.sh"

echo
echo "Expected success markers:"
echo "  GEMINI_KEY_PREFIX=... / GEMINI_KEY_OK"
echo "  GEMINI_MODEL=gemini-flash-latest"
echo "  logs: Gemini configured: model=gemini-flash-latest"
echo
echo "Then hard-refresh the project page and click Run analysis."
