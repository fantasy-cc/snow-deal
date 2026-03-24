# Agent Guide

## Project Overview

**snow-deals** finds the best discounts on ski and snowboard gear across e-commerce product listing pages. The primary interface is a **Tampermonkey userscript** (`tampermonkey/snow-deals.user.js`) that injects discount-percentage badges directly onto product cards and adds a sort-by-discount button — all in the browser with zero context switching. A secondary **Python CLI** (`snow_deals/`) supports bulk data export (CSV, JSON) for the same sites.

## Tech Stack

### Userscript (primary)
- **Runtime:** Tampermonkey / Greasemonkey
- **Language:** Vanilla JavaScript (ES2020+, no build step)
- **APIs:** DOM manipulation, `GM_addStyle`

### CLI (secondary)
- **Language:** Python 3.11+
- **HTTP client:** httpx (async)
- **HTML parsing:** BeautifulSoup4 (lxml)
- **CLI framework:** click
- **Terminal output:** rich

## Project Structure

```
snow-deals/
├── tampermonkey/
│   └── snow-deals.user.js    # Tampermonkey userscript (primary interface)
├── AGENTS.md                 # This file — AI agent instructions
├── PLANS.md                  # Living execution plan
├── README.md                 # Human-oriented project README
├── pyproject.toml            # Python CLI metadata and dependencies
├── snow_deals/               # Python CLI package (secondary interface)
│   ├── __init__.py
│   ├── cli.py                # Click CLI entry point
│   ├── scraper.py            # Orchestrates fetching + parsing across pages
│   ├── models.py             # Product dataclass with discount calculation
│   ├── display.py            # Rich table and CSV/JSON export
│   └── parsers/
│       ├── __init__.py       # Parser registry and auto-discovery
│       ├── base.py           # Abstract base parser interface
│       ├── bluezone.py       # BlueZone Sports parser implementation
│       └── shopify.py        # Shopify stores parser (JSON API)
├── aggregator/               # Awesome Snow Deals — multi-store aggregator (FastAPI + htmx, admin panel, analytics)
```

## Development Workflow

### Userscript
```
1. Install Tampermonkey browser extension
2. Click the Tampermonkey icon → "Create a new script"
3. Paste the contents of tampermonkey/snow-deals.user.js
4. Save (Ctrl+S) and navigate to a supported listing page
```

### CLI
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
snow-deals https://www.bluezonesports.com/skis
```

## Coding Conventions

### Userscript
- Single IIFE, no external dependencies beyond Tampermonkey GM_ APIs.
- All DOM selectors must match those proven in the Python parser (`snow_deals/parsers/bluezone.py`) to keep both interfaces consistent.
- Styles injected via `GM_addStyle`; class names prefixed with `deal-` to avoid collisions.

### CLI
- Use dataclasses for data models, not plain dicts.
- All parsers inherit from `BaseParser` and implement `parse_listing_page` and `get_next_page_url`.
- Keep HTTP fetching in `scraper.py` separate from HTML parsing in `parsers/`.
- Type-annotate all public functions.

## Architecture Decisions

- **Tampermonkey as primary interface:** Users are already on the page — injecting discount info directly is better UX than switching to a terminal. The userscript is a single file with no build step.
- **Shared selectors between userscript and CLI:** Both interfaces use identical CSS selectors (`.card.product-card`, `.product-price .text-accent`, `.product-price del`) validated against the live site. Changes to site HTML should be updated in both places.
- **Plugin-based parsers (CLI):** Each retailer site gets its own parser module in `parsers/`. The registry in `parsers/__init__.py` maps URL patterns to parser classes.
- **Color-coded badges:** 30%+ red, 15-29% orange, 1-14% yellow. No badge for full-price items to avoid visual noise.
