#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/var/www/generation-justice}"
DATABASE_PATH="${DATABASE_PATH:-$APP_DIR/data/generation_justice.db}"
BACKUP_DIR="${BACKUP_DIR:-$APP_DIR/backups}"
STAMP="$(date +%Y%m%d-%H%M%S)"

mkdir -p "$BACKUP_DIR"

if command -v sqlite3 >/dev/null 2>&1; then
    sqlite3 "$DATABASE_PATH" ".backup '$BACKUP_DIR/generation_justice-$STAMP.db'"
else
    cp "$DATABASE_PATH" "$BACKUP_DIR/generation_justice-$STAMP.db"
fi

echo "Backup created: $BACKUP_DIR/generation_justice-$STAMP.db"
