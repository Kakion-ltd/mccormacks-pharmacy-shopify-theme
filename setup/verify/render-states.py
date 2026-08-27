"""Alternate render states — COVERAGE.md items D, F and G.

Each of these is a branch the theme has always had and no preview ever reached,
because the mock data could only ever produce the other side of the condition:
every collection held the same 10 products, customer was null across the
storefront, and the gift card was never expired.

Collection states are served on real handles so a browser can visit them; the
signed-in and expired-card variants are alternate renders of the same URL, so they
are read from disk.
"""
import pathlib
import re
import sys
import urllib.request

BASE = "http://localhost:8734"
PREVIEW = pathlib.Path(__file__).resolve().parents[2] / "preview"

res = []
def ck(name, got, want=True): res.append((got == want, name, got))

def fetch(path):
    with urllib.request.urlopen(BASE + path, timeout=30) as r:
        return r.read().decode("utf-8", "replace")

def read(name):
    p = PREVIEW / name
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else None

# --- D. Empty and filtered collections ---------------------------------------
filtered = fetch("/collections/filtered-fixture")
fempty = fetch("/collections/filtered-empty-fixture")
empty = fetch("/collections/empty-fixture")

# The dismiss glyph sits in its own span, so match to the end of the anchor.
ck("a filtered collection shows removable filter chips",
   len(re.findall(r'<a href="/collections/filtered-fixture".*?&times;.*?</a>', filtered, re.S)) >= 1)
ck("a filtered collection offers Clear all", "Clear all" in filtered)
ck("a filtered collection still lists its products",
   len(re.findall(r'class="pcard"', filtered)), 3)

# The distinction that matters: filtered-to-nothing must not read as an empty
# collection, or the shopper clears their basket-filling instead of their filters.
ck("filtered-to-nothing blames the filters", "No products match your filters" in fempty)
ck("filtered-to-nothing offers a way back", "Clear all filters" in fempty)
ck("filtered-to-nothing does not claim the collection is empty",
   "No products here yet" in fempty, False)

ck("a genuinely empty collection says so", "No products here yet" in empty)
ck("an empty collection offers Continue shopping", "Continue shopping" in empty)
ck("an empty collection does not blame filters",
   "No products match your filters" in empty, False)
ck("neither empty state lists products",
   len(re.findall(r'class="pcard"', fempty)) + len(re.findall(r'class="pcard"', empty)), 0)

# --- F. Signed-in customer ----------------------------------------------------
for stem, signed_out_text, signed_in_text in (
    ("page.wishlist", "Create an account", "My account"),
    ("page.loyalty-rewards-club", "Create an account", "Find your store"),
):
    out_html, in_html = read(f"{stem}.html"), read(f"{stem}.signed-in.html")
    ck(f"{stem}: a signed-in render exists", in_html is not None)
    if in_html is None or out_html is None:
        continue
    ck(f"{stem}: signed out offers to register", signed_out_text in out_html)
    ck(f"{stem}: signed in offers the member route", signed_in_text in in_html)
    ck(f"{stem}: signed in drops the register prompt", signed_out_text in in_html, False)

# --- G. Smaller states --------------------------------------------------------
gc_live, gc_expired = read("gift_card.html"), read("gift_card.expired.html")
ck("an expired gift card render exists", gc_expired is not None)
if gc_expired and gc_live:
    ck("an expired card says it is expired", "expired" in gc_expired.lower())
    ck("a live card does not", "expired" in gc_live.lower(), False)

order = read("customers_order.html")
ck("the order page shows its shipping method",
   order is not None and "Standard delivery" in order)

for ok, name, got in res:
    if not ok:
        print(f"FAIL  {name}   (got {got!r})")
print(f"\n{sum(1 for r in res if r[0])}/{len(res)} render-state checks passed")
sys.exit(0 if all(r[0] for r in res) else 1)
