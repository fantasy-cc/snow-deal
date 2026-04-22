from __future__ import annotations

import json
import logging
import re
from urllib.parse import urlparse

from snow_deals.models import Product
from snow_deals.parsers.base import BaseParser

log = logging.getLogger(__name__)

MAX_API_PAGES = 10


class ShopifyParser(BaseParser):
    """
    Parser for Shopify stores that expose /collections/{handle}/products.json.

    Works with Aspen Ski and Board and other Shopify-based retailers.
    Instead of scraping HTML, this parser uses the Shopify JSON API which
    provides structured price data including compare_at_price for discounts.
    """

    def _get_collection_handle(self, url: str) -> str | None:
        m = re.search(r"/collections/([^/?#]+)", urlparse(url).path)
        return m.group(1) if m else None

    def parse_listing_page(self, html: str, page_url: str) -> list[Product]:
        """Parse a Shopify products.json response (not HTML)."""
        try:
            data = json.loads(html)
        except json.JSONDecodeError:
            log.warning("Response is not JSON, skipping: %s", page_url)
            return []

        products: list[Product] = []
        origin = f"{urlparse(page_url).scheme}://{urlparse(page_url).netloc}"

        for item in data.get("products", []):
            variants = item.get("variants") or []
            # Skip products with no available variants — they're sold out.
            # Shopify variants have `available: bool`; if the field is missing
            # we assume available (some themes omit it).
            if variants and not any(v.get("available", True) for v in variants):
                continue

            # Prefer a live variant for pricing so out-of-stock leads don't skew it.
            variant = next(
                (v for v in variants if v.get("available", True)),
                variants[0] if variants else {},
            )
            price = float(variant.get("price", 0))
            compare = variant.get("compare_at_price")
            original_price = float(compare) if compare else None

            # Extract available sizes from variants
            sizes: list[str] = []
            for v in variants:
                if not v.get("available", True):
                    continue
                # Size is typically option1 or option2; check option names
                for opt_key in ("option1", "option2", "option3"):
                    val = v.get(opt_key)
                    if val and val not in ("Default Title",) and val not in sizes:
                        sizes.append(val)

            # Extract first product image URL
            image_url = None
            images = item.get("images") or []
            if images:
                image_url = images[0].get("src")
            elif item.get("image"):
                image_url = item["image"].get("src")

            products.append(Product(
                name=item.get("title", "Unknown"),
                url=f"{origin}/products/{item.get('handle', '')}",
                current_price=price,
                original_price=original_price,
                sizes=sizes or None,
                product_type=item.get("product_type") or None,
                image_url=image_url,
            ))

        log.info("Parsed %d products from %s", len(products), page_url)
        return products

    def get_next_page_url(self, html: str, current_url: str) -> str | None:
        """Check if there are more pages of JSON results."""
        try:
            data = json.loads(html)
        except json.JSONDecodeError:
            return None

        products = data.get("products", [])
        if len(products) < 250:
            return None

        parsed = urlparse(current_url)
        # Increment page parameter
        m = re.search(r"[?&]page=(\d+)", current_url)
        current_page = int(m.group(1)) if m else 1
        next_page = current_page + 1

        if next_page > MAX_API_PAGES:
            return None

        base = current_url.split("?")[0]
        return f"{base}?limit=250&page={next_page}"

    def get_api_url(self, page_url: str) -> str | None:
        """Convert a collection URL to the Shopify JSON API URL."""
        handle = self._get_collection_handle(page_url)
        if not handle:
            return None
        parsed = urlparse(page_url)
        return f"{parsed.scheme}://{parsed.netloc}/collections/{handle}/products.json?limit=250&page=1"
