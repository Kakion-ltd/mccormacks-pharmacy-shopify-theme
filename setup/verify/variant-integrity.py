"""The page never offers one variant and sells another.

Every check here is a defect that shipped, found by adding a second multi-variant
fixture: two options, three variants of a possible four, genuinely different images
per variant, and variant one both the cheapest and the sold-out one. That last detail
is what makes price_min and selected_or_first_available_variant point at different
variants, which is where most of this went wrong.

The one-option fixture in variants.py caught none of it. Every variant there shared
one photo, its first variant was in stock, and its option matrix had no holes, so a
gallery that ignored the selection, a picker that disagreed with its own form, and a
buy bar that skipped the unavailable path all looked correct.

Driven through a browser: every one of these bugs was in what the page DID, not in
what the markup looked like.
"""
import os
import re
import sys
import urllib.request
from playwright.sync_api import sync_playwright

BASE = f"http://localhost:{os.environ.get('PORT', '8734')}"

# The preview server holds ONE process-global cart. It outlives every script and is
# shared by every browser context and every other process on this port, so a check
# that does not start from empty inherits whatever the last run left behind — and
# variant-integrity deliberately drives a line up to its stock ceiling, after which
# every later add of that product is refused. Start from empty. Set PORT to avoid
# sharing the cart with a parallel session (see 3e442ac).
urllib.request.urlopen(urllib.request.Request(
    BASE + "/cart/clear.js", data=b"{}", method="POST")).read()

TWO = "/products/cerave-moisturising-cream"          # Format x Size, 3 of 4 combinations
ONE = "/products/vitamin-d3-1000iu-60-capsules"      # Pack size, first variant in stock
STOCKED = "/products/cetrine-allergy-10mg-30-tablets"  # single variant, 12 in stock

res = []
def ck(name, got, want=True):
    res.append((got == want, name, got))

def pick(pg, fmt, size):
    pg.locator("[data-opt-index='0']").select_option(label=fmt)
    pg.locator("[data-opt-index='1']").select_option(label=size)
    pg.wait_for_timeout(250)

def shown(pg):
    """Filenames of the gallery frames actually visible."""
    return pg.eval_on_selector_all(
        "[data-pdp-img]",
        "els => els.filter(e => getComputedStyle(e).display !== 'none')"
        ".map(e => e.currentSrc.split('/').pop().split('?')[0])")

def visible(pg, sel):
    el = pg.locator(sel)
    return bool(el.count()) and el.first.is_visible()

with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True)

    for label, vp in (("desktop", {"width": 1440, "height": 1000}),
                      ("mobile", {"width": 390, "height": 844})):
        pg = b.new_context(viewport=vp).new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(BASE + TWO, wait_until="networkidle")
        accept = pg.locator("[data-cc-accept]").first
        if accept.count() and accept.is_visible():
            accept.click()
            pg.wait_for_timeout(300)

        # ---- the picker agrees with the form it submits, from the first paint.
        # It used to read option.selected_value, which can name the first variant's
        # values while price, stock and the submitted id all follow the first
        # AVAILABLE one. The page then showed a sold-out combination at another
        # variant's price and added a third when the button was pressed.
        sel0 = pg.locator("[data-opt-index='0']").first
        sel1 = pg.locator("[data-opt-index='1']").first
        idf = pg.locator("input[name='id']").first
        ck(f"[{label}] two options render two selects", pg.locator("[data-opt-index]").count(), 2)
        ck(f"[{label}] the options are named", [
            pg.locator("label[for^='Opt-']").nth(i).inner_text().strip() for i in range(2)],
            ["Format", "Size"])
        ck(f"[{label}] on load the picker does not show the sold-out first variant",
           [sel0.input_value(), sel1.input_value()], ["Tub", "454ml"])
        ck(f"[{label}] on load the picker matches the variant that would be added",
           idf.input_value(), "40001001")
        ck(f"[{label}] on load the price belongs to the selected combination",
           pg.locator("[data-pdp-price]").first.inner_text().strip(), "€22.50")
        ck(f"[{label}] on load the stock line agrees with the selection",
           "In stock" in pg.locator("[data-pdp-stock]").first.inner_text())

        # ---- a combination no variant covers is its own state, on BOTH add controls.
        # The handler used to return early on it, so the sticky mobile bar kept the
        # last valid variant id, stayed enabled, and added a different product.
        pick(pg, "Pump", "177ml")
        ck(f"[{label}] a real combination sets its own variant", idf.input_value(), "40001002")
        buybar = pg.locator("[data-buybar-add]").first
        ck(f"[{label}] the buy bar follows a real combination", buybar.get_attribute("data-add-id"), "40001002")

        pick(pg, "Pump", "454ml")
        ck(f"[{label}] no such combination disables the main button",
           pg.locator("[data-pdp-submit]").first.is_disabled())
        ck(f"[{label}] no such combination says so on the main button",
           pg.locator("[data-pdp-submit]").first.inner_text().strip().upper(), "UNAVAILABLE")
        ck(f"[{label}] no such combination disables the sticky buy bar", buybar.is_disabled())
        ck(f"[{label}] no such combination says so on the sticky buy bar",
           pg.locator("[data-buybar-label]").first.inner_text().strip().upper(), "UNAVAILABLE")
        ck(f"[{label}] no such combination leaves the buy bar naming no variant",
           buybar.get_attribute("data-add-id"), None)
        ck(f"[{label}] no such combination stops the form submitting an id",
           idf.is_disabled())

        # ---- a sold-out combination is a different state again, and the sticky bar
        # used to be disabled while still reading ADD TO BAG.
        pick(pg, "Tub", "177ml")
        ck(f"[{label}] a sold-out combination disables the buy bar", buybar.is_disabled())
        ck(f"[{label}] a sold-out combination relabels the buy bar",
           pg.locator("[data-buybar-label]").first.inner_text().strip().upper(), "OUT OF STOCK")
        ck(f"[{label}] a sold-out combination still names its variant, for back-in-stock",
           buybar.get_attribute("data-add-id"), "40001000")

        # ---- the gallery follows the selection.
        pick(pg, "Tub", "454ml")
        tub454 = shown(pg)
        pick(pg, "Pump", "177ml")
        pump177 = shown(pg)
        ck(f"[{label}] one gallery frame is visible at a time", len(pump177), 1)
        ck(f"[{label}] the gallery changes with the variant", tub454 != pump177)
        ck(f"[{label}] the gallery shows that variant's own photo",
           pump177, ["prod-optibac-max.jpg"])

        # ---- the offer badges follow it too. Only the strikethrough used to move, so
        # the page could flash SPECIAL OFFER over a variant with no offer.
        ck(f"[{label}] no offer badge on a variant with no offer", visible(pg, "[data-pdp-badge]"), False)
        ck(f"[{label}] no offer pill on a variant with no offer", visible(pg, "[data-pdp-offer]"), False)
        ck(f"[{label}] no strikethrough on a variant with no offer",
           visible(pg, "[data-pdp-compare]"), False)
        pick(pg, "Tub", "454ml")
        ck(f"[{label}] the offer badge returns for a discounted variant", visible(pg, "[data-pdp-badge]"))
        ck(f"[{label}] the offer pill returns for a discounted variant", visible(pg, "[data-pdp-offer]"))
        ck(f"[{label}] the strikethrough is that variant's compare-at",
           pg.locator("[data-pdp-compare]").first.inner_text().strip(), "€26.00")

        # ---- two variants of one product are two tellable-apart lines in the drawer.
        # A single-variant product goes in first so the "names no variant" case is
        # present whatever the shared preview cart happened to be holding.
        pg.goto(BASE + STOCKED, wait_until="networkidle")
        acc = pg.locator("[data-cc-accept]").first
        if acc.count() and acc.is_visible():
            acc.click()
            pg.wait_for_timeout(300)
        pg.locator("[data-pdp-submit]" if label == "desktop" else "[data-buybar-add]").first.click()
        pg.wait_for_timeout(1000)
        pg.locator("[data-cd-close]").first.click()
        pg.wait_for_timeout(400)

        pg.goto(BASE + TWO, wait_until="networkidle")
        for fmt, size in (("Tub", "454ml"), ("Pump", "177ml")):
            pick(pg, fmt, size)
            add = pg.locator("[data-pdp-submit]" if label == "desktop" else "[data-buybar-add]").first
            add.scroll_into_view_if_needed()
            add.click()
            pg.wait_for_timeout(1000)
            pg.locator("[data-cd-close]").first.click()
            pg.wait_for_timeout(400)
        pg.evaluate("window.mccCartDrawer.open()")
        pg.wait_for_timeout(400)
        titles = pg.eval_on_selector_all(
            ".cd-line", "els => els.map(e => [(e.querySelector('.cd-line-title')||{}).innerText,"
                        " (e.querySelector('.cd-line-variant')||{}).innerText || null])")
        ours = [v for t, v in titles if t and "CeraVe Moisturising Cream" in t]
        ck(f"[{label}] two variants of one product are two drawer lines", len(ours), 2)
        ck(f"[{label}] each drawer line names its variant", sorted(ours), ["Pump / 177ml", "Tub / 454ml"])
        others = [v for t, v in titles if t and "CeraVe Moisturising Cream" not in t]
        ck(f"[{label}] the single-variant line is there to compare against", len(others) > 0)
        ck(f"[{label}] a single-variant line names no variant",
           all(v is None for v in others))

        ck(f"[{label}] no JS errors", errs, [])
        pg.close()

    # ---- quantity above stock is a quantity problem, not a sold-out one.
    pg = b.new_context(viewport={"width": 1440, "height": 1000}).new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(BASE + STOCKED, wait_until="networkidle")
    accept = pg.locator("[data-cc-accept]").first
    if accept.count() and accept.is_visible():
        accept.click()
        pg.wait_for_timeout(300)
    before = pg.evaluate("async () => (await (await fetch('/cart.js')).json()).item_count")
    pg.fill("[data-pdp-qty]", "999")
    pg.locator("[data-pdp-submit]").first.click()
    pg.wait_for_timeout(1200)
    err = pg.locator("[data-cd-error]")
    ck("an over-stock add does not claim the item is sold out",
       pg.locator("[data-pdp-submit]").first.inner_text().strip().lower(), "not added")
    ck("an over-stock add shows the shop's own reason", err.is_visible())
    ck("the reason names the limit rather than being generic",
       "only add 12" in err.inner_text())
    ck("an over-stock add adds nothing",
       pg.evaluate("async () => (await (await fetch('/cart.js')).json()).item_count"), before)

    # A good add afterwards clears the message rather than leaving it standing.
    pg.locator("[data-cd-close]").first.click()
    pg.wait_for_timeout(400)
    pg.fill("[data-pdp-qty]", "2")
    pg.locator("[data-pdp-submit]").first.click()
    pg.wait_for_timeout(1200)
    ck("a successful add clears the standing message", err.is_visible(), False)

    # The drawer's own stepper used to swallow a refusal whole: the number did not
    # move, the buttons came back, and nothing said why.
    plus = pg.locator("[data-cd-qty][data-cd-to]").nth(1)
    for _ in range(14):
        if plus.is_disabled():
            break
        plus.click()
        pg.wait_for_timeout(300)
    ck("the drawer stepper stops at the stock ceiling",
       pg.locator(".cd-qty span").first.inner_text().strip(), "12")
    ck("the drawer stepper says why it stopped", err.is_visible())
    ck("the drawer's reason names the limit", "only add 12" in err.inner_text())
    ck("no JS errors on the quantity paths", errs, [])
    pg.close()
    b.close()

# ---- the no-JavaScript buy path, read out of the markup: option selects cannot name
# a variant to /cart/add, so without this a shopper with JS off silently bought
# whichever variant the page was built with.
with urllib.request.urlopen(BASE + TWO, timeout=30) as r:
    html = r.read().decode("utf-8", "replace")
hidden = re.search(r'<input type="hidden" name="id"[^>]*>', html).group(0)
ns = re.search(r"<noscript>.*?</noscript>", html, re.S)
ck("the multi-variant hidden id is not submitted without JS", "disabled" in hidden)
ck("a noscript variant picker exists", bool(ns))
ck("the noscript picker submits an id", 'name="id"' in (ns.group(0) if ns else ""))
ck("the noscript picker offers every variant",
   len(re.findall(r"<option", ns.group(0) if ns else "")), 3)
ck("the noscript picker marks the sold-out variant",
   (ns.group(0) if ns else "").count("disabled"), 1)
ck("the noscript picker preselects the variant the page is built from",
   'value="40001001" selected' in (ns.group(0) if ns else ""))

with urllib.request.urlopen(BASE + ONE, timeout=30) as r:
    one_html = r.read().decode("utf-8", "replace")
ck("a one-option product gets the same no-JS fallback",
   bool(re.search(r"<noscript>.*?name=\"id\".*?</noscript>", one_html, re.S)))

with urllib.request.urlopen(BASE + STOCKED, timeout=30) as r:
    single = r.read().decode("utf-8", "replace")
ck("a single-variant product needs no fallback and keeps a live hidden id",
   "disabled" in re.search(r'<input type="hidden" name="id"[^>]*>', single).group(0), False)

# ---- a card never claims a saving no shopper can buy. product.compare_at_price is a
# minimum across variants, so struck through beside price_min it could advertise a
# discount belonging to a different variant entirely.
with urllib.request.urlopen(BASE + "/collections/skincare", timeout=30) as r:
    grid = r.read().decode("utf-8", "replace")
i = grid.find("CeraVe Moisturising Cream")
card = grid[max(grid.rfind('<div class="pcard"', 0, i), 0):i + 2200]
ck("the two-option card shows a From price", "From €14.50" in card)
ck("the two-option card claims no saving on an undiscounted cheapest variant",
   "SALE</span>" in card, False)
ck("the two-option card strikes through nothing", "line-through" in card, False)
j = grid.find("Sudocrem Antiseptic Healing Cream")
sud = grid[max(grid.rfind('<div class="pcard"', 0, j), 0):j + 2200]
ck("a genuinely discounted product still badges SALE", "SALE</span>" in sud)
ck("and still strikes through its own compare-at", "€8.99" in sud)

for ok, name, got in res:
    if not ok:
        print(f"FAIL  {name}   (got {got!r})")
print(f"\n{sum(1 for r in res if r[0])}/{len(res)} variant integrity checks passed")
sys.exit(0 if all(r[0] for r in res) else 1)
