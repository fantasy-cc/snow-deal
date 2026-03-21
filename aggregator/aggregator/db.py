"""SQLite schema and CRUD operations via aiosqlite."""

from __future__ import annotations

import aiosqlite
from datetime import datetime
from pathlib import Path

from aggregator.models import AggregatedDeal

DB_PATH = Path(__file__).resolve().parent.parent / "deals.db"

SCHEMA = """\
CREATE TABLE IF NOT EXISTS deals (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    store         TEXT    NOT NULL,
    name          TEXT    NOT NULL,
    url           TEXT    NOT NULL UNIQUE,
    current_price REAL    NOT NULL,
    original_price REAL,
    discount_pct  REAL    NOT NULL DEFAULT 0,
    category      TEXT,
    image_url     TEXT,
    scraped_at    TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_discount  ON deals (discount_pct DESC);
CREATE INDEX IF NOT EXISTS idx_category  ON deals (category);
CREATE INDEX IF NOT EXISTS idx_store     ON deals (store);
"""


async def init_db(db_path: Path = DB_PATH) -> None:
    """Create the deals table if it doesn't exist."""
    async with aiosqlite.connect(db_path) as db:
        await db.executescript(SCHEMA)
        await db.commit()


async def upsert_deals(deals: list[AggregatedDeal], db_path: Path = DB_PATH) -> int:
    """Insert or update deals. Returns count of rows affected."""
    async with aiosqlite.connect(db_path) as db:
        count = 0
        for d in deals:
            await db.execute(
                """\
                INSERT INTO deals (store, name, url, current_price, original_price,
                                   discount_pct, category, image_url, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    current_price  = excluded.current_price,
                    original_price = excluded.original_price,
                    discount_pct   = excluded.discount_pct,
                    category       = excluded.category,
                    image_url      = excluded.image_url,
                    scraped_at     = excluded.scraped_at
                """,
                (
                    d.store, d.name, d.url, d.current_price, d.original_price,
                    d.discount_pct, d.category, d.image_url,
                    d.scraped_at.isoformat(),
                ),
            )
            count += 1
        await db.commit()
    return count


async def query_deals(
    *,
    category: str | None = None,
    store: str | None = None,
    min_discount: float = 0,
    sort_by: str = "discount_pct",
    limit: int = 200,
    tax_free_only: bool = False,
    tax_free_stores: set[str] | None = None,
    q: str = "",
    db_path: Path = DB_PATH,
) -> list[AggregatedDeal]:
    """Query deals with optional filters."""
    clauses: list[str] = ["discount_pct >= ?"]
    params: list[object] = [min_discount]

    if category:
        clauses.append("category = ?")
        params.append(category)
    if store:
        clauses.append("store = ?")
        params.append(store)
    if tax_free_only and tax_free_stores:
        placeholders = ", ".join("?" for _ in tax_free_stores)
        clauses.append(f"store IN ({placeholders})")
        params.extend(tax_free_stores)
    if q:
        clauses.append("name LIKE ?")
        params.append(f"%{q}%")

    where = " AND ".join(clauses)
    sort_map = {
        "discount_pct": "discount_pct DESC",
        "price_low": "current_price ASC",
        "price_high": "current_price DESC",
        "store": "store ASC, discount_pct DESC",
        "newest": "scraped_at DESC",
    }
    order = sort_map.get(sort_by, "discount_pct DESC")

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            f"SELECT * FROM deals WHERE {where} ORDER BY {order} LIMIT ?",
            (*params, limit),
        )
        rows = await cursor.fetchall()

    return [
        AggregatedDeal(
            id=row["id"],
            store=row["store"],
            name=row["name"],
            url=row["url"],
            current_price=row["current_price"],
            original_price=row["original_price"],
            discount_pct=row["discount_pct"],
            category=row["category"],
            image_url=row["image_url"],
            scraped_at=datetime.fromisoformat(row["scraped_at"]),
        )
        for row in rows
    ]


async def store_status(db_path: Path = DB_PATH) -> list[dict]:
    """Return per-store stats: deal count, deals with discounts, last scraped time."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""\
            SELECT store,
                   COUNT(*)                          AS deal_count,
                   SUM(CASE WHEN discount_pct > 0 THEN 1 ELSE 0 END) AS discount_count,
                   MAX(scraped_at)                   AS last_scraped
            FROM deals
            GROUP BY store
            ORDER BY store
        """)
        rows = await cursor.fetchall()
    return [dict(row) for row in rows]
