"""Review score scrapers (OutdoorGearLab + The Good Ride) and product matcher."""

from __future__ import annotations

import asyncio
import json
import logging
import re
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher
from typing import NamedTuple

import httpx
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

# OGL category pages that contain review links for snow sports gear.
# Each page lists 8-15 products with links to individual review pages.
OGL_CATEGORY_URLS = [
    # Skis
    "/topics/snow-sports/best-all-mountain-skis",
    "/topics/snow-sports/best-all-mountain-skis-men",
    "/topics/snow-sports/best-all-mountain-skis-womens",
    "/topics/snow-sports/best-backcountry-skis",
    # Snowboards
    "/topics/snow-sports/best-snowboard",
    "/topics/snow-sports/best-snowboard-men",
    "/topics/snow-sports/best-snowboard-womens",
    "/topics/snow-sports/best-splitboard",
    # Boots & bindings
    "/topics/snow-sports/best-ski-boots",
    "/topics/snow-sports/best-ski-boots-womens",
    "/topics/snow-sports/best-backcountry-ski-boots",
    "/topics/snow-sports/best-at-bindings",
    # Protection & visibility
    "/topics/snow-sports/best-ski-helmet",
    "/topics/snow-sports/best-ski-goggles",
    # Clothing
    "/topics/snow-sports/best-ski-pants-men",
    "/topics/snow-sports/best-ski-pants-womens",
    "/topics/snow-sports/best-ski-gloves",
    "/topics/snow-sports/best-ski-gloves-womens",
    "/topics/snow-sports/best-winter-gloves",
    # Accessories
    "/topics/snow-sports/best-ski-socks",
    "/topics/snow-sports/best-backcountry-ski-poles",
    # Additional categories
    "/topics/snow-sports/best-ski-gear",
    "/topics/snow-sports/best-ski-pants",
    "/topics/snow-sports/best-splitboard-bindings",
    "/topics/snow-sports/best-avalanche-beacon",
    "/topics/snow-sports/best-climbing-skins",
    "/topics/snow-sports/best-snowshoes",
]

OGL_BASE = "https://www.outdoorgearlab.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class ReviewData(NamedTuple):
    """A single product review from OutdoorGearLab."""
    product_name: str
    brand: str
    score: int          # 0-100
    award: str | None   # e.g. "Editors' Choice", "Best Value"
    url: str            # Full OGL review URL
    category: str       # OGL category slug


# ---------------------------------------------------------------------------
# Scraping
# ---------------------------------------------------------------------------


def _extract_review_links(html: str) -> list[tuple[str, str]]:
    """Extract (product_name, review_path) pairs from an OGL category page."""
    soup = BeautifulSoup(html, "lxml")
    links = soup.select('a[href*="/reviews/snow-sports/"]')
    seen: set[str] = set()
    products: list[tuple[str, str]] = []
    for link in links:
        href = link.get("href", "")
        if href in seen or not href:
            continue
        seen.add(href)
        name = link.get_text(strip=True)
        # Skip links that are just "review" text or too short
        if name and len(name) > 3 and "review" not in name.lower():
            products.append((name, href))
    return products


def _extract_review_data(html: str, url: str, category: str) -> ReviewData | None:
    """Extract score, brand, and award from an individual OGL review page."""
    soup = BeautifulSoup(html, "lxml")

    # Overall score from .rating_chart_score
    score_el = soup.select_one(".rating_chart_score")
    if not score_el:
        return None
    try:
        score = int(score_el.get_text(strip=True))
    except ValueError:
        return None

    # Product name and brand from JSON-LD
    product_name = ""
    brand = ""
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(script.string)
            if data.get("@type") == "Product":
                product_name = data.get("name", "")
                brand_data = data.get("brand", {})
                brand = brand_data.get("name", "") if isinstance(brand_data, dict) else str(brand_data)
                break
        except (json.JSONDecodeError, TypeError):
            continue

    if not product_name:
        # Fallback: get from page title
        title = soup.select_one("title")
        if title:
            product_name = title.get_text(strip=True).split(" Review")[0].strip()

    # Award
    award_el = soup.select_one(".compare_awards")
    award = award_el.get_text(strip=True) if award_el else None

    return ReviewData(
        product_name=product_name,
        brand=brand,
        score=score,
        award=award,
        url=url,
        category=category,
    )


async def scrape_reviews(
    *, delay: float = 2.0, max_categories: int | None = None,
) -> list[ReviewData]:
    """Scrape review scores from OutdoorGearLab.

    Fetches category pages to discover review URLs, then scrapes each
    individual review page for the overall score and award.
    """
    categories = OGL_CATEGORY_URLS[:max_categories] if max_categories else OGL_CATEGORY_URLS
    all_reviews: list[ReviewData] = []
    # Collect all review URLs first from category pages
    review_urls: list[tuple[str, str, str]] = []  # (name, url, category_slug)

    async with httpx.AsyncClient(
        headers=HEADERS, follow_redirects=True, timeout=30.0,
    ) as client:
        # Phase 1: Discover review URLs from category pages
        for cat_path in categories:
            url = f"{OGL_BASE}{cat_path}"
            try:
                resp = await client.get(url)
                resp.raise_for_status()
            except httpx.HTTPError as e:
                log.error("Failed to fetch OGL category %s: %s", cat_path, e)
                continue

            products = _extract_review_links(resp.text)
            category_slug = cat_path.rsplit("/", 1)[-1].replace("best-", "")
            for name, path in products:
                full_url = f"{OGL_BASE}{path}" if path.startswith("/") else path
                review_urls.append((name, full_url, category_slug))
            log.info("OGL category %s: found %d review links", cat_path, len(products))
            await asyncio.sleep(delay)

        # Deduplicate by URL
        seen_urls: set[str] = set()
        unique_urls: list[tuple[str, str, str]] = []
        for name, url, cat in review_urls:
            if url not in seen_urls:
                seen_urls.add(url)
                unique_urls.append((name, url, cat))

        log.info("OGL: %d unique review pages to scrape", len(unique_urls))

        # Phase 2: Scrape individual review pages
        for name, url, cat in unique_urls:
            try:
                resp = await client.get(url)
                resp.raise_for_status()
            except httpx.HTTPError as e:
                log.warning("Failed to fetch OGL review %s: %s", url, e)
                continue

            review = _extract_review_data(resp.text, url, cat)
            if review:
                all_reviews.append(review)
                log.info("OGL: %s = %d/100 (%s)", review.product_name, review.score, review.award or "no award")
            else:
                log.warning("OGL: Could not extract score from %s", url)

            await asyncio.sleep(delay)

    log.info("OGL scraping complete: %d reviews collected", len(all_reviews))
    return all_reviews


# ---------------------------------------------------------------------------
# The Good Ride (TGR) — snowboard reviews
# ---------------------------------------------------------------------------

TGR_BASE = "https://thegoodride.com"
TGR_SITEMAPS = [
    f"{TGR_BASE}/snowboardreviews-sitemap.xml",
    f"{TGR_BASE}/snowboardreviews-sitemap2.xml",
]

# Qualitative rating → numeric score (0-100 scale)
_TGR_RATING_MAP = {
    "exceptional": 95,
    "great": 85,
    "good": 70,
    "average": 55,
    "below average": 35,
    "bad": 20,
    "poor": 20,
}

# The 9 riding attributes TGR rates on each board
_TGR_RIDING_ATTRS = {
    "powder", "carving", "speed", "switch", "jumps",
    "jibbing", "pipe", "base glide", "uneven snow",
}


def _parse_tgr_sitemap(xml_text: str) -> list[str]:
    """Extract review URLs from a TGR sitemap XML."""
    urls: list[str] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return urls
    # Handle XML namespace
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    for url_el in root.findall(".//sm:url/sm:loc", ns):
        if url_el.text and "/snowboard-reviews/" in url_el.text:
            # Skip the index page itself
            path = url_el.text.rstrip("/")
            if path != f"{TGR_BASE}/snowboard-reviews":
                urls.append(url_el.text)
    return urls


def _extract_tgr_brand(product_name: str) -> str:
    """Extract brand from a TGR product name, handling multi-word brands."""
    name_lower = product_name.lower()
    for brand in _KNOWN_MULTI_WORD_BRANDS:
        if name_lower.startswith(brand):
            return product_name[:len(brand)]
    return product_name.split()[0] if product_name else ""


def _extract_tgr_review(html: str, url: str) -> ReviewData | None:
    """Extract snowboard review data from a TGR review page.

    Parses qualitative ratings (Great/Good/Average/etc.) for riding
    attributes and converts to a 0-100 score.
    """
    soup = BeautifulSoup(html, "lxml")

    # Extract product name from <h1>
    h1 = soup.select_one("h1")
    if not h1:
        return None
    raw_title = h1.get_text(strip=True)
    # Clean title: remove "Snowboard Review", year ranges, "(with video)" etc.
    product_name = re.sub(
        r"\s*(Snowboard\s+Review|Review).*$", "", raw_title, flags=re.IGNORECASE,
    ).strip()
    # Remove trailing year ranges like "2010-2025"
    product_name = re.sub(r"\s+\d{4}[-–]\d{4}\s*$", "", product_name).strip()

    # Extract brand — handle multi-word brands
    brand = _extract_tgr_brand(product_name)

    # Parse riding attribute ratings from page text
    # TGR format: attribute name followed by rating word, e.g. "Carving Great"
    text = soup.get_text(" ", strip=True)
    scores: list[int] = []
    for attr in _TGR_RIDING_ATTRS:
        # Match "Attribute Rating" pattern (case-insensitive)
        pattern = re.compile(
            rf"\b{re.escape(attr)}\s+(exceptional|great|good|average|below\s+average|bad|poor)\b",
            re.IGNORECASE,
        )
        match = pattern.search(text)
        if match:
            rating_text = match.group(1).lower().strip()
            rating_text = re.sub(r"\s+", " ", rating_text)
            if rating_text in _TGR_RATING_MAP:
                scores.append(_TGR_RATING_MAP[rating_text])

    if not scores:
        return None

    # Average all attribute scores
    score = round(sum(scores) / len(scores))

    return ReviewData(
        product_name=product_name,
        brand=brand,
        score=score,
        award=None,
        url=url,
        category="snowboard",
    )


async def scrape_tgr_reviews(
    *, delay: float = 1.5, max_reviews: int | None = None,
) -> list[ReviewData]:
    """Scrape snowboard review scores from The Good Ride.

    Discovers review URLs via sitemaps, then scrapes each review page
    for qualitative ratings converted to 0-100 scores.
    """
    all_reviews: list[ReviewData] = []

    async with httpx.AsyncClient(
        headers=HEADERS, follow_redirects=True, timeout=30.0,
    ) as client:
        # Phase 1: Discover review URLs from sitemaps
        review_urls: list[str] = []
        for sitemap_url in TGR_SITEMAPS:
            try:
                resp = await client.get(sitemap_url)
                resp.raise_for_status()
            except httpx.HTTPError as e:
                log.error("Failed to fetch TGR sitemap %s: %s", sitemap_url, e)
                continue
            urls = _parse_tgr_sitemap(resp.text)
            review_urls.extend(urls)
            log.info("TGR sitemap %s: found %d review URLs", sitemap_url, len(urls))

        # Deduplicate
        review_urls = list(dict.fromkeys(review_urls))
        if max_reviews:
            review_urls = review_urls[:max_reviews]
        log.info("TGR: %d unique review pages to scrape", len(review_urls))

        # Phase 2: Scrape individual review pages
        for i, url in enumerate(review_urls):
            try:
                resp = await client.get(url)
                resp.raise_for_status()
            except httpx.HTTPError as e:
                log.warning("Failed to fetch TGR review %s: %s", url, e)
                continue

            review = _extract_tgr_review(resp.text, url)
            if review:
                all_reviews.append(review)
                log.info(
                    "TGR [%d/%d]: %s = %d/100 (%s)",
                    i + 1, len(review_urls),
                    review.product_name, review.score,
                    review.award or "no award",
                )
            else:
                log.warning("TGR: Could not extract ratings from %s", url)

            await asyncio.sleep(delay)

    log.info("TGR scraping complete: %d reviews collected", len(all_reviews))
    return all_reviews


# ---------------------------------------------------------------------------
# Fuzzy matching
# ---------------------------------------------------------------------------

# Words to strip from product names before matching
_STRIP_WORDS = re.compile(
    r"\b(20\d{2}|mens?|womens?|women'?s|men'?s|unisex|adult|jr|junior|youth|kids?|"
    r"ski|skis|snowboard|snowboards|boot|boots|binding|bindings|helmet|helmets|"
    r"goggle|goggles|glove|gloves|pant|pants|jacket|jackets|"
    r"system|w/|with)\b",
    re.IGNORECASE,
)

_STRIP_PARENS = re.compile(r"\([^)]*\)")
_MULTI_SPACE = re.compile(r"\s+")


def _normalize(name: str) -> str:
    """Normalize a product name for fuzzy matching."""
    name = _STRIP_PARENS.sub(" ", name)
    name = _STRIP_WORDS.sub(" ", name)
    name = _MULTI_SPACE.sub(" ", name).strip().lower()
    return name


_KNOWN_MULTI_WORD_BRANDS = [
    "lib tech", "never summer", "capita spring break", "jones mountain",
    "black crows", "black diamond", "dinosaurs will die",
]

# Normalize brand names — strip suffixes and map aliases
_BRAND_ALIASES: dict[str, str] = {
    "rome snowboards": "rome",
    "jones snowboards": "jones",
    "jones snowboardss": "jones",  # TGR typo
    "black crow": "black crows",
    "blackcrows": "black crows",
    "k2 snowboarding": "k2",
    "gnu snowboards": "gnu",
    "arbor collective": "arbor",
    "dwd": "dinosaurs will die",
}


def _normalize_brand(brand: str) -> str:
    """Normalize a brand name — strip suffixes and apply aliases."""
    b = brand.lower().strip()
    if b in _BRAND_ALIASES:
        return _BRAND_ALIASES[b]
    # Strip trailing "snowboards", "skis", etc.
    for suffix in (" snowboards", " snowboardss", " skis", " boards"):
        if b.endswith(suffix):
            b = b[:-len(suffix)]
            break
    return b


def _extract_brand(name: str) -> str:
    """Extract the brand name (heuristic, supports multi-word brands)."""
    name_lower = name.strip().lower()
    for brand in _KNOWN_MULTI_WORD_BRANDS:
        if name_lower.startswith(brand):
            return _normalize_brand(brand)
    parts = name.strip().split()
    return _normalize_brand(parts[0]) if parts else ""


def _extract_model_key(name: str) -> str:
    """Extract brand + model identifier for comparison.

    Keeps the first 2-4 significant words (brand + model name/number).
    """
    norm = _normalize(name)
    # Keep only alphanumeric tokens
    tokens = [t for t in norm.split() if len(t) > 1 or t.isdigit()]
    # Return first few tokens which typically capture brand + model
    return " ".join(tokens[:4])


_NUMBERS = re.compile(r"\d+")


def _extract_key_numbers(name: str) -> set[str]:
    """Extract significant model numbers from a product name.

    Filters out years (2020-2029) and single digits (often brand noise like K2).
    """
    nums = set(_NUMBERS.findall(name))
    # Remove years and single digits
    nums -= {str(y) for y in range(2020, 2030)}
    nums = {n for n in nums if len(n) >= 2}
    return nums


def match_review_to_deal(
    deal_name: str,
    reviews: list[ReviewData],
    threshold: float = 0.78,
) -> ReviewData | None:
    """Find the best matching review for a deal name using fuzzy matching.

    Returns the best match above the threshold, or None.
    """
    deal_norm = _normalize(deal_name)
    deal_brand = _extract_brand(deal_name)
    deal_model = _extract_model_key(deal_name)
    deal_numbers = _extract_key_numbers(deal_name)
    if not deal_norm or not deal_brand:
        return None

    best_score = 0.0
    best_review: ReviewData | None = None

    for review in reviews:
        review_norm = _normalize(review.product_name)
        review_brand = _normalize_brand(review.brand) if review.brand else _extract_brand(review.product_name)
        if not review_norm:
            continue

        # Brand must match — prevents cross-brand false positives
        if deal_brand != review_brand:
            continue

        # If both have model numbers, at least one must overlap
        review_numbers = _extract_key_numbers(review.product_name)
        if deal_numbers and review_numbers and not (deal_numbers & review_numbers):
            continue

        # Compare model keys (tighter match on core identity)
        review_model = _extract_model_key(review.product_name)
        ratio = SequenceMatcher(None, deal_model, review_model).ratio()

        # Also check full name similarity as tiebreaker
        full_ratio = SequenceMatcher(None, deal_norm, review_norm).ratio()
        ratio = max(ratio, full_ratio)

        if ratio > best_score:
            best_score = ratio
            best_review = review

    if best_score >= threshold and best_review is not None:
        return best_review
    return None
