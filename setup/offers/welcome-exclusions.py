"""Tag the products that must never be caught by the WELCOME10 discount.

  python3 setup/offers/welcome-exclusions.py            # dry run, reads only
  python3 setup/offers/welcome-exclusions.py --write    # tags, and writes the CSV

WHY THIS EXISTS. WELCOME10 is scoped to a smart collection of every product NOT
tagged `pharmacist-review`. That tag is the store's own definition of a medicine
(settings.restricted_tag -- the same tag the PDP gate, the sale grid and the
recommendation rails read), so the scoping is sound. The tagging is not.

On 1 Oct 2026, 217 published products sat in Medicines & Health without it, and
the tagging contradicted itself inside single brand families:

    Nelsons Arnicare 50G Cream            tagged
    Arnicare Arnica Cream 30G             NOT tagged
    Uniflu With Vitamin C Tablets 24Pk    tagged
    Uniflu Cough Stop                     NOT tagged

So `pharmacist-review` alone cannot be trusted to mean "this is a medicine"
until a pharmacist has been through it. `no-welcome-discount` is the second
lock: an explicit, discount-only exclusion that does not claim the product IS a
medicine, only that nobody has confirmed it is not. The collection excludes both
tags, so a product has to clear both to be discountable.

HOW THE LIST WAS DRAWN. All 217 were read, not sampled. The rule applied:

  EXCLUDED  anything instilled, ingested or applied to treat a condition where a
            licensed medicinal product is plausible -- eye and ear drops, nasal
            sprays, head-lice insecticides, haemorrhoid preparations, arnica,
            cold-sore and wart treatments, ingestible actives.
  KEPT      devices, diagnostics, dressings and cosmetics -- plasters, bandages,
            pillboxes, heat and ice packs, hearing-aid batteries, saline rinses,
            pregnancy and drug tests, lozenges sold as confectionery, emollients,
            anti-fog wipes.

The asymmetry is deliberate. Over-excluding costs one product 10% off and a line
on Fergal's sheet. Under-excluding discounts a medicine on a live pharmacy site.

THIS IS NOT THE FIX. It is a holding position until the real question is
answered, which is "should these be tagged pharmacist-review?" -- because if the
answer is yes for any of them, that product also needs the PDP questionnaire
gate, and that is a bigger defect than a discount. The CSV goes to Fergal with
that question attached.
"""
import csv
import json
import os
import subprocess
import sys

SHOP = 'mccormackpharmacy.myshopify.com'
DRY = '--write' not in sys.argv
TAG = 'no-welcome-discount'
HERE = os.path.dirname(os.path.abspath(__file__))
CSV_OUT = os.path.join(HERE, 'welcome-exclusions.csv')

# Exact product titles. Grouped by why, because the "why" is what Fergal is
# being asked to rule on.
EXCLUDE = {
    'named by the client (tagging contradicts itself within the brand)': [
        'Arnicare Arnica Cream 30G',
        'Nelsons Arnicare 50G Cream',
        'Nelsons Arnicare Cooling Gel 30G',
        'Uniflu Cough Stop',
        'Uniflu Immune Defence',
        'Uniflu With Vitamin C Tablets 24Pk',
        'Preparation H Gel 25G',
        'Preparation H Gel 50G',
        'Preparation H Ointment 25G',
    ],
    'instilled into the eye': [
        'Hylo Care 0.1%/2% Eye Drops 7.5Ml',
        'Hylo Dual Pres Free Eye Drops 7.5Ml 0.05%',
        'Hylo Night Ointment',
        'Hylo Tear 0.1% Eye Drops 7.5Ml',
        'Hylo-Forte Lubricating Eye Drops 7.5Ml',
        'Tears Naturale 15Ml Eye Drops',
        'Optase Allergy Eye Drop 0.5Mlsdu',
        'Thealoz Duo Gel 0.4G 30Pk',
        'Fusion Allergy Eye Drops',
        'Fusion Allergy Eye Spray 10Ml',
    ],
    'instilled into the ear': [
        'Cerumol Ear Drops',
        'Cerumol Olive Oil Ear Drops 10Ml',
        'Cl-Ear Ear Relief Drops',
        'Cl-Ear Express Dual Action Ear Drops',
        'Cl-Ear Olive Oil Ear Drops',
    ],
    'nasal or oral spray with an active': [
        'Fusion Allergy Nasal Spray 20Ml',
        'Fusion Allergy Lozenges 24',
        'Sreeze Nasal Spray 10Ml',
        'Sreeze Oral Strips 14Pk',
        'Gelorevoice Blackcurrant',
        'Gelorevoice Cherry',
    ],
    "filed under Children's Medicine": [
        'Kidsner Anti Allergic Spray',
        'Kidsner Cooling Foam For Chickenpox 100Ml',
        'Vamousse Head Lice Treatment Mousse',
        'Virasoothe Gel',
    ],
    'head-lice insecticide': [
        'Full Marks Solution 100Ml',
        'Full Marks Solution 200Ml',
    ],
    'treats a named condition; medicinal status unclear': [
        'Sorefix Rescue Cold Sore Cream',
        'Wartner Wart & Verruca Cryo Freeze Pen',
        'Papilocare Vaginal Gel',
        'Burnshield Hydrogel 50Ml',
        'Ultrapure Hydrogen Peroxide130ml',
        'Cydonia Soothing Arnica Ultra Gel 100Ml',
    ],
    'ingested active': [
        'Bloateze Tablets 20Pk Phoenix',
        'Celtic Wind Cbd Oil 5% 10Ml',
    ],
    'unidentified product, name suggests a medicine': [
        'Tramma Gel',
        'Nubit',
    ],
}


def gql(q, mutate=False):
    cmd = ['npx', 'shopify', 'store', 'execute', '-s', SHOP, '-q', q]
    if mutate:
        cmd.append('--allow-mutations')
    env = {**os.environ, 'CI': '1', 'SHOPIFY_CLI_NO_ANALYTICS': '1'}
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    for n, l in enumerate(r.stdout.splitlines()):
        if l.startswith('{'):
            d = json.loads('\n'.join(r.stdout.splitlines()[n:]), strict=False)
            break
    else:
        raise SystemExit(f'query failed:\n{r.stdout}\n{r.stderr}')
    if d.get('errors'):
        raise SystemExit(json.dumps(d['errors'], indent=1))
    return d.get('data', d)


want = {t: reason for reason, titles in EXCLUDE.items() for t in titles}
print(f'{len(want)} products to carry {TAG} | {"DRY RUN" if DRY else "WRITING"}')

# Pull the whole catalogue once and match on exact title. Matching by title query
# per product would be 46 round trips and would silently miss a renamed product;
# this way an unmatched title is visible and fails loudly.
found, cursor = {}, None
PUB = 'gid://shopify/Publication/341524873547'
while True:
    after = '' if cursor is None else ', after: %s' % json.dumps(cursor)
    d = gql('{ products(first: 250%s) { pageInfo { hasNextPage endCursor } nodes { '
            'id handle title productType tags '
            'publishedOnPublication(publicationId: "%s") } } }' % (after, PUB))['products']
    for n in d['nodes']:
        if n['title'] in want:
            found[n['title']] = n
    if not d['pageInfo']['hasNextPage']:
        break
    cursor = d['pageInfo']['endCursor']

missing = sorted(set(want) - set(found))
if missing:
    raise SystemExit('these titles matched no product -- fix the list rather than '
                     'skipping them:\n  ' + '\n  '.join(missing))

rows = []
for title, n in sorted(found.items()):
    tags = [t.strip().lower().replace(' ', '-') for t in n['tags']]
    rows.append({
        'title': title,
        'handle': n['handle'],
        'product_type': n['productType'] or '',
        'published_online_store': 'yes' if n['publishedOnPublication'] else 'no',
        'already_pharmacist_review': 'yes' if 'pharmacist-review' in tags else 'no',
        'already_no_welcome_discount': 'yes' if TAG in tags else 'no',
        'reason_excluded': want[title],
        'question_for_pharmacist': 'should this be tagged pharmacist-review?',
    })

todo = [r for r in rows if r['already_no_welcome_discount'] == 'no']
print(f'  matched {len(rows)}, already tagged {len(rows) - len(todo)}, to tag {len(todo)}')
print(f'  of these, {sum(1 for r in rows if r["already_pharmacist_review"] == "yes")} '
      'already carry pharmacist-review and were excluded anyway -- tagging them too so '
      'the exclusion survives if that tag is ever removed')

if DRY:
    for r in rows:
        print(f'    [{r["reason_excluded"][:38]:<38}] {r["title"]}')
    print('\ndry run: nothing written. Re-run with --write.')
    raise SystemExit(0)

for r in todo:
    gid = found[r['title']]['id']
    m = ('mutation { tagsAdd(id: %s, tags: [%s]) { userErrors { field message } } }'
         % (json.dumps(gid), json.dumps(TAG)))
    res = gql(m, mutate=True)['tagsAdd']
    if res.get('userErrors'):
        raise SystemExit(f'{r["title"]}: {res["userErrors"]}')
    print(f'  tagged {r["handle"]}')

with open(CSV_OUT, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print(f'\nwrote {CSV_OUT} ({len(rows)} rows)')
