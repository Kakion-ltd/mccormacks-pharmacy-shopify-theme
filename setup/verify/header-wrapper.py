"""Everything inside the Shopify header-group wrapper stays hit-testable.

This wrapper has now caused two defects, and neither could fail locally, because the
preview renders the header straight into body flow and Shopify's per-section wrapper
does not exist here at all:

  1. The header never pinned on a store: `{% sections 'header-group' %}` wraps each
     section in a div exactly as tall as the header, and a sticky child cannot travel
     past its parent's box.
  2. Fixing that with `pointer-events: none` on the wrapper killed the mobile nav
     drawer, the cart drawer and the cart overlay - header.liquid renders all three, so
     on a store they are siblings of .hdr-sticky inside the same wrapper and inherited
     it. They opened and nothing in them could be tapped.

So this check synthesises the wrapper the way Shopify emits it, then asserts what a
finger actually does: elementFromPoint must reach the control, not an ancestor.
Position is not enough - both defects had correct geometry and dead hit-testing.
"""
import os, sys
from playwright.sync_api import sync_playwright

BASE = f"http://localhost:{os.environ.get('PORT', '8734')}"
res = []
def ck(name, got, want=True): res.append((got == want, name, got))

# Rebuild the store's DOM shape: one div.shopify-section.shopify-section-group-header-group
# per section, header.liquid's output (header + both drawers) inside its own.
WRAP = """() => {
  const sticky = document.querySelector('.hdr-sticky');
  if (!sticky) return 'no .hdr-sticky';
  const owned = [sticky,
                 document.querySelector('.mnav-drawer'),
                 document.querySelector('[data-cd-overlay]'),
                 document.querySelector('[data-cd-drawer]')].filter(Boolean);
  const wrap = document.createElement('div');
  wrap.className = 'shopify-section shopify-section-group-header-group';
  sticky.parentNode.insertBefore(wrap, sticky);
  owned.forEach(el => wrap.appendChild(el));
  // the announcement bar is its own section in the same group, and carries the class too
  const ann = document.querySelector('[data-hdr-sentinel]') ? null : wrap.previousElementSibling;
  if (ann && ann !== wrap && !ann.classList.contains('shopify-section')) {
    ann.classList.add('shopify-section', 'shopify-section-group-header-group');
  }
  return {wrapped: owned.length};
}"""

HIT = """(sel) => {
  const el = document.querySelector(sel);
  if (!el) return 'absent';
  const r = el.getBoundingClientRect();
  if (r.width < 1 || r.height < 1) return 'zero-size';
  const x = r.left + r.width / 2, y = r.top + r.height / 2;
  if (y < 0 || y > innerHeight) return 'offscreen';
  const top = document.elementFromPoint(x, y);
  if (!top) return 'nothing-at-point';
  // an ancestor being topmost means the control itself is not receiving the hit
  return (top === el || el.contains(top)) ? true
       : top.tagName + '.' + String(top.className).split(' ')[0].slice(0, 24);
}"""

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    for label, vp, mob in (("1440", {"width": 1440, "height": 900}, False),
                           ("390", {"width": 390, "height": 844}, True)):
        pg = b.new_page(viewport=vp, is_mobile=mob, has_touch=mob)
        pg.goto(BASE + "/collections/medicines-health", wait_until="networkidle")
        pg.wait_for_timeout(250)
        ck(f"[{label}] wrapper synthesised", isinstance(pg.evaluate(WRAP), dict))
        pg.wait_for_timeout(150)

        # the header's own controls
        ck(f"[{label}] search input is hit-testable", pg.evaluate(HIT, ".hdr-search-form input"))
        if mob:
            ck(f"[{label}] hamburger is hit-testable", pg.evaluate(HIT, "[data-mnav-open-btn]"))
            # mobile nav drawer: the defect that shipped
            pg.click("[data-mnav-open-btn]"); pg.wait_for_timeout(450)
            ck(f"[{label}] mnav drawer is open",
               pg.evaluate("() => document.body.hasAttribute('data-mnav-open')"))
            ck(f"[{label}] mnav first link is hit-testable",
               pg.evaluate(HIT, "[data-mnav-panel]:not([hidden]) .mnav-link"))
            ck(f"[{label}] mnav drill-down button is hit-testable",
               pg.evaluate(HIT, "[data-mnav-into]"))
            pg.click("[data-mnav-open-btn]"); pg.wait_for_timeout(350)

        # cart drawer and its overlay, rendered by header.liquid into the same wrapper
        pg.evaluate("""() => {
            document.body.setAttribute('data-cd-open', '');
            const d = document.querySelector('[data-cd-drawer]'), o = document.querySelector('[data-cd-overlay]');
            if (d) d.hidden = false; if (o) o.hidden = false; }""")
        pg.wait_for_timeout(450)
        ck(f"[{label}] cart drawer close button is hit-testable", pg.evaluate(HIT, "[data-cd-close]"))
        # The overlay is full-width-covered by the drawer on a phone, so point-testing it
        # says nothing. Assert the regression signature itself: inheriting
        # pointer-events:none from the wrapper is exactly what made it undismissable.
        ck(f"[{label}] cart overlay still accepts pointer events",
           pg.evaluate("""() => {
             const o = document.querySelector('[data-cd-overlay]');
             return o ? getComputedStyle(o).pointerEvents !== 'none' : 'absent'; }"""))
        ck(f"[{label}] mnav drawer still accepts pointer events",
           pg.evaluate("""() => {
             const d = document.querySelector('.mnav-drawer');
             return d ? getComputedStyle(d).pointerEvents !== 'none' : 'absent'; }"""))
        pg.evaluate("() => document.body.removeAttribute('data-cd-open')")
        pg.wait_for_timeout(250)

        # the reason the wrapper carries pointer-events:none at all: once the header
        # translates away its box stays at the top and must not swallow the page
        pg.evaluate("() => window.scrollTo(0, 1400)")
        pg.evaluate("() => document.querySelector('.hdr-sticky').classList.add('is-hidden')")
        pg.wait_for_timeout(450)
        under = pg.evaluate("""() => {
            const e = document.elementFromPoint(innerWidth / 2, 40);
            if (!e) return 'nothing';
            return e.closest('.shopify-section-group-header-group') ? 'BLOCKED-by-wrapper' : 'page';
        }""")
        ck(f"[{label}] page beneath a hidden header stays clickable", under, "page")
        pg.close()
    b.close()

bad = [r for r in res if not r[0]]
for ok, name, got in res:
    if not ok: print(f"FAIL  {name}   (got {got!r})")
print(f"\n{len(res) - len(bad)}/{len(res)} header-wrapper checks passed")
sys.exit(1 if bad else 0)
