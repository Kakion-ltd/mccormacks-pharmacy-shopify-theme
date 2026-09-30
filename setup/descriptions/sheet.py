import json, collections
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill

HAS = {'fuller-on-live': 'yes', 'different-text-on-live': 'yes',
       'same-on-live': 'no', 'no-description-on-live': 'no'}

rows = json.load(open('broken.json'))
for r in rows:
    r['has_old'] = HAS.get(r['live_site'], 'not checked')
    r['url'] = r['live_url'] or (
        f"https://www.mccormackspharmacy.ie/p/{r['handle']}/{r['sku']}" if r['sku'] else '')

tabs = [
    ('Pharmacist',
     'Medicines. The pharmacist decides the wording for every one of these.',
     [r for r in rows if r['medicine']]),
    ('Restore from old site',
     'All 146 were restored from the old site on 30 September 2026, using its own '
     'wording. Nothing is left on this tab. How To Use and Ingredients went into '
     'the product page tabs at the same time.',
     [r for r in rows if not r['medicine'] and r['has_old'] == 'yes']),
    ('Staff to fix',
     'Not medicines. The old site has no fuller text, or it was never checked, '
     'so the wording has to be written or found elsewhere.',
     [r for r in rows if not r['medicine'] and r['has_old'] != 'yes']),
]

cols = ['Product', 'Medicine?', 'Problem', 'Current text (first 200 characters)',
        'Old site link', 'Does the old site have the full text?']
wb = Workbook()
wb.remove(wb.active)

for name, blurb, items in tabs:
    items.sort(key=lambda r: (r['problems'][0], r['title']))
    ws = wb.create_sheet(name)
    counts = collections.Counter(p for r in items for p in r['problems'])
    ws.append([f'{len(items)} products' if items else 'Nothing left to do'])
    ws.append([blurb])
    for prob, n in counts.most_common():
        ws.append([f'{prob}: {n}'])
    ws.append([])
    head_row = ws.max_row + 1
    ws.append(cols)
    for r in items:
        ws.append([r['title'], 'yes' if r['medicine'] else 'no', '; '.join(r['problems']),
                   r['text'][:200], r['url'], r['has_old']])

    ws['A1'].font = Font(bold=True, size=14)
    ws['A2'].font = Font(italic=True)
    for c in ws[head_row]:
        c.font = Font(bold=True, color='FFFFFF')
        c.fill = PatternFill('solid', fgColor='2F5233')
        c.alignment = Alignment(vertical='center', wrap_text=True)
    ws.freeze_panes = ws.cell(row=head_row + 1, column=1).coordinate
    ws.auto_filter.ref = f'A{head_row}:F{ws.max_row}'
    for col, w in zip('ABCDEF', (42, 11, 34, 70, 60, 20)):
        ws.column_dimensions[col].width = w
    for row in ws.iter_rows(min_row=head_row + 1):
        for c in row:
            c.alignment = Alignment(vertical='top', wrap_text=True)
    print(f'{name:24} {len(items):4}')

wb.save('/Users/matthewtobin/Downloads/Descriptions-To-Fix.xlsx')
print('total', sum(len(i) for _, _, i in tabs))
