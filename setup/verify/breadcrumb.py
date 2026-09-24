"""Breadcrumb — full trail on desktop, one back link on mobile, full trail in the schema.

Below 900px a product or subcategory shows "Back to <parent>" instead of the trail, so
the BreadcrumbList JSON-LD is the only full trail left for Google to read on a phone.
This checks both halves: what each width shows, and that the schema is still there.
"""
import json
import os
import sys
from playwright.sync_api import sync_playwright

BASE = f"http://localhost:{os.environ.get('PORT', '8734')}"
# path, back-link text on mobile (None = keeps its trail), BreadcrumbList names
PAGES = [
    ("/products/vitamin-d3-1000iu-60-capsules", "Back to Everyday Multivitamins",
     ["Home", "Vitamins", "Everyday Multivitamins", "Vitamin D3 1000IU 60 Capsules"]),
    ("/collections/nausea-acid-indigestion-reflux", "Back to Stomach & Gastrointestinal",
     ["Home", "Medicines & Health", "Stomach & Gastrointestinal", "Nausea, Acid Indigestion & Reflux"]),
    ("/collections/everyday-multivitamins", "Back to Vitamins",
     ["Home", "Vitamins", "Everyday Multivitamins"]),
    ("/collections/vitamins", None, ["Home", "Vitamins"]),
    ("/search?q=cream", None, None),
    # pages on snippets/breadcrumb.liquid: a linked parent gets the back link,
    # an unlinked one (Policies) and Prescriptions' link to itself do not
    ("/blogs/health-hub/x", "Back to Health Hub", None),
    ("/account/addresses", "Back to My account", None),
    ("/pages/privacy-policy", None, None),
    ("/pages/prescriptions", None, None),
    ("/pages/about-us", None, None),
]
# Parents that are another view of the same page: the back link is a view button.
# (page, button opening a child view, expected back text, view the back link returns to)
VIEWS = [
    ("/pages/in-store-services", '[data-view-btn="svc-1"]', "Back to In-Store Services", "svc-hub"),
    # the booking view renders only with show_booking_form on, as in this fixture
    ("/preview/page.in-store-services.errors.html", '[data-view-btn="svc-book"]', "Back to In-Store Services", "svc-hub"),
    ("/pages/store-locator", '[data-view-btn="store-1"]', "Back to Store Locator", "locator"),
]

STATE = """() => {
  const vis = (e) => !!e && e.getClientRects().length > 0;
  const shown = (sel) => [...document.querySelectorAll(sel)].find(vis);
  const trail = shown('.crumb-trail');
  const back = shown('.crumb-back');
  const lists = [...document.querySelectorAll('script[type="application/ld+json"]')]
    .map(s => JSON.parse(s.textContent)).filter(d => d['@type'] === 'BreadcrumbList');
  return { trail: vis(trail), back: vis(back) ? back.textContent.trim() : null,
           schema: lists.map(l => l.itemListElement.map(i => i.name)),
           overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth };
}"""

res = []
def ck(name, got, want=True): res.append((got == want, name, got))

with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True)
    for w in (1440, 901, 900, 390):
        pg = b.new_context(viewport={"width": w, "height": 800}).new_page()
        for path, back, schema in PAGES:
            pg.goto(BASE + path, wait_until="networkidle")
            s = pg.evaluate(STATE)
            mobile = w <= 900 and back is not None
            ck(f"[{w}] {path} shows the trail", s["trail"], not mobile)
            ck(f"[{w}] {path} back link", s["back"], back if mobile else None)
            ck(f"[{w}] {path} BreadcrumbList", s["schema"], [schema] if schema else [])
            ck(f"[{w}] {path} no sideways scroll", s["overflow"], False)
        if w == 390:
            for path, opener, back, hub in VIEWS:
                pg.goto(BASE + path, wait_until="networkidle")
                pg.locator(opener + ':visible').first.click()
                s = pg.evaluate(STATE)
                ck(f"[390] {path} {opener} back link", s["back"], back)
                pg.locator(".crumb-back:visible").first.click()
                ck(f"[390] {path} {opener} back returns to {hub}",
                   pg.evaluate(f"() => getComputedStyle(document.querySelector('[data-view=\"{hub}\"]')).display"), "block")
        pg.close()
    b.close()

for ok, name, got in res:
    if not ok:
        print(f"FAIL  {name}   (got {got!r})")
print(f"\n{sum(1 for r in res if r[0])}/{len(res)} breadcrumb checks passed")
sys.exit(0 if all(r[0] for r in res) else 1)
