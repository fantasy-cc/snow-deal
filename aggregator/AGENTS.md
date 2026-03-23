# Agent Guide

## Project Overview

**snow-deals aggregator** is a sub-project within the snow-deals monorepo that scrapes 24 ski and snowboard retailers, stores deal snapshots in SQLite, and serves a ranked deal dashboard via FastAPI + htmx. It integrates product review scores from OutdoorGearLab (ski/boot/gear reviews, 0-100 scale) and The Good Ride (1000+ snowboard reviews, qualitative-to-numeric conversion). It uses Playwright headless browser for JS-rendered and anti-bot sites, httpx/BeautifulSoup for static sites, and reuses `ShopifyParser` and `BlueZoneParser` from the parent `snow_deals` package. Users interact through a Click CLI (scrape/query/fetch-reviews) or a browser-based UI with live filtering by category, store, brand, discount, ski/snowboard length range, review status, and tax-free status.

## Tech Stack

- **Language:** Python 3.11+
- **Web framework:** FastAPI >= 0.110, uvicorn >= 0.29
- **Templating:** Jinja2 >= 3.1, htmx 2.x (CDN, no build step)
- **Database:** SQLite via aiosqlite >= 0.20 (path configurable via `DATABASE_PATH` env var)
- **Deployment:** Render (free tier, Docker) + GitHub Actions (cron scraping every 6 hours)
- **HTTP client:** httpx >= 0.27 (async)
- **Browser automation:** Playwright (headless Chromium with anti-bot stealth)
- **HTML parsing:** BeautifulSoup4 >= 4.12, lxml >= 5.0
- **CLI:** Click >= 8.1
- **Terminal output:** Rich >= 13.0
- **Parent dependency:** `snow_deals` package (ShopifyParser, BlueZoneParser, Product model)

## Project Structure

```
aggregator/
├── pyproject.toml               # Package metadata and dependencies
├── AGENTS.md                    # This file — AI agent instructions
├── PLANS.md                     # Living execution plan
├── README.md                    # Human-oriented project README
├── deals.db                     # SQLite database (gitignored)
├── aggregator/
│   ├── __init__.py
│   ├── config.py                # Store registry (24 stores), category keywords, exclude keywords, brand sets, tax_free flags
│   ├── models.py                # AggregatedDeal dataclass (with sizes, length_min, length_max fields)
│   ├── categorizer.py           # Keyword + brand-based product → category mapping with exclusion filter
│   ├── db.py                    # SQLite schema (deals + reviews tables), init, upsert, query, store_status
│   ├── scraper.py               # Multi-store async orchestrator with dynamic parser registry, sizes cleaning, length extraction
│   ├── reviews.py               # OGL + TGR review scrapers, fuzzy product matcher
│   ├── browser.py               # Playwright-based scraper with per-store JS extractors (9 stores)
│   ├── cli.py                   # Click CLI (refresh, deals, fetch-reviews, generate-codes, list-codes)
│   ├── auth.py                  # Invite-only auth middleware + admin bypass via ADMIN_KEY env var
│   ├── parsers/
│   │   ├── __init__.py          # Parser registry docs
│   │   ├── common.py            # Shared parse_price() used by all BS4 parsers
│   │   ├── alpineshopvt.py      # Alpine Shop VT (BigCommerce)
│   │   ├── thecircle.py         # The Circle Whistler (Lightspeed eCom)
│   │   ├── coloradodiscount.py  # Colorado Discount Skis (custom HTML)
│   │   └── sacredride.py        # Sacred Ride (WooCommerce)
│   └── web/
│       ├── __init__.py
│       ├── app.py               # FastAPI app factory (lifespan init_db, auth middleware)
│       ├── routes.py            # Page + htmx partial + status dashboard routes
│       ├── invite_routes.py     # GET/POST /invite for invite code entry
│       ├── templates/
│       │   ├── index.html       # Main deals page with sticky toolbar, filters (search, category, brand, store, sort, length range, reviewed, tax-free)
│       │   ├── invite.html      # Invite code entry page (dark-themed)
│       │   ├── status.html      # Store status dashboard
│       │   └── partials/
│       │       ├── _card.html       # Shared deal card markup (div-based, not <a>, to avoid nested anchor issue)
│       │       ├── deal_cards.html  # htmx partial for deal grid (initial load)
│       │       └── more_cards.html  # htmx partial for load-more pagination
│       └── static/
│           └── style.css        # Polished dark-theme CSS with sticky toolbar, compact view, review highlights, footer
├── tests/
│   ├── test_parse_price.py      # Shared price parser tests
│   ├── test_categorizer.py      # Keyword categorization tests
│   ├── test_reviews.py          # Brand extraction + fuzzy matching tests
│   ├── test_parsers.py          # BS4 parser tests (AlpineShopVT, ColoradoDiscount, SacredRide)
│   ├── test_db.py               # SQLite CRUD, filters, upsert, brand query tests
│   ├── test_browser_config.py   # Store config registry + raw product parsing tests
│   └── test_scraper.py          # Kids filter + product-to-deal conversion tests
```

## Development Workflow

```bash
# From the aggregator/ directory
python -m venv .venv && source .venv/bin/activate

# Install parent package first (from repo root)
pip install -e ..

# Install aggregator
pip install -e ".[dev]"

# Install Playwright browsers
playwright install chromium

# Run tests (61 tests)
pytest tests/ -v

# Scrape all stores and populate SQLite
snow-deals-agg refresh

# Fetch review scores (OGL + The Good Ride)
snow-deals-agg fetch-reviews               # Both sources
snow-deals-agg fetch-reviews --source tgr   # The Good Ride only
snow-deals-agg fetch-reviews --source ogl   # OutdoorGearLab only

# Query deals from the database
snow-deals-agg deals --min-discount 20 --category skis

# Generate invite codes
snow-deals-agg generate-codes 10

# List invite codes and status
snow-deals-agg list-codes

# Run the web UI (with admin bypass for local dev)
ADMIN_KEY=mysecret uvicorn aggregator.web.app:create_app --factory --reload
# Access: http://localhost:8000/?admin_key=mysecret
# Status dashboard: http://localhost:8000/status

# Production: deployed on Render (https://snow-deals.onrender.com)
# Scraping runs via GitHub Actions cron every 6 hours
```

## Coding Conventions

- **Async throughout:** All I/O (HTTP, SQLite, Playwright) uses async/await.
- **Dataclasses for models:** `AggregatedDeal` wraps `snow_deals.Product` with store/category/sizes metadata.
- **Parser inheritance:** New HTML parsers inherit `BaseParser` from `snow_deals.parsers.base`.
- **Dynamic parser registry:** `scraper.py` uses `_PARSER_REGISTRY` dict with lazy imports via `importlib`.
- **Rate limiting:** Per-domain semaphores in `scraper.py` to avoid hammering retailers.
- **htmx for interactivity:** No JavaScript build step. Dynamic filtering via htmx partials.
- **DRY templates:** Card markup is in `partials/_card.html`, included by both `deal_cards.html` and `more_cards.html`.
- **No nested `<a>` tags:** Deal cards use `<div>` with `onclick` instead of `<a>` to avoid HTML parser issues when cards contain review links.
- **Type-annotate all public functions.**
- **Browser scraping:** Store-specific JS extractors in `browser.py` are inlined into `STORE_CONFIGS` dict as `(wait_selector, js_extract, next_page_selector)` tuples. BigCommerce stores share one config via aliases. Use `forEach` over `for...of` for NodeList iteration. Use `domcontentloaded` (not `networkidle`) for anti-bot sites.
- **Shared price parser:** All BS4 parsers import `parse_price()` from `parsers/common.py` — do not define per-parser copies.
- **Route query helper:** `_fetch_deals()` in `routes.py` centralizes the query + count + review-matching logic shared by `index()` and `deals_fragment()`.

## Architecture Decisions

- **SQLite for persistence:** Avoids re-scraping on every page load. Deals are snapshots refreshed via CLI.
- **Keyword-based categorization:** Product titles and URLs are matched against keyword lists in `config.py`. Shopify collection handles provide strong category signals.
- **Concurrent scraping with `asyncio.gather`:** Each store is scraped in parallel, with per-domain semaphores for rate limiting.
- **Playwright for JS-rendered sites:** Evo, Backcountry, Steep & Cheap, Level Nine Sports, Corbetts, Alpine Shop VT, The Circle Whistler, The House, Peter Glenn, Sacred Ride all require headless browser with anti-bot stealth measures.
- **htmx frontend:** Server-rendered HTML with htmx for dynamic filtering. No build tooling, no client-side framework.
- **Reuse parent parsers:** Shopify and BlueZone parsers are imported from `snow_deals` rather than duplicated.
- **Tax-free tagging:** Canadian stores and stores without WA sales tax nexus are marked `tax_free=True` for UI filtering. Currently: PRFO, The Circle Whistler, Corbetts, Sacred Ride (Canadian), Aspen Ski and Board (no WA nexus).
- **Review score integration:** OGL provides 0-100 scores for ski/boot/gear. The Good Ride provides qualitative snowboard ratings (Great/Good/Average/Below Average/Bad) converted to 0-100 via weighted average. Reviews are cached in-memory per server start. Fuzzy matching uses brand-gating, model number overlap, and SequenceMatcher with 0.72 threshold. Multi-word brands (Lib Tech, Never Summer, etc.) are handled via `_KNOWN_MULTI_WORD_BRANDS`.
- **Separate status dashboard:** Store health/freshness is shown on a dedicated `/status` page with summary stats, freshness legend, and per-store table.
- **Size filtering:** Sizes stored as cleaned text (colors, retail prices, junk stripped by `_clean_sizes()`). Length filtering uses dedicated `length_min`/`length_max` integer columns extracted from cm values, enabling efficient SQL range overlap queries. Dual-range slider in UI.
- **Data quality pipeline:** `EXCLUDE_KEYWORDS` in config.py filters non-snow items (gift cards, headlamps, insoles, etc.). `is_excluded()` in categorizer.py checks name + URL path. Brand-based fallback categorization with hardgoods guard (`NOT_HARDGOODS_KEYWORDS`). URL domain stripping prevents store domain from triggering false category matches.
- **Offset-based pagination:** `/deals` endpoint uses `PAGE_SIZE=60` with load-more button pattern (htmx `outerHTML` swap). Fetches `PAGE_SIZE+1` to detect if more results exist.
- **Kids product filtering:** Kids/junior products are filtered at the scraping layer (`_is_kids_product()` in `scraper.py`) rather than as a UI toggle.
- **Invite-only auth:** Middleware in `auth.py` checks for session cookie or `ADMIN_KEY` env var. Unauthenticated users are redirected to `/invite`. One-time invite codes stored in SQLite, sessions tracked via secure cookies. Admin bypasses via `?admin_key=` query param (persisted as cookie).
- **Deployment architecture:** Scraping and serving are decoupled. GitHub Actions runs the full scraper (with Playwright) every 6 hours and uploads `deals.db` as a GitHub Release asset. Render free tier downloads the DB on cold start via `start.sh` and serves the FastAPI app. `DATABASE_PATH` env var allows configurable DB location.
- **Brand filtering:** Brands are extracted from product names via `SUBSTR(name, 1, INSTR(name||' ',' ')-1)` in SQL. Brand dropdown populated by `get_brands()` in `db.py`.
- **CAD price display:** Stores with `currency="CAD"` in `StoreConfig` display prices as `C$` with a `CAD` tag on deal cards.
- **Browser.py consolidation:** 8 per-store JS wrapper functions were eliminated by inlining JS into a `STORE_CONFIGS` dict. BigCommerce stores (Corbetts, Peter Glenn, Alpine Shop VT) share one config entry via aliases. Shared `_JS_PARSE_PRICE` constant is reused across extractors.

- **Visual design:** Polished dark theme with sticky toolbar for search/filters, gradient logo, header stats, footer. CSS uses CSS custom properties throughout. Reviewed cards get subtle green top-border accent. Filter state synced to URL via `history.replaceState` for back-button persistence.

### Known Data Quality Issues (as of 2026-03-22)

- **Sacred Ride:** Returns 0 products — site may be down or markup changed. Needs investigation.
- **The House:** Products have 0 images — JS extractor doesn't capture `image_url`.
- **PRFO:** Only 65% categorized — broad catalog includes non-snow products.
- **Sports Basement:** Only 43% categorized — same broad catalog issue.
- **Sizes:** Only available from Shopify stores (Aspen, Colorado Ski Shop, PRFO, Ski Depot, Sports Basement). Browser-scraped stores don't extract sizes.
- **Evo:** Only 80 products — browser stores limited to `max_pages=3`, may need increase.
