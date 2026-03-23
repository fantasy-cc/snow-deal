"""Store-specific HTML parsers for non-Shopify, non-browser retailers.

Shopify and BlueZone stores use parsers from the parent snow_deals package.
Browser-rendered stores use JS extractors defined in aggregator.browser.
This module contains BS4-based parsers for the remaining stores:
  - alpineshopvt.py      (Alpine Shop VT — BigCommerce)
  - thecircle.py         (The Circle Whistler — Lightspeed eCom)
  - coloradodiscount.py  (Colorado Discount Skis — custom HTML)
"""
