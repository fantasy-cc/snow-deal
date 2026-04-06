# Findings

Research results, discoveries, and external content collected during project work.

> **Security note:** External content (web searches, API responses, copied docs) goes
> here — never directly into PLANS.md.

## Research & References

- **OutdoorGearLab (OGL):** 26 category URLs scraped. Scores 0-100 from JSON-LD + `.rating_chart_score` CSS selector. Award text also extracted.
- **The Good Ride (TGR):** 7 XML sitemaps (snowboards, bindings, boots, jackets, pants, accessories). Qualitative ratings ("exceptional"=95 … "bad/poor"=20) averaged across attributes → numeric score.
- **Shopify JSON API:** `/collections/{handle}/products.json?limit=250&page=N` — `images[0].src` for product image, `variants[].compare_at_price` for original price.
- **BigCommerce Stencil:** Corbetts, Peter Glenn, Alpine Shop VT share `.card-title`, `.price--withoutTax`, `.price--non-sale` CSS selectors.
- **Backcountry/Steep & Cheap:** Use Chakra UI — price text structured as "Current price: $X / Original price: $Y".
- **The House:** Products have `data-gtmdata` JSON attribute with `{name, price, percentOff}`.

## Discoveries

### Phase 18 (2026-04-05)

- **Brand filter was broken for ~30% of brands.** `get_brands()` used `SUBSTR(name, 1, INSTR(...)-1)` — the first word of the product name. "Lib Tech Skunk Ape" returned "Lib", "2025 Atomic Bent" returned "2025", "Women's Salomon" returned "Women's". Fixed by adding a `brand` column populated at scrape time using `_extract_brand()` from reviews.py, which already handled all these cases.

- **Runtime review matching was O(N×M) on every page load.** `_attach_reviews()` in routes.py iterated all deals (~15K) against all reviews (~2K) on every `/deals` request. For "top_reviewed" sort this fetched up to 10,000 rows then sorted in Python. Fixed with `deal_reviews` join table — matching runs once after `fetch-reviews`, results stored; `query_deals()` LEFT JOINs for O(1) lookup. `top_reviewed` sort is now `ORDER BY deal_reviews.score DESC NULLS LAST`.

- **Length filter was silently including all null-length deals.** The original SQL used `OR length_min IS NULL` when a length range was active. A user filtering "150–180cm skis" would see all 8,712 null-length deals in the results. Fixed: active length range now excludes null-length deals entirely.

- **Browser JS extractors all had image URLs available but never extracted them.** The DOM contained `<img>` elements in every product card. Added `img.getAttribute('data-src') || img.src` to each store's JS extraction object. Images that use lazy-loading set `data-src`; others use `src` directly.

- **`_extract_brand()` from reviews.py was not reused in scraper.py.** Two separate brand-extraction approaches existed (naive SUBSTR in SQL vs. sophisticated function in reviews.py). Consolidated: `scraper.py` now imports `_extract_brand` directly from `reviews`.

### Earlier Phases

- **Playwright:** `domcontentloaded` not `networkidle` for anti-bot sites; `forEach` not `for...of` for NodeList in `page.evaluate()`.
- **Store platform sharing:** Backcountry/Steep & Cheap/Level Nine share Chakra UI; Corbetts/Peter Glenn/Alpine Shop VT share BigCommerce Stencil.
- **Boot disambiguation complexity:** Requires layered approach: URL clues → dedicated boot brands → model names → ambiguous-brand heuristics → GripWalk suffix → touring context.
- **CWD matters:** Always run scrape commands from the `aggregator/` directory — background scrapes from repo root write to wrong DB path.
- **libsql over libsql-client:** `libsql-client` (archived) has WebSocket handshake bug (505 error).

## Error Log

| Error | Context | Resolution | Date |
|-------|---------|------------|------|
| `AssertionError: 'Atomic' not in []` | test_brand_query after brand column added | `_make_deal()` helper didn't set `brand` field; updated test to set `deal.brand = "atomic"` explicitly | 2026-04-05 |
| `AttributeError: routes_module has no attribute '_reviews_cache'` | test_web_routes fixture after removing runtime matching | Removed `monkeypatch.setattr(routes_module, "get_all_reviews", ...)` and `routes_module._reviews_cache = None` lines from fixture; added `get_category_counts` monkeypatch instead | 2026-04-05 |
