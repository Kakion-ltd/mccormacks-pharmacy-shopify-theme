"""Turn preview/ into a static site GitHub Pages can actually serve.

The preview HTML is written for a real store: links are absolute Shopify paths
(/collections/cerave, /pages/about-us) and assets live at /shopify-theme/assets.
Two things break that on Pages:

  1. A project site is served from /<repo>/, so every path starting with "/"
     misses the prefix and 404s — including the stylesheet, so the page loads
     completely unstyled.
  2. /collections/cerave has no file behind it. Locally serve_preview.py maps
     the URL onto preview/categories/cerave.html; a static host can't.

So this writes each page to the directory its URL implies
(collections/cerave/index.html) and prefixes every absolute path with the repo
base. Output goes to _site/, which the Pages workflow uploads.

  python3 setup/build_static_preview.py [--base /repo-name] [--out _site]
"""
import argparse, os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREVIEW = os.path.join(ROOT, 'preview')

# Shopify URL prefixes that appear in the markup. Anything starting with "/"
# that is NOT one of these is left alone, so we never mangle protocol-relative
# URLs or fragments.
PREFIXES = ('collections', 'pages', 'products', 'blogs', 'account',
            'cart', 'search', 'shopify-theme', 'assets')


def public_path(rel):
    """preview-relative filename -> the URL path the store would serve it at."""
    name = os.path.basename(rel)
    if os.path.dirname(rel) == 'categories':
        handle = name[:-5]
        # categories/index.html is our own A-Z listing, not a collection
        return 'collections/index.html' if handle == 'index' else f'collections/{handle}/index.html'
    if name == 'index.html':
        return 'index.html'
    if name == '404.html':
        return '404.html'          # Pages serves this for unknown paths
    stem = name[:-5]
    if stem.startswith('page.'):
        h = stem[5:]
        return 'pages/index.html' if h == '' else f'pages/{h}/index.html'
    if stem.startswith('collection.'):
        return f'collections/{stem[11:]}/index.html'
    if stem.startswith('customers_'):
        tail = stem[10:]
        return 'account/index.html' if tail == 'account' else f'account/{tail}/index.html'
    if stem == 'list-collections':
        # Not /collections/all — that is the all-products collection below, and the
        # theme links to it. This template is an unrouted extra with no canonical URL.
        return 'collections/list/index.html'
    if stem in ('cart', 'search', 'product', 'blog', 'article', 'collection',
                'page', 'password', 'gift_card'):
        return {
            'cart': 'cart/index.html',
            'search': 'search/index.html',
            'product': 'products/index.html',
            'blog': 'blogs/health-hub/index.html',
            'article': 'blogs/health-hub/article/index.html',
            'collection': 'collections/all/index.html',
            'page': 'pages/index.html',
            'password': 'password/index.html',
            'gift_card': 'gift_card/index.html',
        }[stem]
    return f'{stem}/index.html'


def rewrite(html, base):
    """Prefix absolute Shopify paths with the Pages base path."""
    pat = re.compile(r'((?:href|src|action)=")/(' + '|'.join(PREFIXES) + r')(?=[/"?#])')
    html = pat.sub(lambda m: f'{m.group(1)}{base}/{m.group(2)}', html)
    # bare href="/" -> the site root
    html = re.sub(r'((?:href|action)=")/(")', lambda m: f'{m.group(1)}{base}/{m.group(2)}', html)
    # url('/shopify-theme/...') inside inline styles
    html = re.sub(r"(url\(')/(" + '|'.join(PREFIXES) + r")(?=/)",
                  lambda m: f"{m.group(1)}{base}/{m.group(2)}", html)
    return html


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='', help='Pages base path, e.g. /my-repo')
    ap.add_argument('--out', default=os.path.join(ROOT, '_site'))
    a = ap.parse_args()
    base = a.base.rstrip('/')

    if not os.path.isdir(PREVIEW):
        sys.exit('preview/ not found — nothing to publish')
    if os.path.exists(a.out):
        shutil.rmtree(a.out)

    # Assets are referenced as /shopify-theme/assets/... so keep that shape.
    for sub in ('shopify-theme/assets', 'assets'):
        src = os.path.join(ROOT, sub)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(a.out, sub))

    # categories/ first, deliberately. Both categories/beauty.html and the
    # template render collection.beauty.html claim /collections/beauty, but the
    # latter is rendered against the mock collection — it shows "Home /
    # Medicines & Health" as the breadcrumb on every department page. First
    # writer wins, so the per-category render has to go first.
    rels = []
    for dirpath, _dirs, files in os.walk(PREVIEW):
        for f in files:
            if f.endswith('.html'):
                rels.append(os.path.relpath(os.path.join(dirpath, f), PREVIEW))
    rels.sort(key=lambda r: (0 if os.path.dirname(r) == 'categories' else 1, r))

    written, collisions = 0, []
    for rel in rels:
        dest = os.path.join(a.out, public_path(rel))
        if os.path.exists(dest):
            collisions.append(rel)
            continue
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(os.path.join(PREVIEW, rel), encoding='utf-8') as fh:
            html = fh.read()
        with open(dest, 'w', encoding='utf-8') as fh:
            fh.write(rewrite(html, base))
        written += 1

    # The harness renders a single product page, but every product card links to
    # its own /products/<handle>. Without this the grid is full of dead links.
    # They all show the same mock product — enough to review the template.
    product_src = os.path.join(a.out, 'products', 'index.html')
    if os.path.exists(product_src):
        with open(product_src, encoding='utf-8') as fh:
            phtml = fh.read()
        handles = set()
        for dirpath, _d, files in os.walk(a.out):
            for f in files:
                if f.endswith('.html'):
                    with open(os.path.join(dirpath, f), encoding='utf-8') as fh:
                        handles |= set(re.findall(
                            re.escape(base) + r'/products/([a-z0-9][a-z0-9-]*)"', fh.read()))
        for h in sorted(handles):
            dest = os.path.join(a.out, 'products', h, 'index.html')
            if not os.path.exists(dest):
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with open(dest, 'w', encoding='utf-8') as fh:
                    fh.write(phtml)
                written += 1
        print(f'  + {len(handles)} product handles aliased to the mock product page')

    print(f'wrote {written} pages to {a.out} (base={base or "/"})')
    if collisions:
        print(f'skipped {len(collisions)} duplicate targets: {collisions[:5]}')


if __name__ == '__main__':
    main()
