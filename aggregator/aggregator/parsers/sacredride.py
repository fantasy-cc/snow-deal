"""Parser for sacredride.ca (WooCommerce) product listing pages."""

from __future__ import annotations

import logging
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from snow_deals.models import Product
from snow_deals.parsers.base import BaseParser

from aggregator.parsers.common import parse_price as _parse_price

log = logging.getLogger(__name__)


class SacredRideParser(BaseParser):
    """Parser for sacredride.ca WooCommerce product listing pages."""

    def parse_listing_page(self, html: str, page_url: str) -> list[Product]:
        soup = BeautifulSoup(html, "lxml")
        products: list[Product] = []

        for card in soup.select("li.product"):
            # WooCommerce adds the `outofstock` class to the product <li>
            # when the item is not purchasable. Skip those.
            classes = card.get("class") or []
            if "outofstock" in classes or "out-of-stock" in classes:
                continue
            product = self._parse_card(card, page_url)
            if product:
                products.append(product)

        log.info("Parsed %d products from %s", len(products), page_url)
        return products

    def get_next_page_url(self, html: str, current_url: str) -> str | None:
        soup = BeautifulSoup(html, "lxml")
        next_link = soup.select_one("a.next.page-numbers, a[rel='next'], link[rel='next']")
        if next_link and next_link.get("href"):
            return urljoin(current_url, next_link["href"])
        return None

    def _parse_card(self, card: Tag, page_url: str) -> Product | None:
        # Product URL
        link = card.select_one("a.fusion-rollover-title-link, h4.fusion-rollover-title a, a[href*='/product/']")
        if not link or not link.get("href"):
            return None
        url = urljoin(page_url, link["href"])

        # Product name
        name_el = card.select_one("h4.fusion-rollover-title, h4, h2")
        if not name_el:
            return None
        name = name_el.get_text(strip=True)
        if not name:
            return None

        # Prices — WooCommerce uses <del> for original and <ins> for sale price
        current_price: float | None = None
        original_price: float | None = None

        del_el = card.select_one("p.price del .woocommerce-Price-amount, del .woocommerce-Price-amount")
        ins_el = card.select_one("p.price ins .woocommerce-Price-amount, ins .woocommerce-Price-amount")

        if del_el and ins_el:
            original_price = _parse_price(del_el.get_text(strip=True))
            current_price = _parse_price(ins_el.get_text(strip=True))
        else:
            # Not on sale — single price
            price_el = card.select_one("p.price .woocommerce-Price-amount, .woocommerce-Price-amount")
            if price_el:
                current_price = _parse_price(price_el.get_text(strip=True))

        if current_price is None:
            return None

        return Product(
            name=name,
            url=url,
            current_price=current_price,
            original_price=original_price,
        )
