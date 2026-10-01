"""Create the welcome-discount collection and the WELCOME10 code.

  python3 setup/offers/welcome-discount.py           # dry run, reads only
  python3 setup/offers/welcome-discount.py --write   # writes
  python3 setup/offers/welcome-discount.py --write --medicines-audited   # ... after reading the audit

NOT RUN YET. Held pending sign-off (1 Oct 2026). The dry run is safe and is the
thing to look at first: it prints how many published products land in the
collection and, more importantly, how many medicines would.

----------------------------------------------------------------- the collection

"Welcome discount eligible" is every product NOT tagged `pharmacist-review`,
expressed as a one-rule smart collection (TAG NOT_EQUALS). The discount is
scoped to it, so a medicine can never be discounted by WELCOME10.

That safety property rests entirely on the tag. The collection does not know
what a medicine is; it knows what is tagged. If a pharmacy-only product ships
without `pharmacist-review`, it lands in this collection and becomes
discountable, and nothing here will say so. Hence the audit in the dry run:
it lists products that look like medicines (gated, or in a medicines
collection) but carry no `pharmacist-review` tag. Read that list before
--write. At the last count it was 327 tagged and 2021 untagged of 2348 published, with 217
of the untagged sitting in Medicines & Health -- pillboxes, plasters, ice packs and
supports, which are correctly discountable. `pharmacist-review` IS the store's
definition of a medicine (settings.restricted_tag, the same tag the PDP gate, the
sale grid and the recommendation rails read), so the collection and the gate cannot
disagree about what a medicine is. The audit exists to catch a medicine that is
missing its tag, which is a tagging defect rather than a scoping one, and --write
refuses until someone confirms they read the list.

Shopify folds case, accents and punctuation when it matches a tag rule, so
`NOT_EQUALS "pharmacist-review"` also excludes `Pharmacist Review` and
`pharmacist review`. That is the safe direction -- it over-excludes, never
under-excludes -- but it is undocumented, so the dry run asserts it against a
real product rather than trusting it. See MAINTENANCE.md, "Shopify folds
punctuation when it stores a tag".

The collection is published to the Online Store: a customer who clicks through
from the discount needs to be able to see what is in it.

------------------------------------------------------------------- the discount

WELCOME10, 10% off, scoped to that collection, one use per customer, no end
date, does not combine with other product discounts.

ON "first order", which is what the footer and the signup message promise.
Shopify cannot enforce that for guest checkout, and this store has guest
checkout on:

  * `appliesOncePerCustomer` is enforced against the customer record Shopify
    matches from the checkout email. It works, and a second email defeats it.
    This is the closest honest mechanism and it is what we use.

  * Restricting to a "zero previous orders" customer segment DOES exist on the
    Basic plan -- segments are not a plan-gated feature -- but segment
    membership is evaluated against a known customer. A guest has no customer
    record when the code is applied, so the code is refused outright rather
    than allowed. The practical effect is not "first-time buyers only", it is
    "logged-in account holders only", which rejects most of the people the
    offer is aimed at. Deliberately not used. If it is ever wanted, it is
    `customerSelection: {customerSegments: [...]}` and the copy has to change
    with it.

So the promise is one-per-customer, not one-per-person. That was a decision,
not an oversight.
"""
import json
import os
import subprocess
import sys

SHOP = 'mccormackpharmacy.myshopify.com'
DRY = '--write' not in sys.argv

HANDLE = 'welcome-discount-eligible'
TITLE = 'Welcome discount eligible'
TAG = 'pharmacist-review'
# Second lock. `pharmacist-review` is the store's definition of a medicine, but on
# 1 Oct 2026 it contradicted itself inside brand families (Nelsons Arnicare tagged,
# Arnicare Arnica Cream not; Uniflu With Vitamin C tagged, Uniflu Cough Stop not).
# `no-welcome-discount` is an explicit discount-only exclusion for the 46 products
# nobody could clear -- see setup/offers/welcome-exclusions.py, which applies it and
# writes the CSV that asks Fergal whether they should be pharmacist-review instead.
# A product has to clear BOTH tags to be discountable.
EXCL_TAG = 'no-welcome-discount'
CODE = 'WELCOME10'
PERCENT = 0.10
DESC = ('<p>Scopes the WELCOME10 newsletter discount: every product tagged neither '
        '<code>pharmacist-review</code> nor <code>no-welcome-discount</code>. Medicines '
        'carry the first, so they are excluded and WELCOME10 can never discount one. The '
        'second is for products nobody could confirm are not medicines -- eye and ear '
        'drops, head-lice treatments, arnica, haemorrhoid preparations -- held out of the '
        'offer until a pharmacist rules on them. The membership is the tags: adding '
        'either to a product removes it from the offer, removing both adds it. Do not '
        'delete this collection, and do not loosen it to one rule: the discount is scoped '
        'to it, and either change silently widens the offer.</p>')


def gql(q, mutate=False):
    cmd = ['npx', 'shopify', 'store', 'execute', '-s', SHOP, '-q', q]
    if mutate:
        cmd.append('--allow-mutations')
    env = {**os.environ, 'CI': '1', 'SHOPIFY_CLI_NO_ANALYTICS': '1'}
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    lines = r.stdout.splitlines()
    for n, l in enumerate(lines):
        if l.startswith('{'):
            body = '\n'.join(lines[n:])
            break
    else:
        raise SystemExit(f'query failed:\n{r.stdout}\n{r.stderr}')
    d = json.loads(body, strict=False)
    if d.get('errors'):
        raise SystemExit(json.dumps(d['errors'], indent=1))
    return d.get('data', d)


PUB_ONLINE_STORE = 'gid://shopify/Publication/341524873547'

print('welcome discount | %s' % ('DRY RUN' if DRY else 'WRITING'))

# ------------------------------------------------------------------ the audit
# Counted from collection membership and the publication flag, not from
# productsCount: that field flaps -- it has read 0 for a collection whose products
# the same query listed. See MAINTENANCE.md.
tagged = untagged = 0
suspect = []
cursor = None
while True:
    after = '' if cursor is None else ', after: %s' % json.dumps(cursor)
    d = gql('{ products(first: 250%s) { pageInfo { hasNextPage endCursor } nodes { '
            'handle title tags publishedOnPublication(publicationId: "%s") '
            'collections(first: 60) { nodes { handle } } } } }' % (after, PUB_ONLINE_STORE))['products']
    for n in d['nodes']:
        if not n['publishedOnPublication']:
            continue
        norm = [t.strip().lower().replace(' ', '-') for t in n['tags']]
        if TAG in norm or EXCL_TAG in norm:
            tagged += 1
            continue
        untagged += 1
        # a product in a medicines collection but with no pharmacist-review tag is
        # exactly the case that would let a medicine into the discount
        cols = {c['handle'] for c in n['collections']['nodes']}
        if 'medicines-health' in cols:  # untagged by BOTH tags, and in Medicines & Health
            suspect.append((n['handle'], sorted(cols & {'medicines-health', 'erectile-dysfunction',
                                                        'nicotine-replacement', 'pain-relief'})))
    if not d['pageInfo']['hasNextPage']:
        break
    cursor = d['pageInfo']['endCursor']

print(f'  published products: {tagged + untagged}')
print(f'  tagged {TAG}: {tagged}  (excluded from the discount)')
print(f'  untagged: {untagged}  (in the collection, discountable)')
print(f'  in Medicines & Health but NOT tagged {TAG}: {len(suspect)}')
for h, cols in suspect[:40]:
    print(f'      {h}  {cols}')
if len(suspect) > 40:
    print(f'      ... and {len(suspect) - 40} more')
print(f'\n  These are not necessarily medicines. `{TAG}` IS the store\'s definition of a\n'
      '  medicine -- settings.restricted_tag in config/settings_data.json, the same tag the\n'
      '  PDP gate, the sale grid and the recommendation rails all read. Medicines & Health\n'
      '  also holds pillboxes, plasters, ice packs and supports, which are correctly\n'
      '  discountable. The list is here to be read, not to be feared: what matters is\n'
      '  whether anything on it is a medicine that is missing its tag.')
if suspect and not DRY and '--medicines-audited' not in sys.argv:
    raise SystemExit(f'\nSTOPPING: {len(suspect)} products sit in Medicines & Health without the '
                     f'{TAG} tag.\nRead the list above. Any medicine on it would be discounted by '
                     f'{CODE}.\nIf they are all sundries, re-run with --medicines-audited to '
                     'confirm you looked.')

# ------------------------------------------------------------------ collection
have = [c for c in gql('{ collections(first: 2, query: "handle:%s") { nodes { id handle } } }'
                       % HANDLE)['collections']['nodes'] if c['handle'] == HANDLE]
if have:
    coll_gid = have[0]['id']
    print(f'  collection {HANDLE}: already there')
else:
    print(f'  collection {HANDLE}: to create')
    coll_gid = None
    if not DRY:
        m = ('mutation { collectionCreate(input: {title: %s, handle: %s, descriptionHtml: %s, '
             'ruleSet: {appliedDisjunctively: false, rules: '
             '[{column: TAG, relation: NOT_EQUALS, condition: %s}, '
             '{column: TAG, relation: NOT_EQUALS, condition: %s}]}}) '
             '{ collection { id handle } userErrors { field message } } }'
             % (json.dumps(TITLE), json.dumps(HANDLE), json.dumps(DESC),
                json.dumps(TAG), json.dumps(EXCL_TAG)))
        res = gql(m, mutate=True)['collectionCreate']
        if res.get('userErrors'):
            raise SystemExit(f'collection failed: {res["userErrors"]}')
        coll_gid = res['collection']['id']
        print(f'  collection {HANDLE}: created {coll_gid}')

# -------------------------------------------------------------------- discount
existing = gql('{ codeDiscountNodeByCode(code: %s) { id } }' % json.dumps(CODE))
if existing.get('codeDiscountNodeByCode'):
    print(f'  discount {CODE}: already there, leaving it alone')
elif DRY:
    print(f'  discount {CODE}: to create -- {int(PERCENT * 100)}% off {HANDLE}, '
          'once per customer, no end date, does not combine with other product discounts')
else:
    m = ('mutation { discountCodeBasicCreate(basicCodeDiscount: {'
         'title: %s, code: %s, startsAt: %s, appliesOncePerCustomer: true, '
         'customerSelection: {all: true}, '
         'combinesWith: {productDiscounts: false, orderDiscounts: true, shippingDiscounts: true}, '
         'customerGets: {value: {percentage: %s}, items: {collections: {add: [%s]}}}'
         '}) { codeDiscountNode { id } userErrors { field message } } }'
         % (json.dumps(f'{int(PERCENT * 100)}% off first order'), json.dumps(CODE),
            json.dumps('2026-10-01T00:00:00Z'), PERCENT, json.dumps(coll_gid)))
    res = gql(m, mutate=True)['discountCodeBasicCreate']
    if res.get('userErrors'):
        raise SystemExit(f'discount failed: {res["userErrors"]}')
    print(f'  discount {CODE}: created {res["codeDiscountNode"]["id"]}')

print('\nAfter writing, test on the live store (setup/verify/NEEDS-A-STORE.md):')
print('  1. a non-medicine in the bag  -> WELCOME10 takes 10% off it')
print('  2. a medicine in the same bag -> that line is NOT discounted')
print('  3. the same customer, second order -> the code is refused')
