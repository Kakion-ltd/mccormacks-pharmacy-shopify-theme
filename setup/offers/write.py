"""Put the old site's current offers on the store: compare-at prices, the Sale
tag, six corrected prices, the promo-label metafield, and the Electric Picnic
tag removal.

The plan is setup/old-site-offers.csv. Nothing here decides what an offer is;
that was matched and agreed first (MAINTENANCE.md, and the CSV's own columns).

Follows the rule in MAINTENANCE.md, "The store has no worktree": every product
is re-read immediately before it is written and skipped if it differs from what
the plan expected, before-state goes to a log, and every product is re-read
after. Read-only unless --write is passed.

  python3 setup/offers/write.py              # dry run, reads only
  python3 setup/offers/write.py --write      # writes

Scope, and what is deliberately left alone:
  - 89 products get compareAtPrice = the old site's was-price, and the Sale tag.
    Six of those also get the price corrected to the old site's current price.
  - 71 products get custom.promo_label.
  - Electric Picnic Bundle loses the Sale tag.
  - The two Sculpted By Aimee bundles are in the plan's group 1 but are not on
    this store, so they cannot be written. They are Keelan's call (row 16 of the
    confirmation table), along with groups 11-16. Nothing here touches them.
  - The 24 multi-buy products get a label and nothing else: they have no
    was-price on the old site, so a compare-at would be a saving nobody offered,
    and snippets/product-compare-at.liquid would refuse to draw it anyway.
"""
import csv, json, os, subprocess, sys

SHOP = 'mccormackpharmacy.myshopify.com'
DRY = '--write' not in sys.argv
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARCHIVE = os.path.join(ROOT, 'archive', 'store-offers-2026-09-30')

# The labels as approved: no all-caps, no "!!!", sentence case.
TIDY = {
    'While Stocks Last!': 'While stocks last', 'WHILE STOCKS LAST': 'While stocks last',
    'WHILE STOCKS LAST!': 'While stocks last', 'LIMITED TIME ONLY': 'Limited time only',
    'Limited Time Only!': 'Limited time only', 'LIMITED TIME OFFER': 'Limited time offer',
    '3 for €10': '3 for €10', '3 for €5': '3 for €5',
    'Buy 2 for €7 !': 'Buy 2 for €7', 'Buy 4 for €3 !': 'Buy 4 for €3',
    '2 for €52.45': '2 for €52.45',
    'Buy One get one Half Price !': 'Buy one, get one half price',
    'revive Buy 1 get 1 Half Price': 'Buy one, get one half price',
    '20% Off Azio Beauty': '20% off Azio Beauty',
    '50% Off Selected Suncreams !': '50% off selected suncreams',
    '€5 OFF WHILE STOCKS LAST!': '€5 off while stocks last',
    'Free Tanning Mitt for every Bperfect Tan Studio Item Ordered':
        'Free tanning mitt with every Tan Studio item',
    'SAVE OVER €100': 'Save over €100', 'SAVE OVER €50!!!': 'Save over €50',
    'SAVING OVER €150': 'Save over €150', 'Save €50': 'Save €50',
    'Very Limited Quantities Available !': 'Very limited quantities',
    'Limited Availability !': 'Limited availability',
}


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


def money(x):
    return f'{float(x):.2f}'


def errs(res, key):
    return (res.get(key) or {}).get('userErrors') or []


# ---------------------------------------------------------------- build the plan
rows = list(csv.DictReader(open(os.path.join(ROOT, 'setup', 'old-site-offers.csv'),
                                encoding='utf-8')))
# The product id is not in the CSV, so it is looked up by the handle the match
# recorded. Looked up here rather than carried in a snapshot file, so the script
# stays runnable on its own; the guards below are what actually protect the write.
def id_for(handle):
    q = '{ products(first: 2, query: "handle:%s") { nodes { id handle } } }' % handle
    hits = [n for n in gql(q)['products']['nodes'] if n['handle'] == handle]
    if len(hits) != 1:
        raise SystemExit(f'{handle}: {len(hits)} products match that handle')
    return hits[0]['id']

plan = []
for r in rows:
    if not r['store_handle']:
        continue                                    # not on this store: Keelan's call
    g1 = r['group'].startswith('1-')
    g2 = r['group'].startswith('2-')
    electric = 'electric-picnic' in r['store_handle']
    if not (g1 or g2 or electric):
        continue                                    # groups 3 and 4: Keelan's call
    label = TIDY[r['promo_label']] if r['promo_label'] else None
    if r['promo_label'] and r['promo_label'] not in TIDY:
        raise SystemExit(f'no approved wording for {r["promo_label"]!r}')
    plan.append({
        'id': id_for(r['store_handle']), 'handle': r['store_handle'], 'title': r['store_title'],
        'expect_price': money(r['store_price']),
        'set_price': money(r['sale_price']) if g1 else None,
        'set_compare': money(r['old_price']) if g1 and r['old_price'] else None,
        'add_sale_tag': g1, 'remove_sale_tag': electric, 'label': label,
    })

n_price = sum(1 for x in plan if x['set_price'] and x['set_price'] != x['expect_price'])
print(f'{len(plan)} products | {sum(1 for x in plan if x["set_compare"])} compare-at'
      f' | {n_price} price changes | {sum(1 for x in plan if x["label"])} labels'
      f' | {sum(1 for x in plan if x["remove_sale_tag"])} tag removal'
      f' | {"DRY RUN" if DRY else "WRITING"}')

# ------------------------------------------------------- the metafield definition
DEF = ('{ metafieldDefinitions(first: 1, ownerType: PRODUCT, namespace: "custom",'
       ' key: "promo_label") { nodes { id } } }')
if not gql(DEF)['metafieldDefinitions']['nodes']:
    print('metafield definition custom.promo_label: missing')
    if not DRY:
        m = ('mutation { metafieldDefinitionCreate(definition: {name: "Promo label",'
             ' namespace: "custom", key: "promo_label",'
             ' type: "single_line_text_field", ownerType: PRODUCT, description: %s})'
             ' { createdDefinition { id } userErrors { field message code } } }'
             % json.dumps('The offer line a product card shows beside the price, '
                          'e.g. "3 for €10". Nothing dates it; clear it when the '
                          'offer ends.'))
        res = gql(m, mutate=True)
        if errs(res, 'metafieldDefinitionCreate'):
            raise SystemExit(f'definition failed: {errs(res, "metafieldDefinitionCreate")}')
        print('metafield definition custom.promo_label: created')
else:
    print('metafield definition custom.promo_label: already present')

# ------------------------------------------------------------------- the writes
READ = ('{ product(id: "%s") { id handle title tags'
        ' variants(first: 2) { nodes { id price compareAtPrice } }'
        ' metafield(namespace: "custom", key: "promo_label") { value } } }')

os.makedirs(ARCHIVE, exist_ok=True)
log = open(os.path.join(ARCHIVE, 'write-log.jsonl'), 'a', encoding='utf-8')
ok = skipped = failed = 0

for x in plan:
    live = gql(READ % x['id'])['product']
    vs = live['variants']['nodes']
    before = {'handle': live['handle'], 'title': live['title'], 'tags': live['tags'],
              'price': vs[0]['price'], 'compareAtPrice': vs[0]['compareAtPrice'],
              'promo_label': (live.get('metafield') or {}).get('value')}

    why = None
    if live['handle'] != x['handle']:
        why = f'handle is {live["handle"]}, plan says {x["handle"]}'
    elif len(vs) != 1:
        why = f'{len(vs)} variants; the plan assumes one'
    elif money(vs[0]['price']) != x['expect_price']:
        why = f'price is {vs[0]["price"]}, plan expected {x["expect_price"]}'
    elif x['set_compare'] and vs[0]['compareAtPrice']:
        why = f'compare-at already set to {vs[0]["compareAtPrice"]}'
    if why:
        print(f'SKIP  {x["handle"][:44]:46} {why}')
        log.write(json.dumps({'handle': x['handle'], 'skipped': why,
                              'before': before}, ensure_ascii=False) + '\n')
        skipped += 1
        continue

    log.write(json.dumps({'handle': x['handle'], 'id': x['id'], 'before': before,
                          'plan': x}, ensure_ascii=False) + '\n')
    log.flush()
    if DRY:
        ok += 1
        continue

    bad = []
    # price and compare-at
    fields = []
    if x['set_price'] and x['set_price'] != before['price']:
        fields.append(f'price: "{x["set_price"]}"')
    if x['set_compare']:
        fields.append(f'compareAtPrice: "{x["set_compare"]}"')
    if fields:
        m = ('mutation { productVariantsBulkUpdate(productId: "%s", variants: '
             '[{id: "%s", %s}]) { productVariants { id price compareAtPrice }'
             ' userErrors { field message } } }' % (x['id'], vs[0]['id'], ', '.join(fields)))
        bad += errs(gql(m, mutate=True), 'productVariantsBulkUpdate')
    # the Sale tag
    if x['add_sale_tag'] and 'Sale' not in live['tags']:
        m = ('mutation { tagsAdd(id: "%s", tags: ["Sale"]) { node { id }'
             ' userErrors { field message } } }' % x['id'])
        bad += errs(gql(m, mutate=True), 'tagsAdd')
    if x['remove_sale_tag'] and 'Sale' in live['tags']:
        m = ('mutation { tagsRemove(id: "%s", tags: ["Sale"]) { node { id }'
             ' userErrors { field message } } }' % x['id'])
        bad += errs(gql(m, mutate=True), 'tagsRemove')
    # the promo label
    if x['label'] and x['label'] != before['promo_label']:
        m = ('mutation { metafieldsSet(metafields: [{ownerId: "%s", namespace: "custom",'
             ' key: "promo_label", type: "single_line_text_field", value: %s}])'
             ' { metafields { id } userErrors { field message } } }'
             % (x['id'], json.dumps(x['label'])))
        bad += errs(gql(m, mutate=True), 'metafieldsSet')

    after_live = gql(READ % x['id'])['product']       # re-read, always
    av = after_live['variants']['nodes'][0]
    after = {'tags': after_live['tags'], 'price': av['price'],
             'compareAtPrice': av['compareAtPrice'],
             'promo_label': (after_live.get('metafield') or {}).get('value')}
    log.write(json.dumps({'handle': x['handle'], 'after': after,
                          'userErrors': bad}, ensure_ascii=False) + '\n')
    log.flush()

    # did the re-read actually show what was asked for?
    wrong = []
    if x['set_price'] and money(after['price']) != x['set_price']:
        wrong.append(f'price {after["price"]}')
    if x['set_compare'] and money(after['compareAtPrice'] or 0) != x['set_compare']:
        wrong.append(f'compare-at {after["compareAtPrice"]}')
    if x['add_sale_tag'] and 'Sale' not in after['tags']:
        wrong.append('no Sale tag')
    if x['remove_sale_tag'] and 'Sale' in after['tags']:
        wrong.append('Sale tag still there')
    if x['label'] and after['promo_label'] != x['label']:
        wrong.append(f'label {after["promo_label"]!r}')
    if bad or wrong:
        print(f'FAIL  {x["handle"][:44]:46} {bad} {"; ".join(wrong)}')
        failed += 1
    else:
        print(f'ok    {x["handle"][:44]:46} {after["price"]}'
              f'{" was " + after["compareAtPrice"] if after["compareAtPrice"] else ""}'
              f'{"  " + after["promo_label"] if after["promo_label"] else ""}')
        ok += 1

print(f'\n{ok} ok, {skipped} skipped, {failed} failed'
      f'{" (dry run: nothing written)" if DRY else ""}')
sys.exit(1 if failed else 0)
