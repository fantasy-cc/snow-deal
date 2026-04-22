"""Playwright-based browser scraping for JS-rendered and anti-bot sites."""

from __future__ import annotations

import asyncio
import logging
import random
from urllib.parse import urljoin

from playwright.async_api import Page, async_playwright

from snow_deals.models import Product

log = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

VIEWPORT = {"width": 1440, "height": 900}

# Shared JS price parser used by most extractors.
_JS_PARSE_PRICE = """
const parsePrice = (el) => {
    if (!el) return null;
    const m = el.textContent.match(/[\\d,]+\\.\\d{2}/);
    return m ? parseFloat(m[0].replace(/,/g, '')) : null;
};
"""

# ---------------------------------------------------------------------------
# Per-store extraction configs
# ---------------------------------------------------------------------------
# Maps store_type -> (wait_selector, js_extract, next_page_selector | None)
# js_extract is a JS IIFE returning [{name, url, current_price, original_price}]

STORE_CONFIGS: dict[str, tuple[str, str, str | None]] = {
    "evo": (
        ".product-thumb-details",
        f"""() => {{
            {_JS_PARSE_PRICE}
            return Array.from(document.querySelectorAll('.product-thumb-details')).map(card => {{
                const linkEl = card.querySelector('a.product-thumb-link');
                const nameEl = card.querySelector('.product-thumb-title, [class*="product-thumb-title"]');
                const origPriceEl = card.querySelector('.product-thumb-price.slash');
                let salePriceEl = null;
                card.querySelectorAll('.product-thumb-price').forEach(el => {{
                    if (!el.classList.contains('slash')) salePriceEl = el;
                }});
                const imgEl = card.querySelector('img');
                return {{
                    name: nameEl ? nameEl.textContent.trim() : (linkEl ? linkEl.textContent.trim() : ''),
                    url: linkEl ? linkEl.href : '',
                    current_price: parsePrice(salePriceEl) || parsePrice(origPriceEl),
                    original_price: parsePrice(origPriceEl),
                    image_url: imgEl ? (imgEl.getAttribute('data-src') || imgEl.src || null) : null,
                }};
            }});
        }}""",
        'a.results-next',
    ),

    "backcountry": (
        ".chakra-linkbox .price",
        """() => {
            const results = [];
            const seen = new Set();
            document.querySelectorAll('.chakra-linkbox').forEach(card => {
                const link = card.querySelector('a.chakra-linkbox__overlay');
                if (!link || seen.has(link.href)) return;
                seen.add(link.href);
                const pe = card.querySelector('.price');
                if (!pe) return;
                const priceText = pe.textContent;
                const currentMatch = priceText.match(/Current price:\\s*\\$([\\d,]+\\.?\\d*)/);
                const origMatch = priceText.match(/Original price:\\s*\\$([\\d,]+\\.?\\d*)/);
                const currentPrice = currentMatch ? parseFloat(currentMatch[1].replace(/,/g, '')) : null;
                const originalPrice = origMatch ? parseFloat(origMatch[1].replace(/,/g, '')) : null;
                if (!currentPrice) return;
                let name = '';
                card.querySelectorAll('img[alt]').forEach(img => {
                    if (!name && img.alt && img.alt.length > 5) {
                        name = img.alt.trim();
                    }
                });
                if (!name) return;
                const imgEl = card.querySelector('img[alt]') || card.querySelector('img');
                results.push({
                    name, url: link.href, current_price: currentPrice,
                    original_price: originalPrice !== currentPrice ? originalPrice : null,
                    image_url: imgEl ? (imgEl.getAttribute('data-src') || imgEl.src || null) : null,
                });
            });
            return results;
        }""",
        'a[rel="next"], a:has-text("Next Page"), a[href*="?page="], .pagination .next a, [class*="next-page"]',
    ),

    "thehouse": (
        ".product-tile-card, [data-gtmdata]",
        """() => {
            const seen = new Set();
            const results = [];
            document.querySelectorAll('div.product[data-gtmdata]').forEach(t => {
                let data;
                try { data = JSON.parse(t.getAttribute('data-gtmdata')); } catch(e) { return; }
                if (!data || !data.name || !data.price || seen.has(data.name)) return;
                seen.add(data.name);
                const linkEl = t.querySelector('a[href*=".html"]');
                // data.price is the ORIGINAL/list price; dimension4 is the sale price
                const originalPrice = parseFloat(data.price);
                let salePrice = data.dimension4 ? parseFloat(data.dimension4) : null;
                if (!salePrice && data.percentOff && data.percentOff > 0) {
                    salePrice = Math.round(originalPrice * (1 - data.percentOff / 100) * 100) / 100;
                }
                const currentPrice = salePrice || originalPrice;
                const imgEl = t.querySelector('img');
                results.push({
                    name: data.name, url: linkEl ? linkEl.href : '',
                    current_price: currentPrice,
                    original_price: (originalPrice !== currentPrice) ? originalPrice : null,
                    image_url: imgEl ? (imgEl.getAttribute('data-src') || imgEl.src || null) : null,
                });
            });
            return results;
        }""",
        None,
    ),

    # BigCommerce stores (Corbetts, Peter Glenn, Alpine Shop VT) share the same extractor
    "bigcommerce": (
        ".card-title",
        f"""() => {{
            {_JS_PARSE_PRICE}
            const seen = new Set();
            const results = [];
            document.querySelectorAll('.card, .product, .productGrid .product').forEach(card => {{
                const nameEl = card.querySelector('.card-title, h4, h3, h2, [class*="title"], [class*="name"]');
                const name = nameEl ? nameEl.textContent.trim() : '';
                if (!name || seen.has(name)) return;
                seen.add(name);
                const linkEl = card.querySelector('a.card-figure__link, a[href]');
                const currentEl = card.querySelector('.price--withoutTax');
                const origEl = card.querySelector('.price--non-sale, .price--rrp');
                const current = parsePrice(currentEl);
                if (!current) return;
                const imgEl = card.querySelector('img');
                results.push({{
                    name, url: linkEl ? linkEl.href : '',
                    current_price: current, original_price: parsePrice(origEl),
                    image_url: imgEl ? (imgEl.getAttribute('data-src') || imgEl.src || null) : null,
                }});
            }});
            return results;
        }}""",
        'a[rel="next"], .pagination-item--next a, .next a, .pagination .next a',
    ),

    "levelnine": (
        'script#__NEXT_DATA__',
        """() => {
            const el = document.getElementById('__NEXT_DATA__');
            if (!el) return [];
            try {
                const data = JSON.parse(el.textContent);
                const apollo = data.props.pageProps.__APOLLO_STATE__;
                if (!apollo) return [];
                const products = [];
                for (const [key, val] of Object.entries(apollo)) {
                    if (!key.startsWith('Product:') || !val.name) continue;
                    // Skip products that aren't in stock (e.g. OUT_OF_STOCK).
                    if (val.stockStatus && val.stockStatus !== 'IN_STOCK') continue;
                    const agg = val.aggregates;
                    if (!agg || !agg.minSalePrice) continue;
                    const salePrice = agg.minSalePrice;
                    const listPrice = agg.minListPrice;
                    const url = val.url || '';
                    const color = Array.isArray(val.colors) && val.colors[0];
                    const imgPath = color ? (color.tileImage || color.pliImage) : null;
                    const brand = val.brand && val.brand.name ? val.brand.name : '';
                    products.push({
                        name: (brand ? brand + ' ' : '') + val.name,
                        url: url.startsWith('http') ? url : 'https://www.levelninesports.com' + url,
                        current_price: salePrice,
                        original_price: (listPrice && listPrice > salePrice) ? listPrice : null,
                        image_url: imgPath ? 'https://content.backcountry.com' + imgPath : null,
                    });
                }
                return products;
            } catch(e) { return []; }
        }""",
        'a:has-text("Next Page")',
    ),

    "thecircle": (
        ".prod-card[data-product-id]",
        """() => {
            const results = [];
            document.querySelectorAll('.prod-card[data-product-id]').forEach(card => {
                const img = card.querySelector('img[alt]');
                const name = (img && img.alt !== 'Product image') ? img.alt.trim() : '';
                const v = card.querySelector('[data-price]');
                if (!name || !v) return;
                const price = parseFloat(v.getAttribute('data-price'));
                const oldPrice = parseFloat(v.getAttribute('data-old-price'));
                if (!(price > 0)) return;
                results.push({
                    name, url: card.getAttribute('data-url') || '',
                    current_price: price,
                    original_price: (!isNaN(oldPrice) && oldPrice > 0 && oldPrice !== price) ? oldPrice : null,
                    image_url: img ? (img.getAttribute('data-src') || img.src || null) : null,
                });
            });
            return results;
        }""",
        'a.next, a[rel="next"], .pagination .next a',
    ),

    "sacredride": (
        "li.product",
        f"""() => {{
            {_JS_PARSE_PRICE}
            return Array.from(document.querySelectorAll('li.post-card.product, li.product')).map(card => {{
                const linkEl = card.querySelector(
                    'a.fusion-rollover-title-link, h4.fusion-rollover-title a, a[href*="/product/"]'
                );
                const nameEl = card.querySelector('h4.fusion-rollover-title, h4.fusion-title-heading, h4, h2');
                const delEl = card.querySelector('p.price del .woocommerce-Price-amount, del .woocommerce-Price-amount');
                const insEl = card.querySelector('p.price ins .woocommerce-Price-amount, ins .woocommerce-Price-amount');
                const singleEl = card.querySelector('p.price .woocommerce-Price-amount, .woocommerce-Price-amount');
                const imgEl = card.querySelector('img');
                return {{
                    name: nameEl ? nameEl.textContent.trim() : '',
                    url: linkEl ? linkEl.href : '',
                    current_price: parsePrice(insEl) || parsePrice(singleEl),
                    original_price: parsePrice(delEl),
                    image_url: imgEl ? (imgEl.getAttribute('data-src') || imgEl.src || null) : null,
                }};
            }});
        }}""",
        "a.next.page-numbers, a[rel='next']",
    ),

    "skiessentials": (
        '[data-testid="product-card-title"]',
        """() => {
            const parsePrice = (el) => {
                if (!el) return null;
                const m = el.textContent.match(/[\d,]+\.?\d*/);
                return m ? parseFloat(m[0].replace(/,/g, '')) : null;
            };
            const seen = new Set();
            const results = [];
            document.querySelectorAll('.relative.border.border-gray-100').forEach(card => {
                const linkEl = card.querySelector('a[href*="/products/"]');
                if (!linkEl) return;
                const href = linkEl.getAttribute('href');
                if (seen.has(href)) return;
                seen.add(href);
                const nameEl = card.querySelector('[data-testid="product-card-title"]');
                const currentEl = card.querySelector('[data-testid="product-price"]');
                const origEl = card.querySelector('[data-testid="compare-at-price"]');
                const imgEl = card.querySelector('img[alt]');
                const current = parsePrice(currentEl);
                if (!current) return;
                results.push({
                    name: nameEl ? nameEl.textContent.trim() : '',
                    url: linkEl.href || '',
                    current_price: current,
                    original_price: parsePrice(origEl),
                    image_url: imgEl ? (imgEl.src || null) : null,
                });
            });
            return results;
        }""",
        None,  # No pagination — all products load on one page
    ),

    "rei": (
        '[data-ui="product-title"]',
        """() => {
            const seen = new Set();
            const results = [];
            document.querySelectorAll('[data-ui="product-title"]').forEach(titleEl => {
                let card = titleEl;
                while (card && card.tagName !== 'LI') card = card.parentElement;
                if (!card) return;
                const linkEl = card.querySelector('a[href*="/product/"]');
                if (!linkEl) return;
                const href = linkEl.getAttribute('href');
                if (seen.has(href)) return;
                seen.add(href);
                const brandEl = card.querySelector('[data-ui="product-brand"]');
                const name = ((brandEl ? brandEl.textContent.trim() + ' ' : '') + titleEl.textContent.trim()).trim();
                const spans = card.querySelectorAll('span');
                let currentPrice = null;
                let originalPrice = null;
                for (const span of spans) {
                    const text = span.textContent.trim();
                    if (text.match(/^\$[\d,.]+$/)) {
                        const price = parseFloat(text.replace(/[$,]/g, ''));
                        if (!currentPrice) currentPrice = price;
                        else if (!originalPrice) originalPrice = price;
                    }
                }
                const imgEl = card.querySelector('img[id^="image-"]');
                if (!currentPrice) return;
                results.push({
                    name,
                    url: linkEl.href.startsWith('http') ? linkEl.href : 'https://www.rei.com' + href,
                    current_price: currentPrice,
                    original_price: originalPrice,
                    image_url: imgEl ? imgEl.src : null,
                });
            });
            return results;
        }""",
        None,  # Rely on _try_next_page fallback which handles ?page=N URL patterns
    ),

    "mec": (
        'script#__NEXT_DATA__',
        """() => {
            const el = document.getElementById('__NEXT_DATA__');
            if (!el) return [];
            try {
                const data = JSON.parse(el.textContent);
                const results = data.props.pageProps.serverState.initialResults.products_en.results;
                const products = [];
                for (const group of results) {
                    for (const hit of (group.hits || [])) {
                        const title = (hit.title || '').trim();
                        const urlPath = hit.url || '';
                        const salePrice = hit.salePrice;
                        if (!title || !urlPath || !salePrice || salePrice <= 0) continue;
                        // Skip items that aren't available (e.g. OUT_OF_STOCK / NO_INVENTORY).
                        const invStatus = hit.inventoryStatus;
                        if (invStatus && invStatus !== 'IN_STOCK' && invStatus !== 'LOW_STOCK') continue;
                        const price = hit.price;
                        products.push({
                            name: title,
                            url: urlPath.startsWith('http') ? urlPath : 'https://www.mec.ca' + urlPath,
                            current_price: salePrice,
                            original_price: (price && price > salePrice) ? price : null,
                            image_url: hit.image || hit.swatch || null,
                        });
                    }
                }
                return products;
            } catch(e) { return []; }
        }""",
        '.ais-Pagination-item--nextPage a',
    ),
}

# Aliases — stores sharing the same extraction logic
STORE_CONFIGS["corbetts"] = STORE_CONFIGS["bigcommerce"]
STORE_CONFIGS["peterglenn"] = STORE_CONFIGS["bigcommerce"]
STORE_CONFIGS["alpineshopvt"] = STORE_CONFIGS["bigcommerce"]

# Anti-bot stores need longer timeouts
_ANTI_BOT_TYPES = {"evo", "backcountry", "levelnine", "corbetts", "rei", "mec", "thehouse"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_raw_products(raw: list[dict], base_url: str) -> list[Product]:
    """Convert raw JS-extracted dicts to Product instances, filtering invalid."""
    products: list[Product] = []
    for item in raw:
        name = (item.get("name") or "").strip()
        url = (item.get("url") or "").strip()
        current_price = item.get("current_price")

        if not name or current_price is None or current_price <= 0:
            continue

        if url and not url.startswith("http"):
            url = urljoin(base_url, url)

        original_price = item.get("original_price")
        if original_price is not None and original_price <= 0:
            original_price = None

        image_url = (item.get("image_url") or "").strip() or None

        products.append(
            Product(
                name=name,
                url=url,
                current_price=round(current_price, 2),
                original_price=round(original_price, 2) if original_price else None,
                image_url=image_url,
            )
        )
    return products


async def _random_delay(base: float = 1.0, jitter: float = 2.0) -> None:
    await asyncio.sleep(base + random.random() * jitter)


async def _try_next_page(page: Page, next_selector: str | None) -> bool:
    """Attempt to navigate to the next page. Returns True if navigation happened."""
    if not next_selector:
        return False

    # Try explicit CSS selectors first
    for selector in next_selector.split(","):
        selector = selector.strip()
        try:
            el = await page.query_selector(selector)
            if not el:
                continue
            href = await el.get_attribute("href")
            if href and href.startswith("#"):
                # SPA hash navigation — click via JS (may be off-screen) and wait
                await el.evaluate("el => el.click()")
                await asyncio.sleep(3.0)
                return True
            if await el.is_visible():
                if href:
                    # Resolve relative URLs via the element's .href property
                    abs_href = await el.evaluate("el => el.href")
                    await page.goto(abs_href or href, wait_until="domcontentloaded")
                    return True
                await el.click()
                await page.wait_for_load_state("domcontentloaded")
                return True
        except Exception:
            continue

    # Fallback: find "Next Page" text link or next page number in pagination
    try:
        next_url = await page.evaluate("""() => {
            // Try "Next Page" text link
            for (const a of document.querySelectorAll('a')) {
                const txt = a.textContent.trim().toLowerCase();
                if ((txt === 'next page' || txt === 'next' || txt === '›' || txt === '»')
                    && a.href && a.href !== window.location.href) {
                    return a.href;
                }
            }
            // Try page number links: find current page and get next
            const currentUrl = window.location.href;
            const pageMatch = currentUrl.match(/[?&]page=(\\d+)|\\/page(\\d+)/);
            const currentPage = pageMatch ? parseInt(pageMatch[1] || pageMatch[2]) : 1;
            const nextPage = currentPage + 1;
            for (const a of document.querySelectorAll('a[href]')) {
                const href = a.href;
                if (href.includes('page=' + nextPage) || href.includes('/page' + nextPage)) {
                    return href;
                }
            }
            return null;
        }""")
        if next_url:
            await page.goto(next_url, wait_until="domcontentloaded")
            return True
    except Exception:
        pass

    return False


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


async def scrape_with_browser(
    urls: list[str],
    store_name: str,
    store_type: str,
    *,
    max_pages: int = 25,
    delay: float = 2.0,
) -> list[Product]:
    """Scrape product listings using a headless Chromium browser."""
    config = STORE_CONFIGS.get(store_type)
    if config is None:
        log.warning("[%s] No browser config for store_type=%r, skipping", store_name, store_type)
        return []

    wait_selector, js_extract, next_selector = config
    all_products: list[Product] = []
    seen_urls: set[str] = set()

    is_anti_bot = store_type in _ANTI_BOT_TYPES
    nav_timeout = 45000 if is_anti_bot else 30000
    selector_timeout = 30000 if is_anti_bot else 15000

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
            )
            context = await browser.new_context(
                user_agent=USER_AGENT, viewport=VIEWPORT,
                java_script_enabled=True, locale="en-US", timezone_id="America/Denver",
            )
            await context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
            )
            page = await context.new_page()

            for url in urls:
                log.info("[%s] Browser navigating to %s", store_name, url)
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=nav_timeout)
                except Exception as exc:
                    log.error("[%s] Failed to load %s: %s", store_name, url, exc)
                    continue

                if is_anti_bot:
                    await asyncio.sleep(5.0)

                for page_num in range(1, max_pages + 1):
                    try:
                        # Use "attached" state for non-visible elements (e.g. <script>)
                        wait_state = "attached" if wait_selector.startswith("script") else "visible"
                        await page.wait_for_selector(wait_selector, timeout=selector_timeout, state=wait_state)
                    except Exception:
                        log.warning("[%s] Timeout waiting for products (page %d)", store_name, page_num)
                        break

                    await asyncio.sleep(3.0)

                    try:
                        raw: list[dict] = await page.evaluate(js_extract)
                    except Exception as exc:
                        log.error("[%s] JS extraction error: %s", store_name, exc)
                        break

                    products = _parse_raw_products(raw, page.url)
                    new_products = [p for p in products if p.url not in seen_urls]
                    seen_urls.update(p.url for p in new_products)
                    log.info("[%s] Page %d: %d products (%d new) from %s", store_name, page_num, len(products), len(new_products), page.url)
                    all_products.extend(new_products)

                    if not products or page_num >= max_pages:
                        break

                    await _random_delay(delay)
                    if not await _try_next_page(page, next_selector):
                        break

                if url != urls[-1]:
                    await _random_delay(delay)

            await context.close()
            await browser.close()

    except Exception as exc:
        log.error("[%s] Browser scraping failed: %s", store_name, exc)

    log.info("[%s] Browser scraping complete — %d total products", store_name, len(all_products))
    return all_products
