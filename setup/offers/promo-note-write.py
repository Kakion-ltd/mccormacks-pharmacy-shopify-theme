"""Set custom.promo_note on the eight BPerfect Tan Studio products in the free
tanning mitt offer, and create the definition if it is missing.

  python3 setup/offers/promo-note-write.py            # dry run
  python3 setup/offers/promo-note-write.py --write

The sentence exists because a free gift is only free once it is in the bag:
Shopify discounts a gift at the cart and never puts it there, so a customer who
reads "Free tanning mitt with every Tan Studio item" and buys only the tan gets
no mitt and no explanation. The old site has the same gap; this closes it on
ours without automating the add, which was the client's call.

Rich text rather than plain, so the link to the mitt travels with the copy
instead of being assembled in Liquid. The value is setup/offers/promo-note.json,
one file for all eight, so the wording is edited in one place.

Re-reads each product before and after, and skips any product whose promo_label
is not the mitt offer — the note and the label have to agree, and the label is
what the discount was built around.
"""
import json, os, subprocess, sys

SHOP = 'mccormackpharmacy.myshopify.com'
DRY = '--write' not in sys.argv
HERE = os.path.dirname(os.path.abspath(__file__))
LABEL = 'Free tanning mitt with every Tan Studio item'
NOTE = json.dumps(json.load(open(os.path.join(HERE, 'promo-note.json'), encoding='utf-8')),
                  ensure_ascii=False, separators=(',', ':'))


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


have = gql('{ metafieldDefinitions(first: 1, ownerType: PRODUCT, namespace: "custom", '
           'key: "promo_note") { nodes { id } } }')['metafieldDefinitions']['nodes']
print('definition custom.promo_note:', 'present' if have else 'missing',
      '|', 'DRY RUN' if DRY else 'WRITING')
if not have and not DRY:
    m = ('mutation { metafieldDefinitionCreate(definition: {name: "Promo note", '
         'namespace: "custom", key: "promo_note", type: "rich_text_field", '
         'ownerType: PRODUCT, description: %s}) '
         '{ createdDefinition { id } userErrors { field message code } } }'
         % json.dumps('A sentence under the price for an offer the chip cannot '
                      'explain, e.g. that a free gift has to be added to the bag. '
                      'Nothing dates it; clear it when the offer ends.'))
    res = gql(m, mutate=True)['metafieldDefinitionCreate']
    if res.get('userErrors'):
        raise SystemExit(f'definition failed: {res["userErrors"]}')
    print('definition custom.promo_note: created')

# The offer's membership comes from the plan file the labels were written from,
# not a list pasted in here. A metafield-value query (metafields.custom.x:"y")
# looks like it would do this and silently matches nothing on this API version,
# so do not "simplify" it back to that.
import csv
OLD_LABEL = 'Free Tanning Mitt for every Bperfect Tan Studio Item Ordered'
handles = [r['store_handle'] for r in csv.DictReader(
    open(os.path.join(HERE, '..', 'old-site-offers.csv'), encoding='utf-8'))
    if r['promo_label'] == OLD_LABEL and r['store_handle']]
if len(handles) != 8:
    raise SystemExit(f'plan lists {len(handles)} mitt products, expected 8')

found = []
for h in handles:
    hits = [n for n in gql('{ products(first: 2, query: "handle:%s") { nodes { id handle '
                           'metafield(namespace:"custom", key:"promo_label") { value } } } }'
                           % h)['products']['nodes'] if n['handle'] == h]
    if len(hits) != 1:
        raise SystemExit(f'{h}: {len(hits)} products match that handle')
    # the note and the label have to agree: the label is what the discount was built around
    if (hits[0].get('metafield') or {}).get('value') != LABEL:
        raise SystemExit(f'{h}: promo_label is '
                         f'{(hits[0].get("metafield") or {}).get("value")!r}, not the mitt offer')
    found.append(hits[0])
print(f'{len(found)} products carry the mitt label')

ok = 0
log = open(os.path.join(HERE, '..', '..', 'archive', 'store-offers-2026-09-30',
                        'promo-note-log.jsonl'), 'a', encoding='utf-8')
for p in found:
    before = gql('{ product(id: "%s") { metafield(namespace:"custom", key:"promo_note") '
                 '{ value } } }' % p['id'])['product']
    bv = (before.get('metafield') or {}).get('value')
    if bv == NOTE:
        print(f'  SKIP  {p["handle"][:48]:50} already set')
        continue
    log.write(json.dumps({'handle': p['handle'], 'id': p['id'], 'before': bv},
                         ensure_ascii=False) + '\n')
    log.flush()
    if DRY:
        print(f'  would set  {p["handle"][:44]:46}')
        ok += 1
        continue
    m = ('mutation { metafieldsSet(metafields: [{ownerId: "%s", namespace: "custom", '
         'key: "promo_note", type: "rich_text_field", value: %s}]) '
         '{ metafields { id } userErrors { field message } } }'
         % (p['id'], json.dumps(NOTE)))
    errs = gql(m, mutate=True)['metafieldsSet'].get('userErrors') or []
    after = gql('{ product(id: "%s") { metafield(namespace:"custom", key:"promo_note") '
                '{ value } } }' % p['id'])['product']
    av = (after.get('metafield') or {}).get('value')
    log.write(json.dumps({'handle': p['handle'], 'after': av, 'userErrors': errs},
                         ensure_ascii=False) + '\n')
    log.flush()
    if errs or av != NOTE:
        print(f'  FAIL  {p["handle"][:44]:46} {errs}')
    else:
        print(f'  ok    {p["handle"][:44]:46}')
        ok += 1

print(f'\n{ok}/8 {"planned" if DRY else "set"}')
