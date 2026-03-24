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
    # Ski boots — specific keywords first
    ("ski boots", ["ski boot", "ski boots", "cross country boot",
                   "touring boot", "alpine boot",
                   "mach sport"]),
    # Snowboard boots — specific keywords
    ("snowboard boots", ["snowboard boot", "snowboard boots"]),
    # Generic boot — needs further disambiguation via brand/model fallback
    ("boots", [" boa", "boot", "boots"]),
    ("bindings", ["ski binding", "ski bindings", "snowboard binding", "snowboard bindings",
                  "binding", "bindings", "step on"]),
    ("poles", ["ski pole", "ski poles", "pole", "poles"]),
    ("helmets", ["helmet", "helmets", " mips"]),
    ("goggles", ["goggle", "goggles", " otg ", "bonus lens", " mag ", "chromapop",
                 "replacement lens", "flight deck", "flight path",
                 "flight tracker", "line miner", "zonula"]),
    ("jackets", ["jacket", "jackets", "shell", "parka", "anorak", "insulated jacket",
                 "powder town jkt", "gore-tex suit", " jkt",
                 "coat ", "coat", "raincoat", "puffer coat"]),
    ("pants", ["pant", "pants", "bibs", "bib", "bottom "]),
    ("gloves", ["glove", "gloves", "mitten", "mittens", "mitt", "mitts"]),
    ("layers", ["baselayer", "base layer", "midlayer", "mid layer", "fleece",
                "ninja suit", "pullover hood", "hoodie", "hoody", "long sleeve",
                "merino", "therma", "quarter zip", "half zip", "1/4 zip",
                "down sweater", "down hoody", "down vest",
                "base tek", "poly top", "poly bottom",
                "zip up", "full zip", "1/2 zip", "1/2-zip",
                "sweater", "vest ", "turtleneck", "pullover",
                "r1 air", "r2 ", "nano puff",
                "gaiter top", "icecold", "rib top", "loose fit",
                "mock crew", "crew neck", "tight ", "tights",
                "legging",
                "insulated shirt", "flannel shirt",
                "sweatshirt", "crewneck",
                "zip neck", "snap top", "pile snap",
                "insulated flannel", "tech flannel",
                "shacket",
                "oasis ", "200 oasis", "260 tech", "260 vertex",
                "260 quantum", "descender ", "rho ",
                "adult chute", "pull on"]),
    ("accessories", ["neckwear", "neck gaiter", "balaclava", "beanie", "hat ", "sock", "socks",
                     "facemask", "face mask", "tube ", "hood ", "the hood",
                     "duffel", "trolley", "roller bag", "wheeled bag",
                     "backpack", "daypack", "pack ",
                     "footwarmer", "foot warmer", "lip balm",
                     "headband", "clava", "pro clava", "gaiter",
                     "ballcap", "cap ",
                     "stomp pad", "stomp", "traction", "crampon", "spike",
                     "wax", "tuning", "scraper", "brush", "p-tex", "klister",
                     "base binder", "base angle", "base tex", "cork",
                     "red gummy", "structurite", "embro cream",
                     "shin guard", "insole", "outsole", "brake",
                     "beacon", "avalanche", "probe", "shovel",
                     "snowshoe", "snow shoe", "hand warmer", "toe warmer",
                     "boot dryer", "ski lock", "ski strap", "goggle lens",
                     "crab grab", "rescue package",
                     "cord mask", "reflect mask", "striped mask",
                     "ear warmer", "visor",
                     "heli strap", "back protector"]),
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
BOOT_BRANDS: set[str] = {
    "tecnica", "lange", "scarpa", "dalbello", "full tilt",
    "thirtytwo", "dc", "deeluxe",
}
# Brands that ONLY make ski boots — used to disambiguate generic "boot" matches
SKI_BOOT_BRANDS: set[str] = {
    "tecnica", "lange", "scarpa", "dalbello", "full tilt",
    "dahu", "roxa", "alpina",
}
# Brands that ONLY make snowboard boots
SNOWBOARD_BOOT_BRANDS: set[str] = {
    "thirtytwo", "dc", "deeluxe", "nidecker",
}
# Well-known ski model names (without brand prefix) — used when brand extraction fails
SKI_MODEL_NAMES: set[str] = {
    # Atomic
    "maverick", "bent", "redster",
    # Head
    "supershape", "shape", "kore",
    # K2
    "mindbender", "disruption", "reckoner",
    # Nordica
    "enforcer", "unleashed", "dobermann", "nela", "santa",
    # Line
    "pandora",
    # Rossignol
    "experience", "rallybird",
    # Elan
    "ripstick",
    # Armada
    "declivity", "arv", "arw",
    # Blizzard
    "rustler", "sheeva", "anomaly", "brahma",
    # Fischer
    "ranger", "curv",
    # Volkl
    "mantra", "deathwish", "wildcat", "peregrine", "m7",
    # Salomon
    "stance", "qst",
    # Stockli
    "stormrider", "montero",
    # Faction
    "prodigy", "dictator",
    # DPS
    "wailer",
    # Women's-specific ski models
    "secret", "vetta", "siren", "sierra", "maven", "reliance",
    # Generic / multi-brand
    "sender", "freecarver", "revolt",
}
SNOWBOARD_MODEL_NAMES: set[str] = {
    # Burton
    "twinpig", "kilroy", "process", "custom", "flagship", "feelgood",
    "hometown", "dancehaul", "insano", "cartographer", "yeasayer",
    "feelbetter", "swoon",
    # Lib Tech
    "proto", "orca", "ejack", "skunk",
    # Ride
    "warpig", "psychocandy", "shadowban", "berzerker", "algorythm",
    "d.o.a.", "twinpig", "hera", "cadence",
    "orton", "almanac", "excavator", "heartbreaker",
    # Jones
    "tweaker", "cultivator", "spellcaster", "frontier", "mountain",
    "storm", "hovercraft", "stratos", "mind", "flagship",
    "aeronaut", "horizon", "passport", "ultra",
    # CAPiTA
    "thunderstorm", "pathfinder", "mega", "satori",
    # Salomon
    "assassin", "huck", "abstract", "sleepwalker", "super",
    # GNU
    "headspace",
    # Nitro
    "alternator", "slash", "treeline",
    # Yes
    "greats", "typo", "jakk",
    # Ride (more)
    "distortia", "trance",
    # Roxy
    "xoxo",
    # Various
    "rumble", "mercury", "legacy", "dpr", "aura",
    "falcor", "disaster", "meteorite", "strata",
    "cadet", "relapse", "gloss",
}
GOGGLE_MODEL_NAMES: set[str] = {
    "squad", "skyline", "i/o", "sagen", "goliath+",
}
BINDING_MODEL_NAMES: set[str] = {
    "re:flex", "est", "cartel", "mission", "supermatic",
    "griffon", "strive", "stage",
    "citizen", "lexa", "scribe",
}
BOOT_MODEL_NAMES: set[str] = {
    # Ski boot models
    "cochise", "mach1", "hawx", "speedmachine", "s/pro",
    "sportmachine", "promachine", "cabrio", "shadow", "nexo",
    "alltrack", "bfc", "vizion", "xt3",
    "formula", "steadfast", "garabaldi",
    "veloce", "recon", "lupo", "kita",
    "select",
    # Snowboard boot models
    "limelight", "highshot", "lasso", "maysis", "swath",
}
# Ski boot model names — for disambiguation
SKI_BOOT_MODEL_NAMES: set[str] = {
    "cochise", "mach1", "hawx", "speedmachine", "s/pro",
    "sportmachine", "promachine", "cabrio", "shadow", "nexo",
    "alltrack", "bfc", "vizion", "xt3",
    "formula", "steadfast", "garabaldi",
    "veloce", "recon", "lupo", "kita",
    "select",
}
# Snowboard boot model names — for disambiguation
SNOWBOARD_BOOT_MODEL_NAMES: set[str] = {
    # Burton
    "limelight", "highshot", "lasso", "maysis", "swath",
    "photon", "ruler", "imperial", "felix",
    "waverange",
    # DC
    "judge", "phase", "phantom", "control",
    # ThirtyTwo
    "lashed", "stw", "shifty",
    # Salomon
    "launch", "echo", "kiana", "dialogue",
    # Ride
    "jackson",
    # K2
    "boundary", "hanford", "overdraft",
    # Various
    "mint", "invado", "verdict", "hail", "exit",
    "bodega", "profile", "skylab", "mosh", "salsa",
}

# Multi-word model names — checked via substring match on lowered name
# Format: (phrase, category)
MULTI_WORD_MODEL_NAMES: list[tuple[str, str]] = [
    # Skis
    ("black pearl", "skis"),
    ("santa ana", "skis"),
    ("wild belle", "skis"),
    ("pick your line", "skis"),
    ("il moro", "ski boots"),    # Full Tilt Il Moro boot
    # Snowboards
    ("huck knife", "snowboards"),
    ("skate banana", "snowboards"),
    ("evil twin", "snowboards"),
    ("dark horse", "snowboards"),
    ("rally cat", "snowboards"),
    ("space metal", "snowboards"),
    ("birds of a feather", "snowboards"),
    ("ladies choice", "snowboards"),
    ("magic stick", "snowboards"),
    ("d.o.a.", "snowboards"),
    ("super d.o.a.", "snowboards"),
    ("mega merc", "snowboards"),
    ("mega death", "snowboards"),
    ("mind expander", "snowboards"),
    ("storm chaser", "snowboards"),
    ("storm wolf", "snowboards"),
    ("fish 3d", "snowboards"),
    ("cold brew", "snowboards"),
    ("sky pilot", "snowboards"),
    ("deep reach", "snowboards"),
    ("easy rider", "snowboards"),
    ("good company", "snowboards"),
    ("family tree", "snowboards"),
    ("t.rice", "snowboards"),
    ("bryan iguchi", "snowboards"),
    ("danny kass", "snowboards"),
    ("jamie lynn", "snowboards"),
    ("kazu kokubo", "snowboards"),
    ("marcus kleveland", "snowboards"),
    ("outerspace living", "snowboards"),
    ("spring break", "snowboards"),
    ("no drama", "snowboards"),
    ("oh yeah", "snowboards"),
    ("twin sister", "snowboards"),
    # Boots
    ("s/pro alpha", "boots"),
    ("s/pro hv", "boots"),
    ("cabrio lv", "boots"),
    # Bindings
    ("carbon supermatic", "bindings"),
    ("lt supermatic", "bindings"),
    ("lightning supermatic", "bindings"),
    ("step-on", "bindings"),
    ("re:flex", "bindings"),
    # Goggles
    ("low bridge", "goggles"),
    ("bonus lens", "goggles"),
    ("squad photochromic", "goggles"),
    # More snowboard models
    ("cream halldor", "snowboards"),
    ("lil d", "snowboards"),
    ("metal machine", "snowboards"),
    ("source pro", "snowboards"),
    ("source fc", "snowboards"),
    # More ski boots
    ("bcx tour", "ski boots"),
    ("xc comfort", "ski boots"),
    (" hv gw", "ski boots"),
    (" mv gw", "ski boots"),
    (" lv gw", "ski boots"),
    # More snowboard boots
    ("step on boot", "snowboard boots"),
    ("dual boa", "snowboard boots"),
    ("tm-2", "snowboard boots"),
    # XC skis
    ("x-ium skating", "skis"),
    ("cross country", "skis"),
    # Snow suits (jackets category)
    ("snow suit", "jackets"),
    ("insulated suit", "jackets"),
    ("power suit", "jackets"),
    ("freedom suit", "jackets"),
    ("stretch freedom", "jackets"),
    ("sassy beast", "jackets"),
    ("shelter one piece", "jackets"),
    ("shiloh snow", "jackets"),
    # Snowboard (brand+model combos)
    ("wasteland rocker", "snowboards"),
    ("hps louidf", "snowboards"),
    ("hps takaharu", "snowboards"),
    # Ski + binding package
    ("v-shape v2", "skis"),
    # Accessories
    ("windstopper face", "accessories"),
    ("cold scarf", "accessories"),
    ("neckwarmer", "accessories"),
    ("face warmer", "accessories"),
    ("base cleaner", "accessories"),
    ("xc profile set", "accessories"),
    ("clockwork rig", "goggles"),
    ("reflect lens", "goggles"),
    ("m5s lens", "goggles"),
    # Bindings
    ("look pivot", "bindings"),
    ("gripwalk 20", "bindings"),
    ("comp 20 ng", "bindings"),
    # Layers
    ("pile long zip", "layers"),
    ("lana collar", "layers"),
    ("ultraGear quarter", "layers"),
]

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
    "wakeboard", "wakeskate", "wakesurf", "towable ", "water ski", "waterski",
    "kayak", "paddleboard", "sup board", "tube rope", "wake vest",
    "ronix", "connelly", "hyperlite", "o'brien", "liquid force",
    "feelfree", "radar ", "ballast", "pfd", "life jacket",
    "gladiator ", "ho sports", "drysuit", "wetsuit", "swim ",
    "overton", "pwc anchor", "yakattack", "foil package", "slingshot hover",
    # Board sports (non-snow)
    "longboard", "skateboard", "surfboard", "landyachtz", "hawgs wheels",
    "globe ", "surf/skate", "cruiser complete",
    # Cycling
    "bicycle", "cycling", " bike", "bike rack", "bike shoe", "bike carrier",
    "mtb ", "gravel bike", "derailleur", "cassette ", "fork mount",
    "stumpjumper", "bontrager ", "cannondale ", "trek fuel",
    "7mesh ", "sugoi ", "pearl izumi ", "shimano ", "evoc ",
    "aspero ", "turbo como", "saris ", "giro regime", "giro rincon",
    "fox ranger", "e-bike",
    # Running/hiking/outdoor shoes
    "running shoe", "trail shoe", "hiking shoe", "approach shoe",
    "trail runner", "road shoe", "mtn shoe", "mountain shoe",
    "recovery shoe", "recovery flip", "ora recovery",
    "cloudsurfer", "terrex ", "arahi ", "torin ", "anacapa ",
    "peakfreak", "danner ", "keen arcata",
    # Casual shoes / non-boot footwear
    "sandal", "flip flop", "skate shoe", "tennis shoe",
    "vans ", "emerica ", "etnies ", "new balance ", "numeric ",
    "adidas ", "sorel ", " sneaker", "gazelle",
    " mens shoe 20", " womens shoe 20", " ladies shoe 20",
    # Swimwear
    "swimsuit", "swim trunk", "bikini", "swim jammer", "cheekini",
    # Casual clothing
    "t-shirt", "tee ", "jersey", "shorts", "polo ", "tank top",
    "romper", "jumpsuit", "coverall", "overall", "shortall",
    "crop top", "bralette", "halter", "tunic", "kaftan", "skort",
    "bodysuit", "body suit", "one-piece", "1-pce",
    "jogger", "windbreaker", "overshirt", "denim ", "jeans ",
    "button down", "buttondown", "woven shirt", "print shirt",
    "sleeveless", "tech chino", "tech tank", "walkshort",
    "linen ", "corduroy shirt",
    # Casual brands (non-snow clothing in mixed-use stores)
    "katin ", "brixton ", "cotopaxi ", "salty crew ", "billabong ",
    "alp n rock ", "duer ", "free fly ", "jetty ", "kuhl ",
    "purnell ", "indyeva ", "peppermint ", "maloja ",
    "life is good ", "roark ", "rains ", "vessi ", "woodbird ",
    "krimson klover", "super.natural ", "topo designs ", "herschel ",
    # Sunglasses
    "sunglasses", "sunglass",
    # Hats (non-helmet)
    " cap", "trucker hat", " snapback",
    # Underwear
    "bn3th ", "boxer brief", "boxer short", "everyday boxer",
    # Bags / luggage
    "tote bag", "lunch box", "sling bag", "gym bag", "belt bag",
    "travel luggage", "rolling bag", "dry bag", "leg bag", "wash bag",
    # Camping / outdoor gear
    "camping stove", "tent pole", "camping tent", "person tent",
    "sleeping bag", "camp chair", "quad chair", "cloud chair",
    "coleman ", "kelty ", "stansport ", "mac sports",
    "lantern", "flashlight", "headlamp", "binoculars",
    "canopy", "folding cot", "privacy shelter",
    # Home décor / gifts
    "abbott ", "ornament", "advent calendar", "doormat", "gnome",
    "christmas sign", "throw ",
    # Electronics / misc
    "earbuds", "usb-c cable", "gift card",
    "insole", "insoles", "sticker pack", "decal",
    "free returns", "package protection",
    # Other sports
    "soccer", "basketball", "football", "baseball", "tennis ball",
    "fishing rod", "fishing reel", "kneeboard",
    # Sunscreen
    "sunscreen", "spf30", "spf50",
    # Car racks
    "thule ", "wheel carrier",
    # Baby/infant
    "baby supporter", "thule baby", "baby synchilla", "bunting suit", "infants'",
    # Non-snow brand-specific products
    "osprey ", "harricana ", "pj salvage",
    "rab incline", "rab offgrid", "rab torque",
    "poc re-cycle", "vpd air sleeve",
    "specialized rime", "arcade belt",
    # Summer clothing patterns
    "rashguard", "rash guard", "sunshirt", "sun shirt",
    "slide 202", "slipper 202",
    # Misc non-snow
    "tricycle", "race suit", "training mat",
    "tumbler", "quencher", "keychain", "organizer",
    "whippet attachment", "knob nut",
]
