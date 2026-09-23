"""Out-of-stock recovery on the product page.

The sold-out PDP used to be a dead end: a disabled button and nothing else. The
capture is off by default (main-product's show_back_in_stock setting) until the
client confirms who owns the contact inbox, so these checks run against the
product.oos.* fixtures, which setup/render_preview.mjs renders with the setting
forced on (BIS_ON) — proving the capture still works, ready for when it is
switched back on. They assert it is present, is a real submittable form, carries
the product so the email is actionable, and does not claim an automatic alert the
theme cannot send; and separately, that the real store default (off) leaves the
sold-out state clean — no capture, no dangling gap where it would have been.
"""
import os
import pathlib
import sys
from playwright.sync_api import sync_playwright

BASE = f"http://localhost:{os.environ.get('PORT', '8734')}"
OOS = "/products/difflam-sore-throat-spray-30ml"
IN_STOCK = "/products/cetrine-allergy-10mg-30-tablets"
PREVIEW = pathlib.Path(__file__).resolve().parents[2] / "preview"

res = []
def ck(name, got, want=True): res.append((got == want, name, got))

# The real store default: show_back_in_stock off, nothing forced on.
default_html = (PREVIEW / "product.oos.default.html").read_text(encoding="utf-8", errors="replace")
ck("default (setting off): no back-in-stock capture", "data-back-in-stock" in default_html, False)
ck("default (setting off): Out of stock still reads", "Out of stock" in default_html)
ck("default (setting off): add-to-bag still disabled", 'data-pdp-submit' in default_html and "disabled" in default_html.split('data-pdp-submit', 1)[1].split(">", 1)[0])
ck("default (setting off): free delivery line still follows the buy box",
   "Free delivery" in default_html)
# Nothing left hanging where the panel was: the buy box's closing form tag should
# be followed by the free-delivery line with no empty wrapper in between.
after_form = default_html.split("</form>", 1)[-1]
ck("default (setting off): no empty wrapper left behind", "<div></div>" in after_form, False)

with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True)
    for label, vp in (("desktop", {"width": 1440, "height": 900}),
                      ("mobile", {"width": 390, "height": 844})):
        pg = b.new_context(viewport=vp).new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))

        pg.goto(BASE + OOS, wait_until="networkidle")
        bis = pg.locator("[data-back-in-stock]")
        ck(f"[{label}] capture shown on a sold-out product", bis.is_visible())
        ck(f"[{label}] add to bag is disabled", pg.locator("[data-pdp-submit]").is_disabled())

        # A contact form nested inside the product form would be dropped by the parser,
        # silently taking the capture with it.
        ck(f"[{label}] no nested form", pg.evaluate("() => !!document.querySelector('form form')"), False)

        email = bis.locator("input[type=email]")
        ck(f"[{label}] email field present", email.count() == 1)
        ck(f"[{label}] email field is required", email.get_attribute("required") is not None)
        ck(f"[{label}] submits to Shopify's contact form",
           bis.locator("input[name='contact[form_type]']").get_attribute("value"), "back-in-stock")
        ck(f"[{label}] carries the product so the email is actionable",
           "Difflam" in (bis.locator("input[name='contact[product]']").get_attribute("value") or ""))
        ck(f"[{label}] carries a link back to the product",
           "/products/" in (bis.locator("input[name='contact[product_url]']").get_attribute("value") or ""))
        # Shopify may render only email and body into the notification, so the body has
        # to stand alone. A body-less contact post may also be dropped outright.
        body = bis.locator("input[name='contact[body]']").get_attribute("value") or ""
        ck(f"[{label}] sends a message body",
           all(w in body for w in ("Difflam", "SKU:", "/products/")))

        # The theme does not watch inventory. Copy must not imply that it does.
        txt = bis.inner_text().lower()
        ck(f"[{label}] copy does not promise an automatic alert",
           "automatically" not in txt and "we'll email you as soon as" not in txt)
        ck(f"[{label}] copy says a person makes contact", "person" in txt or "our team" in txt)
        ck(f"[{label}] links to the privacy policy",
           bis.locator("a[href*='privacy']").count() >= 1)

        # And it must not appear where there is stock to sell.
        pg.goto(BASE + IN_STOCK, wait_until="networkidle")
        ck(f"[{label}] absent on an in-stock product",
           pg.locator("[data-back-in-stock]").count(), 0)
        ck(f"[{label}] add to bag is enabled there",
           pg.locator("[data-pdp-submit]").first.is_disabled(), False)
        ck(f"[{label}] no JS errors", errs, [])

for ok, name, got in res:
    if not ok:
        print(f"FAIL  {name}   (got {got!r})")
print(f"\n{sum(1 for r in res if r[0])}/{len(res)} back-in-stock checks passed")
sys.exit(0 if all(r[0] for r in res) else 1)
