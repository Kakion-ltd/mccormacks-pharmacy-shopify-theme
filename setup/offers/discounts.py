"""Create the two collections the multi-buy discounts scope to, and the eight
automatic discounts that make the old site's multi-buy offers real.

  python3 setup/offers/discounts.py           # dry run, reads only
  python3 setup/offers/discounts.py --write   # writes

Why Buy X get Y and not a percentage off with a minimum quantity. Shopify has no
"N for a fixed price" discount. A flat percentage with a minimum quantity of 3
gets the exact multiples right and everything else wrong: a 4th item would be
discounted too, so 4 items cost 13.34 where the offer says 13.99. Buy X get Y
only discounts the "get" item once the "buy" quantity is met, so remainders are
charged in full and the arithmetic holds at 3, 4, 5 and 6. The percentages below
are therefore "the discount on the last item", not the saving on the basket:

    3 for 10.00 at 3.99  ->  buy 2 (7.98) + 1 at 49.45% off (2.02)  = 10.00
    3 for  5.00 at 1.99  ->  buy 2 (3.98) + 1 at 48.89% off (1.02)  =  5.00
    2 for  7.00 at 4.89  ->  buy 1 (4.89) + 1 at 56.91% off (2.11)  =  7.00
    2 for 52.45 at 36.99 ->  buy 1 (36.99)+ 1 at 58.21% off (15.46) = 52.45
    4 for  3.00 at 1.50  ->  buy 2 (3.00) + 2 free                  =  3.00

**Shopify truncates the per-line discount to the cent, it does not round it.**
The percentages above are a hair higher than the arithmetic needs for exactly
that reason. The obvious values were one notch lower (49.37% for the first, the
saving divided by the price) and every fixed-price offer then came out a cent
high: 3.99 x 0.4937 = 1.96986, truncated to 1.96, so "3 for EUR 10" charged
10.01. A cent, and the label makes a promise about the total. If a price in one
of these sets ever changes, recompute: aim the product a little past the cent
boundary, do not just divide.

usesPerOrderLimit is deliberately unset on all of them. The mitt offer is "for
every Tan Studio item ordered", and 6 of a 3-for-10 product should be 20.00, not
one discounted trio and three at full price.

The two collections exist only to scope a discount; they are not published to
the Online Store and nothing links to them. See MAINTENANCE.md, "Unlinked store
collections deleted" — these are the exception and say so in their description.
"""
import json, subprocess, sys

SHOP = 'mccormackpharmacy.myshopify.com'
DRY = '--write' not in sys.argv
STARTS = '2026-09-30T00:00:00Z'


def gql(q, mutate=False):
    cmd = ['npx', 'shopify', 'store', 'execute', '-s', SHOP, '-q', q]
    if mutate:
        cmd.append('--allow-mutations')
    r = subprocess.run(cmd, capture_output=True, text=True)
    try:
        d = json.loads(r.stdout, strict=False)
    except Exception:
        raise SystemExit(f'query failed:\n{r.stdout}\n{r.stderr}')
    return d.get('data', d)


def gid(handle):
    q = '{ products(first: 2, query: "handle:%s") { nodes { id handle } } }' % handle
    hits = [n for n in gql(q)['products']['nodes'] if n['handle'] == handle]
    if len(hits) != 1:
        raise SystemExit(f'{handle}: {len(hits)} products match')
    return hits[0]['id']


COLLECTIONS = [
    ('3 for €10', '3-for-10', 'Clearance > 3 for €10'),
    ('3 for €5', '3-for-5', 'Clearance > 3 FOR €5'),
]
DESC = ('<p>Scopes the &quot;%s&quot; automatic discount. Not published and not '
        'linked from anywhere: deleting it silently switches the offer off. The '
        'membership is the tag, so adding the tag to a product adds it to the '
        'offer.</p>')

# title, buy qty, buy set, get qty, get set, percentage off the "get" item
DISCOUNTS = [
    ('3 for €10',                                     2, ('coll', '3-for-10'),
     1, ('coll', '3-for-10'), 0.4945),
    ('3 for €5',                                      2, ('coll', '3-for-5'),
     1, ('coll', '3-for-5'), 0.4889),
    ('Buy 2 for €7 — Batiste',                   1, ('prod', [
        'batiste-dry-shampoo-tropical-200ml', 'batiste-200ml-blush-dry-shampoo']),
     1, ('same', None), 0.5691),
    ('2 for €52.45 — Revive Zest Active',         1, ('prod', [
        'revive-active-zest-active-ages-20-35-30pk']),
     1, ('same', None), 0.5821),
    ('Buy 4 for €3 — BioMiracle wipes',           2, ('prod', [
        'biomiracle-staysafe-hand-cleansing-towlettes-20pk']),
     2, ('same', None), 1.0),
    ('Buy one, get one half price — Revive Active',    1, ('prod', [
        'revive-active-original-30pk', 'revive-active-meno-active',
        'revive-active-joint-complex-30pk']),
     1, ('same', None), 0.5),
    ('Buy one, get one half price — Mitchum',          1, ('prod', [
        'mitchum-roll-on-shwr-frsh-100ml']),
     1, ('same', None), 0.5),
    ('Free tanning mitt with every Tan Studio item',        1, ('prod', [
        'bperfect-tan-studio-tanning-mousse-ultra-dark-200ml',
        'bperfect-tan-studio-self-tanning-body-butter-dark-200ml',
        'bperfect-tan-studio-tanning-liquid-dark-175ml',
        'bperfect-tan-studio-self-tanning-oil-medium-150ml',
        'bperfect-tan-studio-tanning-facial-mist-light-medium-150ml',
        'bperfect-tan-studio-instant-aerosol-tan-ultra-dark-125ml',
        'bperfect-tan-studio-instant-aerosol-tan-medium-125ml',
        'bperfect-tan-studio-instant-aerosol-tan-dark-125ml']),
     1, ('prod', ['bperfect-double-sided-luxury-velvet-tanning-mitt']), 1.0),
]

print('2 collections, %d discounts | %s' % (len(DISCOUNTS), 'DRY RUN' if DRY else 'WRITING'))

# ------------------------------------------------------------------ collections
coll_gid = {}
for title, handle, tag in COLLECTIONS:
    have = gql('{ collections(first: 2, query: "handle:%s") { nodes { id handle '
               'productsCount { count } } } }' % handle)['collections']['nodes']
    have = [c for c in have if c['handle'] == handle]
    if have:
        coll_gid[handle] = have[0]['id']
        print(f'  collection {handle}: already there, '
              f'{have[0]["productsCount"]["count"]} products')
        continue
    n = len(gql('{ products(first: 250, query: %s) { nodes { id } } }'
                % json.dumps(f'tag:"{tag}"'))['products']['nodes'])
    print(f'  collection {handle}: to create, tag matches {n} products')
    if DRY:
        continue
    m = ('mutation { collectionCreate(input: {title: %s, handle: %s, '
         'descriptionHtml: %s, ruleSet: {appliedDisjunctively: false, rules: '
         '[{column: TAG, relation: EQUALS, condition: %s}]}}) '
         '{ collection { id handle productsCount { count } } '
         'userErrors { field message } } }'
         % (json.dumps(title), json.dumps(handle), json.dumps(DESC % title),
            json.dumps(tag)))
    res = gql(m, mutate=True)['collectionCreate']
    if res.get('userErrors'):
        raise SystemExit(f'collection {handle} failed: {res["userErrors"]}')
    coll_gid[handle] = res['collection']['id']
    print(f'  collection {handle}: created, '
          f'{res["collection"]["productsCount"]["count"]} products')

# ------------------------------------------------------------------- discounts
def items(spec, fallback=None):
    kind, val = spec
    if kind == 'same':
        return items(fallback)
    if kind == 'coll':
        return '{collections: {add: [%s]}}' % json.dumps(coll_gid[val])
    return '{products: {productsToAdd: [%s]}}' % ', '.join(
        json.dumps(gid(h)) for h in val)


live = {n['automaticDiscount']['title']
        for n in gql('{ automaticDiscountNodes(first: 100) '
                     '{ nodes { automaticDiscount { ... on DiscountAutomaticBxgy '
                     '{ title } } } } }')['automaticDiscountNodes']['nodes']
        if n['automaticDiscount'].get('title')}

made = skipped = 0
for title, bq, bset, gq, gset, pct in DISCOUNTS:
    if title in live:
        print(f'  SKIP  {title[:46]:48} already on the store')
        skipped += 1
        continue
    print(f'  {"would create" if DRY else "create"}  {title[:44]:46} '
          f'buy {bq} get {gq} at {pct * 100:.2f}%')
    if DRY:
        made += 1
        continue
    m = ('mutation { discountAutomaticBxgyCreate(automaticBxgyDiscount: {'
         'title: %s, startsAt: "%s", '
         'combinesWith: {productDiscounts: true}, '
         'customerBuys: {value: {quantity: "%d"}, items: %s}, '
         'customerGets: {value: {discountOnQuantity: {quantity: "%d", '
         'effect: {percentage: %s}}}, items: %s}}) '
         '{ automaticDiscountNode { id } userErrors { field message code } } }'
         % (json.dumps(title), STARTS, bq, items(bset), gq, repr(pct),
            items(gset, bset)))
    res = gql(m, mutate=True)['discountAutomaticBxgyCreate']
    if res.get('userErrors'):
        raise SystemExit(f'{title} failed: {res["userErrors"]}')
    made += 1

print(f'\n{made} discounts {"planned" if DRY else "created"}, {skipped} already there')
