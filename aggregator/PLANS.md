# snow-deals aggregator — Execution Plan

This is a living document. Keep Progress, Surprises & Discoveries,
Decision Log, and Outcomes & Retrospective up to date as work proceeds.

## Purpose / Big Picture

A user can run `snow-deals-agg refresh` to scrape deals from 24 ski/snowboard retailers into a local SQLite database, `snow-deals-agg fetch-reviews` to pull review scores from OutdoorGearLab and The Good Ride, then browse a FastAPI + htmx web UI to filter and rank deals by category, store, brand, discount percentage, ski/snowboard length range, review status, and tax-free status. Review scores (0-100) are shown on deal cards with award text and review links. "Top reviewed" sort and "Reviewed only" filter help surface expert-validated gear. A CLI is also available for terminal-based querying. A separate status dashboard shows store health and data freshness.

## Progress

### Phase 1: Bootstrap (Complete)
- [x] Scaffold aggregator directory structure
- [x] Create pyproject.toml with dependencies
- [x] Implement store registry and category keywords (config.py)
- [x] Implement AggregatedDeal model (models.py)
- [x] Implement keyword categorizer (categorizer.py)
- [x] Implement SQLite schema and CRUD (db.py)
- [x] Implement multi-store async scraper (scraper.py)
- [x] Implement Click CLI with refresh and deals commands (cli.py)
- [x] Implement FastAPI app with htmx templates (web/)
- [x] Create project documentation (AGENTS.md, PLANS.md, README.md)

### Phase 2: Store Parsers & Browser Scraping (Complete)
- [x] Implement Playwright-based browser scraper (browser.py) with anti-bot stealth
- [x] Implement all store-specific JS extractors
- [x] Fix Backcountry Chakra UI extractor
- [x] Fix Steep & Cheap URL paths
- [x] Fix Level Nine Sports (shares Backcountry parser, anti-bot handling)
- [x] Fix Corbetts BigCommerce price selectors and dedup
- [x] Fix Evo price selectors
- [x] Fix Alpine Shop VT BigCommerce price selectors
- [x] Fix The House GTM percentOff original price calculation
- [x] Fix The Circle Whistler Lightspeed data attributes + lazy-load timing
- [x] Fix Colorado Discount Skis URL
- [x] Remove Powder7 (used items)

### Phase 3: UI Features (Complete)
- [x] Sort control (discount, price low/high, store, newest)
- [x] Deal count display with htmx OOB updates
- [x] Category tags on deal cards
- [x] Store status/freshness dashboard (separate `/status` page)
- [x] Tax-free tags on deal cards and status page
- [x] Header navigation between deals and status pages

### Phase 4: Enhancements (Complete)
- [x] Tax-free filter toggle on deals page
- [x] Verify Corbetts scrape completeness (expanded to 4 URLs, 365+ deals)
- [x] Offset-based pagination with load-more button (PAGE_SIZE=60)
- [x] Compact/comfortable view toggle with localStorage persistence
- [x] "New since last visit" badges with pulse animation
- [x] Search bar with debounced htmx requests
- [x] Size filter (extracted from Shopify variants, displayed on cards)
- [x] Add new stores: Colorado Ski Shop, Peter Glenn, Ski Depot (16 total)

### Phase 5: Codebase Cleanup (Complete)
- [x] Remove stub parser files (evo.py, backcountry.py, rei.py)
- [x] Replace hardcoded parser imports with dynamic registry (`_PARSER_REGISTRY`)
- [x] Extract shared card template (`partials/_card.html`) to DRY up templates
- [x] Fix browser.py formatting (indentation, blank lines)
- [x] Update parsers/__init__.py docstring
- [x] Update all documentation to reflect current state

### Phase 6: Review Score Integration (Complete)
- [x] OutdoorGearLab scraper — 21 category URLs, 0-100 scores for ski/boot/gear
- [x] The Good Ride scraper — 1000+ snowboard reviews via sitemap discovery
- [x] Qualitative-to-numeric conversion (Great=85, Good=70, Average=55, etc.)
- [x] Fuzzy product matching with brand-gating, model number overlap, 0.72 threshold
- [x] Multi-word brand support (Lib Tech, Never Summer, Capita Spring Break, etc.)
- [x] Reviews table in SQLite with upsert/query functions
- [x] In-memory review cache in web routes
- [x] Review score badges on deal cards (color-coded green/orange/red)
- [x] CLI `fetch-reviews` command with `--source` flag (ogl/tgr/all)
- [x] Kids/junior product filtering at scraping layer

### Phase 7: Store Expansion & Tax-Free (Complete)
- [x] Add Sacred Ride (sacredride.ca) — WooCommerce parser + Playwright browser config
- [x] WA-state tax-free focus — Canadian stores + no-nexus stores marked tax_free
- [x] Update Aspen Ski and Board to tax_free
- [x] UI label updated to "Tax Free" (focused on WA state)
- [x] Fix ShopifyParser NameError in scraper.py (use hasattr instead of isinstance)
- [x] Consolidate duplicate multi-word brand lists in reviews.py

### Phase 8: Brand Filtering, CAD Prices & Visual Polish (Complete)
- [x] Brand filter dropdown populated from DB via `get_brands()`
- [x] CAD price display (`C$` prefix + `CAD` tag) for Canadian stores
- [x] Added `currency` field to `StoreConfig` (explicit CAD/USD)
- [x] Visual overhaul — Inter font, refined dark palette, two-row filter layout
- [x] Custom range slider styling, subtle card borders, backdrop-blur on review scores

### Phase 9: Codebase Refactoring & Test Suite (Complete)
- [x] browser.py consolidated — 8 JS wrapper functions eliminated, inlined into `STORE_CONFIGS` dict
- [x] BigCommerce stores (Corbetts, Peter Glenn, Alpine Shop VT) consolidated into single config with aliases
- [x] Shared `_JS_PARSE_PRICE` constant extracted for reuse across browser extractors
- [x] browser.py reduced from ~613 lines to ~280 lines
- [x] Shared `parse_price()` extracted to `parsers/common.py` — all 4 BS4 parsers import from it
- [x] Routes DRY-up — `_fetch_deals()` helper extracts shared query logic from `index()` and `deals_fragment()`
- [x] 57-test suite created across 7 test files covering all core modules
- [x] All tests passing

### Phase 10: Deployment & Auth (Complete)
- [x] GitHub Actions cron workflow — scrapes all stores every 6 hours, uploads `deals.db` as release asset
- [x] Render free tier deployment — Dockerfile, startup script downloads DB from GitHub Releases
- [x] `DATABASE_PATH` env var for configurable DB location
- [x] Invite-only authentication — `invite_codes` + `sessions` tables, auth middleware, `/invite` page
- [x] Admin bypass via `ADMIN_KEY` env var (persistent cookie)
- [x] CLI commands: `generate-codes N`, `list-codes`
- [x] App lifespan hook runs `init_db()` on startup to create tables in downloaded DB
- [x] Site live at https://snow-deals.onrender.com

### Phase 11: Store Expansion (Complete)
- [x] Added 7 new Shopify stores: Comor Sports, Ski Pro AZ, First Stop Board Barn, Fresh Skis, Rude Boys, Skiis & Biikes, Skirack (24 total stores)

### Phase 12: Data Quality & Length Filtering (Complete)
- [x] Dual-range length filter (100-210cm) with `length_min`/`length_max` DB columns
- [x] `_extract_lengths()` parses cm values from sizes strings
- [x] Deals without length data pass through (not filtered out)
- [x] Filter state persistence via `history.replaceState` (survives back-navigation)
- [x] Data quality overhaul — EXCLUDE_KEYWORDS, URL domain stripping, brand-based fallback categorization
- [x] Sizes cleaning — strip colors, retail prices, junk values via `_clean_sizes()`
- [x] Added 7 new Shopify stores (24 total)
- [x] "Reviewed only" filter toggle and "Top reviewed" sort option
- [x] Review row on cards with score badge, award text, and "Read review" link

### Phase 13: Visual Polish & Card Fix (Complete)
- [x] Full CSS rewrite — sticky toolbar, gradient logo, header stats, footer
- [x] Polished dark theme with refined spacing and typography
- [x] Fixed critical card rendering bug — nested `<a>` tags caused HTML parser to shatter card structure
- [x] Changed card element from `<a>` to `<div>` with `onclick` navigation
- [x] Reviewed cards get subtle green top-border accent
- [x] Jinja2 `auto_reload` enabled for development
- [x] Cache-busting CSS version parameter

### Phase 14: Remaining Issues & Next Steps (Current)
- [ ] Fix Sacred Ride — returns 0 products (site down or markup changed)
- [ ] Fix The House — 0 images captured by JS extractor
- [ ] Improve categorization for PRFO (65%) and Sports Basement (43%)
- [ ] Investigate Evo low product count (80 products, may need higher max_pages)
- [ ] Set up Render deploy hook to auto-redeploy after scrape
- [ ] Dark/light theme toggle
- [ ] Price history tracking

## Surprises & Discoveries

- Backcountry, Steep & Cheap, and Level Nine Sports all use the same Chakra UI component library — one extractor works for all three with parser_type aliasing.
- `networkidle` wait strategy causes timeouts on anti-bot sites; `domcontentloaded` + explicit delays is more reliable.
- The Circle Whistler (Lightspeed eCom) lazy-loads variant price attributes after initial render — needs 3s post-selector wait.
- `for...of` on NodeList silently fails in some Playwright `page.evaluate()` contexts — `forEach` is safer.
- Powder7 primarily sells used gear — removed from scraping to keep deal quality high.
- Corbetts uses BigCommerce with BODL data layer — `.price--withoutTax` and `.price--non-sale` selectors.
- Shopify `/products.json` variants include `available` boolean and `option1`/`option2`/`option3` for size data.
- Peter Glenn uses the same BigCommerce Stencil theme as Corbetts — same JS extractor works for both.
- The Good Ride uses snowflake icons (full/half/empty) for ratings but also includes text labels (Great/Good/Average/etc.) which are easier to extract reliably.
- TGR's "Favorite" designation lives only in navigation menus, not on individual review pages — cannot be reliably extracted as an award.
- TGR has 1036 snowboard review URLs across two sitemaps, providing massive snowboard coverage vs OGL's ~8.
- Kids/junior product filtering works better at the scraping layer than as a UI toggle — prevents kids items from ever entering the database.
- Sacred Ride (sacredride.ca) returned 0 products on 2026-03-21 scrape despite parser being implemented — may be a site issue or markup change.
- The House JS extractor captures all product data except images (0/23 have image_url).
- PRFO and Sports Basement have broad catalogs beyond snow sports — only 65% and 43% categorized respectively.
- Sizes are only extractable from Shopify stores via `/products.json` variants. Browser-scraped stores don't expose size data in listing pages.
- Evo only returns ~80 products due to `max_pages=3` limit on browser stores.
- browser.py had 8 nearly identical JS wrapper functions that differed only in selectors — consolidating into a config dict reduced the file by >50%.
- HTML does not allow `<a>` inside `<a>` — the browser parser silently breaks the outer anchor, scattering card content outside the card container. Switching the card to `<div>` with `onclick` fixed this.
- Shopify variant sizes include colors, retail prices, and junk like "Default Title" — needs aggressive cleaning before display.
- Stores with "ski" in their domain (skiisandbiikes.com, skipro.com) caused ALL products to be categorized as "skis" when URL was used for categorization — fixed by stripping domain from URL before matching.
- Brand-based fallback categorization was too aggressive — "Burton" T-shirts became "snowboards". Fixed with NOT_HARDGOODS_KEYWORDS guard.
- Ambiguous brands (K2, Salomon, Rossignol) make both skis and snowboards — cannot use brand for ski/snowboard disambiguation.

## Decision Log

- Decision: Decouple scraping from serving via GitHub Actions + Render
  Rationale: Playwright requires ~500MB Chromium binary — too heavy for Render free tier. GitHub Actions provides free CI with Playwright support. SQLite DB is uploaded as a GitHub Release asset and downloaded by Render on cold start.
  Date: 2026-03-21

- Decision: Invite-only auth with one-time codes instead of user accounts
  Rationale: Simple access control for pre-launch sharing. No email/password infrastructure needed. Admin bypass via env var for developer access.
  Date: 2026-03-21

- Decision: Use SQLite via aiosqlite instead of a full database server
  Rationale: Local-first tool, no need for concurrent writes. SQLite is zero-config and portable.
  Date: 2026-03-20

- Decision: htmx for frontend interactivity instead of React/Vue
  Rationale: No build step, minimal JS, server-rendered HTML. The filtering UI is simple enough that htmx partials cover all needs.
  Date: 2026-03-20

- Decision: Reuse ShopifyParser and BlueZoneParser from snow_deals
  Rationale: Several stores are Shopify-based and BlueZone already has a parser. Avoids code duplication.
  Date: 2026-03-20

- Decision: Per-domain semaphores for rate limiting
  Rationale: Scraping ~16 stores concurrently could overwhelm individual servers. Semaphores limit to 2 concurrent requests per domain.
  Date: 2026-03-20

- Decision: Playwright for JS-rendered stores with anti-bot stealth
  Rationale: 9 stores require JavaScript rendering. Anti-bot measures (webdriver flag hiding) needed for Evo, Backcountry, Level Nine, Corbetts.
  Date: 2026-03-20

- Decision: Remove Powder7 from store registry
  Rationale: Site primarily sells used/consignment items, which don't represent genuine deals.
  Date: 2026-03-20

- Decision: Separate status dashboard at /status instead of inline panel
  Rationale: Keeps the main deals page clean while providing detailed store health information on a dedicated page.
  Date: 2026-03-20

- Decision: Mark Canadian stores as tax-free
  Rationale: PRFO, The Circle Whistler, and Corbetts are Canadian retailers that don't charge US sales tax, which is valuable deal information.
  Date: 2026-03-20

- Decision: Store sizes as comma-separated text rather than a separate table
  Rationale: Sizes are display-only metadata. LIKE filtering is sufficient for the expected query patterns. Avoids schema complexity.
  Date: 2026-03-20

- Decision: Dynamic parser registry with importlib instead of hardcoded imports
  Rationale: Cleaner separation of concerns, lazy loading, and easier to extend with new parser types.
  Date: 2026-03-20

- Decision: Dual review sources — OGL for ski/boot/gear, TGR for snowboards
  Rationale: OGL has excellent ski/boot coverage but only ~8 snowboard reviews. TGR has 1000+ snowboard reviews with qualitative ratings convertible to 0-100 scale.
  Date: 2026-03-20

- Decision: WA state as tax-free reference point
  Rationale: User is based in WA. Canadian stores and stores without WA sales tax nexus are marked tax_free. Evo (Seattle-based) has WA nexus so is not tax-free.
  Date: 2026-03-20

- Decision: Filter kids products at scraping layer, not UI
  Rationale: Kids gear clutters results without adding value. Filtering at `_products_to_deals()` prevents kids items from ever entering the database.
  Date: 2026-03-20

- Decision: Length filter uses dedicated DB columns, not string matching
  Rationale: `length_min`/`length_max` integer columns enable efficient SQL range overlap queries. Only ~8% of deals have length data (Shopify stores only), so deals without length data pass through unfiltered.
  Date: 2026-03-22

- Decision: Deal cards use `<div>` with `onclick` instead of `<a>` wrapper
  Rationale: Review links (`<a>`) inside card links (`<a>`) create invalid nested anchors. The browser parser silently shatters the card structure, making content invisible. `<div>` with JS `onclick` avoids the issue.
  Date: 2026-03-22

- Decision: Multi-layer data quality pipeline
  Rationale: Non-snow items (headlamps, insoles, gift cards) pollute results. EXCLUDE_KEYWORDS catches known junk, URL domain stripping prevents false category matches, brand-based fallback catches uncategorized hardgoods, NOT_HARDGOODS_KEYWORDS prevents clothing from being categorized as skis/snowboards.
  Date: 2026-03-22

## Outcomes & Retrospective

Phases 1–13 complete. 24 stores configured, 20,000+ deals scraped. Review scores integrated from OGL + TGR with "Top reviewed" sort and "Reviewed only" filter. Length range filter with dual-range slider. Data quality pipeline with exclude keywords, URL domain stripping, brand-based fallback categorization, and sizes cleaning. Fixed critical card rendering bug (nested `<a>` tags). Visual redesign with sticky toolbar, gradient logo, polished dark theme. 61-test suite passing. Site deployed to Render free tier (https://snow-deals.onrender.com) with invite-only access. GitHub Actions cron scrapes every 6 hours. Key remaining work: fix data quality issues (Sacred Ride, The House), improve categorization coverage.

## Context and Orientation

This is a sub-project within the snow-deals monorepo (`aggregator/` directory). It depends on the parent `snow_deals` package for `ShopifyParser`, `BlueZoneParser`, and the `Product` model. The aggregator adds multi-store orchestration, Playwright browser scraping, SQLite persistence, keyword categorization, and a web UI. Target retailers are sourced from uscardforum.com — Shopify-based stores use existing parsers; others use Playwright with store-specific JS extractors in `browser.py`.

## Plan of Work

Current focus is on Phase 12 — fixing data quality issues (Sacred Ride, The House images, PRFO/Sports Basement categorization, Evo pagination). Deployment and auth are complete. Site is live at https://snow-deals.onrender.com with invite-only access.

## Validation and Acceptance

- `pip install -e .` succeeds in the aggregator directory (with snow_deals installed).
- `pytest tests/ -v` runs 61 tests, all passing.
- `snow-deals-agg refresh` scrapes stores and populates SQLite (20,000+ deals across 24 stores).
- `snow-deals-agg fetch-reviews` scrapes OGL + TGR reviews and stores in DB.
- `snow-deals-agg deals` displays a Rich table of deals from the database.
- `uvicorn aggregator.web.app:create_app --factory` starts the web UI on localhost:8000.
- Filtering by category, store, brand, sort, discount %, length range, reviewed, and tax-free works via htmx.
- Review score badges with award text and "Read review" links appear on matched deal cards.
- "Top reviewed" sort and "Reviewed only" filter work correctly.
- Load-more pagination works correctly.
- `/status` page shows all 24 stores with freshness indicators.
- Tax-free tags appear on Canadian and no-WA-nexus store deals.
- Size data displays on cards for Shopify-sourced products.
- Brand filter dropdown works for filtering by manufacturer.
- CAD prices display correctly with `C$` prefix on Canadian store deals.
