"""Run the signatures over the live product pull. Reports only; writes nothing."""
import json, os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from signatures import SIGS

DATA = os.environ.get('SWEEP_DATA')          # folder holding the live pull

def load():
    cols = [json.loads(l) for l in open(f'{DATA}/collections.jsonl')]
    prods = [json.loads(l) for l in open(f'{DATA}/products.jsonl')]
    return cols, prods

def in_pool(p, pool):
    if pool is None: return True
    kind, types = pool
    t = p['productType'] or ''
    return t in types if kind == '=' else any(t.startswith(x) for x in types)

def matches(prods, handle):
    pool, hi, md, lo, drop, note = SIGS[handle]
    out = []
    for p in prods:
        if not in_pool(p, pool): continue
        t = p['title']
        if drop and re.search(drop, t, re.I): continue
        for conf, pat in (('high', hi), ('medium', md), ('low', lo)):
            if pat and re.search(pat, t, re.I):
                out.append((conf, p)); break
    return out

if __name__ == '__main__':
    cols, prods = load()
    live = {c['handle']: c['productsCount']['count'] for c in cols}
    tot = collections.Counter()
    for h in SIGS:
        m = matches(prods, h)
        c = collections.Counter(x[0] for x in m)
        tot.update(c)
        print(f"{h:34} now={live.get(h,'?'):>3}  +{len(m):>3}  "
              f"h={c['high']:<3} m={c['medium']:<3} l={c['low']:<3}")
        if '-v' in sys.argv:
            for conf, p in sorted(m, key=lambda x: (x[0], x[1]['title'])):
                print(f"      {conf:6} {p['title'][:58]:58} | {p['productType'][:28]}")
    print('\nTOTAL', dict(tot))
