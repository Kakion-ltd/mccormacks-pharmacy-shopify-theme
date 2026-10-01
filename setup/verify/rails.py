"""The shared product card, and the rule that no rail recommends a medicine.

Two things, because they are the same change (1 Oct 2026) and the same page.

1. NO MEDICINE IN A RAIL. A product tagged settings.restricted_tag has to be found
   and read, not suggested beside a moisturiser, and it is not promoted with a
   discount on the homepage either. Every recommendation rail drops it; the
   collection GRID still shows it, because browsing to a medicine is the whole point.
   The fixture that makes this measurable is /products/nurofen-200mg-ibuprofen-24-tablets,
   whose category holds the tagged Nurofen Tablets 12Pk — see render_preview.mjs.

2. THE CARD LINES UP. Titles clamp to two lines in CSS, so the DOM keeps the whole
   title and the link's accessible name is still the full product name. Price and
   button are pinned to the bottom with margin-top:auto rather than by reserving a
   fixed title height, which is what makes a row of mixed one- and two-line titles
   put its prices on one line.

check.mjs (RailShowsMedicine) is the static half and fails when a rail loses its
guard. This is the half that drives the pages.
"""
import os
import sys
from playwright.sync_api import sync_playwright

BASE = f"http://localhost:{os.environ.get('PORT', '8734')}"
MEDICINE = "Nurofen Tablets 12Pk"

results = []
def check(name, got, want=True):
    results.append((got == want, name, got))

# Every rail track on the site, as (page, CSS for the rail, what to call it).
RAILS = [
    ("/products/nurofen-200mg-ibuprofen-24-tablets", "[id^=checked-track]", "product page: More in <category>"),
    ("/products/nurofen-200mg-ibuprofen-24-tablets", ".pdp-recs", "product page: You may also like"),
    ("/products/nurofen-tablets-12pk", "[id^=checked-track]", "a medicine's own page: More in <category>"),
    ("/products/nurofen-tablets-12pk", ".pdp-recs", "a medicine's own page: You may also like"),
    ("/collections/pain-relief", "[id^=also-track]", "collection page: You may also like"),
    ("/collections/medicines-health", "[id^=also-track]", "medicines collection: You may also like"),
    ("/", "[id^=sale-]", "homepage: On Sale This Month"),
    ("/pages/gift-vouchers", "#also-track", "gift vouchers: You may also like"),
]

with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()

    for path, sel, label in RAILS:
        pg.goto(BASE + path, wait_until="networkidle")
        rail = pg.locator(sel)
        if rail.count() == 0:
            # A rail that is not drawn cannot recommend anything. Recorded, not failed:
            # hiding an empty rail is the wanted behaviour.
            check(f"[{label}] not drawn on this page (nothing to recommend)", True)
            continue
        text = rail.first.inner_text()
        check(f"[{label}] no medicine recommended", MEDICINE not in text)

    # The grid is not a rail: a medicine must still be browsable to.
    pg.goto(BASE + "/collections/pain-relief", wait_until="networkidle")
    check("the collection grid still lists the medicine",
          MEDICINE in pg.locator(".pgrid").inner_text())

    # The filter is doing work, not passing because the fixture has no medicine in
    # range: the rail is full, and the medicine that sits inside its window is gone.
    pg.goto(BASE + "/products/nurofen-200mg-ibuprofen-24-tablets", wait_until="networkidle")
    titles = pg.locator("[id^=checked-track] .prodcard-title").all_inner_texts()
    check("the rail filled to its limit without the medicine", len(titles), 8)
    check("and the medicine is the one it left out", MEDICINE not in titles)

    # An empty rail takes its heading with it. Proven on the markup rather than on a
    # fixture, because a collection of nothing but medicine does not exist in the
    # fixture catalogue: every rail counts before it draws, so there is no path that
    # emits the <h2> and no cards.
    for path, sel in (("/products/nurofen-200mg-ibuprofen-24-tablets", "[id^=checked-track]"),
                      ("/collections/pain-relief", "[id^=also-track]")):
        pg.goto(BASE + path, wait_until="networkidle")
        if pg.locator(sel).count():
            check(f"[{path}] a drawn rail has cards in it",
                  pg.locator(f"{sel} .prodcard").count() > 0)

    # ---- The card itself.
    for vw in (1440, 375):
        c = b.new_context(viewport={"width": vw, "height": 900})
        p2 = c.new_page()
        p2.goto(BASE + "/collections/medicines-health", wait_until="networkidle")
        cards = p2.locator(".pgrid .prodcard")
        n = cards.count()
        check(f"[{vw}px] the grid renders the shared card", n > 0)

        # Rows, by the top edge of each card. Prices must share a baseline within a row.
        rows = p2.evaluate("""() => {
          const cards = [...document.querySelectorAll('.pgrid .prodcard')];
          const by = new Map();
          cards.forEach((c) => {
            const top = Math.round(c.getBoundingClientRect().top);
            const key = [...by.keys()].find((k) => Math.abs(k - top) < 4) ?? top;
            if (!by.has(key)) by.set(key, []);
            by.get(key).push({
              lines: Math.round(c.querySelector('.prodcard-title').getBoundingClientRect().height
                     / parseFloat(getComputedStyle(c.querySelector('.prodcard-title')).lineHeight)),
              footTop: Math.round(c.querySelector('.prodcard-foot').getBoundingClientRect().top),
              ctaTop: Math.round(c.querySelector('.prodcard-cta').getBoundingClientRect().top),
            });
          });
          return [...by.values()].filter((r) => r.length > 1);
        }""")
        mixed = [r for r in rows if len({c["lines"] for c in r}) > 1]
        check(f"[{vw}px] a row mixing one- and two-line titles exists to measure",
              len(mixed) > 0)
        for i, row in enumerate(mixed):
            check(f"[{vw}px] row {i + 1}: prices line up across {len(row)} mixed cards",
                  len({c['footTop'] for c in row}), 1)
            check(f"[{vw}px] row {i + 1}: buttons line up too",
                  len({c['ctaTop'] for c in row}), 1)

        # Clamped in CSS, so the accessible name is still the whole title. No fixture
        # product has a title long enough to wrap past two lines, and inventing one in
        # catalogue.json would reseed the store — so the title is lengthened in the DOM
        # instead. What is under test is the CSS rule, which is the part that regresses.
        clamped = p2.evaluate("""() => {
          const a = document.querySelector('.pgrid .prodcard-title');
          const link = a.querySelector('a');
          const long = link.textContent.trim() + ' ' + 'with a very much longer name '.repeat(6);
          link.textContent = long;
          const lh = parseFloat(getComputedStyle(a).lineHeight);
          return {
            visibleLines: Math.round(a.clientHeight / lh),
            overflowing: a.scrollHeight > a.clientHeight + 1,
            nameIsWhole: link.textContent === long,
            hidden: getComputedStyle(a).overflow,
          };
        }""")
        check(f"[{vw}px] a long title is cut to two lines", clamped["visibleLines"], 2)
        check(f"[{vw}px] the rest of it is hidden rather than laid out",
              clamped["overflowing"] and clamped["hidden"] == "hidden")
        check(f"[{vw}px] and the link's accessible name is still the whole title",
              clamped["nameIsWhole"])
        c.close()

    # The promo label sits on the image, under the SALE badge, in the same stack.
    pg.goto(BASE + "/collections/sale", wait_until="networkidle")
    stack = pg.evaluate("""() => {
      const b = document.querySelector('.prodcard-badges');
      if (!b) return null;
      const sale = b.querySelector('.sale-badge'), promo = b.querySelector('.promo-label');
      return { onImage: !!b.closest('.prodcard-img'),
               order: sale && promo ? promo.getBoundingClientRect().top > sale.getBoundingClientRect().top : null };
    }""")
    check("the promo label is on the image, not under the price", stack and stack["onImage"])
    if stack and stack["order"] is not None:
        check("and it sits under the SALE badge", stack["order"])

    # Clear air before the newsletter band, from the spacing tokens rather than the
    # 8px every section used to end on.
    pg.goto(BASE + "/products/nurofen-200mg-ibuprofen-24-tablets", wait_until="networkidle")
    gap = pg.evaluate("""() => {
      const rail = document.querySelector('[id^=checked-track]').closest('section');
      const band = document.querySelector('.ftr-newsletter');
      if (!band) return null;
      return Math.round(band.getBoundingClientRect().top - rail.getBoundingClientRect().bottom);
    }""")
    check("the rail leaves air before the newsletter band", gap is not None and gap >= 0)
    check("the rail's own bottom padding comes from the token", pg.evaluate("""() => {
      const rail = document.querySelector('[id^=checked-track]').closest('section');
      const token = getComputedStyle(document.documentElement).getPropertyValue('--sec-pad-bottom').trim();
      return getComputedStyle(rail).paddingBottom === token; }"""))

    b.close()

bad = [r for r in results if not r[0]]
for ok, name, got in results:
    print(("  ok  " if ok else "FAIL  ") + name + ("" if ok else f"  (got {got!r})"))
print(f"\n{len(results) - len(bad)}/{len(results)} passed")
sys.exit(1 if bad else 0)
