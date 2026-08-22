"""Local preview server: maps real Shopify URLs onto the rendered preview files,
so the site behaves like a store — /collections/skincare opens the Skincare
category page instead of 404ing.

Plain `python3 -m http.server` cannot do this: the theme's links are absolute
Shopify paths (/collections/<handle>) with no matching file on disk.

  python3 setup/serve_preview.py [port]        # default 8734
  npm run dev                                   # same thing
"""
import os, posixpath, sys, urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREVIEW = os.path.join(ROOT, "preview")


def first_existing(*rels):
    for r in rels:
        if r and os.path.isfile(os.path.join(ROOT, r)):
            return "/" + r
    return None


def route(path):
    """Shopify URL -> preview file. None falls through to the filesystem."""
    p = urllib.parse.unquote(path.split("?")[0].split("#")[0]).rstrip("/") or "/"

    # /index.html would otherwise hit the project's root redirect file, which
    # bounces to the ORIGINAL DESIGN homepage — not what we want to serve.
    if p in ("/", "/index.html", "/index.htm"):
        return "/preview/index.html"
    if p == "/collections":
        return "/preview/list-collections.html"

    if p.startswith("/collections/"):
        handle = p[len("/collections/"):].split("/")[0]
        # Every collection was rendered into categories/. No generic fallback:
        # an unknown handle should 404, not quietly render a blank collection
        # page and hide a broken link.
        return first_existing(f"preview/categories/{handle}.html",
                              f"preview/collection.{handle}.html")
    if p.startswith("/pages/"):
        handle = p[len("/pages/"):].split("/")[0]
        return first_existing(f"preview/page.{handle}.html", "preview/page.html")
    if p.startswith("/products/"):
        return "/preview/product.html"
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

    def send_head(self):
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
