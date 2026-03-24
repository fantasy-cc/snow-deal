# snow-deals aggregator — Execution Plan

This is a living document. Keep Progress, Surprises & Discoveries,
Decision Log, and Outcomes & Retrospective up to date as work proceeds.

## Purpose / Big Picture

A user can run `snow-deals-agg refresh` to scrape deals from 24 ski/snowboard retailers into a local SQLite database, `snow-deals-agg fetch-reviews` to pull review scores from OutdoorGearLab and The Good Ride, then browse a FastAPI + htmx web UI to filter and rank deals by category, store, brand, discount percentage, ski/snowboard length range, review status, and tax-free status. Review scores (0-100) are shown on deal cards with award text and review links. "Top reviewed" sort and "Reviewed only" filter help surface expert-validated gear. A CLI is also available for terminal-based querying. A separate status dashboard shows store health and data freshness.

## Progress

### Phases 1–14: Foundation through Admin Panel (Complete)
Core platform built and refined over 14 phases: 24-store scraper (Shopify + Playwright), SQLite persistence, FastAPI + htmx web UI, OGL + TGR review integration (1,271+ reviews), invite-only auth, admin panel with analytics, glassmorphism UI, length/size/brand/tax-free filtering, load-more pagination, and GitHub Actions + Render deployment. 57→64 test suite established.

### Phase 15: Data Quality & Review Coverage (Complete)
- [x] Zero-discount filtering — removed 3,321 deals with 0% discount, added scraper filter
- [x] Model family matching — two-pass review matcher (exact at 0.78, family fallback at 0.88)
- [x] TGR multi-product expansion — 7 sitemaps (snowboards, bindings, boots, jackets, pants, accessories)
- [x] Brand/model name fallback categorization — BOOT_BRANDS, SKI/BOOT/SNOWBOARD_MODEL_NAMES sets
- [x] Expanded EXCLUDE_KEYWORDS — ~150 keywords covering water sports, cycling, casual brands/clothing, camping, home décor
- [x] Expanded OGL categories — 26 URLs (added splitboard skins, avalanche airbag, snowshoes, women's snowboard)
- [x] Fixed _extract_brand year-prefix handling and _normalize orphaned 's
- [x] Boot category split — "boots" → "ski boots" + "snowboard boots" with `_disambiguate_boot()` function
- [x] SKI_BOOT_BRANDS/SNOWBOARD_BOOT_BRANDS and SKI_BOOT_MODEL_NAMES/SNOWBOARD_BOOT_MODEL_NAMES sets
- [x] MULTI_WORD_MODEL_NAMES (50+ phrase→category tuples), GOGGLE_MODEL_NAMES, expanded BINDING_MODEL_NAMES
- [x] `_MODEL_TO_BRAND` dict (60+ entries) in reviews.py for brandless product review matching
- [x] `_extract_brand()` strips Women's/Men's prefix, falls back to model-to-brand lookup
- [x] Uncategorized rate reduced from 16.2% → 6.7% → 0.7% (104/15,369)
- [x] ~500 non-snow items excluded via expanded EXCLUDE_KEYWORDS
- [x] Review coverage expanded from ~183 to 1,271+ reviews
- [x] 64 tests passing (up from 61)

### Phase 16: Auth Persistence — Turso + JWT (Complete)
- [x] (2026-03-23) Split auth data into separate Turso cloud SQLite (`auth_db.py`) — invite codes, sessions, events persist across Render redeploys
- [x] (2026-03-23) Replace DB session lookup with JWT signed cookies (`auth.py`) — stateless session validation, no network call needed
- [x] (2026-03-23) Create Turso database (`snow-deals-auth`) with embedded replica pattern via `libsql` package
- [x] (2026-03-23) Update admin_routes, event_routes, invite_routes, cli to use `auth_db` imports
- [x] (2026-03-23) Clean deals `db.py` — removed invite_codes/sessions/events tables, kept deals/reviews only
- [x] (2026-03-23) Restore MIGRATIONS for sizes/length_min/length_max columns (lost during auth cleanup, caused 500 on production)
- [x] (2026-03-23) Configure Render env vars: TURSO_URL, TURSO_AUTH_TOKEN, SECRET_KEY
- [x] (2026-03-23) Pre-seed invite codes (SNOW2024, FRESHPOW) in Turso
- [x] (2026-03-23) End-to-end verification: invite flow, JWT persistence, admin panel, main page all working on production

### Phase 17: Remaining Work (Backlog)
- [ ] Fix Sacred Ride — returns 0 products (site down or markup changed)
- [ ] Fix The House — 0 images captured by JS extractor
- [ ] Investigate Evo low product count (80 products, may need higher max_pages)
- [ ] Set up Render deploy hook to auto-redeploy after scrape
- [ ] Dark/light theme toggle
- [ ] Price history tracking

## Surprises & Discoveries

Key lessons learned (see git history for full details):

- **Playwright:** Use `domcontentloaded` not `networkidle` for anti-bot sites; use `forEach` not `for...of` for NodeList in `page.evaluate()`.
- **Store platform sharing:** Backcountry/Steep & Cheap/Level Nine share Chakra UI; Corbetts/Peter Glenn/Alpine Shop VT share BigCommerce Stencil.
- **Review sources:** OGL + TGR are the only viable free sources (Blister lacks scores, SkiMag paywalled). TGR has 1036 snowboard reviews vs OGL's ~8; TGR boots/bindings use snowflake images as ratings.
- **Categorization pitfalls:** Store domains with "ski" triggered false matches (fixed by URL domain stripping). Brand fallback was too aggressive — "Burton" T-shirts became snowboards (fixed with NOT_HARDGOODS_KEYWORDS). Ambiguous brands (K2, Salomon) make both skis and snowboards.
- **Boot disambiguation complexity:** Same brands make both ski/snowboard boots. Requires layered approach: URL clues → dedicated boot brands → model names → ambiguous-brand heuristics → GripWalk suffix → touring context.
- **Brandless products:** Sports Basement lists bare model names — needed `_MODEL_TO_BRAND` lookup for both categorization and review matching.
- **CWD matters:** Always run scrape commands from the `aggregator/` directory — background scrapes from repo root write to wrong DB path.

## Decision Log

### Foundational (2026-03-20)
- **SQLite + aiosqlite** — zero-config, portable, no concurrent write needs
- **FastAPI + htmx** — server-rendered HTML, no build step, htmx partials for filtering
- **Playwright for JS stores** — 9 stores require browser rendering; anti-bot stealth for Evo/Backcountry/Level Nine
- **Reuse parent parsers** — ShopifyParser/BlueZoneParser from `snow_deals` package
- **Per-domain semaphores** — rate limiting to 2 concurrent requests per retailer
- **OGL + TGR dual review sources** — OGL for ski/boot/gear, TGR for 1000+ snowboard reviews
- **WA state tax-free reference** — Canadian stores + no-WA-nexus stores marked tax_free
- **Kids filter at scraping layer** — prevents kids items from entering DB
- **Dynamic parser registry** — `importlib`-based lazy loading in `_PARSER_REGISTRY`

### Deployment & Auth (2026-03-21)
- **GitHub Actions + Render** — Playwright too heavy for Render; Actions scrapes every 6h, uploads DB as release asset
- **Invite-only auth** — reusable codes (max 5 uses), admin bypass via `ADMIN_KEY` env var

### Data Quality & UI (2026-03-22)
- **Multi-layer data quality pipeline** — EXCLUDE_KEYWORDS → URL domain stripping → brand fallback → NOT_HARDGOODS_KEYWORDS guard
- **Two-pass review matching** — exact (0.78 threshold) then family fallback (0.88) for width variants
- **Zero-discount filter** — removed 3,321 full-price items at scraping layer
- **Model name sets** — SKI/BOOT/SNOWBOARD_MODEL_NAMES for brandless product categorization
- **`<div>` cards with `onclick`** — avoids nested `<a>` tag HTML parser bug
- **DB migrations via MIGRATIONS list** — idempotent `ALTER TABLE ADD COLUMN` with try/except
- **TemplateResponse keyword-style** — required by newer Starlette versions

### Auth Persistence (2026-03-23)
- **Turso cloud SQLite for auth** — invite codes, sessions, events survive Render redeploys. `libsql` embedded replica: reads instant (local), writes push via `.sync()`. Free tier: 500M reads/month, 10M writes/month
- **JWT stateless sessions** — `PyJWT` signed cookies replace DB session lookup. Sessions survive server restart and DB wipe (only need `SECRET_KEY` env var)
- **Dual-backend auth_db.py** — Turso when `TURSO_URL` set, local SQLite (`auth.db`) fallback for dev. Same API surface
- **libsql over libsql-client** — `libsql-client` (archived) has WebSocket handshake bug (505 error). `libsql` uses embedded replica with sqlite3-compatible sync API
- **Migration loss bug** — Removing auth from db.py accidentally removed deal column migrations (sizes/length_min/length_max), causing 500 on production where downloaded DB predates those columns

### Earlier (2026-03-23)
- **Boot category split** — "boots" → "ski boots"/"snowboard boots" via multi-layered `_disambiguate_boot()`
- **Model-to-brand lookup** — `_MODEL_TO_BRAND` (60+ entries) enables review matching for brandless products

## Outcomes & Retrospective

Phases 1–16 complete. 24 stores configured, ~15,369 deals (after zero-discount cleanup and ~500 non-snow item exclusions). Review coverage: 1,271+ reviews from OGL (26 categories) and TGR (7 sitemaps). Match rates: skis 20.9%, snowboards 39.8%, ski boots 5.7%, bindings 13.8%. Boot category split into "ski boots" and "snowboard boots" with multi-layered disambiguation. Uncategorized rate reduced from 16.2% → 0.7% (104/15,369) via brand/model name fallback sets, MULTI_WORD_MODEL_NAMES, and expanded EXCLUDE_KEYWORDS (~150 keywords). `_MODEL_TO_BRAND` dict enables review matching for brandless products. Auth persistence solved: invite codes and events in Turso cloud SQLite (survive redeploys), sessions via JWT cookies (stateless). 64-test suite passing. Site live at https://snow-deals.onrender.com. Key remaining work: fix Sacred Ride and The House issues, Evo pagination.

## Context and Orientation

This is a sub-project within the snow-deals monorepo (`aggregator/` directory). It depends on the parent `snow_deals` package for `ShopifyParser`, `BlueZoneParser`, and the `Product` model. The aggregator adds multi-store orchestration, Playwright browser scraping, SQLite persistence, keyword categorization, and a web UI. Target retailers are sourced from uscardforum.com — Shopify-based stores use existing parsers; others use Playwright with store-specific JS extractors in `browser.py`.

## Plan of Work

Phases 1-15 complete. Backlog items in Phase 16. Site live at https://snow-deals.onrender.com.

## Validation and Acceptance

- `pytest tests/ -v` — 64 tests, all passing
- `snow-deals-agg refresh` — scrapes 24 stores into SQLite (~15,369 deals)
- `snow-deals-agg fetch-reviews` — scrapes OGL + TGR reviews (1,271+)
- Web UI at localhost:8000 — filtering, reviews, pagination, status dashboard all functional
