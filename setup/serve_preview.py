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

    # /index.html would otherwise hit the project's root redirect file, which
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
        return first_existing(f"preview/page.{handle}.html", "preview/page.html")
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
        return "/pages/McCormacks Homepage.dc.html"
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


# The mock catalogue, mirroring render_preview.mjs by index. One table feeds both
# the cart line items and the product JSON the wishlist reads, so the two cannot
# disagree about a price the way two copies would.
CATALOGUE = [
    ("fab\u00dc Skin Hair Nails Glow 60 Capsules", "fab\u00dc", 1995, "prod-fabu-glow.jpg", []),
    ("Cetrine Allergy 10mg 30 Tablets", "Cetrine", 799, "prod-cetrine.jpg", []),
    ("Revive Active 30 Sachets", "Revive Active", 6499, "prod-revive.jpg", []),
    ("Optibac Every Day MAX 30 Capsules", "Optibac", 2799, "prod-optibac-max.jpg", []),
    ("Nurofen 200mg Ibuprofen 24 Tablets", "Nurofen", 649, "prod-nurofen.jpg", []),
    ("CeraVe Hydrating Cleanser 236ml", "CeraVe", 1350, "prod-cerave-cleanser.jpg", []),
    ("Sudocrem Antiseptic Healing Cream 125g", "Sudocrem", 799, "prod-sudocrem.jpg", []),
    ("Vitamin D3 1000IU 60 Capsules", "McCormack\u2019s", 999, "prod-vitd.jpg", []),
    ("Nurofen Plus 200mg/12.8mg 24 Tablets", "Nurofen", 1099, "prod-nurofen.jpg", ["pharmacist-only"]),
]


def handleize(title):
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def product_json(i):
    title, vendor, price, img, tags = CATALOGUE[i]
    return {
        "id": 30000000 + i, "title": title, "handle": handleize(title), "vendor": vendor,
        "price": price, "available": True, "tags": tags,
        "featured_image": f"/shopify-theme/assets/{img}",
        "variants": [{"id": 40000000 + i, "title": "Default", "price": price, "available": True}],
    }


def line_for(variant_id):
    """Line item fields the theme's drawer reads."""
    i = int(variant_id) - 40000000
    if not 0 <= i < len(CATALOGUE):
        return None
    title, vendor, price, img, _ = CATALOGUE[i]
    return {
        "id": int(variant_id), "variant_id": int(variant_id), "product_id": 30000000 + i,
        "key": f"{variant_id}:0", "title": title, "product_title": title, "vendor": vendor,
        "variant_title": None, "quantity": 0, "price": price, "final_price": price,
        "original_price": price, "line_price": price, "final_line_price": price,
        "original_line_price": price, "url": f"/products/{handleize(title)}",
        "image": f"/shopify-theme/assets/{img}",
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


def cart_add(variant_id, qty):
    with CART_LOCK:
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
        if p == "/cart/add.js":
            cart = cart_add(data.get("id"), int(data.get("quantity") or 1))
            if cart is None:
                self._json({"description": "Unknown variant in the preview catalogue"}, 422)
                return
            self._json(cart)
        elif p == "/cart/change.js":
            self._json(cart_change(data.get("line"), int(data.get("quantity") or 0)))
        else:
            self.send_error(404)

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
