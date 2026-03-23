"""Multi-store async scraping orchestrator."""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime

import httpx

from aggregator.categorizer import categorize, is_excluded
from aggregator.config import STORES, StoreConfig
from aggregator.models import AggregatedDeal
from snow_deals.models import Product
from snow_deals.parsers.base import BaseParser

log = logging.getLogger(__name__)

# Per-domain semaphore to rate-limit concurrent requests
_semaphores: dict[str, asyncio.Semaphore] = {}
MAX_CONCURRENT_PER_DOMAIN = 2

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def _get_semaphore(domain: str) -> asyncio.Semaphore:
    if domain not in _semaphores:
        _semaphores[domain] = asyncio.Semaphore(MAX_CONCURRENT_PER_DOMAIN)
    return _semaphores[domain]


# Registry mapping parser_type -> (module_path, class_name)
# Browser-only stores (evo, backcountry, thehouse, etc.) are handled by browser.py
# and don't need entries here.
_PARSER_REGISTRY: dict[str, tuple[str, str]] = {
    "shopify":          ("snow_deals.parsers.shopify", "ShopifyParser"),
    "bluezone":         ("snow_deals.parsers.bluezone", "BlueZoneParser"),
    "alpineshopvt":     ("aggregator.parsers.alpineshopvt", "AlpineShopVTParser"),
    "thecircle":        ("aggregator.parsers.thecircle", "TheCircleParser"),
    "coloradodiscount": ("aggregator.parsers.coloradodiscount", "ColoradoDiscountParser"),
    "sacredride":       ("aggregator.parsers.sacredride", "SacredRideParser"),
}


def _get_parser(parser_type: str) -> BaseParser | None:
    """Return the appropriate parser instance for a given parser type."""
    entry = _PARSER_REGISTRY.get(parser_type)
    if entry is None:
        return None
    module_path, class_name = entry
    try:
        import importlib
        module = importlib.import_module(module_path)
        return getattr(module, class_name)()
    except (ImportError, AttributeError) as e:
        log.error("Failed to load parser %s.%s: %s", module_path, class_name, e)
        return None


_CM_PATTERN = re.compile(r'(\d+)\s*cm', re.IGNORECASE)
_RETAIL_PATTERN = re.compile(r',?\s*Retail(?:\s+Price)?:\s*\$[\d,.]+', re.IGNORECASE)
_PRICE_PATTERN = re.compile(r'\$[\d,.]+')
_COLOR_JUNK = re.compile(
    r'\b(Multicolor|Default Title|One Size|One Color)\b,?\s*', re.IGNORECASE
)
# Common color names to strip from sizes
_COLORS = re.compile(
    r'\b(Red|Blue|Green|Black|White|Grey|Gray|Navy|Orange|Yellow|Purple|Pink|Brown|'
    r'Teal|Coral|Sage Green|Black/Black|White/White|Solid \w+)\b/?\.?\s*,?\s*',
    re.IGNORECASE
)


def _clean_sizes(sizes_str: str | None) -> str | None:
    """Clean sizes string by removing prices, colors, and junk values."""
    if not sizes_str:
        return None
    s = _RETAIL_PATTERN.sub('', sizes_str)
    # If the remaining string is mostly prices (e.g. "$0.98, $1.98, ..."), discard it
    parts = [p.strip() for p in s.split(',') if p.strip()]
    non_price_parts = [p for p in parts if not _PRICE_PATTERN.fullmatch(p.strip())]
    if not non_price_parts:
        return None
    s = ', '.join(non_price_parts)
    s = _COLOR_JUNK.sub('', s)
    s = _COLORS.sub('', s)
    s = re.sub(r',\s*,', ',', s).strip(' ,')
    # Truncate overly long sizes
    if len(s) > 120:
        s = s[:117] + '...'
    return s if s else None


def _extract_lengths(sizes_str: str | None) -> tuple[int | None, int | None]:
    """Extract min/max ski/snowboard lengths in cm from a sizes string.

    Returns (length_min, length_max) or (None, None) if no lengths found.
    Filters to plausible ski/board lengths (100-220cm).
    """
    if not sizes_str:
        return None, None
    lengths = [
        int(m) for m in _CM_PATTERN.findall(sizes_str)
        if 100 <= int(m) <= 220
    ]
    if not lengths:
        return None, None
    return min(lengths), max(lengths)


_KIDS_KEYWORDS = re.compile(
    r"\b(junior|jr|kids?|youth|toddler|boys|girls|infant|child|children|grom|little kid|big kid)\b",
    re.IGNORECASE,
)


def _is_kids_product(name: str) -> bool:
    """Return True if the product name indicates kids/junior gear."""
    return bool(_KIDS_KEYWORDS.search(name))


def _products_to_deals(
    products: list[Product], store_name: str
) -> list[AggregatedDeal]:
    """Convert snow_deals Products to AggregatedDeals with categorization.

    Filters out kids/junior products.
    """
    now = datetime.now()
    deals: list[AggregatedDeal] = []
    for p in products:
        if _is_kids_product(p.name) or is_excluded(p.name, p.url):
            continue
        if p.discount_pct <= 0:
            continue
        raw_sizes = ", ".join(p.sizes) if p.sizes else None
        length_min, length_max = _extract_lengths(raw_sizes)
        sizes_str = _clean_sizes(raw_sizes)
        deals.append(
            AggregatedDeal(
                id=None,
                store=store_name,
                name=p.name,
                url=p.url,
                current_price=p.current_price,
                original_price=p.original_price,
                discount_pct=p.discount_pct,
                category=categorize(p.name, p.url, p.product_type or ""),
                sizes=sizes_str,
                length_min=length_min,
                length_max=length_max,
                scraped_at=now,
            )
        )
    return deals


async def scrape_store(
    store: StoreConfig,
    client: httpx.AsyncClient,
    *,
    delay: float = 1.0,
    max_pages: int = 10,
) -> list[AggregatedDeal]:
    """Scrape a single store using HTTP + parser and return AggregatedDeals."""
    sem = _get_semaphore(store.domain)

    parser = _get_parser(store.parser_type)
    if parser is None:
        log.warning("No parser for %s (type=%s), skipping", store.name, store.parser_type)
        return []

    products: list[Product] = []

    for url in store.scrape_urls:
        page = 0
        # For Shopify stores, convert to API URL
        if store.parser_type == "shopify" and hasattr(parser, "get_api_url"):
            current_url: str | None = parser.get_api_url(url)
            if not current_url:
                log.warning("Could not get API URL for %s", url)
                continue
        else:
            current_url = url

        while current_url and page < max_pages:
            page += 1
            async with sem:
                log.info("[%s] Fetching page %d: %s", store.name, page, current_url)
                try:
                    resp = await client.get(current_url)
                    resp.raise_for_status()
                except httpx.HTTPError as e:
                    log.error("[%s] HTTP error: %s", store.name, e)
                    break

            page_products = parser.parse_listing_page(resp.text, current_url)
            products.extend(page_products)

            if not page_products:
                break

            current_url = parser.get_next_page_url(resp.text, current_url)
            if current_url and page < max_pages:
                await asyncio.sleep(delay)

    log.info("[%s] Total products scraped: %d", store.name, len(products))
    return _products_to_deals(products, store.name)


async def scrape_store_browser(
    store: StoreConfig,
    *,
    delay: float = 2.0,
    max_pages: int = 25,
) -> list[AggregatedDeal]:
    """Scrape a single store using Playwright headless browser."""
    try:
        from aggregator.browser import scrape_with_browser
    except ImportError as e:
        log.error("[%s] Playwright not available: %s", store.name, e)
        return []

    products = await scrape_with_browser(
        urls=store.scrape_urls,
        store_name=store.name,
        store_type=store.parser_type,
        max_pages=max_pages,
        delay=delay,
    )
    log.info("[%s] Browser scraped %d products", store.name, len(products))
    return _products_to_deals(products, store.name)


async def scrape_all(
    *,
    stores: list[StoreConfig] | None = None,
    delay: float = 1.0,
    max_pages: int = 10,
) -> list[AggregatedDeal]:
    """Scrape all configured stores concurrently."""
    stores = stores or STORES

    http_stores = [s for s in stores if not s.use_browser]
    browser_stores = [s for s in stores if s.use_browser]

    all_deals: list[AggregatedDeal] = []

    # HTTP-based stores (Shopify JSON, BS4 HTML parsers)
    if http_stores:
        async with httpx.AsyncClient(
            headers=DEFAULT_HEADERS,
            follow_redirects=True,
            timeout=30.0,
        ) as client:
            tasks = [
                scrape_store(store, client, delay=delay, max_pages=max_pages)
                for store in http_stores
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        for store, result in zip(http_stores, results):
            if isinstance(result, Exception):
                log.error("[%s] Scrape failed: %s", store.name, result)
            else:
                all_deals.extend(result)

    # Browser-based stores (Playwright)
    if browser_stores:
        browser_tasks = [
            scrape_store_browser(store, delay=delay, max_pages=max_pages)
            for store in browser_stores
        ]
        results = await asyncio.gather(*browser_tasks, return_exceptions=True)

        for store, result in zip(browser_stores, results):
            if isinstance(result, Exception):
                log.error("[%s] Browser scrape failed: %s", store.name, result)
            else:
                all_deals.extend(result)

    return all_deals
