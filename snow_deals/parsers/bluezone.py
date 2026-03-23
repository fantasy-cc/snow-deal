from __future__ import annotations

import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from snow_deals.models import Product
from snow_deals.parsers.base import BaseParser

log = logging.getLogger(__name__)


def _parse_price(text: str) -> float | None:
    """Extract a numeric price from text like '$639.96' or '639.96'."""
    match = re.search(r"\$?([\d,]+\.?\d*)", text.strip())
    if match:
        return float(match.group(1).replace(",", ""))
    return None


class BlueZoneParser(BaseParser):
    """Parser for bluezonesports.com product listing pages."""

    def parse_listing_page(self, html: str, page_url: str) -> list[Product]:
        soup = BeautifulSoup(html, "lxml")
        products: list[Product] = []

        for card in self._find_product_cards(soup):
            product = self._parse_card(card, page_url)
            if product:
                products.append(product)

        log.info("Parsed %d products from %s", len(products), page_url)
        return products

    def get_next_page_url(self, html: str, current_url: str) -> str | None:
        soup = BeautifulSoup(html, "lxml")

        # BlueZone uses aria-label="Next" on pagination links
        next_link = soup.select_one(
            'a[aria-label="Next"], '
            'a[rel="next"], '
            'li.next a'
        )

        if not next_link:
            for pagination in soup.select(".pagination"):
                for link in pagination.find_all("a"):
                    text = link.get_text(strip=True).lower()
                    if text in ("next", "›", "»", ">"):
                        next_link = link
                        break
                if next_link:
                    break

        if next_link and next_link.get("href"):
            return urljoin(current_url, next_link["href"])
        return None

    def _find_product_cards(self, soup: BeautifulSoup) -> list[Tag]:
        # BlueZone uses .card.product-card
        cards = soup.select(".card.product-card")
        if cards:
            return cards

        for selector in [
            "[class*='product-card']",
            "[class*='product-item']",
            ".product",
        ]:
            cards = soup.select(selector)
            if cards:
                return cards

        return []

    def _parse_card(self, card: Tag, page_url: str) -> Product | None:
        name_el = card.select_one("h3.product-title a, h3 a, h2 a")
        if not name_el:
            return None
        name = name_el.get_text(strip=True)
        if not name:
            return None

        url = urljoin(page_url, name_el.get("href", ""))

        price_div = card.select_one(".product-price")
        if not price_div:
            return None

        current_price, original_price = self._extract_prices(price_div)
        if current_price is None:
            return None

        return Product(
            name=name,
            url=url,
            current_price=current_price,
            original_price=original_price,
        )

    def _extract_prices(self, price_el: Tag) -> tuple[float | None, float | None]:
        current_price: float | None = None
        original_price: float | None = None

        # Current (sale) price is in .text-accent span
        accent = price_el.select_one(".text-accent")
        if accent:
            current_price = _parse_price(accent.get_text())

        # Original price is in <del> tag
        del_el = price_el.select_one("del")
        if del_el:
            original_price = _parse_price(del_el.get_text())

        if current_price is not None:
            return current_price, original_price

        # Fallback: grab any price-like text
        all_prices = []
        for text_node in price_el.find_all(string=re.compile(r"\$[\d,]+\.?\d*")):
            p = _parse_price(text_node)
            if p is not None:
                is_struck = text_node.find_parent(["s", "strike", "del"]) is not None
                all_prices.append((p, is_struck))

        if not all_prices:
            return None, None

        struck = [p for p, s in all_prices if s]
        normal = [p for p, s in all_prices if not s]

        if struck and normal:
            return min(normal), max(struck)
        if len(all_prices) == 1:
            return all_prices[0][0], None

        prices = sorted(p for p, _ in all_prices)
        return prices[0], prices[-1] if len(prices) > 1 else None
