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

### Phase 17: Scraper Health (Complete)
- [x] (2026-04-04) Fix Sacred Ride — switched back to static HTML parser path after Avada markup change; live verification returned 157 discounted deals
- [x] (2026-04-04) Re-verify The House scraper — Playwright extractor returns 236 products on the current sale listing
- [x] (2026-04-04) Re-verify Evo pagination — live Playwright scrape returns 200 products in the first 5 pages

### Phase 18: UX, Data Quality & Filtering (Complete — 2026-04-05)
- [x] Add `image_url TEXT` column to deals schema (migration + upsert + query)
- [x] Extract image URLs in Shopify parser (`images[0].src`) and all 7 browser JS extractors
- [x] Add `brand TEXT` column populated at scrape time using `_extract_brand()` from reviews.py
- [x] Fix `get_brands()` to use the `brand` column (was naive SUBSTR first-word SQL)
- [x] Fix `query_deals()` brand filter to use `brand = ?` (was fragile `name LIKE '{brand} %'`)
- [x] Add `deal_reviews` join table (deal_id, review_id, score, award, review_url)
- [x] Add `compute_and_store_deal_reviews()` in reviews.py — runs fuzzy matching once, stores results
- [x] Call `compute_and_store_deal_reviews()` from `fetch-reviews` CLI command
- [x] Update `query_deals()` to LEFT JOIN `deal_reviews` — `top_reviewed` sort and `reviewed_only` filter now SQL, not Python
- [x] Remove `_reviews_cache`, `_get_reviews()`, `_attach_reviews()` from routes.py (O(N×M) eliminated)
- [x] Add `review_score`, `review_award`, `review_url` fields to `AggregatedDeal` (pre-joined from DB)
- [x] Update `_card.html` to display `deal.image_url` with placeholder fallback
- [x] Add compact view image thumbnail (64×80px) in style.css
- [x] Add deal counts to category/store dropdowns in index.html (`get_category_counts()`)
- [x] Fix length filter: active range now EXCLUDES NULL-length deals (was including them)
- [x] Improve empty state in deal_cards.html (icon + clearer text)
- [x] 71 tests passing after test fixture updates for new schema

### Phase 19: Backlog
- [ ] Set up Render deploy hook to auto-redeploy after scrape
- [ ] Dark/light theme toggle
- [ ] Price history tracking
- [ ] Gender filter (extract Women's/Men's from product name)
- [ ] Improve review match rates for ski boots (5.7%) and bindings (13.8%)

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

### UX, Data Quality & Filtering (2026-04-05)
- **deal_reviews join table** — pre-compute review→deal matches at `fetch-reviews` time; eliminates O(N×M) runtime matching in routes.py; `top_reviewed` sort and `reviewed_only` filter become SQL operations
- **brand column** — extracted at scrape time using `_extract_brand()` (already in reviews.py); fixes multi-word brands ("Lib Tech"), year prefixes ("2025 Atomic"), gender prefixes ("Women's Salomon") in filter dropdown
- **image_url column** — added to all parsers and browser JS extractors; Shopify uses `images[0].src`, browser stores use `data-src || src` pattern
- **Length filter NULL exclusion** — active length range now excludes NULL-length deals (previous behavior silently included all 8,712 null-length deals)

## Outcomes & Retrospective

Phases 1–18 complete. 24 stores configured, ~15,369 deals. Review coverage: 1,271+ reviews from OGL + TGR. Deal cards now show product images, correct multi-word brand names, and pre-computed review scores (O(1) lookup via `deal_reviews` join table — no more O(N×M) runtime fuzzy matching). Category/store dropdowns show live deal counts. Length filter correctly excludes non-length deals when active. Brand column extracted at scrape time using `_extract_brand()` — handles "Lib Tech", "2025 Atomic Bent", "Women's Salomon". 71 tests passing. Site live at https://snow-deals.onrender.com. Key remaining work: run a fresh `refresh` + `fetch-reviews` to populate new columns, Render deploy-hook configuration, price history, and dark/light theme toggle.

## Context and Orientation

This is a sub-project within the snow-deals monorepo (`aggregator/` directory). It depends on the parent `snow_deals` package for `ShopifyParser`, `BlueZoneParser`, and the `Product` model. The aggregator adds multi-store orchestration, Playwright browser scraping, SQLite persistence, keyword categorization, and a web UI. Target retailers are sourced from uscardforum.com — Shopify-based stores use existing parsers; others use Playwright with store-specific JS extractors in `browser.py`.

## Plan of Work

Phases 1-15 complete. Backlog items in Phase 16. Site live at https://snow-deals.onrender.com.

## Validation and Acceptance

- `pytest tests/ -v` — 71 tests, all passing
- `snow-deals-agg refresh` — scrapes 24 stores; verify `image_url` and `brand` populated
- `snow-deals-agg fetch-reviews` — scrapes reviews; verify `deal_reviews` table populated
- Web UI at localhost:8000 — images on cards, brand filter works for "Lib Tech", top-reviewed sort fast, category counts visible in dropdowns, length filter excludes null-length deals
