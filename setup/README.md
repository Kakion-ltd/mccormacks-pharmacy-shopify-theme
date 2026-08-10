# Store setup

Everything needed to provision a Shopify dev store to match the theme in `shopify-theme/`.

## Files
- `taxonomy.json` — the full nav taxonomy extracted from the design mega-menus (source of truth).
- `collections.json` — all 293 category + brand collections (handle, title, level, nav paths, draft description).
- `brands.json` — the 88 brands behind the A–Z index on the Brands page (source for `gen_brands.py` and the brand collections).
- `provision.mjs` — creates collections, nav menus, pages, the Health Hub blog, and the product metafield definitions the product page reads, via the Admin GraphQL API. Idempotent; runnable a step at a time (`collections|menus|pages|blog|metafields|all`).
- `CONVERSION_GUIDE.md` — the design→Liquid conversion rules used to build the theme.
- `extract_taxonomy.py`, `build_manifest.py`, `gen_mega.py`, `gen_category_nav.py`, `gen_brands.py` — regeneration scripts. **The mega menu, category chips, breadcrumbs and brand A–Z are generated** — edit the JSON and re-run, don't hand-edit the snippets.

## Order of operations
1. Create a dev store + a custom app token with scopes: `write_products`, `write_online_store_navigation`, `write_online_store_pages`, `write_content`.
2. `SHOP=store.myshopify.com ADMIN_TOKEN=shpat_xxx node provision.mjs all`
3. Upload the theme: `shopify theme push --path shopify-theme`, or upload `dist/mccormacks-theme.zip` under Online Store → Themes → Add theme → Upload zip (rebuild it with `./setup/package_theme.sh`).
4. Install the free **Search & Discovery** app and enable filters (product type, brand/vendor, price) — the collection template renders `collection.filters` automatically.
5. Import products. **Tag each product with its exact category title(s)** (e.g. `Pain Relief & Headache`, `Vitamins`) — the smart collections match on tags, so tagging = appearing on the right category pages.
6. Install a review app (Judge.me, Loox, Okendo…). Star ratings render from the standard `reviews.rating` metafields as soon as it writes them, and the product page has a review-widget slot — add the app's block to the "Product page" section in the theme editor.
7. In theme settings, assign the homepage "On Sale This Month" collection, hero slides, social URLs (the footer icons stay hidden until set), and — if you want the store locator's "Use my location" button — a latitude/longitude on each store block.

## Known placeholders (must be resolved before launch)
- Withdraw From Contract page: trader legal name, registered address, customer service email/phone, PSI Internet Supply List number ([PLACEHOLDER] markers in the section defaults).
- Real photography for striped-placeholder tiles.
- Checkout is Shopify-hosted: brand it under Settings → Checkout (colors/logo/font); the designed multi-step checkout page cannot be recreated on non-Plus plans.
- Cookie Policy page carries placeholder wording pending the real text and cookie list.
- The 293 collection descriptions are auto-generated draft copy — review before launch.
- The mega menu is generated Liquid, **not** the Shopify navigation menu: editing navigation in admin has no storefront effect. Change `taxonomy.json` and re-run `gen_mega.py` + `gen_category_nav.py`.
