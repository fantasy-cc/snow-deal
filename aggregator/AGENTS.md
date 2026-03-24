# Agent Guide

## Project Overview

**Awesome Snow Deals** (aggregator sub-project within the snow-deals monorepo) scrapes 24 ski and snowboard retailers, stores deal snapshots in SQLite, and serves a ranked deal dashboard via FastAPI + htmx. It integrates product review scores from OutdoorGearLab (ski/boot/gear reviews, 0-100 scale) and The Good Ride (1000+ snowboard reviews, qualitative-to-numeric conversion). It uses Playwright headless browser for JS-rendered and anti-bot sites, httpx/BeautifulSoup for static sites, and reuses `ShopifyParser` and `BlueZoneParser` from the parent `snow_deals` package. Users interact through a Click CLI (scrape/query/fetch-reviews) or a browser-based UI with live filtering by category, store, brand, discount, ski/snowboard length range, review status, and tax-free status. Includes invite-only auth with reusable invite codes (max 5 uses each), admin panel for code management, and lightweight client-side analytics tracking (clicks, page views, filters, searches).

## Tech Stack

- **Language:** Python 3.11+
- **Web framework:** FastAPI >= 0.110, uvicorn >= 0.29
- **Templating:** Jinja2 >= 3.1, htmx 2.x (CDN, no build step)
- **Database:** SQLite via aiosqlite >= 0.20 for deals/reviews (path configurable via `DATABASE_PATH` env var)
- **Auth database:** Turso cloud SQLite via libsql >= 0.1 (invite codes, events) — falls back to local SQLite for dev
- **Auth:** PyJWT >= 2.8 for stateless session cookies
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
│   ├── config.py                # Store registry (24 stores), category keywords, exclude keywords, brand/model/boot name sets, multi-word model names, tax_free flags
│   ├── models.py                # AggregatedDeal dataclass (with sizes, length_min, length_max fields)
│   ├── categorizer.py           # Keyword + brand-based product → category mapping with boot disambiguation and exclusion filter
│   ├── db.py                    # SQLite schema (deals, reviews), CRUD, migrations for sizes/length columns
│   ├── auth_db.py               # Turso cloud SQLite for auth (invite_codes, sessions, events) — local SQLite fallback for dev
│   ├── scraper.py               # Multi-store async orchestrator with dynamic parser registry, sizes cleaning, length extraction
│   ├── reviews.py               # OGL + TGR review scrapers (7 TGR sitemaps), two-pass fuzzy matcher with family fallback, model-to-brand lookup
│   ├── browser.py               # Playwright-based scraper with per-store JS extractors (9 stores)
│   ├── cli.py                   # Click CLI (refresh, deals, fetch-reviews, generate-codes, list-codes)
│   ├── auth.py                  # JWT session auth middleware + admin bypass via ADMIN_KEY env var (no DB lookup for session validation)
│   ├── parsers/
│   │   ├── __init__.py          # Parser registry docs
│   │   ├── common.py            # Shared parse_price() used by all BS4 parsers
│   │   ├── alpineshopvt.py      # Alpine Shop VT (BigCommerce)
│   │   ├── thecircle.py         # The Circle Whistler (Lightspeed eCom)
│   │   ├── coloradodiscount.py  # Colorado Discount Skis (custom HTML)
│   │   └── sacredride.py        # Sacred Ride (WooCommerce)
│   └── web/
│       ├── __init__.py
│       ├── app.py               # FastAPI app factory (lifespan init_db, auth middleware, all routers)
│       ├── routes.py            # Page + htmx partial + status dashboard routes
│       ├── invite_routes.py     # GET/POST /invite for invite code entry
│       ├── admin_routes.py      # GET/POST /admin/codes for invite code management
│       ├── event_routes.py      # POST /api/event (analytics tracking) + GET /admin/stats (dashboard)
│       ├── templates/
│       │   ├── index.html       # Main deals page with sticky toolbar, filters (search, category, brand, store, sort, length range, reviewed, tax-free) + analytics JS
│       │   ├── invite.html      # Invite code entry page (dark-themed)
│       │   ├── status.html      # Store status dashboard
│       │   ├── admin_codes.html # Admin invite code management page
│       │   ├── admin_stats.html # Admin analytics dashboard (KPIs, charts, tables)
│       │   └── partials/
│       │       ├── _card.html       # Shared deal card markup (div-based, not <a>, to avoid nested anchor issue)
│       │       ├── deal_cards.html  # htmx partial for deal grid (initial load)
│       │       └── more_cards.html  # htmx partial for load-more pagination
│       └── static/
│           └── style.css        # Glassmorphism dark theme with gradient accents, glow effects, sticky toolbar
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

# Run tests (64 tests)
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
- **TemplateResponse keyword style:** Always use `templates.TemplateResponse(request=request, name="template.html", context={...})` — newer Starlette rejects positional arguments (causes "unhashable type: dict" errors).
- **Analytics tracking:** Client-side fire-and-forget `fetch()` calls to `POST /api/event` for clicks, page views, filter changes, and searches. Data attributes on deal cards (`data-store`, `data-deal-name`, `data-category`) support event metadata.

## Architecture Decisions

- **SQLite + htmx:** SQLite via aiosqlite for persistence (no re-scraping per page load). Server-rendered HTML with htmx partials for dynamic filtering — no build step.
- **Scraping:** `asyncio.gather` with per-domain semaphores. Playwright for 10 JS-rendered stores (anti-bot stealth). Shopify/BlueZone parsers reused from parent `snow_deals` package.
- **Review matching:** OGL (26 categories, 0-100 scores) + TGR (7 sitemaps, qualitative→numeric). Two-pass fuzzy matching: exact (0.78 threshold) then family fallback (0.88). `_MODEL_TO_BRAND` dict for brandless product matching.
- **Data quality:** Multi-layer pipeline — EXCLUDE_KEYWORDS → URL domain stripping → keyword categorization → boot disambiguation (`_disambiguate_boot()`) → brand/model name fallback → NOT_HARDGOODS_KEYWORDS guard. Uncategorized rate: 0.7%.
- **Deployment:** GitHub Actions scrapes every 6h, uploads `deals.db` as release asset. Render downloads DB on cold start. Auth data (invite codes, events) persists in Turso cloud SQLite — survives redeploys. Sessions use stateless JWT cookies (no DB lookup). Admin panel + analytics dashboard.
- **UI:** Glassmorphism dark theme, sticky toolbar, filter state in URL via `history.replaceState`. Deal cards use `<div>` with `onclick` (not `<a>`) to allow nested review links. CAD prices shown with `C$` prefix. Tax-free filter for WA-based users.

### Known Data Quality Issues (as of 2026-03-23)

- **Sacred Ride:** Returns 0 products — site may be down or markup changed. Needs investigation.
- **The House:** Products have 0 images — JS extractor doesn't capture `image_url`.
- **Uncategorized:** 104 deals (0.7%) remain uncategorized — mostly from Backcountry (18), Level Nine Sports (21), Skirack (25).
- **Sizes:** Only available from Shopify stores (Aspen, Colorado Ski Shop, PRFO, Ski Depot, Sports Basement). Browser-scraped stores don't extract sizes.
- **Evo:** Only 80 products — browser stores limited to `max_pages=3`, may need increase.
- **Review match rates:** Skis 20.9%, snowboards 39.8%, ski boots 5.7%, bindings 13.8% — limited by OGL review volume for some categories.
