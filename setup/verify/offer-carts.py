"""One cart per automatic discount, checked against the real catalogue (30 Sep 2026).

Automatic discounts are applied by Shopify at the cart, not by the theme, so the
only honest check is a real cart. No order is placed: each test builds a cart,
reads /cart.js, and clears it.

  npx shopify theme dev --store mccormackpharmacy.myshopify.com \
      --path shopify-theme --port 9294
  BASE=http://localhost:9294 python3 setup/verify/offer-carts.py

or, once the password page is off, straight at the storefront:

  BASE=https://mccormackpharmacy.myshopify.com \
  STOREFRONT_PASSWORD=<password> python3 setup/verify/offer-carts.py

The `theme dev` quirks are the same ones continue-selling.py documents at
length: Clear-Site-Data on /cart*.js poisons the proxy's own password session,
so it is stripped from every response, and a 401/502/5xx is a flake to be
retried rather than a failure to be scored. Read that docstring before changing
anything here.

Expected totals are the arithmetic in setup/offers/discounts.py and the match
must be **exact**. It was "within a cent" for one run, which passed 9/9 while
every fixed-price offer was in fact a cent high -- Shopify truncates the per-line
discount instead of rounding it, so "3 for EUR 10" was charging 10.01. The
tolerance hid the only defect it was there to find. If a cart is a cent out, the
percentage is wrong; do not widen this again.
"""
import json, os, sys

BASE = os.environ.get('BASE', 'http://localhost:9294')
PASSWORD = os.environ.get('STOREFRONT_PASSWORD')
V = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', 'offers', 'cart-variants.json')))


class Flake(Exception):
    pass


# name, [(handle, qty)], expected total in euro
TESTS = [
    ('3 for €10', [('dove-advanced-care-pampering-shea-butter-vanilla-body-wash-225ml', 1),
                        ('tresemme-lamellar-shine-shampoo-300ml', 1),
                        ('dove-advanced-care-nourishing-silk-body-wash-225ml', 1)], 10.00),
    ('3 for €5', [('johnson-s-soft-pamper-body-wash-400ml', 1),
                       ('johnson-s-soft-nourish-body-wash-400ml', 1),
                       ('johnson-s-soft-energise-body-wash-400ml', 1)], 5.00),
    ('Buy 2 for €7 — Batiste', [('batiste-dry-shampoo-tropical-200ml', 1),
                                          ('batiste-200ml-blush-dry-shampoo', 1)], 7.00),
    ('2 for €52.45 — Zest Active',
     [('revive-active-zest-active-ages-20-35-30pk', 2)], 52.45),
    ('Buy 4 for €3 — BioMiracle',
     [('biomiracle-staysafe-hand-cleansing-towlettes-20pk', 4)], 3.00),
    ('BOGOF half price — Revive Active',
     [('revive-active-original-30pk', 2)], 89.99),
    ('BOGOF half price — Mitchum',
     [('mitchum-roll-on-shwr-frsh-100ml', 2)], 5.70),
    ('Free tanning mitt', [('bperfect-tan-studio-instant-aerosol-tan-dark-125ml', 1),
                           ('bperfect-double-sided-luxury-velvet-tanning-mitt', 1)], 16.95),
    # The remainder case: a 4th item is charged in full, which is the whole
    # reason these are Buy X get Y rather than a percentage with a minimum.
    ('3 for €10, plus a 4th at full price',
     [('dove-advanced-care-pampering-shea-butter-vanilla-body-wash-225ml', 2),
      ('tresemme-lamellar-shine-shampoo-300ml', 1),
      ('dove-advanced-care-nourishing-silk-body-wash-225ml', 1)], 13.99),
]


def strip_csd(route):
    """Drop Clear-Site-Data so theme dev keeps its own password session."""
    if '/cart' in route.request.url:
        r = route.fetch()
        route.fulfill(response=r, headers={k: v for k, v in r.headers.items()
                                           if k.lower() != 'clear-site-data'})
    else:
        route.continue_()


def cart(page):
    st, body = page.evaluate(
        "fetch('/cart.js').then(async r=>[r.status, await r.text()])")
    if st in (401, 502) or st >= 500:
        raise Flake(f'/cart.js -> {st}')
    return json.loads(body)


def run(page):
    page.evaluate("fetch('/cart/clear.js', {method:'POST'})")
    results = []
    for name, items, expect in TESTS:
        page.evaluate("fetch('/cart/clear.js', {method:'POST'})")
        for handle, qty in items:
            st = page.evaluate(
                """([id, q]) => fetch('/cart/add.js', {method:'POST',
                     headers:{'Content-Type':'application/json'},
                     body: JSON.stringify({id: id, quantity: q})}).then(r=>r.status)""",
                [int(V[handle]['vid']), qty])
            if st in (401, 502) or st >= 500:
                raise Flake(f'{name}: /cart/add -> {st}')
            if st != 200:
                results.append((name, None, expect, f'add returned {st}'))
                break
        else:
            c = cart(page)
            total = c['total_price'] / 100
            ok = abs(total - expect) < 0.005      # exact to the cent; see the docstring
            results.append((name, total, expect,
                            '' if ok else f'off by {total - expect:+.2f}'))
    page.evaluate("fetch('/cart/clear.js', {method:'POST'})")
    return results


def main():
    from playwright.sync_api import sync_playwright
    print(f'{BASE}{"  [password page]" if PASSWORD else ""}')
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for attempt in range(4):
            ctx = browser.new_context()
            if not PASSWORD:
                ctx.route('**/*', strip_csd)
            page = ctx.new_page()
            try:
                if PASSWORD:
                    page.goto(f'{BASE}/password', wait_until='load', timeout=90000)
                    page.fill('input[name="password"]', PASSWORD)
                    page.press('input[name="password"]', 'Enter')
                    page.wait_for_load_state('load')
                else:
                    page.goto(BASE, wait_until='load', timeout=90000)
                results = run(page)
            except Flake as e:
                print(f'  flake ({e}) — restarting with a fresh context')
                ctx.close()
                continue
            ctx.close()
            break
        else:
            raise SystemExit('four poisoned sessions in a row; see the docstring')
        browser.close()

    bad = 0
    for name, total, expect, note in results:
        if note:
            bad += 1
            print(f'  FAIL  {name[:40]:42} got '
                  f'{"€%.2f" % total if total is not None else "-":>9}  '
                  f'want €{expect:.2f}   {note}')
        else:
            print(f'  ok    {name[:40]:42} €{total:.2f}')
    print(f'\n{len(results) - bad}/{len(results)} carts match the offer')
    sys.exit(1 if bad else 0)


main()
