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
]

STATE = """() => {
  const vis = (e) => !!e && e.getClientRects().length > 0;
  const trail = document.querySelector('.crumb-trail') ||
    [...document.querySelectorAll('nav[aria-label="Breadcrumb"]')].pop();
  const back = document.querySelector('.crumb-back');
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
        pg.close()
    b.close()

for ok, name, got in res:
    if not ok:
        print(f"FAIL  {name}   (got {got!r})")
print(f"\n{sum(1 for r in res if r[0])}/{len(res)} breadcrumb checks passed")
sys.exit(0 if all(r[0] for r in res) else 1)
