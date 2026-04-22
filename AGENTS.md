# Agent Guide

## Project Overview

**FreshPowder** (repo: `snow-deal`) is a ski & snowboard deal aggregator that tracks prices across 20+ North American retailers every 6 hours, matches expert review scores from OutdoorGearLab and GoodRide, and surfaces the best deals through a fast, filterable web interface. The app is invite-gated for controlled growth, with a public marketing landing page. A secondary Tampermonkey userscript and Python CLI exist for single-site browsing.

**Live at:** https://snow-deals.onrender.com

## Tech Stack

### Web Aggregator (primary — `aggregator/`)
- **Backend:** Python 3.12, FastAPI, aiosqlite
- **Frontend:** Jinja2 templates, htmx 2.0.4, vanilla JS, custom CSS (dark theme)
- **Database:** SQLite (deals), Turso cloud (auth/sessions/events)
- **Auth:** JWT-based invite codes, rate limiting
- **Deployment:** Docker on Render (free tier)
- **Scraping:** GitHub Actions cron (every 6h), httpx + BeautifulSoup4/lxml, Playwright (for JS-rendered/anti-bot sites)
- **Reviews:** OutdoorGearLab + GoodRide score matching

### Tampermonkey Userscript (secondary — `tampermonkey/`)
- Vanilla JS, Tampermonkey GM_ APIs

### Python CLI (secondary — `snow_deals/`)
- Python 3.11+, httpx, click, rich

## Project Structure

```
snow-deal/
├── aggregator/                    # Main product — FreshPowder web app
│   ├── aggregator/
│   │   ├── config.py              # Stores, categories, keywords, model names, brands
│   │   ├── browser.py             # Playwright browser scraping (JS-rendered sites)
│   │   ├── categorizer.py         # Product categorization engine
│   │   ├── db.py                  # SQLite queries (deals, aggregation)
│   │   ├── auth_db.py             # Turso auth DB (invite codes, sessions, events, waitlist)
│   │   ├── auth.py                # JWT middleware, invite validation
│   │   ├── scraper.py             # Multi-store scraper orchestrator
│   │   ├── reviews.py             # Review score matching
│   │   ├── models.py              # Data models
│   │   ├── cli.py                 # Admin CLI (scrape, generate-codes, sync)
│   │   ├── wordlist.py            # Snow-themed words for invite codes
│   │   ├── web/
│   │   │   ├── app.py             # FastAPI app factory
│   │   │   ├── routes.py          # Main routes (/, /deals, /status)
│   │   │   ├── invite_routes.py   # Landing page, invite validation, waitlist
│   │   │   ├── admin_routes.py    # Admin panel (codes, stats)
│   │   │   ├── event_routes.py    # Click/event tracking API
│   │   │   ├── templates/         # Jinja2 templates
│   │   │   │   ├── index.html     # Main deal page (filters, presets, grid)
│   │   │   │   ├── invite.html    # Marketing landing page
│   │   │   │   ├── status.html    # Store health dashboard
│   │   │   │   └── partials/      # Card, grid, pagination partials
│   │   │   └── static/
│   │   │       ├── style.css      # All styles (~1500 lines, CSS variables)
│   │   │       └── img/           # Favicon, hero-bg, empty-state
│   │   └── parsers/               # Per-store scrapers
│   └── tests/
├── tampermonkey/                   # Browser userscript (secondary)
├── snow_deals/                     # Python CLI (secondary)
├── GTM.md                          # Go-to-market strategy
├── .github/workflows/scrape.yml   # Cron scraper (every 6h)
└── Dockerfile
```

## Development Workflow

```bash
# Setup
cd aggregator && pip install -e .

# Run locally
uvicorn aggregator.web.app:create_app --factory --reload

# Run tests
python -m pytest aggregator/tests/ -x -q

# Manual scrape
python -m aggregator.cli scrape

# Generate invite codes
python -m aggregator.cli generate-codes --count 5
```

## Coding Conventions

- **Templates:** Jinja2 + htmx for interactivity, no JS frameworks
- **CSS:** Custom properties (CSS variables), dark theme only, Inter font
- **JavaScript:** Vanilla JS inline in templates, no build step
- **Python:** Type annotations on public functions, async/await throughout
- **Categorization:** Keyword-based in `config.py` — use space-padded keywords to avoid substring false positives (e.g., `" used "` not `"used"`)
- **Model names:** Ambiguous single-word model names go in brand-qualified `MULTI_WORD_MODEL_NAMES`, not generic sets
- **htmx patterns:** `hx-get="/deals"`, `hx-target="#deal-grid"`, `hx-include=".filters [name]"` for filter syncing

## Architecture Decisions

- **Invite-gated access:** Controlled growth via human-readable invite codes (`POWDER-SUMMIT-42`). Landing page is public for SEO/marketing, deal content requires authentication.
- **Server-rendered with htmx:** No SPA framework. Jinja2 templates + htmx partials give fast interactivity with minimal JS complexity. Cards render server-side, filters trigger htmx GETs.
- **SQLite + Turso split:** Deal data in local SQLite (fast reads, scraped every 6h). Auth/session/event data in Turso cloud DB (persistent across deploys).
- **Keyword-based categorization:** Products categorized by keyword matching against name/URL, with brand fallback. Not ML-based — fast, deterministic, debuggable. False positives fixed by expanding `NOT_HARDGOODS_KEYWORDS` or moving ambiguous model names.
- **GitHub Actions scraping:** Runs on cron, not on the web server. Keeps the web app stateless and fast. Scrape results committed to DB.
- **Repo is private** (changed 2026-04-07): Scraper configs, store selectors, and categorization rules are competitive advantages.
