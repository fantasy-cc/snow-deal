"""Tests for browser.py store config registry."""

from aggregator.browser import STORE_CONFIGS, _parse_raw_products
from snow_deals.models import Product


def test_all_expected_configs_exist():
    expected = {"evo", "backcountry", "thehouse", "bigcommerce",
                "levelnine", "thecircle", "sacredride"}
    assert expected.issubset(set(STORE_CONFIGS.keys()))


def test_aliases():
    assert STORE_CONFIGS["corbetts"] is STORE_CONFIGS["bigcommerce"]
    assert STORE_CONFIGS["peterglenn"] is STORE_CONFIGS["bigcommerce"]
    assert STORE_CONFIGS["alpineshopvt"] is STORE_CONFIGS["bigcommerce"]


def test_config_tuple_shape():
    for name, config in STORE_CONFIGS.items():
        assert len(config) == 3, f"{name} config should be (wait_sel, js, next_sel)"
        wait_sel, js_extract, next_sel = config
        assert isinstance(wait_sel, str) and wait_sel
        assert isinstance(js_extract, str) and js_extract
        assert next_sel is None or isinstance(next_sel, str)


def test_parse_raw_products():
    raw = [
        {"name": "Test Ski", "url": "/product/test", "current_price": 499.99,
         "original_price": 599.99},
        {"name": "", "url": "/bad", "current_price": 100},  # empty name, should be filtered
        {"name": "No Price", "url": "/bad2", "current_price": None},  # no price, filtered
    ]
    products = _parse_raw_products(raw, "https://example.com")
    assert len(products) == 1
    assert products[0].name == "Test Ski"
    assert products[0].url == "https://example.com/product/test"


def test_parse_raw_products_absolute_url():
    raw = [{"name": "Abs URL", "url": "https://store.com/product",
            "current_price": 100, "original_price": None}]
    products = _parse_raw_products(raw, "https://example.com")
    assert products[0].url == "https://store.com/product"
