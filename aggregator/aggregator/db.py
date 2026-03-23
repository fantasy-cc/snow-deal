"""SQLite schema and CRUD operations via aiosqlite."""

from __future__ import annotations

import os
import aiosqlite
from datetime import datetime
from pathlib import Path

from aggregator.models import AggregatedDeal

DB_PATH = Path(os.environ.get("DATABASE_PATH", Path(__file__).resolve().parent.parent / "deals.db"))

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
    sizes         TEXT,
    length_min    INTEGER,
    length_max    INTEGER,
    scraped_at    TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_discount  ON deals (discount_pct DESC);
CREATE INDEX IF NOT EXISTS idx_category  ON deals (category);
CREATE INDEX IF NOT EXISTS idx_store     ON deals (store);

CREATE TABLE IF NOT EXISTS reviews (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name  TEXT    NOT NULL,
    brand         TEXT    NOT NULL DEFAULT '',
    score         INTEGER NOT NULL,
    award         TEXT,
    review_url    TEXT    NOT NULL UNIQUE,
    category      TEXT,
    scraped_at    TEXT    NOT NULL
);

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
                                   discount_pct, category, sizes, length_min, length_max, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    current_price  = excluded.current_price,
                    original_price = excluded.original_price,
                    discount_pct   = excluded.discount_pct,
                    category       = excluded.category,
                    sizes          = excluded.sizes,
                    length_min     = excluded.length_min,
                    length_max     = excluded.length_max,
                    scraped_at     = excluded.scraped_at
                """,
                (
                    d.store, d.name, d.url, d.current_price, d.original_price,
                    d.discount_pct, d.category, d.sizes, d.length_min, d.length_max,
                    d.scraped_at.isoformat(),
                ),
            )
            count += 1
        await db.commit()
    return count


async def count_with_length(db_path: Path = DB_PATH) -> int:
    """Return count of deals that have length data."""
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM deals WHERE length_min IS NOT NULL"
        )
        row = await cursor.fetchone()
    return row[0]


async def get_brands(db_path: Path = DB_PATH) -> list[str]:
    """Return distinct brand names (first word of product name), sorted."""
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "SELECT DISTINCT SUBSTR(name, 1, INSTR(name || ' ', ' ') - 1) AS brand "
            "FROM deals WHERE brand != '' ORDER BY brand"
        )
        rows = await cursor.fetchall()
    return [row[0] for row in rows if row[0]]


async def query_deals(
    *,
    category: str | None = None,
    store: str | None = None,
    brand: str | None = None,
    min_discount: float = 0,
    sort_by: str = "discount_pct",
    limit: int = 200,
    offset: int = 0,
    tax_free_only: bool = False,
    tax_free_stores: set[str] | None = None,
    q: str = "",
    size_min: int | None = None,
    size_max: int | None = None,
    count_only: bool = False,
    db_path: Path = DB_PATH,
) -> list[AggregatedDeal] | int:
    """Query deals with optional filters. If count_only=True, returns int."""
    clauses: list[str] = ["discount_pct >= ?"]
    params: list[object] = [min_discount]

    if category:
        clauses.append("category = ?")
        params.append(category)
    if store:
        clauses.append("store = ?")
        params.append(store)
    if brand:
        clauses.append("name LIKE ?")
        params.append(f"{brand} %")
    if tax_free_only and tax_free_stores:
        placeholders = ", ".join("?" for _ in tax_free_stores)
        clauses.append(f"store IN ({placeholders})")
        params.extend(tax_free_stores)
    if q:
        clauses.append("name LIKE ?")
        params.append(f"%{q}%")
    if size_min is not None or size_max is not None:
        length_conds = ["length_min IS NULL"]
        if size_min is not None and size_max is not None:
            length_conds.append("(length_max >= ? AND length_min <= ?)")
            params.extend([size_min, size_max])
        elif size_min is not None:
            length_conds.append("length_max >= ?")
            params.append(size_min)
        elif size_max is not None:
            length_conds.append("length_min <= ?")
            params.append(size_max)
        clauses.append(f"({' OR '.join(length_conds)})")
    where = " AND ".join(clauses)

    if count_only:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute(
                f"SELECT COUNT(*) FROM deals WHERE {where}", params,
            )
            row = await cursor.fetchone()
        return row[0]

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
            f"SELECT * FROM deals WHERE {where} ORDER BY {order} LIMIT ? OFFSET ?",
            (*params, limit, offset),
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
            sizes=row["sizes"],
            length_min=row["length_min"],
            length_max=row["length_max"],
            scraped_at=datetime.fromisoformat(row["scraped_at"]),
        )
        for row in rows
    ]


async def upsert_reviews(reviews: list, db_path: Path = DB_PATH) -> int:
    """Insert or update reviews. Accepts dicts or ReviewData NamedTuples."""
    from datetime import datetime
    now = datetime.now().isoformat()
    async with aiosqlite.connect(db_path) as db:
        count = 0
        for r in reviews:
            if isinstance(r, dict):
                name, brand, score = r["product_name"], r["brand"], r["score"]
                award, url, cat = r["award"], r["review_url"], r["category"]
                scraped = r.get("scraped_at", now)
            else:
                name, brand, score = r.product_name, r.brand, r.score
                award, url, cat = r.award, r.url, r.category
                scraped = now
            await db.execute(
                """\
                INSERT INTO reviews (product_name, brand, score, award, review_url, category, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(review_url) DO UPDATE SET
                    product_name = excluded.product_name,
                    brand        = excluded.brand,
                    score        = excluded.score,
                    award        = excluded.award,
                    category     = excluded.category,
                    scraped_at   = excluded.scraped_at
                """,
                (name, brand, score, award, url, cat, scraped),
            )
            count += 1
        await db.commit()
    return count


async def get_all_reviews(db_path: Path = DB_PATH) -> list[dict]:
    """Return all reviews from the database."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT product_name, brand, score, award, review_url, category FROM reviews ORDER BY score DESC"
        )
        rows = await cursor.fetchall()
    return [dict(row) for row in rows]


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
