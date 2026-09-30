"""Restore the old site's text. Re-reads each product immediately before writing,
refuses if it moved, writes description + the two metafields, reads back and
checks the stored text against the old site word for word.
"""
import json, subprocess, sys
from build_restore import letters, punct

SHOP = 'mccormackpharmacy.myshopify.com'
DRY = '--write' not in sys.argv


def gql(q, mutate=False):
    cmd = ['npx', 'shopify', 'store', 'execute', '-s', SHOP, '-q', q]
    if mutate:
        cmd.append('--allow-mutations')
    r = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(r.stdout[r.stdout.index('{\n  "'):], strict=False)
    except Exception:
        raise SystemExit(f'query failed:\n{r.stdout[-2000:]}\n{r.stderr[-800:]}')


READ = ('{ product(id: "%s") { descriptionHtml tags '
        'h: metafield(namespace:"custom", key:"how_to_use") { value } '
        'g: metafield(namespace:"custom", key:"ingredients") { value } } }')

plan = json.load(open('restore-plan.json'))
print(f'{len(plan)} products |', 'DRY RUN' if DRY else 'WRITING', flush=True)
log = open('restore-log.jsonl', 'a')
ok = skipped = failed = 0

for r in plan:
    live = gql(READ % r['id'])['product']
    if live['descriptionHtml'] != r['before']:
        print(f'SKIP (changed since plan) {r["handle"]}', flush=True)
        skipped += 1
        continue
    if 'pharmacist-review' in live['tags']:
        print(f'SKIP (medicine) {r["handle"]}', flush=True)
        skipped += 1
        continue
    if live['h'] or live['g']:
        print(f'SKIP (tabs already filled) {r["handle"]}', flush=True)
        skipped += 1
        continue

    log.write(json.dumps({'handle': r['handle'], 'id': r['id'],
                          'before_description': live['descriptionHtml'],
                          'before_how_to_use': None, 'before_ingredients': None,
                          'after_description': r['after'],
                          'after_metafields': r['metafields']}) + '\n')
    log.flush()
    if DRY:
        ok += 1
        continue

    mfs = ', '.join('{namespace:"custom", key:"%s", type:"multi_line_text_field", value:%s}'
                    % (k, json.dumps(v)) for k, v in r['metafields'].items())
    m = ('mutation { productUpdate(product: {id: "%s", descriptionHtml: %s%s}) '
         '{ userErrors { field message } } }'
         % (r['id'], json.dumps(r['after']),
            (', metafields: [%s]' % mfs) if mfs else ''))
    res = gql(m, mutate=True)
    errs = res.get('productUpdate', {}).get('userErrors') or []
    if errs:
        print(f'FAIL {r["handle"]}: {errs}', flush=True)
        failed += 1
        continue

    back = gql(READ % r['id'])['product']
    # the stored description must be the old site's Product Information, word for word
    bad = []
    if letters(back['descriptionHtml']) != letters(r['old_text']):
        bad.append('description text differs from the old site')
    gone = punct(r['old_text']) - punct(back['descriptionHtml'])
    if punct(back['descriptionHtml']) - punct(r['old_text']) or not set(gone) <= {'•', '·', ';'}:
        bad.append('punctuation moved beyond bullet markers')
    for key, got in (('how_to_use', back['h']), ('ingredients', back['g'])):
        want = r['metafields'].get(key)
        if want and (not got or letters(got['value']) != letters(want)
                     or punct(got['value']) != punct(want)):
            bad.append(f'{key} does not match the old site')
    if bad:
        print(f'FAIL verify {r["handle"]}: {"; ".join(bad)}', flush=True)
        failed += 1
        continue
    ok += 1
    print(f'  ok {r["handle"][:50]:50} +{",".join(r["metafields"]) or "-"}', flush=True)

print(f'\nrestored+verified {ok} | skipped {skipped} | failed {failed}')
