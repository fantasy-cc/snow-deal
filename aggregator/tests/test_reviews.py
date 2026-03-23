"""Tests for review fuzzy matching and brand extraction."""

from aggregator.reviews import (
    ReviewData,
    _extract_brand,
    _normalize,
    match_review_to_deal,
)


def _make_review(name: str, brand: str = "", score: int = 80) -> ReviewData:
    return ReviewData(
        product_name=name,
        brand=brand or name.split()[0],
        score=score,
        award=None,
        url=f"https://example.com/{name.replace(' ', '-').lower()}",
        category="skis",
    )


class TestExtractBrand:
    def test_single_word(self):
        assert _extract_brand("Atomic Bent 100") == "atomic"

    def test_multi_word_lib_tech(self):
        assert _extract_brand("Lib Tech Skate Banana") == "lib tech"

    def test_multi_word_never_summer(self):
        assert _extract_brand("Never Summer Proto Synthesis") == "never summer"

    def test_empty(self):
        assert _extract_brand("") == ""


class TestNormalize:
    def test_strips_year(self):
        assert "2025" not in _normalize("Atomic Bent 100 2025")

    def test_strips_gender(self):
        norm = _normalize("Salomon QST 98 Women's Skis")
        assert "women" not in norm
        assert "skis" not in norm

    def test_strips_parentheses(self):
        assert "(with video)" not in _normalize("Burton Custom (with video)")


class TestMatchReview:
    def test_exact_match(self):
        reviews = [_make_review("Atomic Bent 100", "Atomic")]
        result = match_review_to_deal("Atomic Bent 100 Skis 2025", reviews)
        assert result is not None
        assert result.product_name == "Atomic Bent 100"

    def test_brand_mismatch_rejected(self):
        reviews = [_make_review("Salomon QST 98", "Salomon")]
        result = match_review_to_deal("Atomic Bent 100", reviews)
        assert result is None

    def test_multi_word_brand_match(self):
        reviews = [_make_review("Lib Tech Skate Banana", "Lib Tech")]
        result = match_review_to_deal("Lib Tech Skate Banana Snowboard 2025", reviews)
        assert result is not None

    def test_no_reviews(self):
        result = match_review_to_deal("Atomic Bent 100", [])
        assert result is None

    def test_model_number_mismatch(self):
        """Different model numbers should not match."""
        reviews = [_make_review("Atomic Bent 100", "Atomic")]
        result = match_review_to_deal("Atomic Bent 120 Skis", reviews)
        assert result is None

    def test_best_match_selected(self):
        reviews = [
            _make_review("Atomic Bent 100", "Atomic", score=85),
            _make_review("Atomic Bent 120", "Atomic", score=75),
        ]
        result = match_review_to_deal("Atomic Bent 100 Skis 2025", reviews)
        assert result is not None
        assert result.score == 85
