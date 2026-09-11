"""Local preview server: maps real Shopify URLs onto the rendered preview files,
so the site behaves like a store — /collections/skincare opens the Skincare
category page instead of 404ing.

Plain `python3 -m http.server` cannot do this: the theme's links are absolute
Shopify paths (/collections/<handle>) with no matching file on disk.

  python3 setup/serve_preview.py [port]        # default 8734
  npm run dev                                   # same thing
"""
import json, os, posixpath, re, sys, threading, urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREVIEW = os.path.join(ROOT, "preview")


def product_page(handle):
    """Which rendered product page serves this handle.

    The sold-out fixture has its own rendering so the out-of-stock buy box and the
    back-in-stock capture are reachable; everything else shares product.html.
    """
    if handle == "difflam-sore-throat-spray-30ml":
        return first_existing("preview/product.oos.html", "preview/product.html")
    if handle == "vitamin-d3-1000iu-60-capsules":
        return first_existing("preview/product.variants.html", "preview/product.html")
    if handle == "cerave-moisturising-cream":
        return first_existing("preview/product.variants2.html", "preview/product.html")
    if handle == "nurofen-plus-200mg-12-8mg-24-tablets":
        return first_existing("preview/product.restricted.html", "preview/product.html")
    # Unknown handles 404, as on Shopify. Serving the generic page for any handle
    # hid dead product links and let verify scripts pass against URLs that do not exist.
    if handle not in HANDLES:
        return None
    return "/preview/product.html"


def first_existing(*rels):
    for r in rels:
        if r and os.path.isfile(os.path.join(ROOT, r)):
            return "/" + r
    return None


def slug(text):
    out = "".join(c if c.isalnum() else "-" for c in text.lower())
    return "-".join(x for x in out.split("-") if x)


def route(path):
    """Shopify URL -> preview file. None falls through to the filesystem."""
    p = urllib.parse.unquote(path.split("?")[0].split("#")[0]).rstrip("/") or "/"
    query = urllib.parse.parse_qs(path.split("?")[1]) if "?" in path else {}

    # AJAX endpoints. On a real store Shopify renders a section per request;
    # here render_preview.mjs --endpoints pre-rendered the responses for the
    # mock catalogue, so predictive search and cart cross-sell actually work
    # in the preview instead of silently doing nothing.
    if p == "/search/suggest":
        term = (query.get("q") or [""])[0].strip()
        return first_existing(f"preview/_suggest/{slug(term)}.html",
                              "preview/_suggest/_none.html")
    if p == "/recommendations/products":
        pid = (query.get("product_id") or [""])[0].strip()
        return first_existing(f"preview/_recs/{slug(pid)}.html")

    # /index.html used to hit a root redirect file (now archive/index.html), which
    # bounces to the ORIGINAL DESIGN homepage — not what we want to serve.
    if p in ("/", "/index.html", "/index.htm"):
        return "/preview/index.html"
    if p == "/collections":
        return "/preview/list-collections.html"

    if p.startswith("/collections/"):
        # Shopify serves /collections/<c>/products/<p> as the PRODUCT page. Routing it
        # to the collection page hid the whole collection-scoped product path from the
        # preview, so nothing could be checked against it.
        rest = p[len("/collections/"):].split("/")
        if len(rest) >= 3 and rest[1] == "products":
            return product_page(rest[2])
        handle = rest[0]
        # Shopify's automatic all-products collection. The empty-collection state
        # links here through routes.all_products_collection_url, so a 404 would be a
        # dead "Continue shopping" button on a page that now actually renders.
        if handle == "all":
            return "/preview/collection.html"
        # The one place a query parameter selects a different rendered page.
        if handle in ("filtered-fixture", "filtered-empty-fixture", "empty-fixture"):
            return first_existing(
                f"preview/collection.{handle.replace('-fixture', '')}.html",
                "preview/collection.html")
        if handle == "paginated-fixture":
            page = "2" if query.get("page", ["1"])[0] == "2" else "1"
            return first_existing(f"preview/collection.paginated.p{page}.html",
                                  "preview/collection.html")
        # Every collection was rendered into categories/. No generic fallback:
        # an unknown handle should 404, not quietly render a blank collection
        # page and hide a broken link.
        return first_existing(f"preview/categories/{handle}.html",
                              f"preview/collection.{handle}.html")
    if p.startswith("/pages/"):
        handle = p[len("/pages/"):].split("/")[0]
        # No generic fallback: a page handle with no template must 404, like a
        # store with no such page, or a dead footer link never shows up.
        return first_existing(f"preview/page.{handle}.html")
    if p.startswith("/products/"):
        return product_page(p[len("/products/"):].split("/")[0])
    if p.startswith("/blogs/"):
        rest = p[len("/blogs/"):].split("/")
        return "/preview/article.html" if len(rest) > 1 and rest[1] else "/preview/blog.html"
    if p == "/cart":
        return "/preview/cart.html"
    if p == "/search":
        return "/preview/search.html"
    if p in ("/account", "/account/login", "/account/register",
             "/account/addresses", "/account/orders"):
        tail = p.replace("/account", "").strip("/")
        return first_existing(f"preview/customers_{tail or 'account'}.html",
                              "preview/customers_account.html")
    if p.startswith("/account"):
        return "/preview/customers_account.html"
    if p == "/design":
        return "/setup/McCormacks Homepage.dc.html"
    return None


# ---------------------------------------------------------------------------
# Cart AJAX API.
#
# SimpleHTTPRequestHandler answers GET only, so /cart/add.js returned 501 and
# every add-to-cart in the preview failed silently — which also meant the cart
# drawer never opened and the cross-sell rail never loaded. This is a minimal
# in-memory stand-in for Shopify's /cart/*.js endpoints: enough to exercise the
# theme's own JavaScript, not a cart implementation.
#
# State is process-global and shared by every visitor, which is fine for a local
# preview and would be wrong for anything else.
CART_LOCK = threading.Lock()
CART = {"items": []}


# The fixture catalogue, read from the same file render_preview.mjs renders from, so
# the cart line items and product JSON cannot disagree with the pages about a price.
with open(os.path.join(ROOT, "setup", "catalogue.json"), encoding="utf-8") as _fh:
    _CAT = json.load(_fh)
CATALOGUE = [(c["t"], c["v"], c["p"], c["img"], c.get("tg", [])) for c in _CAT]
SOLD_OUT = {c["t"] for c in _CAT if c.get("oos")}


def handleize(title):
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


HANDLES = {handleize(t[0]) for t in CATALOGUE}


def _aslist(v):
    """A catalogue optName / pack `o` is a string for one option, a list for several."""
    return list(v) if isinstance(v, list) else [v]


def _variants(i):
    """Variants in the shape /products/<handle>.js gives, with the ids render_preview.mjs
    puts on the page: 40000000+i for a single variant, 40000000+i*100+k per pack.

    featured_image carries the pack's own photo where the fixture gives one — quick
    view swaps the modal image from this field, and with every variant sharing one
    photo there was no way to see whether it had."""
    c = _CAT[i]
    packs = c.get("packs") or []
    if len(packs) > 1:
        out = []
        for k, pk in enumerate(packs):
            vals = _aslist(pk["o"])
            v = {"id": 40000000 + i * 100 + k, "title": " / ".join(vals), "options": vals,
                 "price": pk["p"], "compare_at_price": pk.get("was"),
                 "available": pk.get("oos") is not True,
                 "inventory_quantity": 0 if pk.get("oos") else 12,
                 "featured_image": {"src": f"/shopify-theme/assets/{pk.get('img', c['img'])}"}}
            for n, val in enumerate(vals):
                v[f"option{n + 1}"] = val
            out.append(v)
        return out, _aslist(c.get("optName", "Pack size"))
    return [{"id": 40000000 + i, "title": "Default Title", "option1": "Default Title", "options": ["Default Title"],
             "price": c["p"], "compare_at_price": c.get("was"), "available": c["t"] not in SOLD_OUT,
             "inventory_quantity": 0 if c["t"] in SOLD_OUT else 12,
             "featured_image": None}], ["Title"]


def product_json(i):
    title, vendor, price, img, tags = CATALOGUE[i]
    variants, options = _variants(i)
    return {
        "id": 30000000 + i, "title": title, "handle": handleize(title), "vendor": vendor,
        "url": f"/products/{handleize(title)}",
        "price": min(v["price"] for v in variants), "available": any(v["available"] for v in variants), "tags": tags,
        "featured_image": f"/shopify-theme/assets/{img}", "images": [f"/shopify-theme/assets/{img}"],
        "options": options, "variants": variants,
    }


def _variant_index(variant_id):
    """Catalogue index and variant for either id scheme, or (None, None)."""
    n = int(variant_id) - 40000000
    if n < 0:
        return None, None
    i, k = (n // 100, n % 100) if n >= 100 else (n, 0)
    if not 0 <= i < len(CATALOGUE):
        return None, None
    variants, _ = _variants(i)
    return (i, variants[k]) if k < len(variants) else (None, None)


def line_for(variant_id):
    """Line item fields the theme's drawer reads."""
    i, v = _variant_index(variant_id)
    if i is None:
        return None
    title, vendor, _, img, _ = CATALOGUE[i]
    price = v["price"]
    vtitle = None if v["title"] == "Default Title" else v["title"]
    return {
        "id": int(variant_id), "variant_id": int(variant_id), "product_id": 30000000 + i,
        "key": f"{variant_id}:0", "title": title if not vtitle else f"{title} - {vtitle}", "product_title": title, "vendor": vendor,
        "variant_title": vtitle, "quantity": 0, "price": price, "final_price": price,
        "original_price": price, "line_price": price, "final_line_price": price,
        "original_line_price": price, "url": f"/products/{handleize(title)}",
        # Shopify sends the variant's own photo where it has one, falling back to the
        # product's. Two pack sizes of one product therefore differ by image on a real
        # store, which is precisely why a drawer line that omits variant_title is not
        # obviously wrong until a fixture gives the variants the same picture.
        "image": (v.get("featured_image") or {}).get("src") or f"/shopify-theme/assets/{img}",
    }


def cart_json():
    items = [dict(it) for it in CART["items"]]
    for it in items:
        it["line_price"] = it["price"] * it["quantity"]
        it["final_line_price"] = it["line_price"]
        it["original_line_price"] = it["line_price"]
    total = sum(it["final_line_price"] for it in items)
    return {
        "token": "preview", "item_count": sum(it["quantity"] for it in items),
        "items": items, "total_price": total, "original_total_price": total,
        "items_subtotal_price": total, "total_discount": 0, "currency": "EUR",
        "requires_shipping": True, "note": None, "attributes": {},
    }


class CartError(Exception):
    """A rejected cart write, in the shape Shopify answers with: status, message and
    a `description` written for the shopper. The description is the only part that
    says what to do next, so the theme shows it verbatim."""

    def __init__(self, description):
        super().__init__(description)
        self.payload = {"status": 422, "message": "Cart Error", "description": description}


def _stock(variant_id):
    i, v = _variant_index(variant_id)
    return 0 if v is None else v.get("inventory_quantity", 0)


def cart_add(variant_id, qty):
    with CART_LOCK:
        held = next((it["quantity"] for it in CART["items"] if it["id"] == int(variant_id)), 0)
        limit = _stock(variant_id)
        if held + qty > limit:
            # Shopify's own wording, which is what a shopper reads on the live store.
            raise CartError(f"You can only add {limit} of that item to your cart.")
        for it in CART["items"]:
            if it["id"] == int(variant_id):
                it["quantity"] += qty
                return cart_json()
        line = line_for(variant_id)
        if line is None:
            return None
        line["quantity"] = qty
        CART["items"].append(line)
        return cart_json()


def cart_change(line_no, quantity):
    with CART_LOCK:
        idx = int(line_no) - 1
        if 0 <= idx < len(CART["items"]):
            if quantity <= 0:
                CART["items"].pop(idx)
            else:
                limit = _stock(CART["items"][idx]["id"])
                if quantity > limit:
                    raise CartError(f"You can only add {limit} of that item to your cart.")
                CART["items"][idx]["quantity"] = quantity
        return cart_json()


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        mapped = route(path)
        target = mapped if mapped else urllib.parse.unquote(path.split("?")[0])
        target = posixpath.normpath(target).lstrip("/")
        full = os.path.join(ROOT, target)
        if os.path.isdir(full):
            idx = os.path.join(full, "index.html")
            if os.path.isfile(idx):
                return idx
        return full

    def _json(self, payload, code=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        p = urllib.parse.unquote(self.path.split("?")[0]).rstrip("/")
        if not p.endswith(".js") or not p.startswith("/cart"):
            self.send_error(501, "Unsupported method ('POST')")
            return
        length = int(self.headers.get("Content-Length") or 0)
        try:
            data = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            data = {}
        try:
            if p == "/cart/add.js":
                cart = cart_add(data.get("id"), int(data.get("quantity") or 1))
                if cart is None:
                    self._json({"status": 422, "message": "Cart Error",
                                "description": "Unknown variant in the preview catalogue"}, 422)
                    return
                self._json(cart)
            elif p == "/cart/change.js":
                self._json(cart_change(data.get("line"), int(data.get("quantity") or 0)))
            elif p == "/cart/clear.js":
                # Shopify's own endpoint, and the only way a check can start from a
                # known cart. CART is process-global and outlives every script, so
                # without this each one inherits whatever the last one left — see
                # the clear at the top of variants.py and variant-integrity.py.
                with CART_LOCK:
                    CART["items"] = []
                self._json(cart_json())
            else:
                self.send_error(404)
        except CartError as e:
            self._json(e.payload, 422)

    def send_head(self):
        p = urllib.parse.unquote(self.path.split("?")[0]).rstrip("/")
        if p == "/cart.js":
            self._json(cart_json())
            return None
        # Product JSON, as Shopify serves it. The wishlist reads price, stock and
        # tags from here rather than storing them, so saved items stay current.
        if p.startswith("/products/") and p.endswith(".js"):
            handle = p[len("/products/"):-len(".js")]
            for i, entry in enumerate(CATALOGUE):
                if handleize(entry[0]) == handle:
                    self._json(product_json(i))
                    return None
            self._json({"errors": "Not Found"}, 404)
            return None

        # Unknown store-ish path -> the theme's own 404 page, like a real store.
        p = urllib.parse.unquote(self.path.split("?")[0])
        if not os.path.exists(self.translate_path(self.path)) and not p.startswith("/preview/"):
            fallback = os.path.join(PREVIEW, "404.html")
            if os.path.isfile(fallback):
                body = open(fallback, "rb").read()
                self.send_response(404)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                import io
                return None if self.command == "HEAD" else io.BytesIO(body)
        return super().send_head()

    def end_headers(self):
        # This preview gets rebuilt constantly, and the old root used to be a
        # redirect to the design pages — a cached copy of that keeps sending
        # reviewers to the wrong site. Never let anything cache.
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8734
    print(f"McCormack's preview -> http://localhost:{port}/  (Ctrl-C to stop)")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
