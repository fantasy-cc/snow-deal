"""Store registry and category configuration."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class StoreConfig:
    """Configuration for a single retailer."""

    name: str
    domain: str
    scrape_urls: list[str] = field(default_factory=list)
    parser_type: str = "shopify"
    use_browser: bool = False  # True = use Playwright headless browser
    tax_free: bool = False  # True = store likely doesn't charge US sales tax


# ---------------------------------------------------------------------------
# Store registry — ~16 ski/snowboard retailers sourced from uscardforum.com
# ---------------------------------------------------------------------------

STORES: list[StoreConfig] = [
    # Shopify-based (confirmed Shopify, reuse ShopifyParser from snow_deals)
    StoreConfig(
        "Aspen Ski and Board", "aspenskiandboard.com",
        scrape_urls=[
            "https://www.aspenskiandboard.com/collections/skis",
            "https://www.aspenskiandboard.com/collections/outlet",
        ],
        parser_type="shopify",
    ),
    StoreConfig(
        "PRFO", "prfo.com",
        scrape_urls=[
            "https://www.prfo.com/collections/sales",
            "https://www.prfo.com/collections/ski-skis",
        ],
        parser_type="shopify",
        tax_free=True,  # Canadian store
    ),

    # Sports Basement — confirmed Shopify
    StoreConfig(
        "Sports Basement", "sportsbasement.com",
        scrape_urls=[
            "https://www.sportsbasement.com/collections/skis",
            "https://www.sportsbasement.com/collections/snow",
        ],
        parser_type="shopify",
    ),

    # BlueZone — has working BS4 parser
    StoreConfig(
        "BlueZone Sports", "bluezonesports.com",
        scrape_urls=[
            "https://www.bluezonesports.com/skis",
            "https://www.bluezonesports.com/snowboards",
        ],
        parser_type="bluezone",
    ),

    # BS4 HTML parsers
    StoreConfig(
        "Alpine Shop VT", "alpineshopvt.com",
        scrape_urls=[
            "https://www.alpineshopvt.com/activities/skiing/",
            "https://www.alpineshopvt.com/activities/snowboard/",
        ],
        parser_type="alpineshopvt",
        use_browser=True,
    ),
    StoreConfig(
        "The Circle Whistler", "thecirclewhistler.com",
        scrape_urls=[
            "https://www.thecirclewhistler.com/sale/",
            "https://www.thecirclewhistler.com/snow/",
        ],
        parser_type="thecircle",
        use_browser=True,
        tax_free=True,  # Canadian store
    ),
    StoreConfig(
        "Colorado Discount Skis", "coloradodiscountskis.com",
        scrape_urls=[
            "https://www.coloradodiscountskis.com/store/Atomic_2025.html",
            "https://www.coloradodiscountskis.com/store/Rossignol.html",
            "https://www.coloradodiscountskis.com/store/Salomon_2025.html",
            "https://www.coloradodiscountskis.com/store/Head_2025.html",
            "https://www.coloradodiscountskis.com/store/Volkl_2025.html",
        ],
        parser_type="coloradodiscount",
    ),

    # Browser-based (Playwright) — JS-rendered or anti-bot
    StoreConfig(
        "Evo", "evo.com",
        scrape_urls=[
            "https://www.evo.com/shop/ski/skis",
            "https://www.evo.com/shop/snowboard/snowboards",
        ],
        parser_type="evo",
        use_browser=True,
    ),
    StoreConfig(
        "Backcountry", "backcountry.com",
        scrape_urls=[
            "https://www.backcountry.com/rc/skis",
            "https://www.backcountry.com/rc/snowboards",
        ],
        parser_type="backcountry",
        use_browser=True,
    ),
    StoreConfig(
        "Steep & Cheap", "steepandcheap.com",
        scrape_urls=[
            "https://www.steepandcheap.com/cat/skis",
            "https://www.steepandcheap.com/cat/snowboards",
        ],
        parser_type="backcountry",
        use_browser=True,
    ),
    StoreConfig(
        "The House", "the-house.com",
        scrape_urls=[
            "https://www.the-house.com/search?pmid=on-sale-now",
        ],
        parser_type="thehouse",
        use_browser=True,
    ),
    StoreConfig(
        "Corbetts", "corbetts.com",
        scrape_urls=[
            "https://www.corbetts.com/categories/ski/skis.html",
            "https://www.corbetts.com/snowboards/",
            "https://www.corbetts.com/ski-boots/",
            "https://www.corbetts.com/categories/clearance.html",
        ],
        parser_type="corbetts",
        use_browser=True,
        tax_free=True,  # Canadian store
    ),
    StoreConfig(
        "Level Nine Sports", "levelninesports.com",
        scrape_urls=[
            "https://www.levelninesports.com/cat/ski",
            "https://www.levelninesports.com/cat/snowboards",
        ],
        parser_type="backcountry",
        use_browser=True,
    ),
    # Powder7 removed — site primarily sells used items

    # Shopify — new additions
    StoreConfig(
        "Colorado Ski Shop", "coloradoskishop.com",
        scrape_urls=[
            "https://coloradoskishop.com/collections/clearance",
            "https://coloradoskishop.com/collections/skis",
        ],
        parser_type="shopify",
    ),

    # BigCommerce — browser-based
    StoreConfig(
        "Peter Glenn", "peterglenn.com",
        scrape_urls=[
            "https://peterglenn.com/sale/",
            "https://peterglenn.com/ski/skis/",
            "https://peterglenn.com/ski/ski-boots/",
        ],
        parser_type="peterglenn",
        use_browser=True,
    ),

    # Unreachable — site appears down
    # StoreConfig("Sanction", "sanction.com", parser_type="generic"),
    # StoreConfig("Wiredsport", "wiredsport.com", parser_type="shopify"),  # Oregon (tax-free) but site is down
]


# ---------------------------------------------------------------------------
# Category keywords — used by categorizer.py to classify products
# ---------------------------------------------------------------------------

# Ordered list of (category, keywords) — checked top-to-bottom, first match wins.
# Specific compound terms (e.g. "ski boot") must come BEFORE broad terms (e.g. "ski").
CATEGORY_RULES: list[tuple[str, list[str]]] = [
    # Compound terms first — these prevent "ski boot" from matching "skis"
    ("boots", ["ski boot", "ski boots", "snowboard boot", "snowboard boots",
               "boot", "boots"]),
    ("bindings", ["ski binding", "ski bindings", "snowboard binding", "snowboard bindings",
                  "binding", "bindings"]),
    ("poles", ["ski pole", "ski poles", "pole", "poles"]),
    ("helmets", ["helmet", "helmets"]),
    ("goggles", ["goggle", "goggles"]),
    ("jackets", ["jacket", "jackets", "shell", "parka"]),
    ("pants", ["pant", "pants", "bibs", "bib"]),
    ("gloves", ["glove", "gloves", "mitten", "mittens"]),
    ("layers", ["baselayer", "base layer", "midlayer", "mid layer", "fleece"]),
    ("accessories", ["neck gaiter", "balaclava", "beanie", "hat", "sock", "socks"]),
    # Broad equipment terms last
    ("snowboards", ["snowboard", "snowboards"]),
    ("skis", ["ski", "skis"]),
]
