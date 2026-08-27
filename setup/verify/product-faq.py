"""Product FAQ mechanism.

The theme ships this empty on purpose — FAQ content on medicine products needs
pharmacist sign-off — so what is verified here is the mechanism, not any wording.
The harness fixture deliberately includes a half-filled entry and an answer full
of quotes, because those are the two ways this breaks in production: a question
rendered with no answer, and a JSON-LD block made invalid by punctuation.
"""
import json
import re
import sys
import urllib.request

BASE = "http://localhost:8734"
WITH_FAQ = "/products/fabu-skin-hair-nails-glow-60-capsules"   # harness fixture
WITHOUT_FAQ = "/products/difflam-sore-throat-spray-30ml"       # no faq metafield

res = []
def ck(name, got, want=True): res.append((got == want, name, got))

def fetch(path):
    with urllib.request.urlopen(BASE + path, timeout=30) as r:
        return r.read().decode("utf-8", "replace")

def ld_blocks(html):
    return re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)

def faq_schema(html):
    for b in ld_blocks(html):
        if '"FAQPage"' in b:
            return json.loads(b)      # raises if the block is malformed
    return None

# --- a product that has FAQ content -----------------------------------------
html = fetch(WITH_FAQ)
visible = re.findall(r'<details class="pfaq-item">', html)
ck("FAQ section renders when the metafield has content", len(visible) > 0)

try:
    schema = faq_schema(html)
    ck("FAQPage JSON-LD parses as valid JSON", schema is not None)
except json.JSONDecodeError as e:
    ck(f"FAQPage JSON-LD parses as valid JSON ({e})", False)
    schema = None

if schema:
    qs = schema.get("mainEntity", [])
    ck("schema @type is FAQPage", schema.get("@type"), "FAQPage")
    # The visible copy and the schema read the same metafield through the same
    # validation, so a mismatch means one of them has drifted.
    ck(f"visible questions match schema questions ({len(visible)} vs {len(qs)})",
       len(visible) == len(qs))
    ck("the entry with a blank answer is dropped from schema", len(qs), 2)
    ck("every question has a non-empty name", all(q.get("name", "").strip() for q in qs))
    ck("every question has a non-empty acceptedAnswer",
       all(q.get("acceptedAnswer", {}).get("text", "").strip() for q in qs))
    ck("quotes in an answer survive JSON encoding",
       any('"' in q["acceptedAnswer"]["text"] for q in qs))

ck("the entry with a blank answer is dropped from the visible list", len(visible), 2)
ck("internal links in answers are preserved",
   'href="/pages/shipping"' in html)
ck("answers stay in the DOM when collapsed (no hidden attribute)",
   'class="pfaq-a"' in html and "<details class=\"pfaq-item\" hidden" not in html)

# --- a product with no FAQ metafield ----------------------------------------
html2 = fetch(WITHOUT_FAQ)
ck("no FAQ section on a product without content", "pfaq-item" in html2, False)
ck("no empty heading left behind", "pfaq-heading" in html2, False)
ck("no FAQPage schema emitted without content",
   any('"FAQPage"' in b for b in ld_blocks(html2)), False)
for b in ld_blocks(html2):
    try:
        json.loads(b)
    except json.JSONDecodeError as e:
        ck(f"all JSON-LD on the no-FAQ page stays valid ({e})", False)
ck("all JSON-LD on the no-FAQ page stays valid", True)

for ok, name, got in res:
    if not ok:
        print(f"FAIL  {name}   (got {got!r})")
print(f"\n{sum(1 for r in res if r[0])}/{len(res)} product FAQ checks passed")
sys.exit(0 if all(r[0] for r in res) else 1)
