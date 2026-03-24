# Awesome Snow Deals — Aggregator

Multi-store deal aggregator for ski and snowboard gear. Scrapes 24 retailers, integrates 1,200+ review scores from OutdoorGearLab (skis, boots, gear) and The Good Ride (snowboards, bindings, boots, jackets), stores deal snapshots in SQLite, and serves a ranked dashboard via FastAPI + htmx. Two-pass fuzzy matching links reviews to deals with model family fallback. Includes admin panel for invite code management and analytics dashboard for tracking user behavior. Deployed on Render with GitHub Actions cron for automated scraping. Part of the [snow-deals](../) monorepo.

**Live site:** [snow-deals.onrender.com](https://snow-deals.onrender.com) (invite-only)

## Getting Started

### Prerequisites

- Python 3.11+
- The parent `snow_deals` package installed (see repo root)
- Playwright Chromium browser (`playwright install chromium`)

### Installation

```bash
# From the repo root, install the parent package
pip install -e .

# Then install the aggregator
cd aggregator
pip install -e .

# Install Playwright browser
playwright install chromium
```

### Usage

#### Scrape all stores

```bash
snow-deals-agg refresh
```

#### Fetch review scores

```bash
# Fetch from both sources (OutdoorGearLab + The Good Ride)
snow-deals-agg fetch-reviews

# Fetch from a specific source
snow-deals-agg fetch-reviews --source tgr   # The Good Ride (1,800+ reviews: snowboards, bindings, boots, jackets)
snow-deals-agg fetch-reviews --source ogl   # OutdoorGearLab (ski/boot/gear reviews, 26 categories)
```

#### Query deals from the CLI

```bash
# Top deals across all stores
snow-deals-agg deals

# Filter by category and minimum discount
snow-deals-agg deals --category skis --min-discount 20

# Filter by store
snow-deals-agg deals --store "Evo" --limit 25
```

#### Manage invite codes

```bash
# Generate 10 invite codes
snow-deals-agg generate-codes 10

# List all codes and their status (available/used)
snow-deals-agg list-codes
```

#### Web UI

```bash
# Run locally with admin bypass
ADMIN_KEY=mysecret uvicorn aggregator.web.app:create_app --factory --reload
# Open http://localhost:8000/?admin_key=mysecret
```

The web UI provides:
- Live filtering by category, store, brand, discount percentage, and ski/snowboard length range via htmx
- Review score badges (color-coded) with award text and "Read review" links on matched deal cards
- "Top reviewed" sort and "Reviewed only" filter to surface expert-validated gear
- Search bar with debounced queries
- Sort by discount, price, store, top reviewed, or newest
- Tax-free filter (Canadian stores + no-nexus stores)
- CAD price display for Canadian stores (`C$` prefix + `CAD` tag)
- Sticky toolbar with search and filters
- Compact/comfortable view toggle
- "New since last visit" badges
- Load-more pagination (60 deals per page)
- Filter state persisted in URL (survives back-navigation)
- Store status dashboard at `/status` with data freshness indicators
- Invite-only access with reusable codes (max 5 uses each)
- Admin panel at `/admin/codes` for generating and viewing invite codes
- Analytics dashboard at `/admin/stats` — click tracking, popular filters, top deals

## Deployment

The site is deployed on **Render** (free tier) with scraping running on **GitHub Actions**:

- **Scraping:** GitHub Actions cron runs every 6 hours, uses Playwright for JS-rendered stores, uploads `deals.db` as a GitHub Release
- **Serving:** Render downloads the latest `deals.db` on startup and serves the FastAPI app
- **Auth:** Invite codes stored in Turso cloud SQLite (persist across redeploys). Sessions use JWT signed cookies (stateless, no DB lookup). Admin access via `ADMIN_KEY` env var
- **Admin:** `/admin/codes` for code management, `/admin/stats` for analytics dashboard

### Environment Variables (Render)

| Variable | Purpose |
|----------|---------|
| `DATABASE_PATH` | Path to deals SQLite database (default: `./deals.db`) |
| `ADMIN_KEY` | Admin access key (visit `/?admin_key=VALUE` to authenticate) |
| `TURSO_URL` | Turso database URL for auth persistence (e.g. `libsql://mydb.turso.io`) |
| `TURSO_AUTH_TOKEN` | Turso auth token (from Turso dashboard) |
| `SECRET_KEY` | JWT signing key for session cookies |
| `GITHUB_TOKEN` | (Optional) For downloading `deals.db` from private repos |

## Development

```bash
pip install -e ".[dev]"

# Run tests (64 tests across 7 test files)
pytest tests/ -v

# Lint
ruff check .
```

### Test Coverage

| Test File | Tests | Covers |
|-----------|-------|--------|
| `test_parse_price.py` | 8 | Shared price parser (USD, CAD, commas, edge cases) |
| `test_categorizer.py` | 15 | Keyword categorization (compound terms, URL fallback, exclusion, brand fallback, boot disambiguation) |
| `test_reviews.py` | 10 | Brand extraction, normalization, fuzzy matching |
| `test_parsers.py` | 9 | AlpineShopVT, ColoradoDiscount, SacredRide HTML parsing |
| `test_db.py` | 8 | SQLite CRUD, filters, upsert, brand query, store status |
| `test_browser_config.py` | 5 | Store config registry, aliases, raw product parsing |
| `test_scraper.py` | 2 | Kids filter, product-to-deal conversion, brand categorization |

## Project Structure

```
aggregator/
├── aggregator/
│   ├── config.py          # Store registry (24 stores), category keywords, exclude keywords, brand/model name sets
│   ├── models.py          # AggregatedDeal dataclass (sizes, length_min, length_max)
│   ├── categorizer.py     # Keyword + brand-based categorization with boot disambiguation and exclusion filter
│   ├── db.py              # SQLite schema (deals, reviews), CRUD, store status, migrations
│   ├── auth_db.py         # Turso cloud SQLite for auth (invite codes, sessions, events)
│   ├── auth.py            # JWT session auth middleware + admin bypass (stateless session validation)
│   ├── scraper.py         # Multi-store async scraper with dynamic parser registry
│   ├── reviews.py         # OGL + TGR review scrapers (7 sitemaps), two-pass fuzzy matcher with family fallback
│   ├── browser.py         # Playwright headless browser with per-store JS extractors
│   ├── cli.py             # Click CLI (refresh, deals, fetch-reviews, generate-codes, list-codes)
│   ├── parsers/
│   │   ├── common.py      # Shared parse_price() used by all BS4 parsers
│   │   ├── alpineshopvt.py, thecircle.py, coloradodiscount.py, sacredride.py
│   └── web/               # FastAPI app with htmx templates, admin panel, analytics dashboard
├── tests/                 # 64 tests (parsers, DB, categorizer, reviews, browser, scraper)
├── pyproject.toml
└── README.md
```

## Supported Stores

| Store | Type | Tax Free | Status |
|-------|------|-----------|--------|
| Aspen Ski and Board | Shopify | Yes | Active |
| PRFO | Shopify | Yes (CA) | Active |
| Sports Basement | Shopify | No | Active |
| Colorado Ski Shop | Shopify | No | Active |
| Ski Depot | Shopify | No | Active |
| BlueZone Sports | BS4 | No | Active |
| Colorado Discount Skis | httpx | No | Active |
| Alpine Shop VT | Playwright (BigCommerce) | No | Active |
| The Circle Whistler | Playwright (Lightspeed) | Yes (CA) | Active |
| Evo | Playwright | No | Active |
| Backcountry | Playwright (Chakra UI) | No | Active |
| Steep & Cheap | Playwright (Chakra UI) | No | Active |
| The House | Playwright (GTM) | No | Active |
| Corbetts | Playwright (BigCommerce) | Yes (CA) | Active |
| Level Nine Sports | Playwright (Chakra UI) | No | Active |
| Peter Glenn | Playwright (BigCommerce) | No | Active |
| Sacred Ride | Playwright (WooCommerce) | Yes (CA) | No Data (site issue) |
| Comor Sports | Shopify | Yes (CA) | Active |
| Ski Pro AZ | Shopify | Yes | Active |
| First Stop Board Barn | Shopify | Yes | Active |
| Fresh Skis | Shopify | Yes (CA) | Active |
| Rude Boys | Shopify | Yes (CA) | Active |
| Skiis & Biikes | Shopify | Yes (CA) | Active |
| Skirack | Shopify | Yes | Active |

## License

MIT
