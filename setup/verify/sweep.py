import os
import sys
from playwright.sync_api import sync_playwright
BASE = f"http://localhost:{os.environ.get('PORT', '8734')}"
PAGES = ["/", "/collections/medicines-health", "/collections/skincare", "/products/nurofen-200mg-ibuprofen-24-tablets",
         "/cart", "/search?q=vitamins", "/pages/shipping", "/pages/contact-us",
         "/pages/store-locator", "/blogs/health-hub", "/pages/in-store-services",
         "/pages/prescriptions", "/account/login"]

# Content cut off at the edge, in every state the page can be put in.
#
# main has overflow-x:hidden, so anything wider than the viewport is clipped rather than
# scrolled and never shows in the document scroll width above. That hid the prescription
# selects (21px off at 390) and the services buttons (9px) while this sweep passed. So
# this measures element bounds against the viewport instead, ignoring anything inside an
# ancestor below main that clips or scrolls on purpose (carousels, sliders).
#
# One state is not enough either: the fifth clipped select sat in the "Repeat
# prescriptions" tab, hidden on load. Every <details> and closed accordion in main is
# opened, then each [data-view] tab is shown in turn through its own button, so the
# theme's handler lays it out, not a forced display. Last, a coverage guard: a form
# control that was never on screen and is hidden by a toggle (a hidden attribute or an
# inline display:none, which is how theme.js hides things) fails the check. A new kind of
# toggle this walk does not know how to open then fails loudly instead of going unchecked.
# Stylesheet hiding (.hide-mobile at one width) is layout, not a toggle, and is skipped.
CLIPPED = r"""() => {
  const main = document.querySelector('main'), vw = document.documentElement.clientWidth;
  const onScreen = el => { const r = el.getBoundingClientRect();
    return getComputedStyle(el).visibility !== 'hidden' && r.width > 1 && r.height > 1; };
  const name = el => el.tagName.toLowerCase() + (el.name ? `[name="${el.name}"]` : '')
    + (el.classList[0] ? '.' + el.classList[0] : '') + ` "${(el.textContent || '').trim().slice(0, 30)}"`;
  const controls = [...main.querySelectorAll('input:not([type=hidden]), select, textarea')];
  const seen = new Set(), clips = [];
  const scan = state => {
    const off = [];
    for (const el of main.querySelectorAll('*')) {
      if (!onScreen(el)) continue;
      const r = el.getBoundingClientRect();
      if (r.right <= vw + 1 && r.left >= -1) continue;
      let a = el.parentElement, own = false;
      while (a && a !== main) { if (getComputedStyle(a).overflowX !== 'visible') { own = true; break; } a = a.parentElement; }
      if (!own) off.push([el, Math.round(Math.max(r.right - vw, -r.left))]);
    }
    const els = new Set(off.map(o => o[0]));
    for (const [el, px] of off) if (!els.has(el.parentElement)) clips.push(`${state}: ${name(el)} ${px}px past the edge`);
    controls.forEach(c => { if (onScreen(c)) seen.add(c); });
  };
  main.querySelectorAll('details').forEach(d => { d.open = true; });
  main.querySelectorAll('[data-acc-toggle]').forEach(t => {
    const c = document.querySelector(`[data-acc-content="${t.dataset.accToggle}"]`);
    if (c && c.getAttribute('data-open') !== 'true') t.click();
  });
  scan('on load');
  for (const key of new Set([...main.querySelectorAll('[data-view]')].map(v => v.dataset.view))) {
    const btn = document.querySelector(`[data-view-btn="${key}"]`);
    if (btn) { btn.click(); scan(`tab ${key}`); }
  }
  const unseen = controls.filter(c => !seen.has(c)).filter(c => {
    for (let a = c; a && a !== main; a = a.parentElement)
      if (a.hidden || a.style.display === 'none') return true;
    return false;
  }).map(c => `never shown, hidden by a toggle the sweep cannot open: ${name(c)}`);
  return [...new Set(clips)].concat(unseen);
}"""

bad = []
loads = 0
with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True)
    # Five widths, not two. Three of the eight defects recorded in MAINTENANCE.md
    # ("Correct code, wrong behaviour") lived between 1440 and 390 and were invisible at
    # both: a mega panel asking 1030px of columns inside a 904px panel at 1024, a vh
    # height cap that could not know its own top once the nav wrapped to two rows there,
    # and a compression band from 901 to 1100 whose compensation was never written. The
    # heights are the real ones that ship with those widths - a short viewport is what
    # exposes a cap measured in vh.
    for label, vp in (("1440", {"width":1440,"height":900}),
                      ("1280", {"width":1280,"height":800}),
                      ("1024", {"width":1024,"height":768}),
                      ("390",  {"width":390, "height":844}),
                      # The narrowest common phone. Content clipped at the edge grows as
                      # the screen shrinks: the prescription selects were 21px off at 390
                      # and 51px at 360, the services buttons 9px and 39px.
                      ("360",  {"width":360, "height":780})):
        pg = b.new_page(viewport=vp)
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        for path in PAGES:
            errs.clear()
            loads += 1
            pg.goto(BASE + path, wait_until="networkidle")
            pg.wait_for_timeout(150)
            ow = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
            if ow > 1:
                bad.append(f"{label} {path}: horizontal overflow {ow}px")
            broken = pg.evaluate(
                "Array.from(document.images).filter(i=>i.complete&&i.naturalWidth===0&&!i.classList.contains('img-fallback')).length")
            if broken:
                bad.append(f"{label} {path}: {broken} broken images")
            # the search input must still exist and be usable after the header rewrap
            if pg.locator("[data-ps-input]").count() != 1:
                bad.append(f"{label} {path}: search input missing")
            # and empty everywhere except the results page, which holds the term searched
            want = "vitamins" if path.startswith("/search") else ""
            if pg.locator("[data-ps-input]").input_value() != want:
                bad.append(f"{label} {path}: search input holds {pg.locator('[data-ps-input]').input_value()!r}, want {want!r}")
            # Last, because it opens tabs and accordions and leaves them open.
            for c in pg.evaluate(CLIPPED):
                bad.append(f"{label} {path}: {c}")
            for e in errs:
                bad.append(f"{label} {path}: JS {e}")
        pg.close()
    b.close()
print("\n".join(bad) if bad else
      f"{loads} page-loads clean: no overflow, nothing clipped in any tab or accordion, "
      "no broken images, no JS errors, "
      "search input present on every page, empty off the results page")
sys.exit(1 if bad else 0)
