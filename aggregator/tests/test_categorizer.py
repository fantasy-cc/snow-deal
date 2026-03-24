"""Tests for keyword-based product categorization."""

from aggregator.categorizer import categorize, is_excluded


def test_ski():
    assert categorize("Atomic Bent 100 Skis 2025") == "skis"


def test_snowboard():
    assert categorize("Burton Custom Snowboard") == "snowboards"


def test_ski_boots_not_skis():
    """Compound term 'ski boot' should match 'ski boots', not 'skis'."""
    assert categorize("Salomon S/Pro 130 Ski Boots") == "ski boots"


def test_snowboard_boots():
    """Snowboard boot should match 'snowboard boots'."""
    assert categorize("Burton Photon BOA Snowboard Boots") == "snowboard boots"


def test_generic_boot_ski_brand():
    """Generic 'boot' with ski brand should resolve to 'ski boots'."""
    assert categorize("Lange LX 120 HV GW Ski Boots") == "ski boots"


def test_generic_boot_snowboard_brand():
    """Generic 'boot' with snowboard brand should resolve to 'snowboard boots'."""
    assert categorize("ThirtyTwo Lashed Double BOA") == "snowboard boots"


def test_bindings():
    assert categorize("Marker Griffon 13 Ski Bindings") == "bindings"


def test_helmet():
    assert categorize("Smith Vantage MIPS Helmet") == "helmets"


def test_goggles():
    assert categorize("Oakley Flight Deck Goggles") == "goggles"


def test_jacket():
    assert categorize("Arc'teryx Beta LT Jacket") == "jackets"


def test_pants():
    assert categorize("The North Face Freedom Pants") == "pants"


def test_gloves():
    assert categorize("Hestra Fall Line Gloves") == "gloves"


def test_poles():
    assert categorize("Black Diamond Traverse Ski Poles") == "poles"


def test_uncategorized():
    assert categorize("Generic Product Name") is None


def test_url_fallback():
    """Category can be detected from URL when name is generic."""
    assert categorize("Atomic Pro", url="/collections/skis") == "skis"


def test_ski_bag_is_accessory():
    """Ski bags should be accessories, not skis."""
    assert categorize("Dakine Fall Line Ski Roller Bag") == "accessories"
    assert categorize("Burton Space Sack Snowboard Bag") == "accessories"
    assert categorize("High Sierra Wheeled Double Ski Bag") == "accessories"


def test_mips_helmet():
    """MIPS keyword should categorize as helmets."""
    assert categorize("Smith Nexus MIPS") == "helmets"


def test_snowshoe_is_accessory():
    assert categorize("Atlas Range-BC Snowshoe") == "accessories"


def test_exclude_non_snow():
    """Non-snow-sport items should be excluded."""
    assert is_excluded("Connelly Reverb Wakeboard")
    assert is_excluded("Five Ten Freerider Mountain Bike Shoes")
    assert is_excluded("Arbor Cruiser Skateboard")
    assert not is_excluded("Atomic Bent 100 Skis")
    assert not is_excluded("Burton Custom Snowboard")
