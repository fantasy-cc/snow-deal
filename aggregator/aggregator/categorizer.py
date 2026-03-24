"""Keyword-based product categorization."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from aggregator.config import (
    CATEGORY_RULES, EXCLUDE_KEYWORDS, NOT_HARDGOODS_KEYWORDS,
    SKI_BRANDS, SNOWBOARD_BRANDS, BOOT_BRANDS,
    SKI_BOOT_BRANDS, SNOWBOARD_BOOT_BRANDS,
    SKI_MODEL_NAMES, BOOT_MODEL_NAMES, SNOWBOARD_MODEL_NAMES,
    SKI_BOOT_MODEL_NAMES, SNOWBOARD_BOOT_MODEL_NAMES,
    GOGGLE_MODEL_NAMES, BINDING_MODEL_NAMES,
    MULTI_WORD_MODEL_NAMES,
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


def _disambiguate_boot(name: str, url: str = "") -> str:
    """Disambiguate a generic 'boots' match into 'ski boots' or 'snowboard boots'.

    Uses brand names, model names, and URL clues.
    Returns 'ski boots', 'snowboard boots', or 'boots' if uncertain.
    """
    name_lower = name.lower()
    url_lower = url.lower() if url else ""

    # URL clues
    if "snowboard" in url_lower:
        return "snowboard boots"
    if "ski-boot" in url_lower or "ski_boot" in url_lower:
        return "ski boots"

    # Strip Women's/Men's prefix and leading year for brand check
    clean = name_lower
    for prefix in ("women's ", "men's ", "womens ", "mens ", "unisex "):
        if clean.startswith(prefix):
            clean = clean[len(prefix):]
            break
    parts = clean.split()
    if parts and re.match(r"^20\d{2}$", parts[0]):
        parts = parts[1:]
    first_word = parts[0] if parts else ""
    two_words = " ".join(parts[:2]) if len(parts) >= 2 else ""

    # Check brand
    if first_word in SKI_BOOT_BRANDS or two_words in SKI_BOOT_BRANDS:
        return "ski boots"
    if first_word in SNOWBOARD_BOOT_BRANDS or two_words in SNOWBOARD_BOOT_BRANDS:
        return "snowboard boots"

    # Check model names
    words = set(name_lower.split())
    if words & SKI_BOOT_MODEL_NAMES:
        return "ski boots"
    if words & SNOWBOARD_BOOT_MODEL_NAMES:
        return "snowboard boots"

    # ThirtyTwo alias
    if first_word == "32":
        return "snowboard boots"

    # Brands that make both ski and snowboard boots — check model context
    # Atomic, Salomon, K2, Head, Nordica = primarily ski boot brands
    ski_also_brands = {"atomic", "salomon", "head", "nordica", "k2", "rossignol",
                       "fischer", "volkl", "elan", "blizzard", "dynastar",
                       "dynafit", "movement", "armada"}
    # Vans, Ride, Burton, Nitro, Rome, Bataleon = primarily snowboard boot brands
    snb_also_brands = {"vans", "ride", "burton", "nitro", "rome", "bataleon"}

    if first_word in ski_also_brands:
        return "ski boots"
    if first_word in snb_also_brands:
        return "snowboard boots"

    # GW suffix = GripWalk = ski boots
    if " gw" in name_lower:
        return "ski boots"

    # BOA + touring/backcountry context = ski boots
    if "touring" in name_lower or "backcountry" in name_lower or "alpine" in name_lower:
        return "ski boots"

    return "boots"


def categorize(name: str, url: str = "", product_type: str = "") -> str | None:
    """Return the best-matching category for a product name/URL, or None.

    If keyword matching fails and a Shopify ``product_type`` is provided,
    it is used as a fallback signal.
    """
    text = f"{name} {_url_path(url)}".lower()
    for category, keywords in CATEGORY_RULES:
        if any(kw in text for kw in keywords):
            # Disambiguate generic "boots" into ski/snowboard
            if category == "boots":
                return _disambiguate_boot(name, url)
            return category

    # Fallback: try product_type from Shopify JSON API
    if product_type:
        pt = product_type.lower()
        for category, keywords in CATEGORY_RULES:
            if any(kw in pt for kw in keywords):
                if category == "boots":
                    return _disambiguate_boot(name, url)
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
    if first_word in SKI_BOOT_BRANDS or two_words in SKI_BOOT_BRANDS:
        return "ski boots"
    if first_word in SNOWBOARD_BOOT_BRANDS or two_words in SNOWBOARD_BOOT_BRANDS:
        return "snowboard boots"
    if first_word in BOOT_BRANDS or two_words in BOOT_BRANDS:
        return _disambiguate_boot(name, url)

    # Fallback: multi-word model names (e.g., "Black Pearl", "Huck Knife")
    for phrase, cat in MULTI_WORD_MODEL_NAMES:
        if phrase in name_lower:
            return cat

    # Fallback: known single-word model names (handles cases where brand is missing or is a year)
    words = set(name_lower.split())
    if words & SKI_BOOT_MODEL_NAMES:
        return "ski boots"
    if words & SNOWBOARD_BOOT_MODEL_NAMES:
        return "snowboard boots"
    if words & BOOT_MODEL_NAMES:
        return _disambiguate_boot(name, url)
    if words & GOGGLE_MODEL_NAMES:
        return "goggles"
    if words & BINDING_MODEL_NAMES:
        return "bindings"
    if words & SKI_MODEL_NAMES:
        return "skis"
    if words & SNOWBOARD_MODEL_NAMES:
        return "snowboards"

    return None
