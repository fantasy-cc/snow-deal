# Launch & Growth

## Goal
FreshPowder focuses on growth: seeding users, enabling virality, and preparing for monetization. Target: Seed 100 users and measure viral coefficient.

## Progress
- [ ] Monitor analytics and gather feedback from initial users
- [ ] Implement viral invite loop (auto-generate 3 codes on signup, /my-codes page)
- [ ] Join affiliate programs (AvantLink for evo, Backcountry, REI)
- [ ] Replace direct retailer links with affiliate links
- [ ] Post on Rednote with invite codes
- [ ] Post on USCardForum
- [ ] Weekly "best deals" content for social channels
- [ ] Price history tracking (store historical prices per product)
- [ ] Price alert system (notify when product drops below target)
- [ ] Size watchlist feature
- [ ] Email infrastructure (Resend/Postmark) for alerts and waitlist
- [ ] Pro tier ($5-8/mo) gating premium features
- [ ] Custom domain (freshpowder.deals or similar)

## Findings
- BlueZone Sports pagination shows "1 / 5" but actually has 9 pages (2026-03-13)
- `" used "` keyword with space padding avoids matching "unused"/"refused" — critical for exclusion keywords (2026-04-07)
- Single-word model names like "frontier", "ultra", "hera" are too ambiguous. Must use brand-qualified multi-word entries. (2026-04-07)
- Brand fallback categorization catches accessories as hardgoods — NOT_HARDGOODS_KEYWORDS must be aggressively expanded. (2026-04-07)
- htmx `hx-target="this"` on load-more button leaves the wrapper div. Must use `hx-target="closest .load-more-wrap"` with `hx-swap="outerHTML"`. (2026-04-07)
- Headless Shopify (Hydrogen/Oxygen) stores return 404 on JSON API endpoints — must use Playwright browser scraping. (2026-04-08)
- REI uses hashed CSS class names but stable `data-ui` attributes for product-brand/product-title — use those for resilient selectors. (2026-04-08)
- MEC uses Algolia InstantSearch with `ais-Pagination` classes — standard pagination selectors work. (2026-04-08)
- Shared `_JS_PARSE_PRICE` regex `[\d,]+\.\d{2}` fails on whole-dollar prices like "$1,150" — stores with non-decimal prices need custom `[\d,]+\.?\d*` regex. (2026-04-08)

## Decisions
- Invite-gated access with public landing page to control growth and create exclusivity.
- Repo set to private. Scraper configs and categorization rules are competitive advantages.
- Keyword-based categorization over ML. Fast, deterministic, debuggable.
- SQLite for deals + Turso for auth. Fast/ephemeral deals, persistent auth.
- htmx over React/SPA. Server-rendered templates give fast interactivity without JS framework complexity.

## Archive
- Phase 1: Core Product (Complete)
- Phase 2: Auth & Landing (Complete)
- Phase 3: UI Polish & GTM Readiness (Complete)
- Phase 3b: Store Expansion & Data Quality (Complete)
