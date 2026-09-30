#!/usr/bin/env python3
"""Render the gift voucher product image from card.html.

    python3 artwork/gift-voucher/build.py

The gift card product needs ONE image for SIX denominations, so this card
carries no amount. The old E-Gift Card products each had their own picture with
the price printed on it, which is why none of them could be reused: whichever
you picked was wrong for five of the six.

It is generated rather than drawn so it cannot drift from the card on
/pages/gift-vouchers. card.html copies the colour tokens out of
shopify-theme/assets/base.css and uses the real logo and the real heading font
from shopify-theme/assets/. If the brand colours, the logo or Nunito change,
re-run this; if you edit the picture by hand instead, the two will disagree and
only the page will be right.

Output: 1000x1000 at 2x (2000x2000), white ground, which is what the product
cards, search results and the bag line want.
"""
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
THEME = HERE.parent.parent / "shopify-theme" / "assets"

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit("needs Playwright: pip3 install --user playwright && playwright install chromium")

# card.html loads these next to itself, so the real files come from the theme
# rather than a second copy that could go stale.
for name in ("nunito-variable.woff2", "mulish-variable.woff2", "mccormacks-logo.png"):
    src = THEME / name
    if not src.exists():
        sys.exit(f"missing {src}")
    shutil.copy(src, HERE / name)

out = HERE / "gift-voucher-card.png"
with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_page(viewport={"width": 1000, "height": 1000}, device_scale_factor=2)
    pg.goto((HERE / "card.html").as_uri())
    pg.wait_for_timeout(1200)
    pg.screenshot(path=str(out))
    b.close()

# The copied assets are build inputs, not artwork; leave the folder holding only
# its source and its output.
for name in ("nunito-variable.woff2", "mulish-variable.woff2", "mccormacks-logo.png"):
    (HERE / name).unlink(missing_ok=True)

print(f"wrote {out.relative_to(HERE.parent.parent)}")
