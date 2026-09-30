"""The launch stock rule, checked on the real store (30 Sep 2026).

  changed   (tracking on, count 1, CONTINUE): "In stock", addable twice, the
            bag's + keeps working, and "can't add more" never appears
  untouched (tracking on, count 0, DENY):     "Out of stock", button disabled,
            and clicking it adds nothing

Inventory policy is one of the things `NEEDS-A-STORE.md` lists as unverifiable in
the mock preview, so this has to run against the real catalogue. The storefront
is still behind the password page, so it goes through `theme dev`:

    npx shopify theme dev --store mccormackpharmacy.myshopify.com \
        --path shopify-theme --port 9292
    python3 setup/verify/continue-selling.py

**The harness fights back, and telling the two apart is the whole trick.**
`theme dev` answers `/cart.js` and `/cart/*.js` with a `Clear-Site-Data` header.
Chromium acts on it, the proxy loses its own storefront-password session, and
from then on cart writes come back 502 and then 401 for the rest of that browser
session — which the theme surfaces as its generic "could not update your bag"
line, reading exactly like a real defect in the bag. Two things keep this honest:

  1. that header is stripped from every response, which prevents most of it;
  2. a 401/502/5xx is never scored. Once a session is poisoned it does not
     recover, so the whole run restarts with a fresh browser context.

**Only a 422 is the store refusing an add.** Do not "fix" this script by
treating a 401 or 502 as a failure, and do not delete the retry: it is the
difference between a real finding and an afternoon spent on a proxy bug.

Against the real storefront, once the password comes off, none of this is needed.
"""
import json
import sys
from playwright.sync_api import sync_playwright

BASE = "http://localhost:9292"
CHANGED,   CHANGED_VID   = "aveeno-body-wash", 57050810909003
UNTOUCHED, UNTOUCHED_VID = "sensodyne-pronamel-tp-whitening-75ml", 57050812481867
CANT_ADD = "can't add more"
FLAKE = (401, 407, 429, 500, 502, 503, 504)
PLUS = '[data-cd-qty][aria-label="Increase quantity"]'


class Flake(Exception):
    """The proxy gave up. Says nothing about the store."""


def strip_csd(route):
    """Drop Clear-Site-Data so theme dev keeps its own password session."""
    try:
        r = route.fetch()
        route.fulfill(response=r, headers={k: v for k, v in r.headers.items()
                                           if k.lower() != "clear-site-data"})
    except Exception:
        route.continue_()


def run(page, adds, changes, check):
    def bag_error():
        el = page.locator("[data-cd-error]").first
        return el.inner_text().strip() if el.is_visible() else ""

    def cart():
        st, body = page.evaluate("fetch('/cart.js').then(async r=>[r.status, await r.text()])")
        if st != 200 or not body.strip():
            raise Flake(f"/cart.js -> {st}")
        return json.loads(body)

    def qty(vid):
        line = next((x for x in cart()["items"] if x["variant_id"] == vid), None)
        return line["quantity"] if line else 0

    def clicked(locator, seen):
        """Click, wait, and raise Flake rather than score a proxy failure."""
        seen.clear()
        locator.click()
        page.wait_for_timeout(2600)
        text = bag_error()
        if text and any(s in FLAKE for s in seen):
            raise Flake(f"bag error behind status {seen}")
        return text

    # ===== 1. a changed product: tracking on, count 1, now CONTINUE ============
    print(f"\n== changed: {CHANGED} (tracking on, count 1, CONTINUE)")
    page.goto(f"{BASE}/", wait_until="load", timeout=90000)
    page.evaluate("fetch('/cart/clear.js',{method:'POST'})")
    page.wait_for_timeout(1200)
    page.goto(f"{BASE}/products/{CHANGED}", wait_until="load", timeout=90000)
    page.wait_for_timeout(1500)

    stock = page.locator("[data-pdp-stock]").first.inner_text().strip()
    check("In stock" in stock, 'PDP shows "In stock"', stock)
    btn = page.locator("[data-pdp-submit]").first
    check(not btn.is_disabled(), "ADD TO BAG is enabled", btn.inner_text().strip())

    for n in (1, 2):
        page.wait_for_function("() => { const b = document.querySelector('[data-pdp-submit]');"
                               " return b && !b.disabled; }", timeout=30000)
        text = clicked(page.locator("[data-pdp-submit]").first, adds)
        check(text == "", f"add #{n} through the button: no bag error",
              text or f"no error, status {adds}")
        check(CANT_ADD not in text.lower(), f'add #{n}: no "can\'t add more"',
              text or "no error")
        close = page.locator("[data-cd-close]").first
        if close.is_visible():
            close.click()
            page.wait_for_timeout(900)

    check(qty(CHANGED_VID) == 2, "bag holds 2 of a product whose count is 1",
          f"quantity={qty(CHANGED_VID)}")
    check(422 not in adds, "no 422 from /cart/add", f"statuses={adds}")

    # the bag's own + button: the one path the "can't add more" line is written for
    page.evaluate("window.mccCartDrawer && window.mccCartDrawer.open()")
    page.wait_for_timeout(1800)
    check(page.locator(PLUS).count() > 0, "bag + button present",
          f"count={page.locator(PLUS).count()}")
    for n in (3, 4):
        text = clicked(page.locator(PLUS).first, changes)
        check(text == "", f"bag + to {n}: no bag error", text or "no error")
        check(CANT_ADD not in text.lower(), f'bag + to {n}: no "can\'t add more"',
              text or "no error")
    check(qty(CHANGED_VID) == 4, "bag + took it to 4 on a count of 1",
          f"quantity={qty(CHANGED_VID)}")

    # ===== 2. an untouched product: tracking on, count 0, still DENY ===========
    print(f"\n== untouched: {UNTOUCHED} (tracking on, count 0, DENY)")
    page.goto(f"{BASE}/products/{UNTOUCHED}", wait_until="load", timeout=90000)
    page.wait_for_timeout(1500)

    stock = page.locator("[data-pdp-stock]").first.inner_text().strip()
    check("Out of stock" in stock, 'PDP shows "Out of stock"', stock)
    btn = page.locator("[data-pdp-submit]").first
    label = btn.inner_text().strip()
    check(btn.is_disabled(), "its add button is disabled", f"disabled={btn.is_disabled()}")
    check("OUT OF STOCK" in label.upper(), 'its button reads "OUT OF STOCK"', label)

    before = cart()["item_count"]
    btn.click(force=True)
    page.wait_for_timeout(2000)
    check(cart()["item_count"] == before, "a forced click on it adds nothing",
          f"{before} -> {cart()['item_count']}")
    check(qty(UNTOUCHED_VID) == 0, "it is not in the bag", f"quantity={qty(UNTOUCHED_VID)}")

    # What the store itself does, which is NOT what the button does. Recorded as a
    # note, not a check: it is pre-existing and not what this change is about.
    # See "Nothing on this store stops an oversell at the bag" in MAINTENANCE.md.
    st = page.evaluate(
        """(v) => fetch('/cart/add.js', {method:'POST',
             headers:{'Content-Type':'application/json'},
             body: JSON.stringify({id: v, quantity: 1})}).then(r => r.status)""",
        UNTOUCHED_VID)
    if st in FLAKE:
        raise Flake(f"direct POST -> {st}")
    print(f"  NOTE  a direct POST of this out-of-stock variant -> {st}"
          + (" (refused, as it should be)" if st == 422
             else " — ACCEPTED: this store enforces no stock ceiling at the bag"))


def main():
    fails = []

    def check(ok, label, detail=""):
        print(("  PASS " if ok else "  FAIL ") + label + (f"   [{detail}]" if detail else ""))
        if not ok:
            fails.append(label)

    with sync_playwright() as p:
        br = p.chromium.launch()
        for attempt in range(1, 5):
            fails.clear()
            ctx = br.new_context(viewport={"width": 1280, "height": 900})
            # every response, not only the cart ones: section renders and the
            # recommendations endpoint carry the header too, and one is enough
            ctx.route("**/*", strip_csd)
            page = ctx.new_page()
            adds, changes = [], []
            page.on("response", lambda r: adds.append(r.status) if "/cart/add" in r.url else None)
            page.on("response", lambda r: changes.append(r.status) if "/cart/change" in r.url else None)
            try:
                run(page, adds, changes, check)
                ctx.close()
                break
            except Flake as e:
                ctx.close()
                print(f"    (theme dev proxy gave up: {e} — restarting the run,"
                      f" attempt {attempt + 1} of 4)")
                if attempt == 4:
                    print("\nthe theme dev proxy would not stay up for a whole run;"
                          " nothing was judged")
                    br.close()
                    return 2
        br.close()

    print("\n" + ("ALL PASS" if not fails else f"{len(fails)} FAILED: " + "; ".join(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
