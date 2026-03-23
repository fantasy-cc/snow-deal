"""Tests for the shared price parser."""

from aggregator.parsers.common import parse_price


def test_basic_dollar():
    assert parse_price("$269.99") == 269.99


def test_dollar_with_comma():
    assert parse_price("$1,250.00") == 1250.00


def test_canadian_dollar():
    assert parse_price("C$485.99") == 485.99


def test_no_dollar_sign():
    assert parse_price("579.99") == 579.99


def test_with_label():
    assert parse_price("Was: $299.99") == 299.99


def test_empty_string():
    assert parse_price("") is None


def test_no_price():
    assert parse_price("free shipping") is None


def test_integer_price():
    assert parse_price("$500") == 500.0
