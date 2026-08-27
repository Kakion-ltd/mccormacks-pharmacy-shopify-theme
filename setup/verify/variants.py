"""Multi-variant products.

This surface rendered in no preview until a fixture was added, and it turned out to
be broken: the variants JSON sat after the IIFE that reads it, so getElementById
returned null and selecting a pack size changed nothing at all. These checks exist so
that cannot come back quietly.

Everything here is driven through the browser rather than read out of the HTML,
because the bug was in execution order, not markup — the markup looked correct.
"""
import json
import re
import sys
import urllib.request
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8734"
MULTI = "/products/vitamin-d3-1000iu-60-capsules"      # 3 pack sizes, largest sold out
SINGLE = "/products/cetrine-allergy-10mg-30-tablets"   # one variant

res = []
def ck(name, got, want=True): res.append((got == want, name, got))

with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True)
    for label, vp in (("desktop", {"width": 1440, "height": 900}),
                      ("mobile", {"width": 390, "height": 844})):
        pg = b.new_context(viewport=vp).new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))

        pg.goto(BASE + MULTI, wait_until="networkidle")

        sel = pg.locator("[data-opt-index]").first
        price = pg.locator("[data-pdp-price]").first
        idf = pg.locator("input[name='id']").first
        btn = pg.locator("[data-pdp-submit]").first

        ck(f"[{label}] option picker renders", sel.count() == 1)
        ck(f"[{label}] the option is named", pg.locator("label[for^='Opt-']").first.inner_text().strip(),
           "Pack size")
        ck(f"[{label}] every variant is offered",
           pg.locator("[data-opt-index] option").all_text_contents(),
           ["60 capsules", "120 capsules", "240 capsules"])

        first_id, first_price = idf.input_value(), price.inner_text()

        # The bug: the JSON block sat after the IIFE that reads it, so none of this moved.
        sel.select_option(label="120 capsules")
        pg.wait_for_timeout(300)
        ck(f"[{label}] price follows the selected variant", price.inner_text() != first_price)
        ck(f"[{label}] the submitted variant id follows the selection", idf.input_value() != first_id)
        ck(f"[{label}] price is the second variant's", price.inner_text().strip(), "€16.99")

        sel.select_option(label="240 capsules")
        pg.wait_for_timeout(300)
        ck(f"[{label}] a sold-out variant disables add to bag", btn.is_disabled())
        ck(f"[{label}] a sold-out variant relabels the button",
           btn.inner_text().strip().upper(), "OUT OF STOCK")

        sel.select_option(label="60 capsules")
        pg.wait_for_timeout(300)
        ck(f"[{label}] selecting back restores the first variant", idf.input_value(), first_id)
        ck(f"[{label}] add to bag is enabled again", btn.is_disabled(), False)

        # Variant-specific alt text — the half of image-alt.liquid that no fixture
        # could reach before, because no mock image claimed a variant.
        alts = pg.eval_on_selector_all("img", "els => els.map(e => e.getAttribute('alt'))")
        ck(f"[{label}] images attached to a variant name that variant",
           any(a and "— 120 capsules" in a for a in alts))
        ck(f"[{label}] the shared image keeps the plain product title",
           any(a and a.strip() == "Vitamin D3 1000IU 60 Capsules" for a in alts))

        # A single-variant product must not grow a picker.
        pg.goto(BASE + SINGLE, wait_until="networkidle")
        ck(f"[{label}] no picker on a single-variant product",
           pg.locator("[data-opt-index]").count(), 0)
        ck(f"[{label}] no variants JSON block either",
           pg.locator("script[id^='pdp-variants-']").count(), 0)

        ck(f"[{label}] no JS errors", errs, [])
    b.close()

# Per-variant Offer in the Product schema — never rendered against a real variant list.
with urllib.request.urlopen(BASE + MULTI, timeout=30) as r:
    html = r.read().decode("utf-8", "replace")
schema = None
for blk in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
    if '"Product"' in blk:
        schema = json.loads(blk)
offers = (schema or {}).get("offers", [])
ck("Product schema carries one Offer per variant", len(offers), 3)
ck("each Offer has its own price", len({o.get("price") for o in offers}), 3)
ck("each Offer has its own SKU", len({o.get("sku") for o in offers}), 3)
ck("the sold-out variant is marked OutOfStock",
   sum(1 for o in offers if str(o.get("availability", "")).endswith("OutOfStock")), 1)
ck("the in-stock variants are marked InStock",
   sum(1 for o in offers if str(o.get("availability", "")).endswith("InStock")), 2)

for ok, name, got in res:
    if not ok:
        print(f"FAIL  {name}   (got {got!r})")
print(f"\n{sum(1 for r in res if r[0])}/{len(res)} variant checks passed")
sys.exit(0 if all(r[0] for r in res) else 1)
