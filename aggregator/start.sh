#!/usr/bin/env bash
# Startup script for Render: download the latest deals.db, report freshness,
# then start uvicorn.
set -euo pipefail

DATABASE_PATH="${DATABASE_PATH:-/app/data/deals.db}"
MAX_DB_STALENESS_HOURS="${MAX_DB_STALENESS_HOURS:-18}"
DOWNLOAD_URL="https://github.com/lifan-builds/snow-deal-data/releases/download/latest-data/deals.db"

DB_DIR="$(dirname "$DATABASE_PATH")"
mkdir -p "$DB_DIR"

log() {
    echo "[start.sh] $*"
}

warn() {
    echo "[start.sh] WARNING: $*" >&2
}

check_db_file() {
    local db_path="$1"
    python3 - "$db_path" <<'PY'
import sqlite3
import sys

db_path = sys.argv[1]
try:
    conn = sqlite3.connect(db_path)
    cur = conn.execute("PRAGMA integrity_check")
    row = cur.fetchone()
    conn.close()
    if not row or row[0].lower() != "ok":
        raise RuntimeError(f"integrity_check returned {row!r}")
except Exception as exc:
    print(exc)
    raise SystemExit(1)
PY
}

report_db_freshness() {
    local db_path="$1"
    python3 - "$db_path" "$MAX_DB_STALENESS_HOURS" <<'PY'
import sqlite3
import sys
from datetime import datetime, timezone

db_path = sys.argv[1]
threshold_hours = float(sys.argv[2])

try:
    conn = sqlite3.connect(db_path)
    deal_count = conn.execute("SELECT COUNT(*) FROM deals").fetchone()[0]
    row = conn.execute("SELECT MAX(scraped_at) FROM deals").fetchone()
    conn.close()
except Exception as exc:
    print(f"Unable to inspect freshness: {exc}")
    raise SystemExit(1)

latest = row[0] if row else None
if not latest:
    print(f"Database has no deals yet (count={deal_count}).")
    raise SystemExit(0)

latest_dt = datetime.fromisoformat(latest)
if latest_dt.tzinfo is None:
    latest_dt = latest_dt.replace(tzinfo=timezone.utc)
now = datetime.now(timezone.utc)
age_hours = (now - latest_dt).total_seconds() / 3600
status = "fresh" if age_hours <= threshold_hours else "stale"
print(
    f"Database freshness: {status} "
    f"(latest={latest_dt.isoformat()}, age_hours={age_hours:.1f}, deals={deal_count})"
)
if age_hours > threshold_hours:
    raise SystemExit(2)
PY
}

download_latest_db() {
    local tmp_path
    tmp_path="$(mktemp "${DB_DIR}/deals.db.tmp.XXXXXX")"
    trap 'rm -f "$tmp_path"' RETURN

    log "Downloading latest deals.db from GitHub Releases..."
    curl -fsSL "$DOWNLOAD_URL" -o "$tmp_path"

    if [ ! -s "$tmp_path" ]; then
        warn "Downloaded deals.db is empty. Keeping existing database if present."
        return 1
    fi

    if ! check_db_file "$tmp_path"; then
        warn "Downloaded deals.db is not a valid SQLite database. Keeping existing database if present."
        return 1
    fi

    mv "$tmp_path" "$DATABASE_PATH"
    log "Downloaded deals.db ($(wc -c < "$DATABASE_PATH") bytes)"
    return 0
}

if ! download_latest_db; then
    if [ -f "$DATABASE_PATH" ]; then
        log "Using existing database at $DATABASE_PATH"
    else
        warn "Could not download deals.db and no local database exists. Starting with an empty database."
    fi
fi

if [ -f "$DATABASE_PATH" ] && check_db_file "$DATABASE_PATH"; then
    if ! report_db_freshness "$DATABASE_PATH"; then
        warn "Database is older than ${MAX_DB_STALENESS_HOURS}h."
    fi
fi

log "Starting uvicorn..."
exec uvicorn aggregator.web.app:create_app --factory --host 0.0.0.0 --port "${PORT:-8000}"
