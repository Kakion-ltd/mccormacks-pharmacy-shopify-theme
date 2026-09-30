"""Turn the old site's text into a description + two metafields.
The old site's wording, nothing added. Formatting only, by today's rules.
"""
import json, re, collections, html as H
from fix import fix, head_re

SKIP = {'Returns Policy'}
DIFFERENT = {r['handle'] for r in json.load(open('restore-list.json'))
             if r['live_site'] == 'different-text-on-live'}


def strip(h):
    return re.sub(r'\s+', ' ', H.unescape(re.sub(r'<[^>]+>', ' ', h or ''))).strip()


def letters(s):
    return re.sub(r'[^0-9a-z]', '', strip(s).lower())


def punct(s):
    return collections.Counter(c for c in strip(s) if not c.isalnum() and not c.isspace())


def to_html(txt):
    """Old-site plain text -> HTML. Each line a paragraph, then today's rules."""
    paras = [H.escape(l.strip(), quote=False) for l in txt.split('\n') if l.strip()]
    return fix(''.join('<p>%s</p>' % p for p in paras))


BULLET = re.compile(r'(?<=\S)\s+(?=[•·])')       # inline • starts a line


def to_text(txt):
    """Metafields are plain text: put inline bullets and run-in headings on their
    own line. Markers stay - without <li> they are what makes it read as a list."""
    out = []
    for line in txt.split('\n'):
        line = BULLET.sub('\n', line.strip())
        line = head_re.sub(lambda m: '\n' + m.group(0).strip() + ' ', line)
        out.append(line)
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip()


if __name__ == '__main__':
    old = json.load(open('old-site.json'))
    store = json.load(open('store-now.json'))
    rows, skipped = [], []

    for handle, rec in old.items():
        s = {k: v for k, v in rec['sections'].items() if k not in SKIP}
        pi = s.get('Product Information', '').strip()
        cur = store[handle]
        if not pi:
            skipped.append((handle, 'no Product Information on the old site'))
            continue
        # The three the old site words differently: take its version whatever the
        # length. Both short ones are complete sentences; the store's are cut.
        if handle not in DIFFERENT and len(letters(pi)) <= len(letters(cur['descriptionHtml'])):
            skipped.append((handle, 'old site text is not longer than the store text'))
            continue

        desc = to_html(pi)
        assert letters(desc) == letters(pi), handle
        gone = punct(pi) - punct(desc)
        assert not (punct(desc) - punct(pi)), handle
        assert set(gone) <= {'•', '·', ';'}, (handle, gone)

        mf = {}
        for key, name in (('how_to_use', 'How To Use'), ('ingredients', 'Active Ingredients')):
            v = s.get(name, '').strip()
            if v:
                t = to_text(v)
                assert letters(t) == letters(v) and punct(t) == punct(v), (handle, key)
                mf[key] = t

        rows.append(dict(id=cur['id'], handle=handle, title=None,
                         before=cur['descriptionHtml'], after=desc,
                         old_text=pi, metafields=mf))

    json.dump(rows, open('restore-plan.json', 'w'), indent=1)
    print(f'ready {len(rows)} | skipped {len(skipped)}')
    for h, why in skipped:
        print(f'  skip {h[:48]:48} {why}')
    print('with How To Use :', sum(1 for r in rows if 'how_to_use' in r['metafields']))
    print('with Ingredients:', sum(1 for r in rows if 'ingredients' in r['metafields']))
