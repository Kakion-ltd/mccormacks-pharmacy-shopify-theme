"""Generate snippets/mega-menu.liquid from taxonomy.json.

Every desktop dropdown now comes from the same file as the mobile drawer, the
breadcrumbs and the category chips. It used to be scraped out of the design
handoff HTML with a headless browser, which made the desktop nav the one
surface that could drift from the taxonomy with nothing to catch it, and made
a build depend on Playwright and on an archived design file. All the design
ever supplied that the taxonomy cannot is the panel chrome - width, the no-JS
fallback offset, padding and column count - and that is the table below.

Three shapes, chosen by the data rather than by hand:

  groups   a department with groups. Past ten of them the groups are one flow
           the browser balances (Medicines & Health); below that they are
           split into fixed columns, because a flowed group carries a trailing
           margin at the foot of every column and that costs more than the
           raggedness does at five or seven groups. The split minimises the
           tallest column while keeping taxonomy order, which reproduces the
           splits the designer had drawn by hand.
  flat     a department with no groups, as a wide multi-column list (Vitamins).
  list     the four narrow single-column panels.

Run from setup/: python3 gen_mega.py
"""
import functools
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
THEME = os.path.join(HERE, '..', 'shopify-theme')


def handleize(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    s = s.lower().replace('&', ' ').replace("'", '')
    return re.sub(r'-{2,}', '-', re.sub(r'[^a-z0-9]+', '-', s)).strip('-')


# Only the ampersand needs escaping; apostrophes stay literal, as they were in
# the design markup and as the rest of the generated nav writes them.
amp = lambda s: s.replace('&', '&amp;')

taxonomy = {handleize(m['menu']): m for m in json.load(open(os.path.join(HERE, 'taxonomy.json')))}
handles = {c['handle'] for c in json.load(open(os.path.join(HERE, 'collections.json')))}

# Panel chrome, in nav order. `left` is the no-JS fallback position of a narrow panel; theme.js
# re-aligns those under their trigger at runtime. Wide panels start at the
# container edge. `floor` is the column minimum for a split grid.
PANELS = [
    ('medicines-health', dict(width=1380, pad='30px 30px', cols=6)),
    ('vitamins',         dict(width=1000, pad='34px 32px', cols=4, floor=150, gap=26)),
    ('beauty',           dict(width=1240, pad='30px', cols=4, floor=160)),
    ('skincare',         dict(width=1100, pad='30px', cols=3, floor=180)),
    ('toiletries',       dict(left=379)),
    ('mother-baby',      dict(left=454)),
    ('fragrance',        dict(left=566)),
    ('gifting',          dict(left=648)),
]
FLOW_ABOVE = 10          # groups; above this the panel is one balanced flow

WIDE_BOX = ('position:absolute; left:30px; width:{width}px; max-width:calc(100vw - 60px); top:100%; '
            'z-index:50; background:#ffffff; border:1px solid #e6e7e4; box-shadow:0 24px 44px rgba(0,0,0,.14); '
            'border-radius:0 0 16px 16px; max-height:84vh; overflow:auto; animation:megaIn .16s ease-out;')
LIST_BOX = ('position:absolute; left:{left}px; width:240px; top:100%; z-index:50; background:#ffffff; '
            'border:1px solid #e6e7e4; box-shadow:0 24px 44px rgba(0,0,0,.14); border-radius:0 0 16px 16px; '
            'max-height:74vh; overflow-y:auto; animation:megaIn .16s ease-out;')
HEAD_STYLE = 'display:block; color:var(--c-primary-text); font-weight:800;'
STACK_STYLE = 'display:flex; flex-direction:column; font-size:12px;'
SLIDE_STYLE = ('color:#3a3d39; display:inline-block; padding:2px 0; width:fit-content; '
               'transition:color .14s ease, transform .14s ease;')

missing = []


def url(title):
    h = handleize(title)
    if h not in handles:
        missing.append(title)
    return '/collections/' + h


def balance(costs, k):
    """Split a list into k contiguous runs, minimising the largest run."""
    n = len(costs)

    @functools.lru_cache(None)
    def best(i, k):
        if k == 1:
            return sum(costs[i:]), (n,)
        out = None
        for j in range(i + 1, n - k + 2):
            here = sum(costs[i:j])
            rest, cuts = best(j, k - 1)
            worst = max(here, rest)
            if out is None or worst < out[0]:
                out = (worst, (j,) + cuts)
        return out

    cuts = best(0, k)[1]
    runs, prev = [], 0
    for c in cuts:
        runs.append(list(range(prev, c)))
        prev = c
    return runs


def group_html(g, indent):
    pad = ' ' * indent
    out = [f'{pad}<div class="mega-group">',
           f'{pad}  <a href="{url(g["title"])}" style="{HEAD_STYLE}" class="hov-dark-green">{amp(g["title"])}</a>']
    if g['items']:
        out.append(f'{pad}  <div style="{STACK_STYLE}">')
        out += [f'{pad}    <a href="{url(i)}" style="color:#2A2B2A;" class="hov-green">{amp(i)}</a>' for i in g['items']]
        out.append(f'{pad}  </div>')
    out.append(f'{pad}</div>')
    return out


def grouped_panel(key, cfg):
    groups = taxonomy[key]['groups']
    body = [f'  <div style="{WIDE_BOX.format(**cfg)}">',
            '    <div style="display:flex; align-items:stretch;">']
    if len(groups) > FLOW_ABOVE:
        body.append(f'      <div style="flex:1; padding:{cfg["pad"]}; column-count:{cfg["cols"]};" class="mega-cols">')
        for g in groups:
            body += group_html(g, 8)
        body.append('      </div>')
    else:
        body.append(f'      <div style="flex:1; padding:{cfg["pad"]}; display:grid; '
                    f'grid-template-columns:repeat({cfg["cols"]},minmax({cfg["floor"]}px,1fr)); gap:24px;">')
        for run in balance(tuple(1 + len(g['items']) for g in groups), cfg['cols']):
            body.append('        <div style="display:flex; flex-direction:column; gap:24px;">')
            for i in run:
                body += group_html(groups[i], 10)
            body.append('        </div>')
        body.append('      </div>')
    body += ['    </div>', '  </div>']
    return body


def flat_panel(key, cfg):
    items = taxonomy[key]['flat']
    n, k = len(items), cfg['cols']
    size, extra = divmod(n, k)
    body = [f'  <div style="{WIDE_BOX.format(**cfg)}">',
            '    <div style="display:flex; align-items:stretch;">',
            f'      <div style="flex:1; padding:{cfg["pad"]}; display:grid; '
            f'grid-template-columns:repeat({k},minmax({cfg["floor"]}px,1fr)); gap:{cfg["gap"]}px;">']
    at = 0
    for c in range(k):
        take = size + (1 if c < extra else 0)
        body.append('        <div style="display:flex; flex-direction:column; gap:11px; font-size:14px;">')
        body += [f'          <a href="{url(i)}" style="{SLIDE_STYLE}" class="hov-slide">{amp(i)}</a>'
                 for i in items[at:at + take]]
        body.append('        </div>')
        at += take
    body += ['      </div>', '    </div>', '  </div>']
    return body


def list_panel(key, cfg):
    menu = taxonomy[key]
    items = menu.get('flat') or [g['title'] for g in menu.get('groups', [])]
    body = [f'  <div style="{LIST_BOX.format(**cfg)}">',
            '    <div style="padding:26px 28px; display:flex; flex-direction:column; gap:11px; font-size:14px;">']
    body += [f'      <a href="{url(i)}" class="hov-slide" style="{SLIDE_STYLE}">{amp(i)}</a>' for i in items]
    body += ['    </div>', '  </div>']
    return body


parts = ['{% comment %} Generated by setup/gen_mega.py from taxonomy.json — do not edit by hand. '
         'One panel per department; the mobile drawer and the category chips come from the same file. {% endcomment %}']
for key, cfg in PANELS:
    if key not in taxonomy:
        sys.exit(f'mega menu: unknown department {key}')
    parts.append(f'<div class="mega-panel" data-mega-panel="{key}">')
    if 'left' in cfg:
        parts += list_panel(key, cfg)
    elif taxonomy[key].get('groups'):
        parts += grouped_panel(key, cfg)
    else:
        parts += flat_panel(key, cfg)
    parts.append('</div>')

out = '\n'.join(parts) + '\n'
open(os.path.join(THEME, 'snippets', 'mega-menu.liquid'), 'w').write(out)
n_links = out.count('<a href=')
print(f'mega-menu: {len(PANELS)} panels, {n_links} links, {len(out)} bytes')
if missing:
    sys.exit('links with no collection: ' + ', '.join(sorted(set(missing))))
