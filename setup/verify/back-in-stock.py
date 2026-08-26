"""Out-of-stock recovery on the product page.

The sold-out PDP used to be a dead end: a disabled button and nothing else. These
assert the capture is present, is a real submittable form, carries the product so
the email is actionable, and does not claim an automatic alert the theme cannot send.
"""
import sys
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8734"
OOS = "/products/difflam-sore-throat-spray-30ml"
IN_STOCK = "/products/cetrine-allergy-tablets"

res = []
def ck(name, got, want=True): res.append((got == want, name, got))

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
