"""Playwright-based browser scraping for JS-rendered and anti-bot sites."""

from __future__ import annotations

import asyncio
import logging
import random
import re
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


# ---------------------------------------------------------------------------
# Per-store extraction configs
# ---------------------------------------------------------------------------

# Each config maps store_type -> dict with:
#   wait_selector: CSS selector to wait for before extraction
#   js_extract: JavaScript snippet evaluated via page.evaluate() that returns
#               an array of {name, url, current_price, original_price, image_url}
#   next_page:  dict with strategy ("click" or "url") and selector/pattern


def _evo_js() -> str:
    return """
    () => {
        const thumbs = document.querySelectorAll('.product-thumb-details');
        return Array.from(thumbs).map(card => {
            const linkEl = card.querySelector('a.product-thumb-link');
            const nameEl = card.querySelector('.product-thumb-title, [class*="product-thumb-title"]');
            // Original price has class "product-thumb-price slash"
            const origPriceEl = card.querySelector('.product-thumb-price.slash');
            // Sale price is .product-thumb-price without .slash
            const allPrices = card.querySelectorAll('.product-thumb-price');
            let salePriceEl = null;
            allPrices.forEach(el => {
                if (!el.classList.contains('slash')) salePriceEl = el;
            });
            const imgEl = card.querySelector('img');

            const parsePrice = (el) => {
                if (!el) return null;
                const m = el.textContent.match(/[\\d,]+\\.\\d{2}/);
                return m ? parseFloat(m[0].replace(/,/g, '')) : null;
            };

            return {
                name: nameEl ? nameEl.textContent.trim()
                     : (linkEl ? linkEl.textContent.trim() : ''),
                url: linkEl ? linkEl.href : '',
                current_price: parsePrice(salePriceEl) || parsePrice(origPriceEl),
                original_price: parsePrice(origPriceEl),
                image_url: imgEl ? (imgEl.src || imgEl.dataset.src || null) : null,
            };
        });
    }
    """


def _backcountry_js() -> str:
    return """
    () => {
        const results = [];
        const seen = new Set();
        const cards = document.querySelectorAll('.chakra-linkbox');
        cards.forEach(card => {
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
            const imgs = card.querySelectorAll('img[alt]');
            let name = '';
            let imgUrl = null;
            imgs.forEach(img => {
                if (!name && img.alt && img.alt.length > 5) {
                    name = img.alt.trim();
                    imgUrl = img.src || null;
                }
            });
            if (!name) return;
            results.push({
                name: name,
                url: link.href,
                current_price: currentPrice,
                original_price: originalPrice !== currentPrice ? originalPrice : null,
                image_url: imgUrl,
            });
        });
        return results;
    }
    """


def _thehouse_js() -> str:
    return """
    () => {
        const tiles = document.querySelectorAll('[data-gtmdata]');
        const seen = new Set();
        const results = [];
        tiles.forEach(t => {
            const raw = t.getAttribute('data-gtmdata');
            if (!raw) return;
            let data;
            try { data = JSON.parse(raw); } catch(e) { return; }
            if (!data || !data.name || !data.price || seen.has(data.name)) return;
            seen.add(data.name);

            const linkEl = t.querySelector('a[href*=".html"]');
            const imgEl = t.querySelector('img');

            let originalPrice = null;
            if (data.percentOff && data.percentOff > 0) {
                originalPrice = Math.round(data.price / (1 - data.percentOff / 100) * 100) / 100;
            }

            results.push({
                name: data.name,
                url: linkEl ? linkEl.href : '',
                current_price: data.price,
                original_price: originalPrice,
                image_url: imgEl ? (imgEl.src || null) : null,
            });
        });
        return results;
    }
    """


def _corbetts_js() -> str:
    return """
    () => {
        const cards = document.querySelectorAll('.card, .product');
        const seen = new Set();
        const results = [];
        cards.forEach(card => {
            const linkEl = card.querySelector('a.card-figure__link, a[href]');
            const nameEl = card.querySelector('.card-title, h4, h3');
            const name = nameEl ? nameEl.textContent.trim() : '';
            if (!name || seen.has(name)) return;
            seen.add(name);
            // BigCommerce: .price--withoutTax for sale, .price--non-sale or .price--rrp for original
            const currentEl = card.querySelector('.price--withoutTax');
            const origEl = card.querySelector('.price--non-sale, .price--rrp');
            const imgEl = card.querySelector('img');

            const parsePrice = (el) => {
                if (!el) return null;
                const m = el.textContent.match(/[\\d,]+\\.\\d{2}/);
                return m ? parseFloat(m[0].replace(/,/g, '')) : null;
            };

            const current = parsePrice(currentEl);
            if (!current) return;

            results.push({
                name: name,
                url: linkEl ? linkEl.href : '',
                current_price: current,
                original_price: parsePrice(origEl),
                image_url: imgEl ? (imgEl.src || imgEl.dataset.src || null) : null,
            });
        });
        return results;
    }
    """


def _levelnine_js() -> str:
    return """
    () => {
        const cards = document.querySelectorAll(
            '.product-item, [class*="product-card"], [class*="product-item"], '
            + '.grid-item, [class*="ProductCard"]'
        );
        return Array.from(cards).map(card => {
            const linkEl = card.querySelector('a[href]');
            const nameEl = card.querySelector(
                '.product-item-name, [class*="product-name"], '
                + '[class*="title"], h2, h3'
            );
            const salePriceEl = card.querySelector(
                '.special-price .price, [class*="sale"], '
                + '[class*="special"], .price'
            );
            const origPriceEl = card.querySelector(
                '.old-price .price, [class*="old"], [class*="original"], '
                + '[class*="compare"], s, del'
            );
            const imgEl = card.querySelector('img');

            const parsePrice = (el) => {
                if (!el) return null;
                const txt = el.textContent.replace(/[^0-9.]/g, '');
                const val = parseFloat(txt);
                return isNaN(val) ? null : val;
            };

            return {
                name: nameEl ? nameEl.textContent.trim() : '',
                url: linkEl ? linkEl.href : '',
                current_price: parsePrice(salePriceEl),
                original_price: parsePrice(origPriceEl),
                image_url: imgEl ? (imgEl.src || imgEl.dataset.src || null) : null,
            };
        });
    }
    """




def _alpineshopvt_js() -> str:
    return """
    () => {
        const cards = document.querySelectorAll('.product, .productGrid .product, [class*="product-card"]');
        return Array.from(cards).map(card => {
            const linkEl = card.querySelector('a[href]');
            const nameEl = card.querySelector('h4, h3, h2, [class*="title"], [class*="name"]');
            // BigCommerce: .price--withoutTax for current, .price--non-sale for "Was" price
            const currentEl = card.querySelector('.price--withoutTax');
            const origEl = card.querySelector('.price--non-sale');
            const imgEl = card.querySelector('img');

            const parsePrice = (el) => {
                if (!el) return null;
                const prices = el.textContent.match(/[\\d,]+\\.\\d{2}/g);
                if (!prices) return null;
                const vals = prices.map(p => parseFloat(p.replace(/,/g, ''))).filter(v => v > 0);
                return vals.length ? Math.min(...vals) : null;
            };

            return {
                name: nameEl ? nameEl.textContent.trim() : '',
                url: linkEl ? linkEl.href : '',
                current_price: parsePrice(currentEl),
                original_price: parsePrice(origEl),
                image_url: imgEl ? (imgEl.src || imgEl.dataset.src || null) : null,
            };
        });
    }
    """


def _thecircle_js() -> str:
    return """
    () => {
        const cards = document.querySelectorAll('.prod-card[data-product-id]');
        const results = [];
        cards.forEach(card => {
            const img = card.querySelector('img[alt]');
            const name = (img && img.alt !== 'Product image') ? img.alt.trim() : '';
            const v = card.querySelector('[data-price]');
            if (!name || !v) return;
            const price = parseFloat(v.getAttribute('data-price'));
            const oldPrice = parseFloat(v.getAttribute('data-old-price'));
            if (!(price > 0)) return;
            results.push({
                name: name,
                url: card.getAttribute('data-url') || '',
                current_price: price,
                original_price: (!isNaN(oldPrice) && oldPrice > 0 && oldPrice !== price) ? oldPrice : null,
                image_url: img ? img.src : null,
            });
        });
        return results;
    }
    """


# Maps store_type -> (wait_selector, js_extract_fn, next_page_selector | None)
STORE_CONFIGS: dict[str, tuple[str, str, str | None]] = {
    "evo": (
        '.product-thumb-details',
        _evo_js(),
        '.page-next a, a[rel="next"], [class*="load-more"]',
    ),
    "backcountry": (
        '.chakra-linkbox .price',
        _backcountry_js(),
        'a[rel="next"], .pagination .next a, [class*="next-page"]',
    ),
    # steepandcheap uses same parser_type="backcountry" in config, handled above
    "thehouse": (
        '.product-tile-card, [data-gtmdata]',
        _thehouse_js(),
        None,  # Infinite scroll, no pagination
    ),
    "corbetts": (
        '.card-title',
        _corbetts_js(),
        'a[rel="next"], .pagination-item--next a, .next a',
    ),
    "levelnine": (
        '.product-item, [class*="product-card"], [class*="product-item"]',
        _levelnine_js(),
        'a.next, a[rel="next"], .pages-item-next a',
    ),
"alpineshopvt": (
        '.product, .productGrid .product',
        _alpineshopvt_js(),
        'a[rel="next"], .pagination .next a',
    ),
    "thecircle": (
        '.prod-card[data-product-id]',
        _thecircle_js(),
        'a.next, a[rel="next"], .pagination .next a',
    ),
    "peterglenn": (
        '.card-title',
        _corbetts_js(),  # Same BigCommerce Stencil theme as Corbetts
        'a[rel="next"], .pagination-item--next a, .next a',
    ),
}


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

        if not name or current_price is None:
            continue
        if current_price <= 0:
            continue

        # Ensure absolute URL
        if url and not url.startswith("http"):
            url = urljoin(base_url, url)

        original_price = item.get("original_price")
        if original_price is not None and original_price <= 0:
            original_price = None

        image_url = item.get("image_url")
        if image_url and not image_url.startswith("http"):
            image_url = urljoin(base_url, image_url)

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
    """Sleep for base + random(0, jitter) seconds."""
    await asyncio.sleep(base + random.random() * jitter)


async def _try_next_page(
    page: Page,
    next_selector: str | None,
) -> bool:
    """Attempt to navigate to the next page. Returns True if navigation happened."""
    if not next_selector:
        return False

    # Try each selector in the comma-separated list
    for selector in next_selector.split(","):
        selector = selector.strip()
        try:
            el = await page.query_selector(selector)
            if el and await el.is_visible():
                href = await el.get_attribute("href")
                if href:
                    await page.goto(href, wait_until="domcontentloaded")
                    return True
                # No href — try clicking
                await el.click()
                await page.wait_for_load_state("domcontentloaded")
                return True
        except Exception:
            continue
    return False


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


async def scrape_with_browser(
    urls: list[str],
    store_name: str,
    store_type: str,
    *,
    max_pages: int = 3,
    delay: float = 2.0,
) -> list[Product]:
    """Scrape product listings using a headless Chromium browser.

    This is intended for stores that block normal HTTP requests (403),
    require JavaScript rendering, or employ anti-bot measures.

    Parameters
    ----------
    urls:
        Starting URLs to scrape (e.g. category / sale pages).
    store_name:
        Human-readable store name for logging.
    store_type:
        Key into ``STORE_CONFIGS`` that determines which CSS selectors
        and extraction JS to use.
    max_pages:
        Maximum number of paginated pages to follow per starting URL.
    delay:
        Base delay in seconds between page navigations.

    Returns
    -------
    list[Product]
        Parsed product objects from the rendered DOM.
    """
    config = STORE_CONFIGS.get(store_type)
    if config is None:
        log.warning(
            "[%s] No browser config for store_type=%r, skipping",
            store_name,
            store_type,
        )
        return []

    wait_selector, js_extract, next_selector = config
    all_products: list[Product] = []

    # Anti-bot sites need longer waits for JS to render products
    anti_bot_types = {"evo", "backcountry", "levelnine", "corbetts"}
    is_anti_bot = store_type in anti_bot_types
    wait_until = "domcontentloaded"
    nav_timeout = 45000 if is_anti_bot else 30000
    selector_timeout = 30000 if is_anti_bot else 15000

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                ],
            )
            context = await browser.new_context(
                user_agent=USER_AGENT,
                viewport=VIEWPORT,
                java_script_enabled=True,
                locale="en-US",
                timezone_id="America/Denver",
            )
            # Hide webdriver flag
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            """)
            page = await context.new_page()

            for url in urls:
                log.info("[%s] Browser navigating to %s", store_name, url)
                pages_scraped = 0

                try:
                    await page.goto(url, wait_until=wait_until, timeout=nav_timeout)
                except Exception as exc:
                    log.error("[%s] Failed to load %s: %s", store_name, url, exc)
                    continue

                # Extra delay for anti-bot sites to let JS render products
                if is_anti_bot:
                    await asyncio.sleep(5.0)

                while pages_scraped < max_pages:
                    pages_scraped += 1

                    # Wait for product elements to appear
                    try:
                        await page.wait_for_selector(
                            wait_selector, timeout=selector_timeout
                        )
                    except Exception:
                        log.warning(
                            "[%s] Timeout waiting for products on %s (page %d)",
                            store_name,
                            page.url,
                            pages_scraped,
                        )
                        break

                    # Pause for lazy-loaded images / prices / variant data
                    await asyncio.sleep(3.0)

                    # Extract product data via JS
                    try:
                        raw: list[dict] = await page.evaluate(js_extract)
                        log.debug(
                            "[%s] Raw JS returned %d items (first: %s)",
                            store_name,
                            len(raw) if raw else 0,
                            raw[0] if raw else "none",
                        )
                    except Exception as exc:
                        log.error(
                            "[%s] JS extraction error on %s: %s",
                            store_name,
                            page.url,
                            exc,
                        )
                        break

                    products = _parse_raw_products(raw, page.url)
                    log.info(
                        "[%s] Page %d: extracted %d products from %s",
                        store_name,
                        pages_scraped,
                        len(products),
                        page.url,
                    )
                    all_products.extend(products)

                    if not products:
                        # No products found — stop paginating this URL
                        break

                    if pages_scraped >= max_pages:
                        break

                    # Attempt pagination
                    await _random_delay(delay)
                    navigated = await _try_next_page(page, next_selector)
                    if not navigated:
                        break

                # Delay before next starting URL
                if url != urls[-1]:
                    await _random_delay(delay)

            await context.close()
            await browser.close()

    except Exception as exc:
        log.error("[%s] Browser scraping failed: %s", store_name, exc)

    log.info(
        "[%s] Browser scraping complete — %d total products",
        store_name,
        len(all_products),
    )
    return all_products
