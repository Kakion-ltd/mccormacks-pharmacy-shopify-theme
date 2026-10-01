#!/usr/bin/env python3
"""Build the two handover workbooks: Keelan's decisions and Fergal's pharmacist calls.

    SWEEP_DATA=<pull folder> python3 setup/categorisation/handover.py

Everything here was deliberately NOT applied on 1 Oct 2026. The high-confidence
tags went on; these are what was held back and why.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
import match
from findings import WRONG_CATEGORY
from signatures import SIGS

HEAD, YELLOW = '2F5233', 'FFF2A8'
HERE = os.path.dirname(os.path.abspath(__file__))
cols, prods = match.load()
live = {c['handle']: c for c in cols}
local = {c['handle']: c for c in json.load(open('setup/collections.json'))}
med = lambda p: 'yes' if 'pharmacist-review' in p['tags'] else 'no'
path_of = lambda h: (local.get(h) or {}).get('nav_paths', ['—'])[0]
hits = lambda pat: sorted([p for p in prods if re.search(pat, p['title'], re.I)], key=lambda p: p['title'])

def sheet(wb, name, title, blurb, cols_, widths, rows, yellow_cols=()):
    ws = wb.create_sheet(name)
    ws.append([title]); ws.append([blurb]); ws.append([])
    hr = ws.max_row + 1
    ws.append(cols_)
    for r in rows: ws.append(r)
    ws['A1'].font = Font(bold=True, size=14)
    ws['A2'].font = Font(italic=True); ws['A2'].alignment = Alignment(wrap_text=True, vertical='top')
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
    ws.auto_filter.ref = f'A{hr}:{chr(ord("A") + len(cols_) - 1)}{ws.max_row}'
    for col, w in zip([chr(ord('A') + i) for i in range(len(cols_))], widths):
        ws.column_dimensions[col].width = w
    for row in ws.iter_rows(min_row=hr + 1):
        for c in row: c.alignment = Alignment(vertical='top', wrap_text=True)

# ======================================================== Keelan
wb = Workbook(); wb.remove(wb.active)
MERGED_AWAY = {'cuticle-nail-care', 'dry-skin'}

rows = []
for h in sorted(SIGS, key=lambda h: (path_of(h), h)):
    if h in MERGED_AWAY or h not in live: continue
    for conf, p in match.matches(prods, h):
        if conf != 'medium': continue
        rows.append([live[h]['title'], path_of(h), f'add tag "{live[h]["title"]}"', p['title'],
                     p['productType'] or '(none)', p['vendor'], med(p), SIGS[h][5], ''])
sheet(wb, 'Medium confidence', f'{len(rows)} products where the page is right but the placement is a judgement',
 'The 681 high-confidence tags went on the store on 1 Oct 2026. These did not. Each one is a '
 'product that plausibly belongs on the page but that a person should look at — a throat lozenge '
 'that is half confectionery, a hot water bottle that is half a gift. Tick Approve and they go on '
 'in the next run.',
 ['Page', 'Where it sits', 'What to do', 'Product', 'Type now', 'Brand', 'Medicine?', 'Note', 'Approve'],
 [27, 40, 30, 54, 30, 18, 10, 58, 10], rows, yellow_cols=(9,))

rows = []
for pat, label, now, prop_t, prop_tag in [
  ('^Tena', 'Continence — pads, pants and men’s guards', "Toiletries > Feminine Care / Men's Grooming",
   'Pharmacy > Continence Care', 'Continence Care + Pads / Pants / Bladder Weakness'),
  ('^Durex', 'Condoms and one lubricant', "Toiletries > Men's Grooming",
   'Pharmacy > Sexual Health', 'Condoms (not Durex Play)')]:
    for p in hits(pat):
        rows.append([label, p['title'], p['productType'], prop_t, prop_tag, p['vendor'], med(p), '', ''])
sheet(wb, 'Tena and Durex moves', f'{len(rows)} products that need a product TYPE change, not just a tag',
 'Held back on purpose. Every other change in this sweep added a tag, which only affects which '
 'page a product appears on. These change the product type, which moves the product between '
 'departments and, for Durex, turns on the pharmacist lines in buy-assurance. That is a bigger '
 'change than a tag and it wanted your sign-off first. The Continence Care group and its four '
 'leaves are empty today because all 12 Tena lines sit under Feminine Care and Men’s Grooming.',
 ['What', 'Product', 'Type now', 'Proposed type', 'Proposed tag', 'Brand', 'Medicine?', 'Your notes', 'Approve'],
 [38, 50, 36, 30, 40, 16, 10, 26, 10], rows, yellow_cols=(9,))

rows = [
 ['Remove a tag', 'Sidena 50Mg Tablets 4 Pack',
  'tags are "Pharmacy" and "Sexual Health" as two separate tags',
  'replace both with the single tag "Pharmacy > Sexual Health"',
  'Not done: every write in this sweep was tagsAdd, so nothing could lose a tag. This one needs a '
  'removal. Harmless today — the page matches on type, not these tags — but the tags are wrong. '
  'It is the comma-split trap in MAINTENANCE.', 'yes', ''],
 ['Remove a tag', 'Tena Lady Discreet Med Pant 6Pk', 'tagged "Quest"', 'swap "Quest" for "Tena Lady"',
  'Not done, same reason. It currently shows on the Quest brand page and not on Tena Lady.', 'no', ''],
]
sheet(wb, 'Tag removals not done', '2 fixes that need a tag taken off',
 'The brief for this run was tagsAdd only, never tagsSet or tagsRemove, so that no product could '
 'lose a tag by accident. Both of these need a removal, so both were reported rather than done.',
 ['What', 'Product', 'Problem', 'Proposed fix', 'Why it was not done', 'Medicine?', 'Approve'],
 [16, 40, 52, 46, 74, 10, 10], rows, yellow_cols=(7,))

rows = [
 ['La Roche-Posay', '/collections/la-roche-posay', 0,
  'Linked from the brand A–Z, the brand slider and the Brands page, but no product carries the '
  'vendor under any spelling. The page is live and empty.', ''],
 ['Pro-Ven Biotics', '/collections/proven', 0,
  'Same — live, linked, empty. The brand slider calls it "Pro-Ven Biotics", so someone meant to '
  'stock it.', ''],
 ['Elizabeth Arden', '/collections/elizabeth-arden', 0,
  'The only empty brand page generated from brands.json. Linked from the brand A–Z.', ''],
]
sheet(wb, 'Stock these or drop the page', '3 brand pages that are live, linked and empty',
 'Nothing was touched. Each is a two-way decision and both ways need work beyond this sweep: '
 'stock the brand, or remove the page AND its three theme links in the same change, or the Brands '
 'page gets a link that goes nowhere. Write "stock" or "remove" in Approve.',
 ['Brand', 'Page', 'Products', 'Situation', 'Approve: stock or remove'], [22, 40, 11, 96, 26], rows,
 yellow_cols=(5,))

out_k = os.path.join(HERE, 'Keelan-Decisions.xlsx'); wb.save(out_k)

# ======================================================== Fergal
wb = Workbook(); wb.remove(wb.active)
rows = []
for p in hits('Uddermint'):
    rows.append([p['title'], p['vendor'], p['productType'], '|'.join(p['tags']) or '(none)', med(p),
     'A veterinary udder cream, licensed for dairy cattle.',
     'It is on the Vitamins page because its type says "Vitamins & Supplements" and it carries no '
     'tags at all. It is not a supplement. People do buy it as a menthol muscle rub, so the obvious '
     'move is Muscle & Joint Pain — but that would present a veterinary product as a human '
     'medicine, which is your call and not ours. The alternatives are a veterinary page (none '
     'exists today) or taking it off the website.', ''])
for p in hits('^Fleaway Plus'):
    rows.append([p['title'], p['vendor'], p['productType'], '|'.join(p['tags']), med(p),
     'A veterinary flea treatment.',
     'Typed "Pharmacy > Companion Animal", which the taxonomy has no page for, so it reaches the '
     'Medicines & Health department and then stops. Already tagged pharmacist-review. The old site '
     'had /c/pet-health/. Decide whether McCormack’s sells pet health online at all; if yes we '
     'add the page, if no these come off.', ''])
sheet(wb, 'Veterinary products', f'{len(rows)} veterinary products held for a pharmacist decision',
 'Deliberately not touched in the 1 Oct 2026 categorisation sweep. Both were excluded from the '
 '681 automatic tag additions. Neither is a human medicine, and where a veterinary product should '
 'sit on a pharmacy website is a regulatory judgement, not a categorisation one.',
 ['Product', 'Brand', 'Type now', 'Tags now', 'pharmacist-review?', 'What it is',
  'The decision', 'Approve / your direction'],
 [44, 15, 28, 40, 16, 40, 86, 28], rows, yellow_cols=(8,))

out_f = os.path.join(HERE, 'Fergal-Pharmacist-Calls.xlsx'); wb.save(out_f)
for o in (out_k, out_f): print('wrote', o)
