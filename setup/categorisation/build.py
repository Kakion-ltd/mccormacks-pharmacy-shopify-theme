#!/usr/bin/env python3
"""Build the categorisation sweep workbook.

    SWEEP_DATA=<folder with the live pull> python3 setup/categorisation/build.py

Reads collections.jsonl / products.jsonl (a read-only Admin API pull), the
signatures and the hand-made findings. Writes one xlsx. Touches nothing else:
no tags, no types, no collections.
"""
import collections, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

import match
from findings import ORPHANS, RULE_FIXES, STAY_EMPTY, WRONG_CATEGORY
from signatures import SIGS

HEAD, YELLOW = '2F5233', 'FFF2A8'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Categorisation-Sweep.xlsx')

cols, prods = match.load()
live = {c['handle']: c for c in cols}
local = {c['handle']: c for c in json.load(open('setup/collections.json'))}
orphan_handles = set(json.load(open(f"{match.DATA}/nocat.json")))
med = lambda p: 'yes' if 'pharmacist-review' in p['tags'] else 'no'

def rule_of(h):
    c = live.get(h)
    if not c or not c.get('ruleSet'): return 'manual / none'
    rs = c['ruleSet']
    j = ' OR ' if rs['appliedDisjunctively'] else ' AND '
    return j.join(f"{r['column']} {r['relation']} \"{r['condition']}\"" for r in rs['rules'])

def path_of(h):
    l = local.get(h)
    return l['nav_paths'][0] if l and l.get('nav_paths') else '—'

def title_of(h):
    return (live.get(h) or {}).get('title') or local.get(h, {}).get('title', h)

# ---------------------------------------------------------------- the proposals
proposals = {h: match.matches(prods, h) for h in SIGS}
CONF_ORDER = {'high': 0, 'medium': 1, 'low': 2}

wb = Workbook(); wb.remove(wb.active)

def sheet(name, title, blurb, cols_, widths, rows, yellow_cols=()):
    ws = wb.create_sheet(name)
    ws.append([title]); ws.append([blurb]); ws.append([])
    hr = ws.max_row + 1
    ws.append(cols_)
    for r in rows: ws.append(r)
    ws['A1'].font = Font(bold=True, size=14)
    ws['A2'].font = Font(italic=True)
    ws['A2'].alignment = Alignment(wrap_text=True, vertical='top')
    for c in ws[hr]:
        c.font = Font(bold=True, color='FFFFFF')
        c.fill = PatternFill('solid', fgColor=HEAD)
        c.alignment = Alignment(vertical='center', wrap_text=True)
    for i in yellow_cols:
        ws.cell(row=hr, column=i).fill = PatternFill('solid', fgColor=YELLOW)
        ws.cell(row=hr, column=i).font = Font(bold=True, color='000000')
        for r in range(hr + 1, ws.max_row + 1):
            ws.cell(row=r, column=i).fill = PatternFill('solid', fgColor=YELLOW)
    ws.freeze_panes = ws.cell(row=hr + 1, column=1).coordinate
    last = chr(ord('A') + len(cols_) - 1)
    ws.auto_filter.ref = f'A{hr}:{last}{ws.max_row}'
    for col, w in zip([chr(ord('A') + i) for i in range(len(cols_))], widths):
        ws.column_dimensions[col].width = w
    for row in ws.iter_rows(min_row=hr + 1):
        for c in row: c.alignment = Alignment(vertical='top', wrap_text=True)
    return ws

# ---------------------------------------------------------------- 1. Summary
cat_level = lambda h: local.get(h, {}).get('level') in ('menu', 'group', 'leaf')
empty = [c for c in cols if c['productsCount']['count'] == 0]
thin = [c for c in cols if 1 <= c['productsCount']['count'] <= 3]
empty_cat = [c for c in empty if not local.get(c['handle']) or cat_level(c['handle'])]
thin_cat = [c for c in thin if not local.get(c['handle']) or cat_level(c['handle'])]
empty_brand = [c for c in empty if local.get(c['handle'], {}).get('level') == 'brand']
thin_brand = [c for c in thin if local.get(c['handle'], {}).get('level') == 'brand']
stay = {h for h, *_ in STAY_EMPTY}
empty_cat_h = [c['handle'] for c in empty_cat]
would_fill = [h for h in SIGS if live.get(h, {}).get('productsCount', {}).get('count', 0) == 0 and proposals[h]]
conf_tot = collections.Counter(c for m in proposals.values() for c, _ in m)
tagged_products = {p['handle'] for m in proposals.values() for _, p in m}
med_rows = sum(1 for m in proposals.values() for _, p in m if med(p) == 'yes')
no_leaf_types = collections.Counter()
LEAFH = {h for h, c in local.items() if c['level'] == 'leaf'}
leaf_types = {r['condition'].lower() for h in LEAFH if live.get(h, {}).get('ruleSet')
              for r in live[h]['ruleSet']['rules'] if r['column'] == 'TYPE'}
for p in prods:
    if (p['productType'] or '').lower() not in leaf_types: no_leaf_types[p['productType']] += 1

sheet('Summary', 'Categorisation sweep — 1 October 2026',
 'Read only. Nothing on the store was changed. Counts come from a read-only Admin API pull of all '
 '316 collections and all 2,426 products (types, vendors, tags, descriptions), taken 1 Oct 2026. '
 'Every proposed change has a yellow Approve column on its own tab. "Medicine?" means the product '
 'carries the pharmacist-review tag.',
 ['What', 'Count', 'Note'], [52, 10, 86], [
  ['Collections on the store', len(cols), '309 generated from taxonomy.json plus 7 others'],
  ['— empty (0 products)', len(empty), f'{len(empty_cat)} category pages, {len(empty_brand)} brand page'],
  ['— 1–3 products', len(thin), f'{len(thin_cat)} category pages, {len(thin_brand)} brand pages'],
  ['', '', ''],
  [f'The {len(empty_cat)} empty category pages reconcile as:', '', 'every one of them is on one of the three rows below'],
  ['— would fill with 4 or more products', len([h for h in would_fill if len(proposals[h]) > 3]),
   'see Fill empty pages'],
  ['— would fill, but only to 1–3 products', len([h for h in would_fill if len(proposals[h]) <= 3]),
   'the page works but stays thin; that is all McCormack’s stocks for it'],
  ['— stay empty, or should be removed', len([h for h in empty_cat_h if not proposals.get(h)]),
   'nothing is stocked for them — see Stay empty or remove'],
  ['Thin pages (1–3) this sweep would add to', len([h for h in SIGS if 1 <= live.get(h, {}).get('productsCount', {}).get('count', 0) <= 3 and proposals[h]]),
   f'of {len(thin_cat)} thin category pages — see Fill thin pages'],
  ['', '', ''],
  ['Proposed product→page rows, total', sum(len(m) for m in proposals.values()),
   'a product can land on more than one page, which is intended'],
  ['— high confidence', conf_tot['high'], 'unambiguous: brand, licensed ingredient or exact product type'],
  ['— medium confidence', conf_tot['medium'], 'right category, placement is a judgement call'],
  ['— low confidence', conf_tot['low'],
   'nil on purpose: a product that could only be guessed at was left unplaced rather than '
   'given a low-confidence tag. Those are on No sub-category page as a bulk decision.'],
  ['Distinct products touched', len(tagged_products), f'of {len(prods)} on the store'],
  ['— rows that are medicines (pharmacist-review)', med_rows, 'pharmacist signs these off'],
  ['', '', ''],
  ['Products on no category page at all', len(orphan_handles),
   'not 195 — that was the 25 Sep figure and 175 of them were retyped the same day'],
  ['Products on a department but no sub-category page', sum(n for t, n in no_leaf_types.items()),
   f'spread over {len(no_leaf_types)} product types that no leaf rule names — the real gap'],
  ['', '', ''],
  ['Products in a wrong category', sum(len([p for p in prods if re.search(r[0], p["title"], re.I)]) for r in WRONG_CATEGORY),
   f'{len(WRONG_CATEGORY)} findings — see Wrong category'],
  ['Collection rules that should change', len(RULE_FIXES), 'see Rules to change'],
 ])

# ---------------------------------------------------------------- 2/3. fill tabs
def fill_rows(handles):
    out = []
    for h in sorted(handles, key=lambda h: (path_of(h), h)):
        for conf, p in sorted(proposals[h], key=lambda x: (CONF_ORDER[x[0]], x[1]['title'])):
            out.append([title_of(h), path_of(h), rule_of(h),
                        f'add tag "{title_of(h)}"', p['title'], p['productType'] or '(none)',
                        p['vendor'], conf, med(p), SIGS[h][5], ''])
    return out

FILLCOLS = ['Page', 'Where it sits', 'Rule now', 'What to do', 'Product', 'Type now',
            'Brand', 'Confidence', 'Medicine?', 'Note', 'Approve']
FILLW = [27, 40, 34, 26, 54, 30, 17, 11, 10, 60, 10]

sheet('Fill empty pages', f'{len(would_fill)} empty pages this sweep would fill',
 'Every one of these pages matches on a tag that no product carries (TAG EQUALS <page title>). '
 'The fix is to put that tag on the products listed. The rule needs no change. Where the rule '
 'itself is the problem instead, the page is on the Rules to change tab.',
 FILLCOLS, FILLW, fill_rows(would_fill), yellow_cols=(11,))

thin_fill = [h for h in SIGS if 1 <= live.get(h, {}).get('productsCount', {}).get('count', 0) <= 3 and proposals[h]]
sheet('Fill thin pages', f'{len(thin_fill)} pages with 1–3 products this sweep would add to',
 'Same job as the empty pages: these have a tag rule and one to three products tagged, so the '
 'tagging was started and not finished. "Already on" is the live count.',
 ['Page', 'Already on', 'Where it sits', 'Rule now', 'What to do', 'Product', 'Type now',
  'Brand', 'Confidence', 'Medicine?', 'Note', 'Approve'],
 [27, 11, 38, 32, 26, 54, 28, 17, 11, 10, 56, 10],
 [[r[0], live[h]['productsCount']['count']] + r[1:] for h in sorted(thin_fill, key=lambda h: (path_of(h), h))
  for r in [row for row in fill_rows([h])]],
 yellow_cols=(12,))

# ---------------------------------------------------------------- 4. no category page
rows = []
for pat, what, now, prop, conf in ORPHANS:
    for p in sorted([p for p in prods if re.search(pat, p['title'], re.I) and p['handle'] in orphan_handles],
                    key=lambda p: p['title']):
        rows.append([p['title'], what, p['productType'] or '(no type)', p['vendor'], prop, conf, med(p), ''])
sheet('No category page', f'{len(rows)} products on no category page at all',
 'The last count in MAINTENANCE was 195, on 25 Sep 2026; 175 of those were retyped the same day '
 'and 20 were held for a decision. These 21 are what is left. A product with no type, or a type '
 'that is a season ("New", "Christmas Shop") or a promotion ("Bundles"), reaches no page.',
 ['Product', 'What it is', 'Type now', 'Brand', 'Proposed type / page', 'Confidence', 'Medicine?', 'Approve'],
 [54, 48, 24, 18, 52, 11, 10, 10], rows, yellow_cols=(8,))

# ---------------------------------------------------------------- 5. no leaf page
rows = [[t or '(no type)', n, 'yes' if t in ('New', 'Sale', 'Christmas Shop', 'Bundles', '') else '',
         ''] for t, n in no_leaf_types.most_common()]
sheet('No sub-category page', f'{sum(n for _, n in no_leaf_types.items())} products reach a department but no sub-category page',
 'This is the bigger half of the problem and it is structural, not per product. Every filled leaf '
 'page on the store is filled by a TYPE rule; every empty one matches a tag nobody applied. These '
 'are the product types that no leaf rule names, so their products stop at the department page. '
 'The Fill tabs place the ones a title can place; the rest need either a TYPE rule per leaf or a '
 'bulk tagging decision from Keelan.',
 ['Product type', 'Products', 'Type is a season or promotion, not a category', 'Approve a rule for it'],
 [46, 11, 44, 24], rows, yellow_cols=(4,))

# ---------------------------------------------------------------- 6. wrong category
rows = []
for pat, what, now, prop_t, prop_tag, conf, why in WRONG_CATEGORY:
    hits = sorted([p for p in prods if re.search(pat, p['title'], re.I)], key=lambda p: p['title'])
    rows.append([what, '; '.join(p['title'] for p in hits)[:600], len(hits), now, prop_t, prop_tag,
                 conf, 'yes' if any(med(p) == 'yes' for p in hits) else 'no', why, ''])
rows.sort(key=lambda r: (CONF_ORDER[r[6]], -r[2]))
sheet('Wrong category', f'{len(rows)} findings — products on a page that does not describe them',
 'Uddermint in Vitamins was the example given; it is the first row. The pattern it belongs to is '
 'veterinary, seasonal and department-level mistakes. Several are one product of a range filed '
 'away from its siblings, which is how a range ends up split over four pages.',
 ['What it is', 'Products', 'How many', 'Type now', 'Proposed type', 'Proposed tag',
  'Confidence', 'Medicine?', 'Why it is wrong', 'Approve'],
 [46, 56, 10, 40, 36, 40, 11, 10, 72, 10], rows, yellow_cols=(10,))

# ---------------------------------------------------------------- 7. rules
sheet('Rules to change', f'{len(RULE_FIXES)} collections where the rule is the problem, not the products',
 'Changing a rule is cheaper than tagging products and it keeps working as stock changes. The last '
 'three rows are not single collections but the shape of the whole problem.',
 ['Page', 'Rule now', 'Proposed rule', 'Effect', 'Why', 'Approve'],
 [34, 44, 46, 20, 90, 10],
 [[t, now, prop, gain, why, ''] for _, t, now, prop, gain, why in RULE_FIXES], yellow_cols=(6,))

# ---------------------------------------------------------------- 8. stay empty
sheet('Stay empty or remove', f'{len(STAY_EMPTY)} pages with nothing to put in them',
 'No products were invented for these. Four should be removed outright, two are merchandising '
 'pages the client fills, and four stay thin because one or two products is all that is stocked.',
 ['Page', 'Verdict', 'Why', 'Approve'], [34, 26, 104, 10],
 [[t, v, why, ''] for _, t, v, why in STAY_EMPTY], yellow_cols=(4,))

wb.save(OUT)
print('wrote', OUT)
for ws in wb: print(f'  {ws.title:24} {ws.max_row - 4:5} rows')
