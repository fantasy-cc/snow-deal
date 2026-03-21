"""API and page routes for the aggregator web UI."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from datetime import datetime, timedelta

from aggregator.config import CATEGORY_RULES, STORES
from aggregator.db import query_deals, store_status

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

router = APIRouter()

TAX_FREE_STORES = {s.name for s in STORES if s.tax_free}
STORE_DOMAINS = {s.name: s.domain for s in STORES}


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


@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    category: str | None = None,
    store: str | None = None,
    min_discount: float = Query(0, alias="min_discount"),
    sort: str = Query("discount_pct", alias="sort"),
    tax_free: str = Query("", alias="tax_free"),
    q: str = Query("", alias="q"),
):
    tax_free_only = tax_free == "1"
    deals = await query_deals(
        category=category, store=store, min_discount=min_discount,
        sort_by=sort, limit=200,
        tax_free_only=tax_free_only, tax_free_stores=TAX_FREE_STORES,
        q=q,
    )

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "deals": deals,
            "deal_count": len(deals),
            "categories": [cat for cat, _ in CATEGORY_RULES],
            "stores": [s.name for s in STORES],
            "tax_free_stores": TAX_FREE_STORES,
            "current_category": category,
            "current_store": store,
            "current_min_discount": min_discount,
            "current_sort": sort,
            "current_tax_free": tax_free,
            "current_q": q,
        },
    )


@router.get("/status", response_class=HTMLResponse)
async def status_page(request: Request):
    """Dedicated store status dashboard."""
    statuses = await _build_store_statuses()
    total_deals = sum(s["deal_count"] for s in statuses)
    total_discounts = sum(s["discount_count"] for s in statuses)
    online = sum(1 for s in statuses if s["freshness"] != "offline")
    return templates.TemplateResponse(
        "status.html",
        {
            "request": request,
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
    min_discount: float = Query(0, alias="min_discount"),
    sort: str = Query("discount_pct", alias="sort"),
    tax_free: str = Query("", alias="tax_free"),
    q: str = Query("", alias="q"),
):
    """htmx partial — returns just the deal cards for dynamic filtering."""
    tax_free_only = tax_free == "1"
    deals = await query_deals(
        category=category, store=store, min_discount=min_discount,
        sort_by=sort, limit=200,
        tax_free_only=tax_free_only, tax_free_stores=TAX_FREE_STORES,
        q=q,
    )
    return templates.TemplateResponse(
        "partials/deal_cards.html",
        {"request": request, "deals": deals, "deal_count": len(deals),
         "tax_free_stores": TAX_FREE_STORES},
    )
