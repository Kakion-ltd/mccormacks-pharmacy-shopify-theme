"""A collection with nothing published disappears from the nav, by itself.

The rule is decided at render time: taxonomy.json stays the complete map of the
shop, and every nav surface asks `collections[handle].all_products_count == 0`
before it draws a link. So a category comes back on its own the moment a product
is tagged into it, with nothing to regenerate and nobody to remember.

That makes it exactly the kind of rule nothing can see. The generated nav still
lists all 178 links, so mega-taxonomy.py and chips-taxonomy.py pass whether the
guards are there or not -- they check the map, not the render. And the preview
gives every collection a healthy product count, so the guards never fire. Both
halves have to be checked on purpose:

  Part 1, against the source: every collection link in the generated nav carries
  a guard, and the hand-written surfaces (header, pill row, footer) go through
  snippets/nav-hide.liquid.

  Part 2, against the render: setup/render_preview.mjs makes `condoms` and
  `sport` empty. `condoms` is a leaf with a live sibling, so one link goes and
  the group stays. `sport` is a childless group, so it goes whole. Anything that
  breaks the guards shows up here as a link that should not be on the page.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(HERE)
BASE = f"http://localhost:{os.environ.get('PORT', '8734')}"

res = []
def ck(name, got, want=True): res.append((got == want, name, got))

theme = lambda *p: open(os.path.join(ROOT, 'shopify-theme', *p)).read()

# ---------------------------------------------------------------- part 1: source
RULE = 'all_products_count == 0'
ck('nav-hide.liquid states the rule', RULE in theme('snippets', 'nav-hide.liquid'))
ck('nav-hide only hides on a known zero, never on nil',
   'if nh_handle != blank and collections[nh_handle].all_products_count == 0' in theme('snippets', 'nav-hide.liquid'))

for f in ('mega-menu.liquid', 'mobile-nav.liquid', 'category-chip.liquid', 'category-breadcrumb.liquid'):
    ck(f'{f} guards its links', RULE in theme('snippets', f))

for f in ('header.liquid', 'category-pills.liquid', 'footer.liquid'):
    ck(f'sections/{f} goes through nav-hide', "render 'nav-hide'" in theme('sections', f))

# Every /collections/ anchor in the generated nav sits inside a guard. Counting
# unless-depth rather than looking for the nearest opening tag, because there are two
# guard forms -- `unless collections[h]...` for one handle and `assign shown` +
# `unless shown == 0` for a group -- and matching only the first form silently passed
# every group and department link the first time this was written.
UNLESS = re.compile(r'{%-?\s*(unless|endunless)\b')
for f in ('mega-menu.liquid', 'mobile-nav.liquid'):
    src = theme('snippets', f)
    events = [(m.start(), m.group(1)) for m in UNLESS.finditer(src)]
    unguarded, depth, at = [], 0, 0
    for m in re.finditer(r'<a [^>]*href="/collections/([a-z0-9-]+)"', src):
        while at < len(events) and events[at][0] < m.start():
            depth += 1 if events[at][1] == 'unless' else -1
            at += 1
        if depth < 1:
            unguarded.append(m.group(1))
    ck(f'{f}: no unguarded collection link', sorted(set(unguarded)), [])

# ---------------------------------------------------------------- part 2: render
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print('playwright missing — source checks only')
    sync_playwright = None

if sync_playwright:
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        for label, w, h in (('desktop', 1440, 900), ('mobile', 390, 844)):
            pg = b.new_context(viewport={'width': w, 'height': h}).new_page()
            pg.goto(BASE + '/', wait_until='networkidle')
            hrefs = pg.eval_on_selector_all('a[href^="/collections/"]', 'els => els.map(e => e.getAttribute("href"))')
            ck(f'[{label}] the empty leaf is gone from the nav', '/collections/condoms' in hrefs, False)
            ck(f'[{label}] the empty childless group is gone', '/collections/sport' in hrefs, False)
            ck(f'[{label}] its live sibling stayed', '/collections/erectile-dysfunction' in hrefs)
            ck(f'[{label}] the group above it stayed', '/collections/sexual-health' in hrefs)
            ck(f'[{label}] the department stayed', '/collections/medicines-health' in hrefs)

            # the chip row on a sibling's page drops the empty chip but keeps the rest
            pg.goto(BASE + '/collections/erectile-dysfunction', wait_until='networkidle')
            chips = pg.eval_on_selector_all('.chip', 'els => els.map(e => e.getAttribute("href"))')
            ck(f'[{label}] empty sibling has no chip', '/collections/condoms' in chips, False)
            ck(f'[{label}] the current category keeps its chip', '/collections/erectile-dysfunction' in chips)
        b.close()

bad = [r for r in res if not r[0]]
for ok, name, got in res:
    if not ok:
        print(f'FAIL  {name}  (got {got!r})')
print(f'\n{len(res) - len(bad)}/{len(res)} empty-collection nav checks passed')
sys.exit(1 if bad else 0)
