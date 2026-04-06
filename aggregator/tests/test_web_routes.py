"""Web route integration tests for auth, SEO, and rate limiting."""

from __future__ import annotations

import asyncio
from datetime import datetime
from functools import partial

import pytest
from fastapi.testclient import TestClient

import aggregator.auth_db as auth_db_module
import aggregator.db as db_module
import aggregator.web.app as app_module
import aggregator.web.routes as routes_module
from aggregator.models import AggregatedDeal
from aggregator.web import admin_routes, event_routes, invite_routes


def _make_deal(name: str = "Atomic Bent 100", store: str = "Evo") -> AggregatedDeal:
    return AggregatedDeal(
        id=None,
        store=store,
        name=name,
        url=f"https://example.com/{name.replace(' ', '-').lower()}",
        current_price=499.99,
        original_price=599.99,
        discount_pct=16.5,
        category="skis",
        sizes=None,
        length_min=None,
        length_max=None,
        scraped_at=datetime.now(),
    )


@pytest.fixture
def isolated_app(tmp_path, monkeypatch):
    deals_db = tmp_path / "deals.db"
    auth_db_path = tmp_path / "auth.db"

    monkeypatch.setenv("AUTH_DB_PATH", str(auth_db_path))
    monkeypatch.delenv("TURSO_URL", raising=False)
    monkeypatch.delenv("TURSO_AUTH_TOKEN", raising=False)

    async def _init_test_db():
        await db_module.init_db(deals_db)

    monkeypatch.setattr(app_module, "init_db", _init_test_db)
    monkeypatch.setattr(routes_module, "query_deals", partial(db_module.query_deals, db_path=deals_db))
    monkeypatch.setattr(routes_module, "get_brands", partial(db_module.get_brands, db_path=deals_db))
    monkeypatch.setattr(routes_module, "get_category_counts", partial(db_module.get_category_counts, db_path=deals_db))
    monkeypatch.setattr(routes_module, "count_with_length", partial(db_module.count_with_length, db_path=deals_db))
    monkeypatch.setattr(routes_module, "store_status", partial(db_module.store_status, db_path=deals_db))

    auth_db_module._conn = None
    auth_db_module.TURSO_URL = ""
    auth_db_module.TURSO_AUTH_TOKEN = ""
    invite_routes.invite_submit_limiter.clear()
    admin_routes.admin_create_codes_limiter.clear()
    event_routes.event_post_limiter.clear()

    yield deals_db

    auth_db_module._conn = None


def test_private_mode_redirects_home_without_session(isolated_app, monkeypatch):
    monkeypatch.setenv("PUBLIC_MODE", "0")
    monkeypatch.setenv("SECRET_KEY", "test-secret")

    with TestClient(app_module.create_app()) as client:
        response = client.get("/", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/invite"


def test_private_mode_requires_secret_key(isolated_app, monkeypatch):
    monkeypatch.setenv("PUBLIC_MODE", "0")
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError, match="SECRET_KEY must be set"):
        with TestClient(app_module.create_app()):
            pass


def test_public_mode_serves_homepage_and_public_robots(isolated_app, monkeypatch):
    monkeypatch.setenv("PUBLIC_MODE", "1")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    asyncio.run(db_module.init_db(isolated_app))
    asyncio.run(db_module.upsert_deals([_make_deal()], isolated_app))

    with TestClient(app_module.create_app()) as client:
        home = client.get("/")
        robots = client.get("/robots.txt")
        admin = client.get("/admin/codes", follow_redirects=False)

    assert home.status_code == 200
    assert "FreshPowder" in home.text
    assert 'property="og:title"' in home.text
    assert robots.status_code == 200
    assert "Allow: /" in robots.text
    assert "Disallow: /admin" in robots.text
    assert admin.status_code == 302
    assert admin.headers["location"] == "/"


def test_invite_submission_sets_session_cookie(isolated_app, monkeypatch):
    monkeypatch.setenv("PUBLIC_MODE", "0")
    monkeypatch.setenv("SECRET_KEY", "test-secret")

    async def _valid_code(code: str) -> bool:
        return code == "FRESH123"

    async def _record_code_use(code: str) -> None:
        return None

    monkeypatch.setattr(invite_routes, "validate_invite_code", _valid_code)
    monkeypatch.setattr(invite_routes, "record_code_use", _record_code_use)

    with TestClient(app_module.create_app()) as client:
        response = client.post("/invite", data={"code": "fresh123"}, follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/"
    assert "snow_deals_session=" in response.headers["set-cookie"]


def test_mutating_routes_are_rate_limited(isolated_app, monkeypatch):
    monkeypatch.setenv("PUBLIC_MODE", "0")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setattr(invite_routes, "INVITE_SUBMIT_LIMIT", 1)
    monkeypatch.setattr(event_routes, "EVENT_POST_LIMIT", 1)
    invite_routes.invite_submit_limiter.clear()
    event_routes.event_post_limiter.clear()

    with TestClient(app_module.create_app()) as client:
        first_invite = client.post("/invite", data={"code": "badcode"})
        second_invite = client.post("/invite", data={"code": "badcode"})
        first_event = client.post("/api/event", json={"event_type": "page_view"})
        second_event = client.post("/api/event", json={"event_type": "page_view"})

    assert first_invite.status_code == 200
    assert second_invite.status_code == 429
    assert "Too many invite attempts" in second_invite.text
    assert first_event.status_code == 200
    assert second_event.status_code == 429
    assert second_event.json()["error"] == "rate_limited"
