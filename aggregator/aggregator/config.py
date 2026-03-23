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
    tax_free: bool = False  # True = no sales tax for WA buyers (Canadian stores, no-nexus stores)
    currency: str = "USD"   # Price currency (USD or CAD)


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
            "https://www.aspenskiandboard.com/collections/snowboards",
            "https://www.aspenskiandboard.com/collections/sale-ski-boots",
            "https://www.aspenskiandboard.com/collections/sale-snowboard-boots",
        ],
        parser_type="shopify",
        tax_free=True,  # No WA sales tax nexus
    ),
    StoreConfig(
        "PRFO", "prfo.com",
        scrape_urls=[
            "https://www.prfo.com/collections/sales",
            "https://www.prfo.com/collections/ski-skis",
            "https://www.prfo.com/collections/snowboard-snowboards",
            "https://www.prfo.com/collections/ski-ski-bindings",
            "https://www.prfo.com/collections/snowboard-snowboard-bindings",
        ],
        parser_type="shopify",
        tax_free=True, currency="CAD",
    ),

    # Sports Basement — confirmed Shopify
    StoreConfig(
        "Sports Basement", "sportsbasement.com",
        scrape_urls=[
            "https://www.sportsbasement.com/collections/skis",
            "https://www.sportsbasement.com/collections/snow",
            "https://www.sportsbasement.com/collections/ski-deals",
            "https://www.sportsbasement.com/collections/snowboard-gear-deals",
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
        tax_free=True, currency="CAD",
    ),
    StoreConfig(
        "Colorado Discount Skis", "coloradodiscountskis.com",
        scrape_urls=[
            "https://www.coloradodiscountskis.com/store/Atomic_2026.html",
            "https://www.coloradodiscountskis.com/store/Atomic_2025.html",
            "https://www.coloradodiscountskis.com/store/Atomic_2024.html",
            "https://www.coloradodiscountskis.com/store/Head_2026.html",
            "https://www.coloradodiscountskis.com/store/Head_2025.html",
            "https://www.coloradodiscountskis.com/store/Head_2024.html",
            "https://www.coloradodiscountskis.com/store/Salomon_2026.html",
            "https://www.coloradodiscountskis.com/store/Salomon_2025.html",
            "https://www.coloradodiscountskis.com/store/Salomon_2024.html",
            "https://www.coloradodiscountskis.com/store/Rossignol.html",
            "https://www.coloradodiscountskis.com/store/Volkl_2026.html",
            "https://www.coloradodiscountskis.com/store/Volkl_2025.html",
            "https://www.coloradodiscountskis.com/store/Volkl_2024.html",
            "https://www.coloradodiscountskis.com/store/Fischer_2026.html",
            "https://www.coloradodiscountskis.com/store/Fischer_2025.html",
            "https://www.coloradodiscountskis.com/store/Fischer_2024.html",
            "https://www.coloradodiscountskis.com/store/Nordica_2026.html",
            "https://www.coloradodiscountskis.com/store/Nordica_2025.html",
            "https://www.coloradodiscountskis.com/store/Nordica_2024.html",
            "https://www.coloradodiscountskis.com/store/Blizzard_2026.html",
            "https://www.coloradodiscountskis.com/store/Blizzard_2025.html",
            "https://www.coloradodiscountskis.com/store/Blizzard_2024.html",
            "https://www.coloradodiscountskis.com/store/Ogasaka.html",
            "https://www.coloradodiscountskis.com/store/FIS_Skis.html",
        ],
        parser_type="coloradodiscount",
    ),

    # Browser-based (Playwright) — JS-rendered or anti-bot
    StoreConfig(
        "Evo", "evo.com",
        scrape_urls=[
            "https://www.evo.com/shop/ski/skis",
            "https://www.evo.com/shop/snowboard/snowboards",
            "https://www.evo.com/shop/sale/ski/skis",
            "https://www.evo.com/shop/sale/snowboard/snowboards",
        ],
        parser_type="evo",
        use_browser=True,
    ),
    StoreConfig(
        "Backcountry", "backcountry.com",
        scrape_urls=[
            "https://www.backcountry.com/rc/skis",
            "https://www.backcountry.com/rc/snowboards",
            "https://www.backcountry.com/rc/ski-snowboard-on-sale",
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
            "https://www.the-house.com/search?pmid=on-sale-now&start=0&sz=240",
            "https://www.the-house.com/search?pmid=on-sale-now&start=240&sz=240",
            "https://www.the-house.com/search?pmid=on-sale-now&start=480&sz=240",
            "https://www.the-house.com/search?pmid=on-sale-now&start=720&sz=240",
            "https://www.the-house.com/search?pmid=on-sale-now&start=960&sz=240",
            "https://www.the-house.com/search?pmid=on-sale-now&start=1200&sz=240",
            "https://www.the-house.com/search?pmid=on-sale-now&start=1440&sz=240",
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
        tax_free=True, currency="CAD",
    ),
    StoreConfig(
        "Level Nine Sports", "levelninesports.com",
        scrape_urls=[
            "https://www.levelninesports.com/cat/ski",
            "https://www.levelninesports.com/cat/snowboards",
            "https://www.levelninesports.com/shop/promos/clearance-sale",
        ],
        parser_type="levelnine",
        use_browser=True,
    ),
    # Powder7 removed — site primarily sells used items

    # Shopify — new additions
    StoreConfig(
        "Colorado Ski Shop", "coloradoskishop.com",
        scrape_urls=[
            "https://coloradoskishop.com/collections/clearance",
            "https://coloradoskishop.com/collections/skis",
            "https://coloradoskishop.com/collections/snowboards",
            "https://coloradoskishop.com/collections/ski-bindings",
        ],
        parser_type="shopify",
    ),
    StoreConfig(
        "Ski Depot", "ski-depot.com",
        scrape_urls=[
            "https://ski-depot.com/collections/skis",
            "https://ski-depot.com/collections/ski-boots",
            "https://ski-depot.com/collections/ski-bindings",
            "https://ski-depot.com/collections/summer-sizzler-deals",
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

    # WooCommerce — BS4 HTML parser
    StoreConfig(
        "Sacred Ride", "sacredride.ca",
        scrape_urls=[
            "https://sacredride.ca/product-category/winter/skis/",
            "https://sacredride.ca/product-category/winter/snowboards/",
            "https://sacredride.ca/product-category/winter/boots/",
            "https://sacredride.ca/product-category/winter/snowboard-boots/",
            "https://sacredride.ca/product-category/winter/bindings/",
            "https://sacredride.ca/product-category/winter/snowboard-bindings/",
            "https://sacredride.ca/product-category/winter/helmets/",
            "https://sacredride.ca/product-category/winter/goggles/",
        ],
        parser_type="sacredride",
        use_browser=True,
        tax_free=True, currency="CAD",
    ),

    # New Shopify stores
    # SkiEssentials uses headless Shopify (Hydrogen) — JSON API returns 404
    StoreConfig(
        "Comor Sports", "comorsports.com",
        scrape_urls=[
            "https://comorsports.com/collections/ski-sale",
            "https://comorsports.com/collections/snowboard-snowboards",
            "https://comorsports.com/collections/ski-boots-sale",
        ],
        parser_type="shopify",
        tax_free=True, currency="CAD",
    ),
    StoreConfig(
        "Ski Pro AZ", "skipro.com",
        scrape_urls=[
            "https://skipro.com/collections/sale",
            "https://skipro.com/collections/previous-season-sale",
        ],
        parser_type="shopify",
        tax_free=True,  # Arizona, no WA nexus
    ),
    StoreConfig(
        "First Stop Board Barn", "firststopboardbarn.com",
        scrape_urls=[
            "https://www.firststopboardbarn.com/collections/sale",
            "https://www.firststopboardbarn.com/collections/clearance-mens-snowboard",
            "https://www.firststopboardbarn.com/collections/clearance-snowboard-gear",
        ],
        parser_type="shopify",
        tax_free=True,  # Vermont, no WA nexus
    ),
    StoreConfig(
        "Fresh Skis", "freshskis.com",
        scrape_urls=[
            "https://www.freshskis.com/collections/clearance",
        ],
        parser_type="shopify",
        tax_free=True, currency="CAD",
    ),
    StoreConfig(
        "Rude Boys", "rudeboys.com",
        scrape_urls=[
            "https://rudeboys.com/collections/sale-bindings",
        ],
        parser_type="shopify",
        tax_free=True, currency="CAD",
    ),
    StoreConfig(
        "Skiis & Biikes", "skiisandbiikes.com",
        scrape_urls=[
            "https://skiisandbiikes.com/collections/all-sale",
        ],
        parser_type="shopify",
        tax_free=True, currency="CAD",
    ),
    StoreConfig(
        "Skirack", "skirack.com",
        scrape_urls=[
            "https://www.skirack.com/collections/sale",
        ],
        parser_type="shopify",
        tax_free=True,  # Vermont, no WA nexus
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
    # Bags/cases FIRST — prevent "ski bag" from matching "skis"
    ("accessories", ["ski bag", "snowboard bag", "board bag", "ski case",
                     "roller bag", "gear bag", "boot bag", "ski sleeve",
                     "ski sack", "board sack", "ski roller", "ski tote"]),
    # Compound terms — prevent "ski boot" from matching "skis"
    ("boots", ["ski boot", "ski boots", "snowboard boot", "snowboard boots",
               "boot", "boots", " boa"]),
    ("bindings", ["ski binding", "ski bindings", "snowboard binding", "snowboard bindings",
                  "binding", "bindings"]),
    ("poles", ["ski pole", "ski poles", "pole", "poles"]),
    ("helmets", ["helmet", "helmets", " mips"]),
    ("goggles", ["goggle", "goggles", " otg "]),
    ("jackets", ["jacket", "jackets", "shell", "parka", "anorak", "insulated jacket"]),
    ("pants", ["pant", "pants", "bibs", "bib"]),
    ("gloves", ["glove", "gloves", "mitten", "mittens", "mitt", "mitts"]),
    ("layers", ["baselayer", "base layer", "midlayer", "mid layer", "fleece",
                "ninja suit", "pullover hood", "hoodie", "hoody", "long sleeve",
                "merino", "therma", "quarter zip", "half zip", "1/4 zip",
                "down sweater", "down hoody", "down vest",
                "base tek", "poly top", "poly bottom",
                "zip up", "full zip", "1/2 zip", "1/2-zip",
                "sweater", "vest ", "turtleneck", "pullover",
                "r1 air", "r2 ", "nano puff"]),
    ("accessories", ["neckwear", "neck gaiter", "balaclava", "beanie", "hat ", "sock", "socks",
                     "facemask", "face mask", "tube ", "hood ", "the hood",
                     "duffel", "trolley", "roller bag", "wheeled bag",
                     "backpack", "daypack", "pack ",
                     "footwarmer", "foot warmer", "lip balm",
                     "stomp pad", "stomp", "traction", "crampon", "spike",
                     "wax", "tuning", "scraper", "brush", "p-tex",
                     "shin guard", "insole", "outsole", "brake",
                     "beacon", "avalanche", "probe", "shovel",
                     "snowshoe", "snow shoe", "hand warmer", "toe warmer",
                     "boot dryer", "ski lock", "ski strap", "goggle lens"]),
    # Splitboard before snowboard (compound match)
    ("snowboards", ["splitboard", "splitboards", "snowboard", "snowboards"]),
    ("skis", ["ski", "skis"]),
]

# Brand-based categorization fallback — when keyword matching fails,
# products from these brands are likely skis or snowboards.
# Only used when no category was found via keyword matching.
# NOTE: Brands that make BOTH skis and snowboards (K2, Salomon, Rossignol)
# are excluded — they're ambiguous without more context.
SKI_BRANDS: set[str] = {
    "atomic", "blizzard", "dynastar", "elan", "faction", "fischer",
    "head", "nordica", "volkl",
    "armada", "black crows", "dps", "icelantic",
    "kastle", "liberty", "moment", "on3p", "ogasaka", "sego",
    "4frnt", "j skis",
}
SNOWBOARD_BRANDS: set[str] = {
    "burton", "capita", "gnu", "lib tech", "never summer",
    "nitro", "ride", "rome", "yes", "bataleon",
}

# Words that indicate a product is NOT hardgoods (skip brand-matching)
NOT_HARDGOODS_KEYWORDS: list[str] = [
    "tee ", "t-shirt", "shirt", "hoodie", "hoody", "sweater", "vest",
    "cap ", "hat ", "beanie", "sticker", "decal",
    "leash", "scraper", "tool", "bag ", "pack ", "backpack",
    "towel", "blanket", "sandal", "shoe ", "slipper",
    "crew ", "jersey", "short ", "shorts", "dress", "romper",
]

# Products matching these patterns are excluded entirely (non-snow-sport items)
EXCLUDE_KEYWORDS: list[str] = [
    # Water sports
    "wakeboard", "wakeskate", "wakesurf", "towable tube", "towable ",
    "water ski", "waterski", "kayak", "paddleboard", "sup board",
    "tube rope", "wake vest",
    # Board sports (non-snow)
    "longboard", "skateboard", "surfboard",
    # Cycling
    "bike rack", "bicycle", "cycling", "mountain bike", "bike shoe",
    "mtb shoe", "mtb ", "gravel bike", " bike",
    # Camping/hiking
    "camping stove", "tent pole",
    "running shoe", "trail shoe", "hiking shoe",
    # Swimwear
    "swimsuit", "swim trunk", "bikini", "swim jammer", "swim bottom",
    "cheekini", "hipster",
    # Casual clothing (non-snow)
    "t-shirt", "tee ", "jersey", "shorts", "jammer",
    " cap", "trucker hat", "trucker cap",
    # Footwear (non-boot)
    "sandal", "flip flop", "skate shoe", "skate shoes",
    # Non-snow apparel
    "polo ", "tank top",
    # Non-snow equipment
    "kneeboard", "slime wheel",
    "zero gravity chair", "padded chair",
    "climbing block",
    # Summer/casual apparel
    "romper", "linen ", "walkshort",
    "rashguard", "rash guard",
    # Drinkware/accessories
    "tumbler", "quencher",
    "recovery shoe", "recovery shoes",
    # Other sports
    "golf footbed", "soccer", "basketball", "football", "baseball", "tennis ball",
    "fishing rod", "fishing reel",
    # Water sports (specific brands/products)
    "ronix", "connelly", "hyperlite", "o'brien",
    "mainline", "wakeboard", "party cove",
    # Cycling (specific)
    "stumpjumper", "mountain bike", "bike shoe", "cycling shoe",
    # Casual/non-snow
    "keychain", "denim ", "jeans ", "collapsible seat",
    "nomad seat", "power block", "glacier glasses",
    "original denim", "print shirt",
    "landyachtz", "hawgs wheels",
    "bike carrier", "fork mount",
    # Misc non-snow
    "gift card", "digital gift card",
    "headlamp", "insole", "insoles",
    "free returns", "package protection",
    "watersports flag", "shop wheels",
    "sticker pack", "decal",
]
