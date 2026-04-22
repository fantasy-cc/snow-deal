# Context

## Project
FreshPowder (snow-deal) is a ski & snowboard deal aggregator that tracks prices across 20+ North American retailers every 6 hours, matches expert review scores from OutdoorGearLab and GoodRide, and surfaces the best deals through a fast, filterable web interface. Features invite-gated access with a public marketing landing page, a secondary Tampermonkey userscript, and Python CLI.

## Structure
- `aggregator/` - Main product: FreshPowder web app (FastAPI, htmx, Turso/SQLite, Playwright)
- `tampermonkey/` - Browser userscript (secondary)
- `snow_deals/` - Python CLI (secondary)
- `.github/workflows/` - Cron scraper (every 6h)

## Rules

### Never
1. Never commit secrets (cookies.json, .env, Turso tokens) — they're in-tree and must stay untracked
2. Never scrape without testing categorization first — mis-categorized products pollute the feed
3. Never skip the freshness/stock checks when adding a new parser

### Always
1. Always space-pad exclusion keywords (" used " not "used") to avoid substring false positives
2. Always run python -m pytest aggregator/tests/ -x -q before commit
3. Always verify selectors live via Playwright MCP before adding a new store

### Objectives
1. All tests pass (python -m pytest aggregator/tests/ -x -q exits 0)
2. Web app boots cleanly (uvicorn aggregator.web.app:create_app --factory exits 0 startup)
3. Scraper runs without parser errors (python -m aggregator.cli scrape exits 0)

## Workflow
- Setup: `cd aggregator && pip install -e .`
- Run: `uvicorn aggregator.web.app:create_app --factory --reload`
- Test: `python -m pytest aggregator/tests/ -x -q`
- Run Scrape: `python -m aggregator.cli scrape`

## Learned Patterns
1. Exclusion keyword design: space-padded `" used "` prevents matching "unused"/"refused". Prepend space to search string so keywords match at start: `f" {name} {url}".lower()`.
2. Model name ambiguity: Single-word names like "frontier", "ultra", "hera" are too ambiguous. Must use brand-qualified multi-word entries.
3. Brand fallback categorization catches accessories as hardgoods — NOT_HARDGOODS_KEYWORDS must be aggressively expanded.
4. htmx load-more pattern: `hx-target="this"` on the button leaves the wrapper div. Must use `hx-target="closest .load-more-wrap"` with `hx-swap="outerHTML"`.
5. Headless Shopify (Hydrogen/Oxygen) stores return 404 on JSON API endpoints — must use Playwright browser scraping.
6. Shared `_JS_PARSE_PRICE` regex `[\d,]+\.\d{2}` fails on whole-dollar prices like "$1,150" — stores with non-decimal prices need custom `[\d,]+\.?\d*` regex.
