"""Remove on every bag line, and "bag" not "cart" in the header.

Drawer (against the preview server's in-memory cart):
  1. Each line has a Remove button under its quantity control, labelled
     "Remove <product>" for a screen reader.
  2. Remove takes the line out at once and the subtotal and free-delivery message
     follow it; focus lands on the drawer, not <body>.
  3. Removing the last medicine turns "Review bag and check out" back into the
     checkout form. The preview has no Section Rendering API, so the main-cart
     answer is faked from what is really in the cart, as Shopify would render it.
  4. Minus on a quantity of 1 still removes the line.
Bag page (static render, so the request is what is checked):
  5. Remove sits under the stepper, is labelled per line, posts quantity 0 and
     reloads; without JS its href does the same.
Header:
  6. "My Bag", no "My Cart"; the bag page's tab title says bag.
"""
import json
import os
import sys
from playwright.sync_api import sync_playwright

BASE = f"http://localhost:{os.environ.get('PORT', '8734')}"
MEDICINE = 40000008   # Nurofen Tablets 12Pk, the preview's only tagged medicine
OTHER = 40000002

results = []
def check(name, got, want=True):
    results.append((got == want, name, got))

with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1200, "height": 900})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.route("**/recommendations/**", lambda r: r.fulfill(status=200, body=""))

    medicine_html = pg.request.get(BASE + "/cart?fixture=medicine").text()
    plain_html = pg.request.get(BASE + "/cart").text()
    def section(route):
        items = json.loads(pg.request.get(BASE + "/cart.js").text())["items"]
        has = any(it["variant_id"] == MEDICINE for it in items)
        route.fulfill(status=200, content_type="text/html", body=medicine_html if has else plain_html)
    pg.route("**/cart?section_id=main-cart", section)

    pg.goto(BASE + "/products/vitamin-d3-1000iu-60-capsules", wait_until="networkidle")
    pg.evaluate("""async ([a, c]) => {
        await fetch('/cart/clear.js', {method: 'POST'});
        for (const id of [a, c]) await fetch('/cart/add.js', {method: 'POST',
            headers: {'Content-Type': 'application/json'}, body: JSON.stringify({id, quantity: 1})});
        window.mccCartDrawer.render(await (await fetch('/cart.js')).json());
        window.mccCartDrawer.open();
    }""", [MEDICINE, OTHER])
    pg.wait_for_timeout(600)

    lines = pg.locator("[data-cd-items] .cd-line")
    check("drawer: two lines", lines.count(), 2)
    labels = pg.eval_on_selector_all(".cd-remove", "els => els.map(e => e.getAttribute('aria-label'))")
    check("drawer: a Remove per line", len(labels), 2)
    check("drawer: Remove is labelled with the product",
          all(l and l.startswith("Remove ") and len(l) > len("Remove ") for l in labels))
    first = pg.locator(".cd-line").first
    qty_box = first.locator(".cd-qty").bounding_box()
    rm_box = first.locator(".cd-remove").bounding_box()
    check("drawer: Remove sits under the quantity control", rm_box["y"] >= qty_box["y"] + qty_box["height"] - 1)
    check("drawer: medicine bag shows the review route",
          pg.evaluate("!document.querySelector('[data-cd-medicine]').hidden"))

    subtotal = pg.locator("[data-cd-subtotal]").inner_text()
    ship = pg.locator("[data-cd-ship-msg]").inner_text()
    med_line = pg.locator(".cd-line", has=pg.locator(".cd-remove[aria-label*='Nurofen']"))
    med_line.locator(".cd-remove").click()
    pg.wait_for_timeout(700)
    check("drawer: Remove took the line out", lines.count(), 1)
    check("drawer: no Nurofen line left", pg.locator(".cd-remove[aria-label*='Nurofen']").count(), 0)
    check("drawer: subtotal changed", pg.locator("[data-cd-subtotal]").inner_text() != subtotal)
    # The message follows the bag: a countdown that moves with the total, or "You
    # have free delivery" while the bag stays over the threshold.
    after = pg.locator("[data-cd-ship-msg]").inner_text()
    left = pg.evaluate("""async () => {
        const t = parseInt(document.querySelector('[data-cd-drawer]').dataset.cdThreshold, 10);
        return t - (await (await fetch('/cart.js')).json()).total_price; }""")
    if left <= 0:
        check("drawer: free-delivery message says free over the threshold", after, "You have free delivery")
    else:
        check("drawer: free-delivery countdown follows the total",
              after.endswith("away from free delivery") and after != ship)
    check("drawer: last medicine gone -> checkout form back",
          pg.evaluate("""() => ({review: !document.querySelector('[data-cd-medicine]').hidden,
                                 checkout: !document.querySelector('[data-cd-checkout-form]').hidden})"""),
          {"review": False, "checkout": True})
    check("drawer: focus kept inside the drawer",
          pg.evaluate("!!document.activeElement.closest('[data-cd-drawer]')"))

    # Minus on a quantity of 1 still removes.
    pg.locator(".cd-line").first.locator(".cd-qty button").first.click()
    pg.wait_for_timeout(600)
    check("drawer: minus to zero removes the line", lines.count(), 0)
    check("drawer: empty bag state shows", pg.locator("[data-cd-empty]").is_visible())

    # Bag page.
    pg.goto(BASE + "/cart?fixture=medicine", wait_until="networkidle")
    rows = pg.locator(".cart-row")
    rm = pg.locator(".cart-row .cart-remove")
    check("bag page: a Remove per line", rm.count(), rows.count())
    row0 = rows.first
    step = row0.locator(".cart-step").first.bounding_box()
    r0 = row0.locator(".cart-remove").bounding_box()
    check("bag page: Remove sits under the stepper", r0["y"] >= step["y"] + step["height"] - 1)
    check("bag page: Remove is labelled with the product",
          (row0.locator(".cart-remove").get_attribute("aria-label") or "").startswith("Remove ")
          and len(row0.locator(".cart-remove").get_attribute("aria-label")) > len("Remove "))
    check("bag page: no-JS href removes line 1",
          row0.locator(".cart-remove").get_attribute("href"), "/cart/change?line=1&quantity=0")
    posted = {}
    def change(route):
        posted.update(json.loads(route.request.post_data or "{}"))
        route.fulfill(status=200, content_type="application/json", body="{}")
    pg.route("**/cart/change.js", change)
    with pg.expect_navigation():
        row0.locator(".cart-remove").click()
    check("bag page: Remove posts quantity 0 for its line", posted, {"line": 1, "quantity": 0})
    check("bag page: stays on the bag page (reload, not the no-JS route)", pg.url.split("?")[0], BASE + "/cart")

    # Header and title.
    check("header: My Bag label", pg.locator(".icon-label", has_text="My Bag").count() >= 1)
    check("header: no My Cart anywhere",
          pg.evaluate("!document.body.innerText.includes('My Cart') && !document.querySelector('[aria-label=\"My Cart\"]')"))
    check("header: mobile icon label", pg.locator("a.cart-mobile").get_attribute("aria-label"), "My Bag")
    check("bag page tab title says bag", pg.title().startswith("Your bag"))

    pg.evaluate("fetch('/cart/clear.js', {method: 'POST'})")
    check("no page errors", errs, [])
    b.close()

for ok, name, got in results:
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"  (got {got!r})"))
print(f"{sum(ok for ok, _, _ in results)}/{len(results)} bag-remove checks passed")
sys.exit(0 if all(ok for ok, _, _ in results) else 1)
