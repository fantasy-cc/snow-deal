"""API and page routes for the aggregator web UI."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from datetime import datetime, timedelta

from aggregator.config import CATEGORY_RULES, STORES
from aggregator.db import count_with_length, get_all_reviews, get_brands, query_deals, store_status
from aggregator.reviews import ReviewData, match_review_to_deal

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))
templates.env.auto_reload = True

router = APIRouter()

TAX_FREE_STORES = {s.name for s in STORES if s.tax_free}
STORE_DOMAINS = {s.name: s.domain for s in STORES}
# Stores that price in CAD
CAD_STORES = {s.name for s in STORES if s.currency == "CAD"}

# Cached review data — loaded once, refreshed on server restart
_reviews_cache: list[ReviewData] | None = None


async def _get_reviews() -> list[ReviewData]:
    """Load reviews from DB, cached in memory."""
    global _reviews_cache
    if _reviews_cache is None:
        rows = await get_all_reviews()
        _reviews_cache = [
            ReviewData(
                product_name=r["product_name"],
                brand=r["brand"],
                score=r["score"],
                award=r["award"],
                url=r["review_url"],
                category=r["category"],
            )
            for r in rows
        ]
    return _reviews_cache


def _attach_reviews(deals: list, reviews: list[ReviewData]) -> dict:
    """Match reviews to deals, return a dict of deal_id -> review info."""
    review_map: dict[int, dict] = {}
    for deal in deals:
        match = match_review_to_deal(deal.name, reviews)
        if match:
            review_map[deal.id] = {
                "score": match.score,
                "award": match.award,
                "url": match.url,
            }
    return review_map


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
) -> tuple[list, bool, int | None, dict]:
    """Shared query logic: fetch deals page, optional count, and review matches."""
    tax_free_only = tax_free == "1"
    reviewed_only = reviewed == "1"

    # For "top_reviewed" sort or "reviewed_only" filter, we fetch more and filter in Python
    if sort == "top_reviewed" or reviewed_only:
        all_deals = await query_deals(
            category=category, store=store, brand=brand, min_discount=min_discount,
            sort_by="discount_pct", limit=10000, offset=0,
            tax_free_only=tax_free_only, tax_free_stores=TAX_FREE_STORES,
            q=q, size_min=size_min, size_max=size_max,
        )
        reviews = await _get_reviews()
        review_map = {}
        for deal in all_deals:
            match = match_review_to_deal(deal.name, reviews)
            if match:
                review_map[deal.id] = {
                    "score": match.score,
                    "award": match.award,
                    "url": match.url,
                }
        if reviewed_only:
            all_deals = [d for d in all_deals if d.id in review_map]
        if sort == "top_reviewed":
            all_deals.sort(key=lambda d: review_map.get(d.id, {}).get("score", 0), reverse=True)

        deal_count = len(all_deals) if count else None
        deals = all_deals[offset:offset + PAGE_SIZE]
        has_more = len(all_deals) > offset + PAGE_SIZE
        # Filter review_map to only include current page deals
        page_ids = {d.id for d in deals}
        review_map = {k: v for k, v in review_map.items() if k in page_ids}
        return deals, has_more, deal_count, review_map

    deals = await query_deals(
        category=category, store=store, brand=brand, min_discount=min_discount,
        sort_by=sort, limit=PAGE_SIZE + 1, offset=offset,
        tax_free_only=tax_free_only, tax_free_stores=TAX_FREE_STORES,
        q=q, size_min=size_min, size_max=size_max,
    )
    has_more = len(deals) > PAGE_SIZE
    deals = deals[:PAGE_SIZE]

    deal_count = None
    if count:
        deal_count = await query_deals(
            category=category, store=store, brand=brand, min_discount=min_discount,
            sort_by=sort, limit=10000,
            tax_free_only=tax_free_only, tax_free_stores=TAX_FREE_STORES,
            q=q, size_min=size_min, size_max=size_max, count_only=True,
        )

    reviews = await _get_reviews()
    review_map = _attach_reviews(deals, reviews) if reviews else {}

    return deals, has_more, deal_count, review_map


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
    deals, has_more, deal_count, review_map = await _fetch_deals(
        category=category, store=store, brand=brand, min_discount=min_discount,
        sort=sort, tax_free=tax_free, q=q, size_min=size_min, size_max=size_max,
        reviewed=reviewed,
    )
    brands = await get_brands()
    length_count = await count_with_length()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "deals": deals,
            "deal_count": deal_count,
            "categories": [cat for cat, _ in CATEGORY_RULES],
            "stores": [s.name for s in STORES],
            "brands": brands,
            "tax_free_stores": TAX_FREE_STORES,
            "cad_stores": CAD_STORES,
            "review_map": review_map,
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
    deals, has_more, deal_count, review_map = await _fetch_deals(
        category=category, store=store, brand=brand, min_discount=min_discount,
        sort=sort, tax_free=tax_free, q=q, size_min=size_min, size_max=size_max,
        reviewed=reviewed, offset=offset, count=not is_load_more,
    )

    template = "partials/more_cards.html" if is_load_more else "partials/deal_cards.html"
    return templates.TemplateResponse(
        template,
        {"request": request, "deals": deals, "deal_count": deal_count,
         "tax_free_stores": TAX_FREE_STORES, "cad_stores": CAD_STORES,
         "review_map": review_map,
         "has_more": has_more, "next_offset": offset + PAGE_SIZE},
    )
