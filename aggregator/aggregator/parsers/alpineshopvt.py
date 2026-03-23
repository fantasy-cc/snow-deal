from __future__ import annotations

import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from snow_deals.models import Product
from snow_deals.parsers.base import BaseParser

from aggregator.parsers.common import parse_price as _parse_price

log = logging.getLogger(__name__)


class AlpineShopVTParser(BaseParser):
    """Parser for alpineshopvt.com (BigCommerce) product listing pages."""

    def parse_listing_page(self, html: str, page_url: str) -> list[Product]:
        soup = BeautifulSoup(html, "lxml")
        products: list[Product] = []

        for card in soup.select(".product"):
            product = self._parse_card(card, page_url)
            if product:
                products.append(product)

        log.info("Parsed %d products from %s", len(products), page_url)
        return products

    def get_next_page_url(self, html: str, current_url: str) -> str | None:
        soup = BeautifulSoup(html, "lxml")

        next_link = soup.select_one('a[rel="next"]')
        if not next_link and (pagination := soup.select_one(".pagination")):
            for link in pagination.find_all("a"):
                text = link.get_text(strip=True).lower()
                if text in ("next", "›", "»", ">"):
                    next_link = link
                    break

        if next_link and next_link.get("href"):
            return urljoin(current_url, next_link["href"])
        return None

    def _parse_card(self, card: Tag, page_url: str) -> Product | None:
        # Product name from h4 inside a link
        h4 = card.select_one("a h4")
        if not h4:
            return None
        name = h4.get_text(strip=True)
        if not name:
            return None

        # Product URL: first <a> with href in the card
        first_link = card.select_one("a[href]")
        url = urljoin(page_url, first_link["href"]) if first_link else page_url

        # Prices
        current_price: float | None = None
        original_price: float | None = None

        sale_el = card.select_one(".sale-price")
        was_el = card.select_one(".was-price")
        msrp_el = card.select_one(".msrp")

        if sale_el:
            sale_text = sale_el.get_text(strip=True)
            # Handle price ranges like "Now: $239.99 - $299.99" — take the lower
            prices_in_range = re.findall(r"\$?([\d,]+\.?\d*)", sale_text)
            if prices_in_range:
                parsed = [float(p.replace(",", "")) for p in prices_in_range]
                current_price = min(parsed)

            # Original price: prefer was-price, fall back to msrp
            if was_el:
                original_price = _parse_price(was_el.get_text(strip=True))
            elif msrp_el:
                original_price = _parse_price(msrp_el.get_text(strip=True))
        else:
            # No sale price — use MSRP as current price, no original
            if msrp_el:
                current_price = _parse_price(msrp_el.get_text(strip=True))
            elif was_el:
                current_price = _parse_price(was_el.get_text(strip=True))

        if current_price is None:
            return None

        return Product(
            name=name,
            url=url,
            current_price=current_price,
            original_price=original_price,
        )
