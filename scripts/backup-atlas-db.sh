#!/usr/bin/env bash
# Backup / restore helpers for local Atlas Postgres (Sprint 5.5).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT_DIR="${ATLAS_BACKUP_DIR:-$ROOT/backups}"
CONTAINER="${ATLAS_DB_CONTAINER:-atlas-db}"
DB_USER="${ATLAS_DB_USER:-atlas}"
DB_NAME="${ATLAS_DB_NAME:-atlas}"

mkdir -p "$OUT_DIR"

cmd="${1:-backup}"

if [[ "$cmd" == "backup" ]]; then
  file="$OUT_DIR/atlas-$STAMP.sql.gz"
  echo "Backing up $DB_NAME from $CONTAINER -> $file"
  docker exec "$CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$file"
  echo "OK: $file"
  exit 0
fi

if [[ "$cmd" == "restore" ]]; then
  file="${2:-}"
  if [[ -z "$file" || ! -f "$file" ]]; then
    echo "Usage: $0 restore <backup.sql.gz>" >&2
    exit 1
  fi
  echo "Restoring $file into $CONTAINER/$DB_NAME (destructive)"
  gunzip -c "$file" | docker exec -i "$CONTAINER" psql -U "$DB_USER" -d "$DB_NAME"
  echo "OK: restore complete"
  exit 0
fi

echo "Usage: $0 [backup|restore <file>]" >&2
exit 1
