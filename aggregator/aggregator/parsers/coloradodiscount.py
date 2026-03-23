from __future__ import annotations

import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from snow_deals.models import Product
from snow_deals.parsers.base import BaseParser

from aggregator.parsers.common import parse_price as _parse_price

log = logging.getLogger(__name__)


class ColoradoDiscountParser(BaseParser):
    """Parser for coloradodiscountskis.com product listing pages."""

    def parse_listing_page(self, html: str, page_url: str) -> list[Product]:
        soup = BeautifulSoup(html, "lxml")
        products: list[Product] = []

        for li in soup.find_all("li"):
            product = self._parse_li(li, page_url)
            if product:
                products.append(product)

        log.info("Parsed %d products from %s", len(products), page_url)
        return products

    def get_next_page_url(self, html: str, current_url: str) -> str | None:
        # This site uses separate pages per brand/year; no pagination within
        # a single listing page.
        return None

    def _parse_li(self, li: Tag, page_url: str) -> Product | None:
        links = li.find_all("a")
        if not links:
            return None

        # Find the first <a> with a title attribute for the product URL
        titled_link: Tag | None = None
        for link in links:
            if link.get("title"):
                titled_link = link
                break

        # Product name: prefer second <a> text, fall back to title attr
        name: str | None = None
        if len(links) >= 2:
            name = links[1].get_text(strip=True)
        if not name and titled_link:
            name = titled_link.get("title", "").strip()
        if not name:
            return None

        # Product URL
        if titled_link and titled_link.get("href"):
            url = urljoin(page_url, titled_link["href"])
        else:
            url = urljoin(page_url, links[0].get("href", ""))

        # Prices: extract all dollar amounts from the li's text content
        # The text often looks like "$1,250.00$579.99"
        li_text = li.get_text()
        price_matches = re.findall(r"\$[\d,]+\.?\d*", li_text)
        if not price_matches:
            return None

        parsed_prices = []
        for pm in price_matches:
            p = _parse_price(pm)
            if p is not None:
                parsed_prices.append(p)

        if not parsed_prices:
            return None

        current_price: float
        original_price: float | None = None

        if len(parsed_prices) == 1:
            current_price = parsed_prices[0]
        else:
            # First price is original, second is sale price
            original_price = parsed_prices[0]
            current_price = parsed_prices[1]

        return Product(
            name=name,
            url=url,
            current_price=current_price,
            original_price=original_price,
        )
