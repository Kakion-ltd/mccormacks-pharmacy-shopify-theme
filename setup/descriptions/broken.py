"""Find product descriptions that are cut off, empty or clearly wrong.
Report only - nothing here writes to the store.
"""
import json, re, html as H, collections, csv, os

REPO = '/Users/matthewtobin/Kakion/Active Projects/McCormacks-Site'
CUT_LO, CUT_HI = 485, 500          # where the April import sliced the source

DICT = {w.strip().lower() for w in open('/usr/share/dict/words')}
CORPUS = collections.Counter()      # words seen complete elsewhere on the store


def text(h):
    t = re.sub(r'<[^>]+>', ' ', h or '')
    return re.sub(r'\s+', ' ', H.unescape(t)).strip()


def inner_len(h):
    return len(re.sub(r'^<p>|</p>$', '', (h or '').strip()))


prods = [json.loads(l) for l in open('products.jsonl')]
for p in prods:
    for w in re.findall(r"[a-z']{2,}", text(p['descriptionHtml']).lower()):
        CORPUS[w] += 1

sku = {}
for l in open(f'{REPO}/archive/store-cleanup-2026-09-30/all-variants-after.jsonl'):
    d = json.loads(l)
    sku.setdefault(d['handle'], d.get('sku') or '')

prev = {r['handle']: r for r in
        csv.DictReader(open(f'{REPO}/setup/truncated-descriptions-2026-09-28.csv'))}


def is_fragment(tok):
    """Last token looks like half a word."""
    w = tok.lower().strip('.,;:)(“”"\'')
    if not w or not w.isalpha():
        return False
    for stem in (w, w.rstrip('s'), re.sub(r'(es|ed|ing|ly|er)$', '', w),
                 re.sub(r'ies$', 'y', w)):
        if stem in DICT:
            return False
    # a real brand/product word shows up complete elsewhere on the store
    return CORPUS[w] < 3


BRANDS = {'bioXtra'}   # CamelCase that is a real brand, not a missing space


def runtogether(t):
    """A missing space between two words. Word-boundary anchored, so CamelCase
    inside a brand ("SylliFlor", "ThermaCare") does not match at all."""
    for m in re.finditer(r"\b[a-z]{3,}[A-Z][a-z]{3,}\b", t):
        if m.group(0) not in BRANDS:
            return m.group(0)
    return None


rows = []
for p in prods:
    h = p['descriptionHtml'] or ''
    t = text(h)
    n = inner_len(h)
    probs = []

    if not t:
        probs.append('No description at all')
    else:
        toks = t.split()
        ends_clean = bool(re.search(r'[.!?:)\]”"’]$', t))
        if not ends_clean and toks and is_fragment(toks[-1]):
            probs.append('Cut off in the middle of a word')
        elif not ends_clean and CUT_LO <= n <= CUT_HI:
            probs.append('Cut off in the middle of a sentence')
        if re.search(r'[a-z]\?[A-Z]|\?[A-Z]{3}|Ã.|â€|�', t):
            probs.append('Odd characters in the text')
        if runtogether(t):
            probs.append('Two words run together with no space between')
        sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', t) if len(s.strip()) > 40]
        if [s for s, c in collections.Counter(sents).items() if c > 1]:
            probs.append('The same sentence appears twice')
        if re.search(r'(?i)\b(lorem ipsum|placeholder|to be confirmed|tbc|test description)\b', t):
            probs.append('Placeholder text, not a real description')

    if probs:
        old = prev.get(p['handle'], {})
        rows.append(dict(handle=p['handle'], title=p['title'],
                         medicine='pharmacist-review' in p['tags'],
                         problems=probs, text=t, sku=sku.get(p['handle'], ''),
                         live_url=old.get('live_url', ''),
                         live_site=old.get('live_site', ''),
                         was_listed=p['handle'] in prev))

json.dump(rows, open('broken.json', 'w'), indent=1)
c = collections.Counter(x for r in rows for x in r['problems'])
print('products with a problem:', len(rows),
      '| medicines:', sum(1 for r in rows if r['medicine']))
for k, v in c.most_common():
    print(f'  {v:5d}  {k}')
