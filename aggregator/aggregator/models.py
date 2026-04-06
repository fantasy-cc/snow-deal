"""Aggregated deal model wrapping snow_deals.Product."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class AggregatedDeal:
    """A deal record enriched with store and category metadata."""

    id: int | None
    store: str
    name: str
    url: str
    current_price: float
    original_price: float | None
    discount_pct: float
    category: str | None
    sizes: str | None  # Comma-separated available sizes
    length_min: int | None  # Shortest length in cm (extracted from sizes)
    length_max: int | None  # Longest length in cm (extracted from sizes)
    scraped_at: datetime
    image_url: str | None = None
    brand: str | None = None
    review_score: int | None = None
    review_award: str | None = None
    review_url: str | None = None
