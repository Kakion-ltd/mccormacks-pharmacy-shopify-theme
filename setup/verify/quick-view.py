"""Quick view on product cards.

An eye button over the card image opens a modal built from /products/<handle>.js.
Checks the pharmacy gate (no eye on a restricted product), the hover reveal, the
variant picker, Add To Bag through the real cart endpoint, focus handling, that the
page is inert behind the modal, that phones never see the eye, and that hovering a
row of cards does not fire a request per card.

    python3 setup/verify/quick-view.py          # against http://localhost:8734
    PORT=8736 python3 setup/verify/quick-view.py
"""
import os, sys
from playwright.sync_api import sync_playwright

BASE = f"http://localhost:{os.environ.get('PORT', '8734')}"
GRID = "/collections/skincare"                 # normal cards, one on sale
VARIANTS = "/collections/everyday-multivitamins"  # Vitamin D3 has pack sizes
RESTRICTED = "/collections/pain-relief"        # Nurofen Plus carries the gate tag
fails = 0
def ck(label, got, want=True):
    global fails
    ok = got == want
    fails += 0 if ok else 1
    print(("ok  " if ok else "FAIL") + "  " + label + ("" if ok else f"  (got {got!r})"))

with sync_playwright() as pw:
    b = pw.chromium.launch()
    p = b.new_context(viewport={"width": 1440, "height": 900}).new_page()
    p.goto(BASE + GRID, wait_until="networkidle"); p.evaluate("document.querySelector('[data-cc-banner]')?.setAttribute('hidden','')")
    cards = p.locator(".pcard")
    restricted_here = p.locator(".pcard").filter(has_text="Nurofen Plus").count()
    ck("every card in the grid has an eye, except the restricted one", p.locator(".pcard .qv-btn").count(), cards.count() - restricted_here)
    eye = cards.first.locator(".qv-btn")
    ck("eye is hidden until hover", eye.evaluate("e=>getComputedStyle(e).opacity"), "0")

    # prefetch: listener first, then one settled hover, then a fast sweep, then a settle
    reqs = []
    p.on("request", lambda r: reqs.append(r.url) if "/products/" in r.url and r.url.endswith(".js") else None)
    cards.first.hover(); p.wait_for_timeout(700)
    ck("eye shows on card hover", eye.evaluate("e=>getComputedStyle(e).opacity"), "1")
    heart = cards.first.locator(".wish-btn").bounding_box(); eb = eye.bounding_box()
    ck("eye is 38px and sits under the heart with a gap", (round(eb["height"]), round(eb["y"] - (heart["y"] + heart["height"]))), (38, 8))
    ck("a hover that settles prefetches exactly one", len(reqs), 1)
    n = min(cards.count(), 8)
    for i in range(1, n):
        bb = cards.nth(i).bounding_box(); p.mouse.move(bb["x"] + bb["width"] / 2, bb["y"] + 40); p.wait_for_timeout(40)
    p.mouse.move(5, 5); p.wait_for_timeout(450)
    ck(f"sweeping {n - 1} more cards fires nothing", len(reqs), 1)
    cards.nth(1).hover(); p.wait_for_timeout(500)
    ck("resting on another card fetches it once", len(reqs), 2)
    cards.first.hover(); p.wait_for_timeout(500)
    ck("a card already fetched is not fetched again", len(reqs), 2)

    # open, focus, inert
    title = cards.first.locator("h3 a").inner_text().strip()
    eye.click(); p.wait_for_selector("[data-qv] .qv-title")
    ck("modal opens with the card's product", p.locator("#qv-title").inner_text().strip(), title)
    ck("opening reused the prefetched JSON", len(reqs), 2)
    ck("focus lands on the close button", p.evaluate("document.activeElement?.hasAttribute('data-qv-close')"))
    ck("dialog is labelled by the title", p.locator("[data-qv]").get_attribute("aria-labelledby"), "qv-title")
    ck("page behind the modal is inert", p.evaluate("document.querySelector('main').inert"))
    ck("price is shown", p.locator("[data-qv-price]").inner_text().startswith("€"))
    ck("link to the full product page", p.locator("[data-qv] .qv-link").get_attribute("href").startswith("/products/"))
    p.keyboard.press("Escape"); p.wait_for_timeout(250)
    ck("Escape closes", p.evaluate("document.body.hasAttribute('data-qv-open')"), False)
    ck("focus returns to the eye", p.evaluate("document.activeElement?.hasAttribute('data-qv-open')"))
    ck("page is no longer inert", p.evaluate("document.querySelector('main').inert"), False)

    # variants
    p.goto(BASE + VARIANTS, wait_until="networkidle"); p.evaluate("document.querySelector('[data-cc-banner]')?.setAttribute('hidden','')")
    card = p.locator(".pcard").filter(has_text="Vitamin D3").first
    card.hover(); card.locator(".qv-btn").click(); p.wait_for_selector("[data-qv-opt]")
    sel = p.locator("[data-qv-opt]").first
    ck("a select per option", p.locator("[data-qv-opt]").count(), 1)
    id_before = p.locator("[data-qv-add]").get_attribute("data-add-id"); price_before = p.locator("[data-qv-price]").inner_text()
    sel.select_option(index=1); p.wait_for_timeout(100)
    ck("changing the option changes the variant id", p.locator("[data-qv-add]").get_attribute("data-add-id") != id_before)
    ck("and the price", p.locator("[data-qv-price]").inner_text() != price_before)
    sel.select_option(index=2); p.wait_for_timeout(100)
    ck("a sold-out pack disables Add", p.locator("[data-qv-add]").is_disabled())
    ck("and says so", p.locator("[data-qv-add]").inner_text().strip(), "Out of stock")
    sel.select_option(index=0); p.wait_for_timeout(100)
    with p.expect_request(lambda r: r.url.endswith("/cart/add.js") and r.method == "POST") as req:
        p.locator("[data-qv-add]").click()
    p.wait_for_timeout(500)
    ck("Add posts to the cart endpoint", req.value.method, "POST")
    ck("the modal closes on add", p.evaluate("document.body.hasAttribute('data-qv-open')"), False)
    ck("and the cart drawer opens", p.evaluate("document.body.hasAttribute('data-cd-open')"))

    # gate
    p.goto(BASE + RESTRICTED, wait_until="networkidle")
    r = p.locator(".pcard").filter(has_text="Nurofen Plus").first
    ck("restricted product card has no eye", r.locator(".qv-btn").count(), 0)
    ck("but other cards on the same page do", p.locator(".pcard .qv-btn").count() > 0)

    # search results
    p.goto(BASE + "/search?q=vitamin", wait_until="networkidle")
    ck("search result cards carry the eye", p.locator(".srch-card .qv-btn").count() > 0)

    # phone: no hover, no eye
    m = b.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True).new_page()
    m.goto(BASE + GRID, wait_until="networkidle")
    ck("no eye on a touch device", m.locator(".pcard .qv-btn").first.evaluate("e=>getComputedStyle(e).display"), "none")
    b.close()

print(f"\n{'all' if not fails else fails} quick view checks {'passed' if not fails else 'FAILED'}")
sys.exit(1 if fails else 0)
