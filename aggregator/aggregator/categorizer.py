"""Keyword-based product categorization."""

from __future__ import annotations

from urllib.parse import urlparse

from aggregator.config import (
    CATEGORY_RULES, EXCLUDE_KEYWORDS, NOT_HARDGOODS_KEYWORDS,
    SKI_BRANDS, SNOWBOARD_BRANDS,
)


def _url_path(url: str) -> str:
    """Extract just the path from a URL, ignoring the domain.

    This prevents store domains like 'skiisandbiikes.com' or 'skipro.com'
    from falsely matching the 'ski' keyword.
    """
    if not url:
        return ""
    try:
        return urlparse(url).path
    except Exception:
        return url


def is_excluded(name: str, url: str = "") -> bool:
    """Return True if the product is a non-snow-sport item that should be excluded."""
    text = f"{name} {_url_path(url)}".lower()
    return any(kw in text for kw in EXCLUDE_KEYWORDS)


def categorize(name: str, url: str = "", product_type: str = "") -> str | None:
    """Return the best-matching category for a product name/URL, or None.

    If keyword matching fails and a Shopify ``product_type`` is provided,
    it is used as a fallback signal.
    """
    text = f"{name} {_url_path(url)}".lower()
    for category, keywords in CATEGORY_RULES:
        if any(kw in text for kw in keywords):
            return category

    # Fallback: try product_type from Shopify JSON API
    if product_type:
        pt = product_type.lower()
        for category, keywords in CATEGORY_RULES:
            if any(kw in pt for kw in keywords):
                return category

    # Fallback: brand-name matching (first word of product name)
    # Skip if the product looks like clothing/accessories, not hardgoods
    name_lower = name.lower()
    if any(kw in name_lower for kw in NOT_HARDGOODS_KEYWORDS):
        return None

    first_word = name_lower.split()[0] if name_lower else ""
    # Also check two-word brands like "black crows", "lib tech"
    two_words = " ".join(name_lower.split()[:2]) if len(name_lower.split()) >= 2 else ""

    if first_word in SKI_BRANDS or two_words in SKI_BRANDS:
        return "skis"
    if first_word in SNOWBOARD_BRANDS or two_words in SNOWBOARD_BRANDS:
        return "snowboards"

    return None
