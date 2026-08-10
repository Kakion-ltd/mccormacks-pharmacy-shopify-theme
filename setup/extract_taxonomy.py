"""Extract the full nav taxonomy from the homepage mega-menu markup -> JSON."""
import json
from playwright.sync_api import sync_playwright

MENUS = {  # sc-if hole name -> menu label
    'oPharm': 'Medicines & Health',
    'oSupp': 'Vitamins',
    'oSkin': 'Skincare',
    'oBeauty': 'Beauty',
    'oToil': 'Toiletries',
    'oBaby': 'Mother & Baby',
    'oFrag': 'Fragrance',
    'oGifts': 'Gifting',
}

JS = """async (menus) => {
  const txt = await (await fetch('McCormacks%20Homepage.dc.html')).text();
  const doc = new DOMParser().parseFromString(txt, 'text/html');
  const out = [];
  for (const [key, label] of Object.entries(menus)) {
    const holder = [...doc.querySelectorAll('sc-if')].find(n => (n.getAttribute('value')||'').includes(key));
    if (!holder) { out.push({menu: label, error: 'dropdown not found'}); continue; }
    const groups = [];
    let flat = [];
    let cur = null;
    for (const a of holder.querySelectorAll('a')) {
      if (a.closest('div[style*="eef2e8"]')) continue;  // promo side panel
      const style = a.getAttribute('style') || '';
      const text = a.textContent.trim().replace(/\\s+/g, ' ');
      if (!text) continue;
      if (style.includes('#3f6b4f') && style.includes('800')) {
        cur = { title: text, items: [] };
        groups.push(cur);
      } else if (style.includes('#5a6153') || style.includes('#3a3d39')) {
        (cur ? cur.items : flat).push(text);
      }
    }
    out.push({ menu: label, groups, flat });
  }
  return out;
}"""

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page()
    pg.goto('http://localhost:8734/pages/McCormacks%20Homepage.dc.html')
    data = pg.evaluate(JS, MENUS)
    b.close()

# top-level entries with no dropdown
data += [{'menu': m, 'groups': [], 'flat': []} for m in ('Sale', 'Brands', 'Services')]

with open('taxonomy_raw.json', 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

for m in data:
    n_groups = len(m.get('groups', []))
    n_items = sum(len(g['items']) for g in m.get('groups', [])) + len(m.get('flat', []))
    print(f"{m['menu']}: {n_groups} groups, {n_items} leaf items")
print('total leaves:', sum(sum(len(g['items']) for g in m.get('groups', [])) + len(m.get('flat', [])) for m in data))
