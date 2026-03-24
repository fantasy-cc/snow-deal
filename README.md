# snow-deals

Find the best discounts on ski and snowboard gear. Adds discount-percentage badges directly onto product cards in your browser and lets you sort by best deal with one click.

## Tampermonkey Userscript (Primary)

The userscript runs directly on supported retailer pages — no terminal needed.

### What it does

- Adds a **discount % badge** to every product card that's on sale (color-coded: red for 30%+, orange for 15-29%, yellow for 1-14%)
- Adds a **Sort by Discount** button that reorders the product grid from best to worst deal
- Shows a summary line: "X of Y on sale (up to Z% off)"

### Installation

1. Install [Tampermonkey](https://www.tampermonkey.net/) in your browser
2. Click the Tampermonkey icon in the toolbar, then **Create a new script**
3. Delete the template code and paste the contents of [`tampermonkey/snow-deals.user.js`](tampermonkey/snow-deals.user.js)
4. Press **Ctrl+S** (or Cmd+S) to save
5. Navigate to any supported product listing:
   - [bluezonesports.com/skis](https://www.bluezonesports.com/skis)
   - [aspenskiandboard.com/collections/skis](https://www.aspenskiandboard.com/collections/skis)

Discount badges and the sort button appear automatically. Clicking "Sort by Discount" fetches ALL pages and ranks every product.

## Python CLI (Secondary)

For bulk data export across all paginated pages.

### Prerequisites

- Python 3.11+

### Installation

```bash
git clone <repo-url> && cd snow-deals
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Usage

```bash
# BlueZone Sports (HTML scraping)
snow-deals https://www.bluezonesports.com/skis

# Aspen Ski and Board (Shopify JSON API)
snow-deals https://www.aspenskiandboard.com/collections/skis

# Only show items with 10%+ discount
snow-deals https://www.bluezonesports.com/skis --min-discount 10

# Export to CSV
snow-deals https://www.aspenskiandboard.com/collections/skis --format csv --output deals.csv

# Export to JSON
snow-deals https://www.bluezonesports.com/skis --format json --output deals.json
```

## Project Structure

```
snow-deals/
├── tampermonkey/
│   └── snow-deals.user.js    # Tampermonkey userscript (primary)
├── snow_deals/               # Python CLI package (secondary)
│   ├── cli.py                # CLI entry point
│   ├── scraper.py            # Page fetching and orchestration
│   ├── models.py             # Product data model
│   ├── display.py            # Output formatting (table, CSV, JSON)
│   └── parsers/              # Site-specific parsers
│       ├── base.py           # Abstract parser interface
│       ├── bluezone.py       # BlueZone Sports (HTML)
│       └── shopify.py        # Shopify stores (JSON API)
├── aggregator/               # Awesome Snow Deals — multi-store aggregator with admin panel & analytics
├── pyproject.toml
└── README.md
```

## Supported Sites

| Site | Type | Userscript | CLI |
|------|------|-----------|-----|
| [BlueZone Sports](https://www.bluezonesports.com) | HTML scraping | Yes | Yes |
| [Aspen Ski and Board](https://www.aspenskiandboard.com) | Shopify JSON API | Yes | Yes |

## Adding a New Site

### Shopify stores
Shopify stores expose `/collections/{handle}/products.json` with structured pricing data. Adding a new Shopify store usually only requires registering the domain — no custom parser needed.

### Non-Shopify stores
1. Create a new parser in `snow_deals/parsers/` inheriting from `BaseParser`
2. Register the URL pattern in `snow_deals/parsers/__init__.py`
3. Add a `@match` pattern and site adapter in `tampermonkey/snow-deals.user.js`

## License

MIT
