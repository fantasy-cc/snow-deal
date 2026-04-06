# Evaluation & Contracts

Quality contracts and verification criteria for FreshPowder aggregator work.

## Grading Criteria

- **Functionality:** Features work end-to-end: scrape → store → serve → filter → display
- **Code Quality:** Async throughout, typed dataclasses, no duplicate logic, no runtime O(N×M) operations in hot paths
- **Testing:** `pytest tests/ -v` all pass; new columns/functions have DB-level tests; web route changes have route tests
- **Data Quality:** Uncategorized rate ≤ 1%, brand filter returns correct multi-word brands, image_url populated for Shopify stores

## Active Sprint Contracts

### Phase 19: Render Deploy Hook
- **Verification:** After scrape completes in GitHub Actions, Render service automatically redeploys (visible in Render deploy log)
- **Acceptance:** `RENDER_DEPLOY_HOOK_URL` secret set in GitHub Actions; curl step in scrape.yml fires successfully

### Phase 19: Price History
- **Verification:** DB has a `price_history` table; re-scraping same URL with new price adds a row; UI shows a sparkline or "was $X" annotation
- **Acceptance threshold:** Price changes tracked for at least 30 days; no existing deal data lost

## Evaluation Log

| Date | Task | Grade | Notes |
|------|------|-------|-------|
| 2026-04-05 | Phase 18 — image_url, brand, deal_reviews | **Pass** | 71/71 tests; 15 files changed, 298 insertions/129 deletions; commit f912a47 |
| 2026-04-05 | test_brand_query | Fixed | Initial failure: brand column NULL in test fixture; resolved by setting `deal.brand` explicitly |
| 2026-04-05 | test_web_routes fixture | Fixed | `_reviews_cache` / `get_all_reviews` references removed from fixture after routes.py cleanup |
