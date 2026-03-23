"""Auth database — invite codes, sessions, events.

Uses Turso (cloud SQLite) when TURSO_URL is set, otherwise falls back
to a local SQLite file (auth.db) for development.
"""

from __future__ import annotations

import logging
import os
import secrets
from datetime import datetime, timedelta

log = logging.getLogger(__name__)

TURSO_URL = os.environ.get("TURSO_URL", "")
TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN", "")

AUTH_SCHEMA = """\
CREATE TABLE IF NOT EXISTS invite_codes (
    code       TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    max_uses   INTEGER NOT NULL DEFAULT 5
);

CREATE TABLE IF NOT EXISTS sessions (
    token       TEXT PRIMARY KEY,
    invite_code TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT    NOT NULL,
    session    TEXT,
    deal_url   TEXT,
    deal_name  TEXT,
    store      TEXT,
    category   TEXT,
    metadata   TEXT,
    created_at TEXT    NOT NULL
);
"""

# ---------------------------------------------------------------------------
# Backend abstraction — Turso (libsql) vs local aiosqlite
# ---------------------------------------------------------------------------

_turso_client = None


def _use_turso() -> bool:
    return bool(TURSO_URL)


async def _get_turso():
    """Return a reusable Turso client (created on first call)."""
    global _turso_client
    if _turso_client is None:
        import libsql_client
        _turso_client = libsql_client.create_client(
            url=TURSO_URL,
            auth_token=TURSO_AUTH_TOKEN,
        )
    return _turso_client


async def _turso_execute(sql: str, params: tuple = ()) -> list:
    """Execute a query on Turso and return rows as list of tuples."""
    client = await _get_turso()
    rs = await client.execute(sql, params)
    return rs.rows


async def _turso_execute_many(statements: list[tuple[str, tuple]]) -> None:
    """Execute multiple statements on Turso in a batch."""
    client = await _get_turso()
    from libsql_client import Statement
    batch = [Statement(sql, params) for sql, params in statements]
    await client.batch(batch)


async def _local_path():
    """Return the local auth.db path."""
    from pathlib import Path
    return Path(os.environ.get("AUTH_DB_PATH",
                               Path(__file__).resolve().parent.parent / "auth.db"))


# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------

async def init_auth_db() -> None:
    """Create auth tables if they don't exist."""
    if _use_turso():
        client = await _get_turso()
        for stmt in AUTH_SCHEMA.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                await client.execute(stmt)
        log.info("Auth DB initialized (Turso: %s)", TURSO_URL)
    else:
        import aiosqlite
        db_path = await _local_path()
        async with aiosqlite.connect(db_path) as db:
            await db.executescript(AUTH_SCHEMA)
            await db.commit()
        log.info("Auth DB initialized (local: %s)", db_path)


# ---------------------------------------------------------------------------
# Invite codes
# ---------------------------------------------------------------------------

async def create_invite_codes(codes: list[str], max_uses: int = 5) -> int:
    """Insert invite codes. Returns count created."""
    now = datetime.now().isoformat()
    created = 0

    if _use_turso():
        for code in codes:
            try:
                await _turso_execute(
                    "INSERT INTO invite_codes (code, created_at, max_uses) VALUES (?, ?, ?)",
                    (code, now, max_uses),
                )
                created += 1
            except Exception:
                pass  # duplicate
    else:
        import aiosqlite
        db_path = await _local_path()
        async with aiosqlite.connect(db_path) as db:
            for code in codes:
                try:
                    await db.execute(
                        "INSERT INTO invite_codes (code, created_at, max_uses) VALUES (?, ?, ?)",
                        (code, now, max_uses),
                    )
                    created += 1
                except aiosqlite.IntegrityError:
                    pass
            await db.commit()

    return created


async def validate_invite_code(code: str) -> bool:
    """Check if an invite code is valid and under its max_uses limit."""
    if _use_turso():
        rows = await _turso_execute(
            "SELECT max_uses FROM invite_codes WHERE code = ?", (code,)
        )
        if not rows:
            return False
        max_uses = rows[0][0]
        count_rows = await _turso_execute(
            "SELECT COUNT(*) FROM sessions WHERE invite_code = ?", (code,)
        )
        use_count = count_rows[0][0]
        return use_count < max_uses
    else:
        import aiosqlite
        db_path = await _local_path()
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute(
                "SELECT max_uses FROM invite_codes WHERE code = ?", (code,)
            )
            row = await cursor.fetchone()
            if not row:
                return False
            max_uses = row[0]
            cursor = await db.execute(
                "SELECT COUNT(*) FROM sessions WHERE invite_code = ?", (code,)
            )
            use_count = (await cursor.fetchone())[0]
            return use_count < max_uses


async def record_code_use(code: str) -> None:
    """Record that an invite code was used (insert a session row for counting)."""
    now = datetime.now().isoformat()
    token = secrets.token_urlsafe(16)  # just for tracking, not used as session

    if _use_turso():
        await _turso_execute(
            "INSERT INTO sessions (token, invite_code, created_at) VALUES (?, ?, ?)",
            (token, code, now),
        )
    else:
        import aiosqlite
        db_path = await _local_path()
        async with aiosqlite.connect(db_path) as db:
            await db.execute(
                "INSERT INTO sessions (token, invite_code, created_at) VALUES (?, ?, ?)",
                (token, code, now),
            )
            await db.commit()


async def list_invite_codes() -> list[dict]:
    """Return all invite codes with usage counts."""
    if _use_turso():
        rows = await _turso_execute(
            "SELECT ic.code, ic.created_at, ic.max_uses, COUNT(s.token) AS use_count "
            "FROM invite_codes ic "
            "LEFT JOIN sessions s ON s.invite_code = ic.code "
            "GROUP BY ic.code "
            "ORDER BY ic.created_at"
        )
        return [
            {"code": r[0], "created_at": r[1], "max_uses": r[2], "use_count": r[3]}
            for r in rows
        ]
    else:
        import aiosqlite
        db_path = await _local_path()
        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT ic.code, ic.created_at, ic.max_uses, COUNT(s.token) AS use_count "
                "FROM invite_codes ic "
                "LEFT JOIN sessions s ON s.invite_code = ic.code "
                "GROUP BY ic.code "
                "ORDER BY ic.created_at"
            )
            rows = await cursor.fetchall()
        return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Events / analytics
# ---------------------------------------------------------------------------

async def log_event(
    event_type: str,
    session: str | None = None,
    deal_url: str | None = None,
    deal_name: str | None = None,
    store: str | None = None,
    category: str | None = None,
    metadata: str | None = None,
) -> None:
    """Log a user event (page view, click, filter, etc.)."""
    now = datetime.now().isoformat()

    if _use_turso():
        await _turso_execute(
            "INSERT INTO events (event_type, session, deal_url, deal_name, store, category, metadata, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (event_type, session, deal_url, deal_name, store, category, metadata, now),
        )
    else:
        import aiosqlite
        db_path = await _local_path()
        async with aiosqlite.connect(db_path) as db:
            await db.execute(
                "INSERT INTO events (event_type, session, deal_url, deal_name, store, category, metadata, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (event_type, session, deal_url, deal_name, store, category, metadata, now),
            )
            await db.commit()


async def get_click_stats(days: int = 7) -> dict:
    """Get click-through statistics for the admin dashboard."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()

    if _use_turso():
        by_type = [
            {"event_type": r[0], "cnt": r[1]}
            for r in await _turso_execute(
                "SELECT event_type, COUNT(*) AS cnt FROM events "
                "WHERE created_at >= ? GROUP BY event_type ORDER BY cnt DESC",
                (cutoff,),
            )
        ]
        clicks_by_store = [
            {"store": r[0], "cnt": r[1]}
            for r in await _turso_execute(
                "SELECT store, COUNT(*) AS cnt FROM events "
                "WHERE event_type = 'click' AND created_at >= ? AND store IS NOT NULL "
                "GROUP BY store ORDER BY cnt DESC",
                (cutoff,),
            )
        ]
        top_deals = [
            {"deal_name": r[0], "store": r[1], "deal_url": r[2], "cnt": r[3]}
            for r in await _turso_execute(
                "SELECT deal_name, store, deal_url, COUNT(*) AS cnt FROM events "
                "WHERE event_type = 'click' AND created_at >= ? AND deal_name IS NOT NULL "
                "GROUP BY deal_url ORDER BY cnt DESC LIMIT 20",
                (cutoff,),
            )
        ]
        clicks_by_day = [
            {"day": r[0], "cnt": r[1]}
            for r in await _turso_execute(
                "SELECT DATE(created_at) AS day, COUNT(*) AS cnt FROM events "
                "WHERE event_type = 'click' AND created_at >= ? "
                "GROUP BY day ORDER BY day",
                (cutoff,),
            )
        ]
        views_by_day = [
            {"day": r[0], "cnt": r[1]}
            for r in await _turso_execute(
                "SELECT DATE(created_at) AS day, COUNT(*) AS cnt FROM events "
                "WHERE event_type = 'page_view' AND created_at >= ? "
                "GROUP BY day ORDER BY day",
                (cutoff,),
            )
        ]
        rows = await _turso_execute(
            "SELECT COUNT(DISTINCT session) AS cnt FROM events "
            "WHERE created_at >= ? AND session IS NOT NULL",
            (cutoff,),
        )
        unique_sessions = rows[0][0] if rows else 0
        filter_usage = [
            {"metadata": r[0], "cnt": r[1]}
            for r in await _turso_execute(
                "SELECT metadata, COUNT(*) AS cnt FROM events "
                "WHERE event_type = 'filter' AND created_at >= ? AND metadata IS NOT NULL "
                "GROUP BY metadata ORDER BY cnt DESC LIMIT 15",
                (cutoff,),
            )
        ]
    else:
        import aiosqlite
        db_path = await _local_path()
        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row

            cursor = await db.execute(
                "SELECT event_type, COUNT(*) AS cnt FROM events "
                "WHERE created_at >= ? GROUP BY event_type ORDER BY cnt DESC",
                (cutoff,),
            )
            by_type = [dict(r) for r in await cursor.fetchall()]

            cursor = await db.execute(
                "SELECT store, COUNT(*) AS cnt FROM events "
                "WHERE event_type = 'click' AND created_at >= ? AND store IS NOT NULL "
                "GROUP BY store ORDER BY cnt DESC",
                (cutoff,),
            )
            clicks_by_store = [dict(r) for r in await cursor.fetchall()]

            cursor = await db.execute(
                "SELECT deal_name, store, deal_url, COUNT(*) AS cnt FROM events "
                "WHERE event_type = 'click' AND created_at >= ? AND deal_name IS NOT NULL "
                "GROUP BY deal_url ORDER BY cnt DESC LIMIT 20",
                (cutoff,),
            )
            top_deals = [dict(r) for r in await cursor.fetchall()]

            cursor = await db.execute(
                "SELECT DATE(created_at) AS day, COUNT(*) AS cnt FROM events "
                "WHERE event_type = 'click' AND created_at >= ? "
                "GROUP BY day ORDER BY day",
                (cutoff,),
            )
            clicks_by_day = [dict(r) for r in await cursor.fetchall()]

            cursor = await db.execute(
                "SELECT DATE(created_at) AS day, COUNT(*) AS cnt FROM events "
                "WHERE event_type = 'page_view' AND created_at >= ? "
                "GROUP BY day ORDER BY day",
                (cutoff,),
            )
            views_by_day = [dict(r) for r in await cursor.fetchall()]

            cursor = await db.execute(
                "SELECT COUNT(DISTINCT session) AS cnt FROM events "
                "WHERE created_at >= ? AND session IS NOT NULL",
                (cutoff,),
            )
            unique_sessions = (await cursor.fetchone())["cnt"]

            cursor = await db.execute(
                "SELECT metadata, COUNT(*) AS cnt FROM events "
                "WHERE event_type = 'filter' AND created_at >= ? AND metadata IS NOT NULL "
                "GROUP BY metadata ORDER BY cnt DESC LIMIT 15",
                (cutoff,),
            )
            filter_usage = [dict(r) for r in await cursor.fetchall()]

    return {
        "by_type": by_type,
        "clicks_by_store": clicks_by_store,
        "top_deals": top_deals,
        "clicks_by_day": clicks_by_day,
        "views_by_day": views_by_day,
        "unique_sessions": unique_sessions,
        "filter_usage": filter_usage,
        "days": days,
    }
