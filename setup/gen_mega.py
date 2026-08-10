"""Transform the homepage's 8 mega-dropdown blocks into snippets/mega-menu.liquid.
Keeps the design markup verbatim; swaps template-hole attrs for data attributes,
style-hover for utility classes, and .dc.html hrefs for /collections/<handle> URLs."""
import json, re
from playwright.sync_api import sync_playwright

MENUS = [  # sc-if key -> (panel key, menu label)
    ('oPharm', 'medicines-health'), ('oSupp', 'vitamins'), ('oSkin', 'skincare'),
    ('oBeauty', 'beauty'), ('oToil', 'toiletries'), ('oBaby', 'mother-baby'),
    ('oFrag', 'fragrance'), ('oGifts', 'gifting'),
]

import unicodedata

def handleize(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    s = s.lower().replace('&', ' ').replace("'", '')
    return re.sub(r'-{2,}', '-', re.sub(r'[^a-z0-9]+', '-', s)).strip('-')

handles = {c['handle'] for c in json.load(open('/Users/matthewtobin/Web Apps/design_handoff_mccormacks_site/setup/collections.json'))}

HOVER_MAP = [
    ('color:#82c914; transform:translateX(4px);', 'hov-slide'),
    ('color:#82c914;', 'hov-green'),
    ('color:#6ba30f;', 'hov-green-dk'),
    ('color:#3f6b4f;', 'hov-dark-green'),
]

JS = """async (keys) => {
  const txt = await (await fetch('McCormacks%20Homepage.dc.html')).text();
  const doc = new DOMParser().parseFromString(txt, 'text/html');
  const out = {};
  for (const key of keys) {
    const holder = [...doc.querySelectorAll('sc-if')].find(n => (n.getAttribute('value')||'').includes(key));
    out[key] = holder ? holder.innerHTML : null;
  }
  return out;
}"""

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page()
    pg.goto('http://localhost:8734/pages/McCormacks%20Homepage.dc.html')
    blocks = pg.evaluate(JS, [k for k, _ in MENUS])
    b.close()

def link_for(text, panel=None):
    text = re.sub(r'\s+', ' ', text.strip())
    text = re.sub(r'^image\s+', '', text)  # promo tiles: placeholder token before label
    h = handleize(text)
    if h in handles:
        return f'/collections/{h}'
    return f'/collections/{panel}' if panel else None

unmapped = []

def transform(html, panel_key):
    # strip template-hole event attrs
    html = re.sub(r'\s*on[A-Za-z]+="\{\{[^}]*\}\}"', '', html)
    # style-hover -> classes
    def hover_repl(m):
        val = m.group(1).strip()
        for style, cls in HOVER_MAP:
            if val == style.rstrip(';') or val == style:
                return f'data-addclass="{cls}"'
        return f'data-addclass-unknown="{val}"'
    html = re.sub(r'style-hover="([^"]*)"', hover_repl, html)
    # merge data-addclass into class attr (anchors here have no class attr in design)
    html = re.sub(r'data-addclass="([^"]*)"', r'class="\1"', html)
    # rewrite hrefs based on anchor text
    def href_repl(m):
        attrs, inner = m.group(1), m.group(2)
        text = re.sub(r'<[^>]+>', ' ', inner)
        text = re.sub(r'\s+', ' ', text).replace('&amp;', '&').strip()
        h = handleize(re.sub(r'^image\s+', '', text))
        if h not in handles:
            unmapped.append((panel_key, text))
        url = link_for(text, panel_key)
        new_attrs = re.sub(r'href="[^"]*"', f'href="{url}"', attrs)
        return f'<a {new_attrs}>{inner}</a>'
    html = re.sub(r'<a ([^>]*)>(.*?)</a>', href_repl, html, flags=re.S)
    return html

# Panels overridden to a simple single-column list, no promo images (client request).
# left offsets = measured trigger positions at 1440; theme.js re-aligns at runtime,
# these are the no-JS fallback.
SINGLE_COLUMN = {'toiletries': 379, 'mother-baby': 454, 'fragrance': 566, 'gifting': 648}

def single_column_panel(panel):
    taxonomy = json.load(open('/Users/matthewtobin/Web Apps/design_handoff_mccormacks_site/setup/taxonomy.json'))
    menu = next(m for m in taxonomy if handleize(m['menu']) == panel)
    items = m_items = menu.get('flat') or [g['title'] for g in menu.get('groups', [])]
    links = '\n'.join(
        f'<a href="{link_for(i, panel)}" class="hov-slide" style="color:#3a3d39; display:inline-block; padding:2px 0; '
        f'width:fit-content; transition:color .14s ease, transform .14s ease;">{i.replace("&", "&amp;")}</a>'
        for i in items)
    left = SINGLE_COLUMN[panel]
    return (f'<div style="position:absolute; left:{left}px; width:240px; top:100%; z-index:50; background:#ffffff; '
            f'border:1px solid #e6e7e4; box-shadow:0 24px 44px rgba(0,0,0,.14); border-radius:0 0 16px 16px; '
            f'max-height:74vh; overflow-y:auto; animation:megaIn .16s ease-out;">\n'
            f'<div style="padding:26px 28px; display:flex; flex-direction:column; gap:11px; font-size:14px;">\n'
            f'{links}\n</div>\n</div>')

parts = ["{% comment %} Generated from design handoff mega-menu markup. Regenerate with setup/gen_mega.py {% endcomment %}"]
for key, panel in MENUS:
    if panel in SINGLE_COLUMN:
        parts.append(f'<div class="mega-panel" data-mega-panel="{panel}">\n{single_column_panel(panel)}\n</div>')
        continue
    inner = blocks[key]
    assert inner, f'missing dropdown {key}'
    parts.append(f'<div class="mega-panel" data-mega-panel="{panel}">\n{transform(inner, panel)}\n</div>')

out = '\n'.join(parts)
path = '/Users/matthewtobin/Web Apps/design_handoff_mccormacks_site/shopify-theme/snippets/mega-menu.liquid'
import os
os.makedirs(os.path.dirname(path), exist_ok=True)
open(path, 'w').write(out)
print('wrote', len(out), 'chars')
print('unknown hover styles:', len(re.findall('data-addclass-unknown', out)))
print('unmapped links:', len(unmapped))
for u in sorted(set(unmapped)): print('  ', u)
