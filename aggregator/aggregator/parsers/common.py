"""Shared utilities for HTML parsers."""

from __future__ import annotations

import re


def parse_price(text: str) -> float | None:
    """Extract a numeric price from text like '$269.99', 'C$485.99', or '579.99'."""
    match = re.search(r"(?:C?\$)?([\d,]+\.?\d*)", text.strip())
    if match:
        return float(match.group(1).replace(",", ""))
    return None
