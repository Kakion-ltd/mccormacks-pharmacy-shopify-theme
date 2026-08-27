"""Paginated collections.

Nothing beyond page 1 had ever rendered: the fixture collection held 10 products
against `by 24`, and the harness's paginate tag was stubbed to pages:1 with no parts.
So the page links, next/prev and every ?page= URL existed only in source.

That matters beyond tidiness. The open canonical question (OVERNIGHT-QUESTIONS.md Q1,
item 2) is what Shopify canonicalises on page 2 — and if it points every page back to
page 1, deep products on a 293-collection catalogue become invisible to Google. These
checks make the markup that produces those URLs real and testable locally, ahead of
that being answered on the dev store.

What they cannot do is tell you what Shopify puts in rel=canonical. The harness mocks
canonical_url, and it is asserted here only as present, never as correct.
"""
import re
import sys
import urllib.request

BASE = "http://localhost:8734"
PAGED = "/collections/paginated-fixture"     # 30 products, 24 per page
SMALL = "/collections/vitamins"              # under one page

res = []
def ck(name, got, want=True): res.append((got == want, name, got))

def fetch(path):
    with urllib.request.urlopen(BASE + path, timeout=30) as r:
        return r.read().decode("utf-8", "replace")

def cards(html):
    return len(re.findall(r'class="pcard"', html))

def page_links(html):
    return re.findall(r'<a href="(/collections/paginated-fixture[^"]*)"[^>]*>([^<]{1,12})<', html)

def titles(html):
    return re.findall(r'<h3[^>]*><a href="/products/([^"]+)"', html)

p1 = fetch(PAGED)
p2 = fetch(PAGED + "?page=2")

ck("page 1 shows a full page of products", cards(p1), 24)
ck("page 2 shows the remainder", cards(p2), 6)
ck("the two pages list different products", titles(p1)[:3] != titles(p2)[:3])

l1 = page_links(p1)
l2 = page_links(p2)
ck("page 1 links forward to page 2", any(u.endswith("?page=2") for u, _ in l1))
ck("page 1 offers Next", any(t.strip() == "Next" for _, t in l1))
ck("page 1 offers no Previous", any(t.strip() == "Previous" for _, t in l1), False)
ck("page 2 links back to page 1",
   any(u == "/collections/paginated-fixture" for u, _ in l2))
ck("page 2 offers no Next", any(t.strip() == "Next" for _, t in l2), False)
ck("page 1 is not linked as ?page=1", any(u.endswith("?page=1") for u, _ in l1), False)

# A collection that fits on one page must render no pagination at all, rather than
# a lone disabled "1".
small = fetch(SMALL)
ck("no pagination on a single-page collection",
   len(re.findall(r'href="[^"]*\?page=\d+"', small)), 0)

# Present, not correct: the harness mocks canonical_url, so this only proves the tag
# is emitted on a paginated page. What Shopify actually puts here is Q1.
ck("page 2 still emits a canonical tag",
   '<link rel="canonical"' in p2)

for ok, name, got in res:
    if not ok:
        print(f"FAIL  {name}   (got {got!r})")
print(f"\n{sum(1 for r in res if r[0])}/{len(res)} pagination checks passed")
sys.exit(0 if all(r[0] for r in res) else 1)
