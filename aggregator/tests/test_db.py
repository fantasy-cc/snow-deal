"""Tests for SQLite database operations."""

import asyncio
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from aggregator.db import (
    get_all_reviews,
    get_brands,
    init_db,
    query_deals,
    store_status,
    upsert_deals,
    upsert_reviews,
)
from aggregator.models import AggregatedDeal


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test.db"


def _make_deal(name="Atomic Bent 100", store="Evo", price=499.99, orig=599.99, **kw):
    return AggregatedDeal(
        id=None,
        store=store,
        name=name,
        url=kw.get("url", f"https://example.com/{name.replace(' ', '-').lower()}"),
        current_price=price,
        original_price=orig,
        discount_pct=round((1 - price / orig) * 100, 1) if orig else 0,
        category=kw.get("category", "skis"),
        sizes=kw.get("sizes"),
        length_min=kw.get("length_min"),
        length_max=kw.get("length_max"),
        scraped_at=datetime.now(),
    )


class TestDB:
    def test_init_and_upsert(self, db_path):
        async def _run():
            await init_db(db_path)
            deals = [_make_deal()]
            count = await upsert_deals(deals, db_path)
            assert count == 1

        asyncio.run(_run())

    def test_query_deals(self, db_path):
        async def _run():
            await init_db(db_path)
            await upsert_deals([
                _make_deal("Atomic Bent 100", "Evo", 499.99, 599.99, category="skis"),
                _make_deal("Burton Custom", "Backcountry", 399.99, 499.99, category="snowboards",
                           url="https://example.com/burton-custom"),
            ], db_path)

            # Query all
            all_deals = await query_deals(db_path=db_path)
            assert len(all_deals) == 2

            # Filter by category
            skis = await query_deals(category="skis", db_path=db_path)
            assert len(skis) == 1
            assert skis[0].name == "Atomic Bent 100"

            # Filter by store
            evo = await query_deals(store="Evo", db_path=db_path)
            assert len(evo) == 1

            # Count only
            count = await query_deals(count_only=True, db_path=db_path)
            assert count == 2

        asyncio.run(_run())

    def test_upsert_updates_existing(self, db_path):
        async def _run():
            await init_db(db_path)
            deal = _make_deal("Atomic Bent 100", price=499.99, orig=599.99)
            await upsert_deals([deal], db_path)

            # Update price
            deal_updated = _make_deal("Atomic Bent 100", price=449.99, orig=599.99)
            await upsert_deals([deal_updated], db_path)

            deals = await query_deals(db_path=db_path)
            assert len(deals) == 1
            assert deals[0].current_price == 449.99

        asyncio.run(_run())

    def test_brand_query(self, db_path):
        async def _run():
            await init_db(db_path)
            await upsert_deals([
                _make_deal("Atomic Bent 100", url="https://example.com/atomic"),
                _make_deal("Salomon QST 98", url="https://example.com/salomon"),
            ], db_path)

            brands = await get_brands(db_path)
            assert "Atomic" in brands
            assert "Salomon" in brands

        asyncio.run(_run())

    def test_reviews_crud(self, db_path):
        async def _run():
            await init_db(db_path)
            reviews = [{
                "product_name": "Atomic Bent 100",
                "brand": "Atomic",
                "score": 85,
                "award": "Editors' Choice",
                "review_url": "https://ogl.com/atomic-bent-100",
                "category": "skis",
                "scraped_at": datetime.now().isoformat(),
            }]
            count = await upsert_reviews(reviews, db_path)
            assert count == 1

            all_reviews = await get_all_reviews(db_path)
            assert len(all_reviews) == 1
            assert all_reviews[0]["score"] == 85

        asyncio.run(_run())

    def test_store_status(self, db_path):
        async def _run():
            await init_db(db_path)
            await upsert_deals([
                _make_deal("Atomic Bent 100", "Evo"),
                _make_deal("Salomon QST 98", "Evo", url="https://example.com/qst"),
            ], db_path)

            statuses = await store_status(db_path)
            assert len(statuses) == 1
            assert statuses[0]["store"] == "Evo"
            assert statuses[0]["deal_count"] == 2

        asyncio.run(_run())

    def test_text_search(self, db_path):
        async def _run():
            await init_db(db_path)
            await upsert_deals([
                _make_deal("Atomic Bent 100"),
                _make_deal("Salomon QST 98", url="https://example.com/qst"),
            ], db_path)

            results = await query_deals(q="Bent", db_path=db_path)
            assert len(results) == 1
            assert "Bent" in results[0].name

        asyncio.run(_run())

    def test_min_discount_filter(self, db_path):
        async def _run():
            await init_db(db_path)
            await upsert_deals([
                _make_deal("Big Discount", price=300, orig=600),  # 50% off
                _make_deal("Small Discount", price=550, orig=600, url="https://example.com/small"),  # ~8% off
            ], db_path)

            results = await query_deals(min_discount=20, db_path=db_path)
            assert len(results) == 1
            assert results[0].name == "Big Discount"

        asyncio.run(_run())
