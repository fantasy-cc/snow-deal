"""API and page routes for the aggregator web UI."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates

from datetime import datetime, timedelta

from aggregator.auth import is_public_mode
from aggregator.config import CATEGORY_RULES, STORES
from aggregator.db import (
    count_with_length, get_brands, get_category_counts, query_deals, store_status,
)

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))
templates.env.auto_reload = True

router = APIRouter()

TAX_FREE_STORES = {s.name for s in STORES if s.tax_free}
STORE_DOMAINS = {s.name: s.domain for s in STORES}
# Stores that price in CAD
CAD_STORES = {s.name for s in STORES if s.currency == "CAD"}


async def _build_store_statuses() -> list[dict]:
    """Build annotated store status list with freshness indicators."""
    statuses = await store_status()
    now = datetime.now()
    for st in statuses:
        last = datetime.fromisoformat(st["last_scraped"])
        age = now - last
        st["age_hours"] = age.total_seconds() / 3600
        if age < timedelta(hours=6):
            st["freshness"] = "fresh"
        elif age < timedelta(hours=24):
            st["freshness"] = "stale"
        else:
            st["freshness"] = "old"
        st["last_scraped_fmt"] = last.strftime("%b %d, %H:%M")
        st["domain"] = STORE_DOMAINS.get(st["store"], "")
        st["tax_free"] = st["store"] in TAX_FREE_STORES
    stores_with_data = {s["store"] for s in statuses}
    for s in STORES:
        if s.name not in stores_with_data:
            statuses.append({
                "store": s.name,
                "deal_count": 0,
                "discount_count": 0,
                "last_scraped": None,
                "age_hours": None,
                "freshness": "offline",
                "last_scraped_fmt": "never",
                "domain": s.domain,
                "tax_free": s.tax_free,
            })
    statuses.sort(key=lambda s: s["store"])
    return statuses


PAGE_SIZE = 60


async def _fetch_deals(
    *,
    category: str | None,
    store: str | None,
    brand: str | None,
    min_discount: float,
    sort: str,
    tax_free: str,
    q: str,
    size_min: int | None,
    size_max: int | None,
    reviewed: str,
    offset: int = 0,
    count: bool = True,
) -> tuple[list, bool, int | None]:
    """Fetch a page of deals. Reviews are pre-joined via deal_reviews table."""
    tax_free_only = tax_free == "1"
    reviewed_only = reviewed == "1"

    deals = await query_deals(
        category=category, store=store, brand=brand, min_discount=min_discount,
        sort_by=sort, limit=PAGE_SIZE + 1, offset=offset,
        tax_free_only=tax_free_only, tax_free_stores=TAX_FREE_STORES,
        q=q, size_min=size_min, size_max=size_max,
        reviewed_only=reviewed_only,
    )
    has_more = len(deals) > PAGE_SIZE
    deals = deals[:PAGE_SIZE]

    deal_count = None
    if count:
        deal_count = await query_deals(
            category=category, store=store, brand=brand, min_discount=min_discount,
            sort_by=sort,
            tax_free_only=tax_free_only, tax_free_stores=TAX_FREE_STORES,
            q=q, size_min=size_min, size_max=size_max,
            reviewed_only=reviewed_only, count_only=True,
        )

    return deals, has_more, deal_count


@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    category: str | None = None,
    store: str | None = None,
    brand: str | None = None,
    min_discount: float = Query(0, alias="min_discount"),
    sort: str = Query("discount_pct", alias="sort"),
    tax_free: str = Query("", alias="tax_free"),
    q: str = Query("", alias="q"),
    size_min: int | None = Query(None, alias="size_min"),
    size_max: int | None = Query(None, alias="size_max"),
    reviewed: str = Query("", alias="reviewed"),
):
    deals, has_more, deal_count = await _fetch_deals(
        category=category, store=store, brand=brand, min_discount=min_discount,
        sort=sort, tax_free=tax_free, q=q, size_min=size_min, size_max=size_max,
        reviewed=reviewed,
    )
    brands = await get_brands()
    length_count = await count_with_length()
    category_counts = await get_category_counts()
    store_statuses = await store_status()
    store_counts = {s["store"]: s["deal_count"] for s in store_statuses}

    return templates.TemplateResponse(
        request=request, name="index.html",
        context={
            "deals": deals,
            "deal_count": deal_count,
            "categories": list(dict.fromkeys(cat for cat, _ in CATEGORY_RULES if cat != "boots")),
            "stores": [s.name for s in STORES],
            "brands": brands,
            "tax_free_stores": TAX_FREE_STORES,
            "cad_stores": CAD_STORES,
            "category_counts": category_counts,
            "store_counts": store_counts,
            "current_category": category,
            "current_store": store,
            "current_brand": brand,
            "current_min_discount": min_discount,
            "current_sort": sort,
            "current_tax_free": tax_free,
            "current_reviewed": reviewed,
            "current_q": q,
            "current_size_min": size_min,
            "current_size_max": size_max,
            "length_count": length_count,
            "has_more": has_more,
            "next_offset": PAGE_SIZE,
        },
    )


@router.get("/robots.txt", response_class=PlainTextResponse)
async def robots_txt():
    """Serve search-engine crawl rules."""
    if is_public_mode():
        return PlainTextResponse(
            "User-agent: *\n"
            "Allow: /\n"
            "Disallow: /admin\n"
            "Disallow: /invite\n"
            "Disallow: /api/\n"
        )
    return PlainTextResponse("User-agent: *\nDisallow: /\n")


@router.get("/status", response_class=HTMLResponse)
async def status_page(request: Request):
    """Dedicated store status dashboard."""
    statuses = await _build_store_statuses()
    total_deals = sum(s["deal_count"] for s in statuses)
    total_discounts = sum(s["discount_count"] for s in statuses)
    online = sum(1 for s in statuses if s["freshness"] != "offline")
    return templates.TemplateResponse(
        request=request, name="status.html",
        context={
            "store_statuses": statuses,
            "total_deals": total_deals,
            "total_discounts": total_discounts,
            "online_count": online,
            "total_count": len(statuses),
        },
    )


@router.get("/deals", response_class=HTMLResponse)
async def deals_fragment(
    request: Request,
    category: str | None = None,
    store: str | None = None,
    brand: str | None = None,
    min_discount: float = Query(0, alias="min_discount"),
    sort: str = Query("discount_pct", alias="sort"),
    tax_free: str = Query("", alias="tax_free"),
    q: str = Query("", alias="q"),
    size_min: int | None = Query(None, alias="size_min"),
    size_max: int | None = Query(None, alias="size_max"),
    reviewed: str = Query("", alias="reviewed"),
    offset: int = Query(0, alias="offset"),
):
    """htmx partial — returns deal cards for dynamic filtering."""
    is_load_more = offset > 0
    deals, has_more, deal_count = await _fetch_deals(
        category=category, store=store, brand=brand, min_discount=min_discount,
        sort=sort, tax_free=tax_free, q=q, size_min=size_min, size_max=size_max,
        reviewed=reviewed, offset=offset, count=not is_load_more,
    )

    template = "partials/more_cards.html" if is_load_more else "partials/deal_cards.html"
    return templates.TemplateResponse(
        request=request, name=template,
        context={"deals": deals, "deal_count": deal_count,
                 "tax_free_stores": TAX_FREE_STORES, "cad_stores": CAD_STORES,
                 "has_more": has_more, "next_offset": offset + PAGE_SIZE},
    )
