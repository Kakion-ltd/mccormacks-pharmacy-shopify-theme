#!/usr/bin/env python3
"""Build setup/redirects.csv (Shopify import format) from the old site's URL lists.

Inputs: archive/old-site-2026-09-30/{products,categories,brands}.txt (old sitemap
paths), a store pull (products + collections JSON) and the old category listing
pages, which give each old product its old category so an unmatched product can
land on that category's collection.

  python3 setup/build_redirects.py <store-products.json> <store-collections.json> <old-cats-dir> <published.json>

published.json maps handle -> [status, publishedOnOnlineStore]; a product that is
not ACTIVE and on the Online Store gets its collection, not its product page.
"""
import csv, json, os, re, sys, urllib.parse
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OLD = os.path.join(ROOT, "archive/old-site-2026-09-30")
prods = json.load(open(sys.argv[1]))
cols = {c["handle"]: c for c in json.load(open(sys.argv[2]))}
cats_dir = sys.argv[3]
published = json.load(open(sys.argv[4]))
def on_site(h):
    st, pub = published.get(h, ("MISSING", False))
    return st == "ACTIVE" and bool(pub)
collections_json = {c["handle"]: c for c in json.load(open(os.path.join(ROOT, "setup/collections.json")))}

# ---- old category -> new path (hand-mapped 30 Sep 2026; '?' marks a judgement call)
CAT = {
 "pharmacy/10": "pharmacy", "cold-and-flu/41": "cold-flu-allergy", "pain-relief/42": "pain-relief",
 "allergy-relief/40": "hayfever-allergy", "childrens-medicine/43": "baby-health?",
 "stomach-and-digestion/44": "stomach-gastrointestinal", "first-aid/45": "first-aid",
 "oral-health/53": "mouth-oral-care", "womens-health/48": "womens-health", "medical-devices/50": "pharmacy?",
 "medicated-skincare/49": "dermatological-skincare", "eye-and-ear-care/46": "eye-ear-health",
 "travel-essentials-/737": "travel", "pet-health/716": "pharmacy?", "nicotine-replacement/52": "nicotine-replacement",
 "foot-and-nail-care/47": "foot-care", "sensitive-conditions/51": "sensitive-conditions", "sexual-health/54": "sexual-health",
 "back-to-school/689": "children-vitamins?", "covid-19/679": "self-testing-kits",
 "vitamins-and-supplements/36": "vitamins", "vitamins-and-immune-support/80": "immune-support",
 "weight-management/74": "slimming", "energy-and-vitality/71": "energy-wellbeing",
 "probiotics-and-gut-health/77": "probiotics-digestive-health", "sleep-aids-and-stress-relief/82": "sleep-rest",
 "muscle-joint-and-bone/79": "joint-bone-health", "womens-wellbeing/76": "womens-health", "mens-wellbeing/75": "mens-health",
 "brain-health-and-omega-oils/70": "fish-oils-omegas", "childrens-supplements/73": "children-vitamins",
 "healthy-heart/81": "heart-health", "eyes-and-ears/78": "eye-health", "health-foods/72": "vitamins?",
 "other-supplements/83": "vitamins", "skincare/12": "skincare", "face/63": "facial-skincare", "cleanse/62": "cleanser",
 "body-care/66": "body-skincare", "eye-care/64": "eye-cream", "masks-and-peels/65": "face-masks",
 "hands-and-feet/67": "hands-nails", "mens-skincare/68": "mens-grooming", "sun-care-and-spf/69": "sun",
 "beauty/11": "beauty", "face/57": "face", "tanning/60": "tanning", "eyes/55": "eyes",
 "brushes-and-accessories/61": "makeup-brushes", "lips/58": "lips", "nails/59": "nails", "brows-and-lashes/56": "eyebrows",
 "mother-and-baby/38": "mother-baby", "soothers-and-accessories/99": "baby-accessories", "feeding/96": "baby-feeding",
 "baby-health/320": "baby-health", "baby-wipes-and-changing/97": "baby-wipes-toiletries",
 "bathing-and-skincare/95": "baby-skincare", "maternity-care/98": "maternity-care",
 "toiletries/37": "toiletries", "bath-and-shower/84": "bath-shower", "deodorant/86": "deodorant", "hair-care/88": "hair-care",
 "feminine-care/89": "feminine-care", "mens-grooming/91": "mens-grooming", "dental-and-whitening/87": "dental-care",
 "electrical/92": "toiletries?", "hair-removal/90": "toiletries?", "handsoap-and-sanitiser/85": "bath-shower?",
 "travel/93": "travel", "masks-gloves-and-ppe/94": "first-aid?",
 "fragrance-and-gift/39": "gifting", "gifts-for-her/680": "gifts-for-her", "gifts-for-him/353": "gifts-for-him",
 "gifts-for-kids-/753": "gifting?", "all-fragrances/733": "fragrance", "womens-fragrance/101": "womens-fragrance",
 "mens-fragrance/102": "mens-fragrance", "hampers/104": "/pages/hampers-made-to-order", "gift-vouchers/100": "/pages/gift-vouchers",
 "candles-and-diffusers/103": "candles-diffusers", "gifts-for-the-home/354": "candles-diffusers?",
 "new/7": "new-in?", "new-in---pharmacy/1000010": "pharmacy", "new-in---vitamins-and-supplements/1000036": "vitamins",
 "new-in---skincare/1000012": "skincare", "new-in---beauty/1000011": "beauty", "new-in---mother-and-baby/1000038": "mother-baby",
 "new-in---toiletries/1000037": "toiletries", "new-in---fragrance-and-gift/1000039": "gifting", "new-in---clearance-/1000700": "sale",
 "our-brands/8": "/pages/brands", "our-irish-brands-/338": "/pages/brands?", "mrs-glam/208": "bperfect?", "carter-beauty/146": "/pages/brands?",
 "sale/9": "sale", "sale/750": "sale", "bundles-/741": "bundles", "clearance-/700": "sale?", "3-for-10/751": "sale?", "3-for-5/701": "sale?",
 "services/19": "/pages/in-store-services", "online-services/324": "/pages/prescriptions?", "instore-services/325": "/pages/in-store-services",
 "about-us/14": "/pages/about-us", "locations-and-opening-hours/25": "/pages/store-locator", "contact-us/15": "/pages/contact-us",
 "ask-a-pharmacist/341": "/pages/contact-us?", "book-a-vaccination/34": "/pages/flu-vaccine-clinic?",
 "delivery-and-collection/17": "/pages/shipping", "returns-policy/18": "/pages/returns",
 "competitions/366": "/pages/loyalty-rewards-club?", "weee-recycling-old-appliance-/707": "/pages/returns?",
 "terms-and-conditions/22": "/pages/terms-and-conditions", "privacy-policy/23": "/pages/privacy-policy",
 "registered-internet-supply-pharmacy/26": "/pages/internet-supply-pharmacy",
}
PAGES = {"/subscribe": "/pages/loyalty-rewards-club?", "/cookies": "/pages/cookie-policy"}

def slug(t):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", t.lower().replace("&", "and").replace("'", ""))).strip("-")

by_title = {c["title"]: c["handle"] for c in collections_json.values()}
def parent_of(handle):
    """Climb collections.json until a collection with products is found."""
    seen = set(); start = handle
    while handle and handle not in seen and cols.get(handle, {}).get("productsCount", {}).get("count", 0) == 0:
        seen.add(handle)
        meta = collections_json.get(handle)
        if not meta:
            break
        handle = by_title.get(meta.get("group")) or by_title.get(meta.get("parent_menu"))
    return handle or start

def col_path(handle):
    handle = parent_of(handle) or handle
    assert handle in cols, handle
    return "/collections/" + handle

def cat_target(key):
    t = CAT[key]
    sure = not t.endswith("?")
    t = t.rstrip("?")
    return (t if t.startswith("/") else col_path(t)), sure

# ---- brands: collection, else the vendor listing, else the brands page
vendors = {}
for p in prods:
    vendors.setdefault(slug(p["vendor"]), p["vendor"])
vendors_flat = {k.replace("-", ""): v for k, v in vendors.items()}
def brand_target(s):
    s = s.rstrip("-")
    if s in cols and cols[s]["productsCount"]["count"]:
        return "/collections/" + s, "brand-collection"
    v = vendors.get(s) or vendors_flat.get(s.replace("-", ""))
    if v:
        return "/collections/vendors?q=" + urllib.parse.quote(v), "brand-vendor"
    # no vendor of that name, but products whose title starts with it: the search page lists them
    w = s.replace("-", " ")
    if len(w) >= 4 and any(slug(p["title"]).startswith(s + "-") or slug(p["title"]) == s for p in prods):
        return "/search?q=" + urllib.parse.quote_plus(w) + "&type=product", "brand-search"
    return "/pages/brands", "brand-unmatched"

# ---- products
bc, titles = {}, {}
for p in prods:
    for v in p["variants"]["nodes"]:
        b = (v["barcode"] or "").strip()
        if b:
            bc.setdefault(b, p["handle"])
    titles.setdefault(slug(p["title"]), p["handle"])
by_handle = {p["handle"]: p for p in prods}
SIZE = re.compile(r"^\d+(\.\d+)?(ml|g|kg|mg|pk|s|pack|tablets|tabs|caps|capsules|sachets|l|x|pc|pcs|piece)?$")
def words(s): return [w for w in s.split("-") if w]
def core(s): return {w for w in words(s) if not SIZE.match(w) and not w.isdigit()}
title_index = {}
for t, h in titles.items():
    ws = words(t)
    if ws: title_index.setdefault(ws[0], []).append((t, h))
def fuzzy(s):
    ws = words(s)
    if not ws: return None
    best = (0, None)
    for t, h in title_index.get(ws[0], []):
        a, b = core(s), core(t)
        if not a or not b: continue
        j = len(a & b) / len(a | b)
        if j > best[0]: best = (j, h)
    return best[1] if best[0] >= 0.6 else None

def product_landing(h):
    """Where a product that is off the website goes: its most specific collection."""
    p = by_handle[h]
    cs = [c["handle"] for c in p["collections"]["nodes"] if c["handle"] not in ("frontpage", "pharmacist-review-required") and c["handle"] in cols]
    cs = [c for c in cs if cols[c]["productsCount"]["count"]]
    if not cs: return None
    return "/collections/" + min(cs, key=lambda c: cols[c]["productsCount"]["count"])

# old product -> old category ids from the fetched listing pages
old_cat_of = {}
cat_size = Counter()
for f in os.listdir(cats_dir):
    cid = f.split("_")[0]
    for m in set(re.findall(r'href="(/p/[^"]+)"', open(os.path.join(cats_dir, f), errors="ignore").read())):
        old_cat_of.setdefault(m, set()).add(cid)
        cat_size[cid] += 1
cat_by_id = {k.split("/")[1]: k for k in CAT}
def old_category_target(path):
    ids = [i for i in old_cat_of.get(path, ()) if i in cat_by_id and not CAT[cat_by_id[i]].startswith("/")]
    if not ids: return None
    cid = min(ids, key=lambda i: cat_size[i])
    return cat_target(cat_by_id[cid])[0]

rows = []
def add(frm, to, kind, note=""):
    rows.append((frm, to, kind, note))

for line in open(os.path.join(OLD, "categories.txt")):
    path = line.strip()
    if not path: continue
    if path in PAGES:
        add(path, PAGES[path].rstrip("?"), "page", "" if not PAGES[path].endswith("?") else "check")
        continue
    key = path[len("/c/"):]
    if key in CAT:
        to, sure = cat_target(key)
        add(path, to, "category" if not to.startswith("/pages") else "page", "" if sure else "check")
    else:
        to, kind = brand_target(key.split("/")[0])
        add(path, to, kind, "" if kind != "brand-unmatched" else "check")

for line in open(os.path.join(OLD, "brands.txt")):
    path = line.strip()
    key = path[len("/c/"):]
    if key in CAT: continue  # already covered by the category sitemap
    to, kind = brand_target(key.split("/")[0])
    add(path, to, kind, "" if kind != "brand-unmatched" else "check")

for line in open(os.path.join(OLD, "products.txt")):
    path = line.strip()
    if not path: continue
    _, _, s, pid = path.split("/", 3)
    h = bc.get(pid) or bc.get(pid.lstrip("0"))
    kind = "barcode"
    if not h:
        h = titles.get(s); kind = "title"
    if not h:
        h = fuzzy(s); kind = "title-fuzzy"
    if h:
        if not on_site(h):
            to = product_landing(h) or old_category_target(path)
            add(path, to or "/collections/all", "off-website", h if to else "no collection; check")
        else:
            add(path, "/products/" + h, kind, "" if kind != "title-fuzzy" else "closest: " + by_handle[h]["title"])
        continue
    to = old_category_target(path)
    if to:
        add(path, to, "parent-category", ""); continue
    bt, bk = brand_target(words(s)[0])
    if bk != "brand-unmatched":
        add(path, bt, "parent-brand", "check"); continue
    add(path, "/collections/all", "unmatched", "check")

# dedupe on from-path (first wins), drop self-redirects
seen, out = set(), []
for r in rows:
    if r[0] in seen or r[0] == r[1]: continue
    seen.add(r[0]); out.append(r)

with open(os.path.join(ROOT, "setup/redirects.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["Redirect from", "Redirect to"])
    for r in out: w.writerow(r[:2])
with open(os.path.join(ROOT, "setup/redirects-review.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["Redirect from", "Redirect to", "Match", "Note"])
    for r in out: w.writerow(r)
c = Counter(r[2] for r in out)
print(len(out), "redirects"); [print(f"  {k:18} {v}") for k, v in sorted(c.items())]
print("  flagged 'check':", sum(1 for r in out if "check" in r[3]))
