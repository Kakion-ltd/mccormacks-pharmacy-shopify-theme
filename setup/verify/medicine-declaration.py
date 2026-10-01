"""PSI 2.5 soft gate: a medicine goes through the bag page's over-18 / leaflet tick.

  1. A bag holding a medicine shows the required tick box inside the checkout form,
     named exactly as the Flow expects, blocks submit until ticked, and drops the
     express buttons (they are not submit buttons, so they would skip the tick).
  2. An ordinary bag shows no tick box and keeps the express buttons.
  3. A medicine's product page has no Buy it now; an ordinary one keeps it.
  4. The drawer sends a medicine bag to the bag page, an ordinary bag to checkout,
     and fails closed (bag page) when it cannot ask the server.
"""
import os
import sys
from playwright.sync_api import sync_playwright

BASE = f"http://localhost:{os.environ.get('PORT', '8734')}"
ATTR = "attributes[Over 18 and will follow the leaflet]"  # the Flow matches this key

results = []
def check(name, got, want=True):
    results.append((got == want, name, got))

with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1200, "height": 900})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))

    # 1. Medicine bag.
    pg.goto(BASE + "/cart?fixture=medicine", wait_until="networkidle")
    box = "form[action='/cart'] [data-medicine-declaration] input[type=checkbox]"
    check("medicine bag: tick box inside the checkout form", pg.locator(box).count(), 1)
    check("medicine bag: tick box is required", pg.locator(box).get_attribute("required") is not None)
    check("medicine bag: attribute name", pg.locator(box).get_attribute("name"), ATTR)
    check("medicine bag: value", pg.locator(box).get_attribute("value"), "Yes")
    check("medicine bag: form invalid until ticked",
          pg.evaluate("document.querySelector(\"%s\").form.checkValidity()" % box), False)
    pg.locator(box).check()
    check("medicine bag: form valid once ticked",
          pg.evaluate("document.querySelector(\"%s\").form.checkValidity()" % box), True)
    check("medicine bag: no express buttons", pg.locator(".cart-express").count(), 0)

    # Pre-payment disclosure. The pharmacist review happens AFTER payment, so the
    # customer must be told before they pay that the order can be refused and refunded.
    # These three checks lived on the questionnaire modal until 1 Oct 2026, when the
    # client had the note removed from it; the copy is here now, beside the tick and
    # directly above "Checkout securely", so the checks are here too. This is the last
    # screen before payment, which is the screen the undertaking has to be on — if it
    # disappears from here it has disappeared from the journey.
    decl = pg.locator("[data-medicine-declaration]").inner_text().lower()
    check("medicine bag: pre-payment disclosure is shown",
          pg.locator("[data-medicine-declaration]").is_visible())
    check("medicine bag: disclosure says a pharmacist reviews the order",
          "pharmacist reviews" in decl)
    check("medicine bag: disclosure says an unsuitable order is refunded", "refund" in decl)

    # 2. Ordinary bag.
    pg.goto(BASE + "/cart", wait_until="networkidle")
    check("ordinary bag: no tick box", pg.locator("[data-medicine-declaration]").count(), 0)
    check("ordinary bag: express buttons kept", pg.locator(".cart-express").count(), 1)

    # 3. Product pages.
    pg.goto(BASE + "/products/nurofen-tablets-12pk", wait_until="networkidle")
    check("medicine PDP: no Buy it now", pg.locator(".pdp-express").count(), 0)
    # Since 30 Sep 2026 a tagged medicine is gated by the questionnaire too (the default
    # over-18 / other-medication pair), so its buy box is the form-less gated one. The
    # plain Add to bag is GONE on purpose: a product form here would be the no-JS hole.
    check("medicine PDP: no product form at all", pg.locator("form[data-ajax-add]").count(), 0)
    check("medicine PDP: opens the questionnaire instead", pg.locator("[data-open-questionnaire]").count() > 0, True)
    pg.goto(BASE + "/products/vitamin-d3-1000iu-60-capsules", wait_until="networkidle")
    check("ordinary PDP: Buy it now kept", pg.locator(".pdp-express").count(), 1)

    # 4. Drawer. The harness's /cart ignores section_id, so answer it per case.
    medicine_html = pg.request.get(BASE + "/cart?fixture=medicine").text()
    plain_html = pg.request.get(BASE + "/cart").text()
    cart = {"item_count": 1, "total_price": 1000, "items": [{
        "product_id": 1, "product_title": "X", "url": "/", "quantity": 1,
        "final_line_price": 1000, "original_line_price": 1000, "vendor": "V"}]}

    def drawer_state(answer):
        pg.unroute("**/cart?section_id=main-cart")
        pg.route("**/cart?section_id=main-cart", answer)
        pg.evaluate("c => window.mccCartDrawer.render(c)", cart)
        pg.wait_for_timeout(400)
        return pg.evaluate("""() => ({
            medicine: !document.querySelector('[data-cd-medicine]').hidden,
            checkout: !document.querySelector('[data-cd-checkout-form]').hidden })""")

    pg.route("**/recommendations/**", lambda r: r.fulfill(status=200, body=""))
    s = drawer_state(lambda r: r.fulfill(status=200, content_type="text/html", body=medicine_html))
    check("drawer, medicine bag: review route, no checkout", s, {"medicine": True, "checkout": False})
    s = drawer_state(lambda r: r.fulfill(status=200, content_type="text/html", body=plain_html))
    check("drawer, ordinary bag: checkout, no review route", s, {"medicine": False, "checkout": True})
    s = drawer_state(lambda r: r.abort())
    check("drawer, server unreachable: fails closed", s, {"medicine": True, "checkout": False})

    check("no page errors", errs, [])
    b.close()

for ok, name, got in results:
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"  (got {got!r})"))
sys.exit(0 if all(ok for ok, _, _ in results) else 1)
