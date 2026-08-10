"""taxonomy.json -> setup/collections.json (every category as a Shopify collection,
with draft description_html per category — flagged for client copy review)."""
import json, re, unicodedata, os

HERE = os.path.dirname(os.path.abspath(__file__))

def handleize(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    s = s.lower().replace('&', ' ').replace("'", '')
    return re.sub(r'-{2,}', '-', re.sub(r'[^a-z0-9]+', '-', s)).strip('-')

raw = json.load(open(os.path.join(HERE, 'taxonomy.json')))

# Top-level nav entries that are NOT collections (content pages)
PAGES = {'Brands', 'Services'}
collections = {}  # handle -> record

def add(title, level, parent_menu=None, group=None):
    h = handleize(title)
    if h not in collections:
        collections[h] = {'handle': h, 'title': title, 'level': level,
                          'parent_menu': parent_menu, 'group': group, 'nav_paths': []}
    path = ' > '.join(x for x in (parent_menu, group, title) if x)
    collections[h]['nav_paths'].append(path)
    return h

for m in raw:
    menu = m['menu']
    if menu in PAGES:
        continue
    add(menu, 'menu')
    for g in m.get('groups', []):
        add(g['title'], 'group', parent_menu=menu)
        for item in g['items']:
            add(item, 'leaf', parent_menu=menu, group=g['title'])
    for item in m.get('flat', []):
        add(item, 'leaf', parent_menu=menu)

# extra collections referenced by the designs outside the nav
for extra in ('New In', 'Bundles', 'Hot Offers'):
    add(extra, 'menu')

# Brand collections behind the A–Z index on the Brands page (vendor-matched in
# provision.mjs). Source of truth: setup/brands.json, also used by gen_brands.py.
for b in json.load(open(os.path.join(HERE, 'brands.json'))):
    collections[b['handle']] = {'handle': b['handle'], 'title': b['title'], 'level': 'brand',
                                'parent_menu': 'Brands', 'group': None,
                                'nav_paths': [f"Brands > {b['title']}"]}

# draft description copy per level — client to review before launch
EXTRA_DESCRIPTIONS = {
    'new-in': "The latest arrivals at McCormack's Pharmacy — new brands, new formulas and fresh stock added every week.",
    'bundles': "Multi-buy bundles built by our pharmacists — save on the essentials you already buy together.",
    'hot-offers': "This month's hottest offers across pharmacy, vitamins, skincare and more. While stocks last.",
}

def describe(c):
    t, menu = c['title'], c['parent_menu']
    if c['handle'] in EXTRA_DESCRIPTIONS:
        return f"<p>{EXTRA_DESCRIPTIONS[c['handle']]}</p>"
    if c['level'] == 'brand':
        return f"<p>Shop the full {t} range at McCormack's Pharmacy — trusted stockist with fast delivery across Ireland and Click &amp; Collect from all seven stores.</p>"
    if c['level'] == 'menu':
        return f"<p>Explore our full {t} range — pharmacist-approved essentials with free delivery over €65 and Click &amp; Collect from all seven McCormack's stores.</p>"
    if c['level'] == 'group':
        return f"<p>Shop {t} at McCormack's Pharmacy, part of our {menu} range. Advice from our pharmacists on every order and free delivery over €65.</p>"
    return f"<p>Browse {t} — trusted brands, pharmacist guidance and fast dispatch from our registered Irish pharmacy. Part of our {menu} range.</p>"

for c in collections.values():
    c['description_html'] = describe(c)

out = sorted(collections.values(), key=lambda c: (c['level'] != 'menu', c['handle']))
with open(os.path.join(HERE, 'collections.json'), 'w') as f:
    json.dump(out, f, indent=2, ensure_ascii=False)

levels = {}
for c in out:
    levels[c['level']] = levels.get(c['level'], 0) + 1
shared = [c for c in out if len(c['nav_paths']) > 1]
print('collections:', len(out), levels)
print('shared handles (multiple nav paths):', len(shared))
for c in shared:
    print('  ', c['handle'], '<-', c['nav_paths'])
