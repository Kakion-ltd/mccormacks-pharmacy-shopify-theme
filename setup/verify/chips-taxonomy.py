"""Category pills must match the taxonomy — labels and links, exactly.

The pills and the mega menu both derive from taxonomy.json, but the pills
passed through a hand-typed chip_links override on Medicines & Health and
drifted: three of its seven pills pointed at a leaf from another group, a
group from another department, and a different department entirely. This
walks every generated chip set and asserts each (label, handle) pair exists
in the taxonomy, and that every department page's pills are exactly its
first seven groups (or leaves, for flat departments) in taxonomy order.

Runs against the generated snippet, not a live server, so it also fails at
build time if gen_category_nav.py and taxonomy.json fall out of step.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(HERE)
tax = json.load(open(os.path.join(HERE, "taxonomy.json")))

sys.path.insert(0, HERE)
CHIPS = open(os.path.join(ROOT, "shopify-theme", "snippets", "category-chips.liquid")).read()


def handleize(t):
    # mirror of gen_category_nav.py's handleize - apostrophes drop, & becomes a gap
    import unicodedata
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    t = t.lower().replace("&", " ").replace("'", "")
    return re.sub(r"-{2,}", "-", re.sub(r"[^a-z0-9]+", "-", t)).strip("-")


def unesc(t):
    return t.replace("&amp;", "&").replace("&#39;", "'").replace("&#x27;", "'")


res = []
def ck(name, got, want=True): res.append((got == want, name, got))

# every (label, handle) the taxonomy knows, per department
dept_pairs = {}
for m in tax:
    pairs = set()
    for g in m.get("groups", []):
        pairs.add((g["title"], handleize(g["title"])))
        for i in g.get("items", []):
            pairs.add((i, handleize(i)))
    for i in m.get("flat", []):
        pairs.add((i, handleize(i)))
    dept_pairs[handleize(m["menu"])] = pairs
all_pairs = set().union(*dept_pairs.values())

# parse the generated snippet: {%- when 'a' or 'b' -%} followed by chip renders
blocks = re.findall(r"{%-\s*when (.*?)-%}\n((?:{% render 'category-chip'[^\n]*\n)+)", CHIPS)
ck("chip sets parsed from the generated snippet", len(blocks) > 30)

chip_re = re.compile(r"h: '([^']+)', l: '([^']*)'")
for whens, body in blocks:
    selectors = re.findall(r"'([^']+)'", whens)
    chips = [(unesc(l), h) for h, l in chip_re.findall(body)]
    # which department do these selectors belong to?
    dept = next((d for d, pairs in dept_pairs.items()
                 if any(sel == d or any(h == sel for _, h in pairs) for sel in selectors)), None)
    pool = dept_pairs.get(dept, all_pairs)
    for label, h in chips:
        ck(f"'{label}' -> /collections/{h} exists in taxonomy ({dept or 'any'})",
           (label, h) in pool)

# department pages: exactly the first seven, in taxonomy order
for m in tax:
    mh = handleize(m["menu"])
    groups, flat = m.get("groups", []), m.get("flat", [])
    expected = [(g["title"], handleize(g["title"])) for g in groups][:7] if groups \
        else [(i, handleize(i)) for i in flat][:7]
    if not expected:
        continue
    blk = next((b for w, b in blocks if f"'{mh}'" in w), None)
    ck(f"{m['menu']}: department page has a chip set", blk is not None)
    if blk:
        got = [(unesc(l), h) for h, l in chip_re.findall(blk)]
        ck(f"{m['menu']}: pills are the first {len(expected)} taxonomy entries in order",
           got == expected)

# the merchant override must not silently reintroduce drift on department templates
import glob
for p in glob.glob(os.path.join(ROOT, "shopify-theme", "templates", "collection.*.json")):
    handle = os.path.basename(p)[len("collection."):-len(".json")]
    if handle not in dept_pairs or not dept_pairs[handle]:
        continue  # merch collections (sale, new-in, bundles) may promote freely
    d = json.load(open(p))
    for sec in d["sections"].values():
        cl = sec.get("settings", {}).get("chip_links") or ""
        for line in [l for l in cl.split("\n") if l.strip()]:
            label, _, url = (x.strip() for x in line.partition("|"))
            h = url.replace("/collections/", "").strip("/ ")
            ck(f"override on {handle}: '{label}' matches taxonomy", (label, h) in dept_pairs[handle])

for ok, name, got in res:
    if not ok:
        print(f"FAIL  {name}   (got {got!r})")
print(f"\n{sum(1 for r in res if r[0])}/{len(res)} chip taxonomy checks passed")
sys.exit(0 if all(r[0] for r in res) else 1)
