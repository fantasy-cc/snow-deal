"""Tests for the scraper module — product-to-deal conversion and kids filtering."""

from datetime import datetime

from aggregator.scraper import _is_kids_product, _products_to_deals
from snow_deals.models import Product


def test_kids_filter():
    assert _is_kids_product("Atomic Bent Junior 100") is True
    assert _is_kids_product("Burton Grom Snowboard") is True
    assert _is_kids_product("K2 Youth Skis") is True
    assert _is_kids_product("Atomic Bent 100") is False


def test_products_to_deals():
    products = [
        Product(name="Atomic Bent 100", url="https://example.com/bent",
                current_price=499.99, original_price=599.99),
        Product(name="Burton Grom Kids Snowboard", url="https://example.com/grom",
                current_price=199.99, original_price=249.99),
    ]
    deals = _products_to_deals(products, "TestStore")
    # Kids product should be filtered out
    assert len(deals) == 1
    assert deals[0].name == "Atomic Bent 100"
    assert deals[0].store == "TestStore"
    # "Atomic" is a known ski brand, so brand-matching categorizes it
    assert deals[0].category == "skis"
