"""Write the reformatted descriptions. Re-reads each product immediately before
writing and refuses if it has changed since the plan was made (MAINTENANCE.md,
"The store has no worktree"). Logs before-state and re-reads after.
"""
import json, re, subprocess, sys, collections, html as H

SHOP = 'mccormackpharmacy.myshopify.com'
DRY = '--write' not in sys.argv


def gql(q, mutate=False):
    cmd = ['npx', 'shopify', 'store', 'execute', '-s', SHOP, '-q', q]
    if mutate:
        cmd.append('--allow-mutations')
    r = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(r.stdout, strict=False)
    except Exception:
        raise SystemExit(f'query failed:\n{r.stdout}\n{r.stderr}')


def strip(h):
    t = re.sub(r'<[^>]+>', ' ', h or '')
    return re.sub(r'\s+', ' ', H.unescape(t)).strip()


def letters(h):
    return re.sub(r'[^0-9a-z]', '', strip(h).lower())


def punct(h):
    return collections.Counter(c for c in strip(h) if not c.isalnum() and not c.isspace())


plan = json.load(open('proposed.json')) + json.load(open('manual.json'))
print(f'{len(plan)} products |', 'DRY RUN' if DRY else 'WRITING')

log = open('write-log.jsonl', 'a')
ok = skipped = failed = 0

for r in plan:
    gid = r['id']
    live = gql('{ product(id: "%s") { descriptionHtml } }' % gid)['product']['descriptionHtml']
    if live != r['before']:
        print(f'SKIP (changed since plan) {r["handle"]}')
        skipped += 1
        continue
    log.write(json.dumps({'handle': r['handle'], 'id': gid, 'title': r['title'],
                          'before': live, 'after': r['after'],
                          'by_hand': r.get('by_hand', False)}) + '\n')
    log.flush()
    if DRY:
        ok += 1
        continue

    m = ('mutation { productUpdate(product: {id: "%s", descriptionHtml: %s}) '
         '{ product { id } userErrors { field message } } }'
         % (gid, json.dumps(r['after'])))
    res = gql(m, mutate=True)
    errs = res.get('productUpdate', {}).get('userErrors') or []
    if errs:
        print(f'FAIL {r["handle"]}: {errs}')
        failed += 1
        continue

    back = gql('{ product(id: "%s") { descriptionHtml } }' % gid)['product']['descriptionHtml']
    same_letters = letters(back) == letters(r['before'])
    added = punct(back) - punct(r['before'])
    removed = punct(r['before']) - punct(back)
    if not same_letters or added or not set(removed) <= {'-', '–', '*', '•', ';'}:
        print(f'FAIL verify {r["handle"]}: letters={same_letters} added={dict(added)} '
              f'removed={dict(removed)}')
        failed += 1
        continue
    ok += 1
    print(f'  ok {r["handle"]}')

print(f'\nwritten+verified {ok} | skipped {skipped} | failed {failed}')
