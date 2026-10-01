#!/usr/bin/env python3
"""Apply the categorisation sweep to the store. Logs every write so it can be reversed.

    SWEEP_DATA=<pull folder> python3 setup/categorisation/apply.py rules
    SWEEP_DATA=<pull folder> python3 setup/categorisation/apply.py merges
    SWEEP_DATA=<pull folder> python3 setup/categorisation/apply.py tags [--only <handle>] [--limit N]
    ... add --dry-run to print the mutations and write nothing

Every mutation goes through `shopify store execute --allow-mutations`; without that
flag the CLI refuses to mutate, which is why no read in this repo can write by accident.

tagsAdd only. Never tagsSet, never tagsRemove: a product cannot lose a tag here.
After each product is written its tags are read BACK and both the requested tag and
the stored tags are logged, because Shopify splits a tag on commas (MAINTENANCE) and
the log has to record what the store actually holds, not what was asked for.
"""
import csv, json, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import match
from signatures import SIGS

STORE = 'mccormackpharmacy.myshopify.com'
HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, 'applied-2026-10-01.csv')
DRY = '--dry-run' in sys.argv

def gql(query, mutate=False):
    cmd = ['npx', 'shopify', 'store', 'execute', '-s', STORE, '-q', query]
    if mutate: cmd.append('--allow-mutations')
    env = dict(os.environ, CI='1', SHOPIFY_CLI_NO_ANALYTICS='1')
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if r.returncode != 0:
        raise SystemExit(f'STOPPED: store execute failed\n{r.stderr[-2000:]}')
    try:
        j = json.loads(r.stdout)
    except ValueError:
        raise SystemExit(f'STOPPED: unparseable response\n{r.stdout[:2000]}')
    return j.get('data', j)

def errs(payload, what):
    e = (payload or {}).get('userErrors') or []
    if e: raise SystemExit(f'STOPPED: {what}: {json.dumps(e)}')

rows = []
def log(**kw):
    rows.append(kw)

def flush():
    if not rows: return
    cols = ['phase', 'object', 'id', 'handle', 'title', 'action', 'requested',
            'stored_after', 'before', 'after', 'reverse_with', 'note']
    new = not os.path.exists(LOG)
    with open(LOG, 'a', newline='') as f:
        w = csv.DictWriter(f, cols)
        if new: w.writeheader()
        for r in rows: w.writerow({c: r.get(c, '') for c in cols})
    print(f'logged {len(rows)} rows -> {LOG}')
    rows.clear()   # flush is called per batch; without this each flush re-appends the lot

def count(handle):
    d = gql('{ collectionByHandle(handle: "%s") { productsCount { count } } }' % handle)
    return d['collectionByHandle']['productsCount']['count']

def tags_of(pid):
    d = gql('{ product(id: "%s") { tags } }' % pid)
    return d['product']['tags']

# ---------------------------------------------------------------- phase: rules
RULES = {
 'brain-health':   {'appliedDisjunctively': False,
   'rules': [{'column': 'TYPE', 'relation': 'EQUALS', 'condition': 'Supplements > Brain Health & Omega Oils'}]},
 'baby-feeding':   {'appliedDisjunctively': False,
   'rules': [{'column': 'TYPE', 'relation': 'EQUALS', 'condition': 'Baby > Feeding'}]},
 'travel-sickness': {'appliedDisjunctively': False,
   'rules': [{'column': 'TAG', 'relation': 'EQUALS', 'condition': 'Travel Sickness'}]},
}
PREDICTED = {'brain-health': 12, 'baby-feeding': 2, 'travel-sickness': 2}

# Travel Sickness swaps a vendor rule for a tag rule, and NO product carries that tag
# yet. Changing the rule first would take the page from 2 products to 0, so the two the
# vendor rule currently matches are tagged BEFORE the swap. Caught by --dry-run.
PRE_TAG = {'travel-sickness': ('Travel Sickness', ('Kwells', 'Stugeron'))}

def pre_tag(handle, prods):
    spec = PRE_TAG.get(handle)
    if not spec: return
    tag, vendors = spec
    for p in [x for x in prods if (x['vendor'] or '') in vendors]:
        if tag in p['tags']:
            print(f'  already tagged {tag!r}: {p["title"][:50]}'); continue
        if DRY:
            print(f'  DRY pre-tag {tag!r} -> {p["title"][:50]}'); continue
        mut = ('mutation { tagsAdd(id: "%s", tags: ["%s"]) { userErrors { field message } } }'
               % (p['id'], tag))
        errs(gql(mut, mutate=True)['tagsAdd'], f'tagsAdd {p["handle"]}')
        after = tags_of(p['id'])
        print(f'  pre-tagged {p["title"][:44]}  stored={after}')
        log(phase='rules', object='product', id=p['id'], handle=p['handle'], title=p['title'],
            action='tagsAdd (before the rule swap)', requested=tag,
            before='|'.join(p['tags']), stored_after='|'.join(after),
            reverse_with=f'tagsRemove id={p["id"]} tags=["{tag}"]',
            note=f'without this the {handle} rule swap would empty the page')

def q_ruleset(rs):
    inner = ', '.join('{column: %s, relation: %s, condition: "%s"}'
                      % (r['column'], r['relation'], r['condition'].replace('"', '\\"'))
                      for r in rs['rules'])
    return '{appliedDisjunctively: %s, rules: [%s]}' % (str(rs['appliedDisjunctively']).lower(), inner)

def do_rules():
    cols_live, prods = match.load()
    byh = {c['handle']: c for c in cols_live}
    for h, want in RULES.items():
        c = byh[h]
        before_rule = json.dumps(c['ruleSet'], sort_keys=True)
        before_n = count(h)
        print(f'\n{h}: before {before_n} products, rule {before_rule}')
        pre_tag(h, prods)
        mut = ('mutation { collectionUpdate(input: {id: "%s", ruleSet: %s}) '
               '{ collection { handle } userErrors { field message } } }' % (c['id'], q_ruleset(want)))
        if DRY:
            print('  DRY', mut); continue
        errs(gql(mut, mutate=True)['collectionUpdate'], f'collectionUpdate {h}')
        time.sleep(4)
        after_n = count(h)
        pred = PREDICTED[h]
        ok = 'MATCHES PREDICTION' if after_n == pred else f'DIFFERS from predicted {pred}'
        print(f'  after {after_n} products  ({ok})')
        log(phase='rules', object='collection', id=c['id'], handle=h, title=c['title'],
            action='collectionUpdate ruleSet', requested=json.dumps(want, sort_keys=True),
            before=before_rule, after=str(after_n),
            reverse_with=f'collectionUpdate id={c["id"]} ruleSet={before_rule}',
            note=f'count {before_n} -> {after_n}; sheet predicted {pred}; {ok}')

# ---------------------------------------------------------------- phase: merges
MERGES = [  # dead handle, surviving handle, tag the survivor matches
 ('cuticle-nail-care', 'nail-care', 'Nail Care'),
 ('dry-skin', 'dry-skin-eczema-psoriasis', 'Dry Skin, Eczema & Psoriasis'),
]

def do_merges():
    cols_live, prods = match.load()
    byh = {c['handle']: c for c in cols_live}
    sys.path.insert(0, os.environ['SWEEP_DATA'])
    from rules import members
    pub = gql('{ publications(first: 10) { nodes { id name } } }')['publications']['nodes']
    online = next(p['id'] for p in pub if p['name'] == 'Online Store')
    for dead, alive, tag in MERGES:
        dc, ac = byh[dead], byh[alive]
        on_dead = members(dc, prods)
        before_alive = count(alive)
        print(f'\n{dead} -> {alive}: {len(on_dead)} on the dead page, survivor has {before_alive}')
        # 1. make sure every product on the dead page is on the survivor
        for p in on_dead:
            already = p in members(ac, prods)
            if already:
                print(f'  already on {alive}: {p["title"][:52]}')
                log(phase='merge', object='product', id=p['id'], handle=p['handle'], title=p['title'],
                    action='no tag needed', requested=tag, stored_after='|'.join(p['tags']),
                    note=f'already matches {alive} before any write')
                continue
            if DRY:
                print(f'  DRY tagsAdd {tag!r} -> {p["title"][:52]}'); continue
            mut = ('mutation { tagsAdd(id: "%s", tags: ["%s"]) { userErrors { field message } } }'
                   % (p['id'], tag.replace('"', '\\"')))
            errs(gql(mut, mutate=True)['tagsAdd'], f'tagsAdd {p["handle"]}')
            after = tags_of(p['id'])
            print(f'  tagged {p["title"][:46]}  stored={after}')
            log(phase='merge', object='product', id=p['id'], handle=p['handle'], title=p['title'],
                action='tagsAdd', requested=tag, before='|'.join(p['tags']), stored_after='|'.join(after),
                reverse_with=f'tagsRemove id={p["id"]} tags={json.dumps(sorted(set(after)-set(p["tags"])))}',
                note=f'merge {dead} -> {alive}')
        # 2. unpublish the dead collection (never delete)
        if DRY:
            print(f'  DRY unpublish {dead}'); continue
        mut = ('mutation { publishableUnpublish(id: "%s", input: [{publicationId: "%s"}]) '
               '{ userErrors { field message } } }' % (dc['id'], online))
        errs(gql(mut, mutate=True)['publishableUnpublish'], f'unpublish {dead}')
        print(f'  unpublished {dead} from Online Store')
        log(phase='merge', object='collection', id=dc['id'], handle=dead, title=dc['title'],
            action='publishableUnpublish (Online Store)', before='published', after='unpublished',
            reverse_with=f'publishablePublish id={dc["id"]} publicationId={online}',
            note='collection kept, not deleted')
        # 3. redirect the dead URL at the survivor
        frm, to = f'/collections/{dead}', f'/collections/{alive}'
        mut = ('mutation { urlRedirectCreate(urlRedirect: {path: "%s", target: "%s"}) '
               '{ urlRedirect { id } userErrors { field message } } }' % (frm, to))
        res = gql(mut, mutate=True)['urlRedirectCreate']
        errs(res, f'urlRedirectCreate {frm}')
        rid = (res.get('urlRedirect') or {}).get('id', '')
        print(f'  redirect {frm} -> {to}  ({rid})')
        log(phase='merge', object='urlRedirect', id=rid, handle=dead, title=frm,
            action='urlRedirectCreate', after=to,
            reverse_with=f'urlRedirectDelete id={rid}', note='not added to redirects.csv: that file is generated')
        after_alive = count(alive)
        print(f'  {alive} now {after_alive} (was {before_alive})')

# ---------------------------------------------------------------- phase: tags
SKIP_TARGETS = {'cuticle-nail-care', 'dry-skin'}   # pages being retired by the merges

def high_plan():
    cols_live, prods = match.load()
    byh = {c['handle']: c for c in cols_live}
    plan = {}
    for h in SIGS:
        if h in SKIP_TARGETS or h not in byh: continue
        tag = byh[h]['title']
        for conf, p in match.matches(prods, h):
            if conf != 'high': continue
            plan.setdefault(p['id'], {'p': p, 'tags': [], 'pages': []})
            plan[p['id']]['tags'].append(tag)
            plan[p['id']]['pages'].append(h)
    return plan

def do_tags():
    only = sys.argv[sys.argv.index('--only') + 1] if '--only' in sys.argv else None
    limit = int(sys.argv[sys.argv.index('--limit') + 1]) if '--limit' in sys.argv else None
    plan = high_plan()
    if only:
        plan = {k: v for k, v in plan.items() if only in v['pages']}
    items = sorted(plan.values(), key=lambda v: v['p']['title'])
    if limit: items = items[:limit]
    print(f'{len(items)} products, {sum(len(v["tags"]) for v in items)} tag additions'
          f'{" (only " + only + ")" if only else ""}')
    # One product per CLI call cost ~10s, which put a 646-product run past an hour and
    # risked being killed before the log was written. Mutations are batched with GraphQL
    # aliases instead (BATCH per call), the log is flushed after every batch rather than
    # at the end, and `stored_after` comes from one bulk re-pull once the writes are done
    # instead of a read-back per product. Same writes, same log, ~30 calls instead of 1300.
    BATCH = 20
    for s in range(0, len(items), BATCH):
        chunk = items[s:s + BATCH]
        parts = []
        for n, v in enumerate(chunk):
            tags = sorted(set(v['tags']))
            tl = ', '.join('"%s"' % t.replace('"', '\\"') for t in tags)
            parts.append('a%d: tagsAdd(id: "%s", tags: [%s]) { userErrors { field message } }'
                         % (n, v['p']['id'], tl))
        if DRY:
            for v in chunk:
                print(f'  DRY {v["p"]["title"][:50]:50} += {sorted(set(v["tags"]))}')
            continue
        d = gql('mutation { %s }' % ' '.join(parts), mutate=True)
        for n, v in enumerate(chunk):
            errs(d.get(f'a{n}'), f'tagsAdd {v["p"]["handle"]}')
        for v in chunk:
            p, tags = v['p'], sorted(set(v['tags']))
            split = [t for t in tags if ',' in t]
            log(phase='tags', object='product', id=p['id'], handle=p['handle'], title=p['title'],
                action='tagsAdd', requested='|'.join(tags), before='|'.join(p['tags']),
                reverse_with='see stored_after; tagsRemove the tags not in `before`',
                note=('requested tag contains a comma, Shopify stores it split: '
                      + '|'.join(split)) if split else '')
        flush()
        print(f'  {min(s + BATCH, len(items))}/{len(items)} written '
              f'(last: {chunk[-1]["p"]["title"][:40]})')
    if not DRY:
        verify_stored(items)

def verify_stored(items):
    """Fill stored_after from one bulk re-pull, and check every requested tag landed."""
    import csv as _csv
    want = {v['p']['id']: sorted(set(v['tags'])) for v in items}
    got, cur, n = {}, '', 0
    while True:
        after = 'null' if not cur else '"%s"' % cur
        d = gql('{ products(first: 250, after: %s) { pageInfo { hasNextPage endCursor } '
                'nodes { id tags } } }' % after)['products']
        for x in d['nodes']:
            if x['id'] in want: got[x['id']] = x['tags']
        if not d['pageInfo']['hasNextPage'] or n > 20: break
        cur = d['pageInfo']['endCursor']; n += 1
    missing = []
    for pid, tags in want.items():
        stored = got.get(pid, [])
        for t in tags:
            parts = [x.strip() for x in t.split(',')]
            if not all(x in stored for x in parts): missing.append((pid, t, stored))
    print(f'\nverify: {len(want)} products checked, {len(missing)} requested tags not stored')
    for pid, t, stored in missing[:10]: print(f'   MISSING {t!r} on {pid} (has {stored})')
    # rewrite the log with stored_after filled in
    path = LOG
    if os.path.exists(path):
        with open(path) as f: all_rows = list(_csv.DictReader(f))
        for r in all_rows:
            if r['phase'] == 'tags' and r['id'] in got:
                r['stored_after'] = '|'.join(got[r['id']])
                gained = sorted(set(got[r['id']]) - set(r['before'].split('|') if r['before'] else []))
                r['reverse_with'] = f'tagsRemove id={r["id"]} tags={json.dumps(gained)}'
        with open(path, 'w', newline='') as f:
            w = _csv.DictWriter(f, all_rows[0].keys()); w.writeheader(); w.writerows(all_rows)
        print(f'log completed with stored_after + exact reversal -> {path}')
    if missing: raise SystemExit(f'STOPPED: {len(missing)} requested tags are not on the store')

if __name__ == '__main__':
    phase = sys.argv[1] if len(sys.argv) > 1 else ''
    try:
        {'rules': do_rules, 'merges': do_merges, 'tags': do_tags}[phase]()
    except KeyError:
        raise SystemExit('usage: apply.py rules|merges|tags [--only H] [--limit N] [--dry-run]')
    finally:
        flush()
