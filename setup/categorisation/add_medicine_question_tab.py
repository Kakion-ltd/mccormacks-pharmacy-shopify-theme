"""Add the "Is this a medicine?" tab to Fergal-Pharmacist-Calls.xlsx.

The 46 products held out of the WELCOME10 discount, with the question that
actually matters attached: should each be tagged pharmacist-review?

Source of truth is setup/offers/welcome-exclusions.csv, written by
setup/offers/welcome-exclusions.py when it applied the tags. This script only
formats; re-running it replaces the tab rather than appending a second copy.

Formatting follows the workbook's existing "Veterinary products" tab: bold title
in row 1, a wrapped note in row 2, blank row 3, headers in row 4, data from row
5, wrapped text throughout, and the columns Fergal fills in filled FFF2A8. The
one deliberate difference is the frozen pane: that tab freezes at A4, which
scrolls its own header off the screen, so this one freezes at A5 and keeps the
header in view over 46 rows.
"""
import csv
import os
import shutil

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill

HERE = os.path.dirname(os.path.abspath(__file__))
BOOK = os.path.join(HERE, 'Fergal-Pharmacist-Calls.xlsx')
ROWS = os.path.join(HERE, '..', 'offers', 'welcome-exclusions.csv')
# "Is this a medicine?" without the question mark: Excel forbids ? \ / * [ ] : in a
# sheet name and openpyxl refuses it outright. The question mark survives in the
# title row and in the column F header, where it reads as a question anyway.
TAB = 'Is this a medicine'
YELLOW = PatternFill('solid', start_color='FFF2A8', end_color='FFF2A8')
WRAP = Alignment(wrap_text=True, vertical='top')

NOTE = ("These 46 products are in Medicines & Health but are not tagged pharmacist-review, "
        "so the store does not treat them as medicines: no questions before purchase, and "
        "they would be discountable. We could not confirm they are not medicines, so they "
        "are held out of the WELCOME10 welcome discount by a second tag, no-welcome-discount. "
        "That tag is a holding position, not an answer. The question is column F. If any of "
        "these should be pharmacist-review, it needs the questions before purchase as well, "
        "which matters more than the discount.")

TRIGGER = ("The tagging disagrees with itself inside brands, which is why this tab exists: "
           "Nelsons Arnicare 50G Cream is tagged and Arnicare Arnica Cream 30G is not; "
           "Uniflu With Vitamin C Tablets 24Pk is tagged and Uniflu Cough Stop is not.")

HEADERS = ['Product', 'Type now', 'pharmacist-review now?', 'Why we held it',
           'Should this be pharmacist-review?', 'Your notes']
WIDTHS = {'A': 46.0, 'B': 32.0, 'C': 22.0, 'D': 46.0, 'E': 30.0, 'F': 34.0}
INPUT_COLS = ('E', 'F')

rows = list(csv.DictReader(open(ROWS)))
assert rows, 'welcome-exclusions.csv is empty'

wb = openpyxl.load_workbook(BOOK)
if TAB in wb.sheetnames:
    del wb[TAB]
ws = wb.create_sheet(TAB)

ws['A1'] = f'{len(rows)} products held out of the welcome discount, pending a pharmacist call'
ws['A1'].font = Font(bold=True)
ws['A2'] = NOTE
ws['A2'].alignment = WRAP
ws['A3'] = TRIGGER
ws['A3'].alignment = WRAP

for col, h in zip('ABCDEF', HEADERS):
    c = ws[f'{col}5']
    c.value = h
    c.alignment = WRAP
    if col in INPUT_COLS:
        c.fill = YELLOW

for n, r in enumerate(sorted(rows, key=lambda x: x['title']), start=6):
    ws[f'A{n}'] = r['title']
    ws[f'B{n}'] = r['product_type']
    ws[f'C{n}'] = r['already_pharmacist_review']
    ws[f'D{n}'] = r['reason_excluded']
    for col in 'ABCDEF':
        ws[f'{col}{n}'].alignment = WRAP
    for col in INPUT_COLS:
        ws[f'{col}{n}'].fill = YELLOW

for col, w in WIDTHS.items():
    ws.column_dimensions[col].width = w
ws.freeze_panes = 'A6'

wb.save(BOOK)
print(f'{BOOK}: tabs now {wb.sheetnames}')
print(f'  "{TAB}": {len(rows)} products, headers row 5, data rows 6-{5 + len(rows)}')

dest = os.path.expanduser('~/Downloads/Fergal-Pharmacist-Calls.xlsx')
shutil.copy2(BOOK, dest)
print(f'copied to {dest}')
