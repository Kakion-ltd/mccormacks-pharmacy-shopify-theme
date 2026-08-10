# Overnight Build Report — McCormack's Pharmacy Shopify Theme

**Date:** 9 Aug 2026 · **Scope:** Make the design handoff Shopify-ready, build out every individual category page, audit, fix findings.

## What was delivered

### 1. A complete, uploadable Shopify Online Store 2.0 theme — `shopify-theme/`
- **155 files: 62 Liquid sections/snippets/layouts, 38 JSON templates**, all 26 design pages recreated per the hifi handoff (near-verbatim markup, design tokens as CSS variables, Mulish + Arial Rounded stacks).
- **Global shell**: announcement bar, header (search, wishlist/cart/account, cart count badge), all **8 mega-menus generated from the design markup** with every link mapped to a real collection URL, mobile drawer, footer (newsletter via `{% form 'customer' %}`, PSI badge, payment icons, mobile accordions).
- **Homepage**: 11 sections (hero slider with 5 editable slide blocks, category pills, promo strip, collection-driven "On Sale This Month" grid with AJAX add-to-bag, feature tiles, popular categories, hot offers, reviews blocks, brand slider, services grid).
- **Collection template** driving every category page: real storefront facet filters (`collection.filters` — brand/list/price), sort, pagination, sale badges, FAQ blocks, "You may also like" rail, empty-state that keeps layout. Variants: `collection.sale`, `collection.new-in`, `collection.bundles`, `collection.medicines-health` (design-specific banner/SEO copy).
- **Product template** generalized from the fabÜ design: gallery, variant/price sync, metafield-driven tabs (description/ingredients/how-to-use), rating metafields, recommendations with fallback, sticky mobile buybar.
- **Cart** (bag step; Shopify-hosted checkout noted in-code as not themeable), AJAX quantity/remove, free-delivery progress bar, discount code.
- **Classic customer accounts**: login/recover, register, reset/activate, dashboard with orders + prescriptions CTA, order detail, addresses CRUD.
- **Content pages**: About, Contact (working contact form), Careers (role blocks), Store Locator (7 stores as editable blocks), In-Store Services (9 services, hub→detail→booking), Prescriptions (submit/repeat forms), Health Hub blog + article, Brands index, Gift Vouchers (amount picker, delivery method, scheduling UI), 7 legal/delivery pages, **Withdraw From Contract** with full client-side validation + reference-number success panel and printable EU model form — all `[PLACEHOLDER]` legal markers preserved.
- Plus required boilerplate: 404, password, gift card, search, list-collections, generic page.

### 2. Every individual category page — `setup/`
- `taxonomy.json` — full nav taxonomy extracted from the design mega-menus (11 top-level menus, 30 groups, 163 leaf categories).
- `collections.json` — **210 collections** (handle, title, level, nav paths), deduped where the design reuses a category, plus 5 brand collections.
- `provision.mjs` — idempotent Admin GraphQL script that creates all 210 collections (smart, tag-matched; vendor-matched for brands), the 3-level navigation menu, all 16 pages (wired to their templates), and the Health Hub blog. One command: `node provision.mjs all`.
- Every category link in the theme resolves to a manifest handle (210 distinct links verified).

## Audit

Three layers, all automated and repeatable (scripts in `setup/` + scratchpad):
1. **theme-check** (Shopify's official linter) over the whole theme.
2. **Render smoke tests** — every template rendered with mocked Shopify objects (products, cart, customer, filters, orders); output scanned for errors and un-ported design artifacts.
3. **Visual + functional pass** — 24 full-page screenshots of rendered templates compared against the design references; Playwright drives mega-menus, drawer, hero dots, rails, accordions, withdraw validation.

### Findings fixed (5)
| # | Finding | Fix |
|---|---------|-----|
| 1 | 35 `<img>` tags missing width/height (CLS risk) | Added real intrinsic dimensions from asset files |
| 2 | Section schema name over Shopify's 25-char limit | Shortened |
| 3 | 5 brand links (`/collections/cerave` …) had no collection behind them | Added brand collections to manifest + vendor-rule provisioning |
| 4 | Required generic `page` template missing (uploads would fail validation) | Added `main-page` section + `templates/page.json` |
| 5 | Newsletter styling relied on form-attribute passthrough | Moved to wrapper div (robust in any renderer) |

### Warnings triaged, not bugs (7 remaining)
- 271 `HardcodedRoutes` → nav taxonomy is deliberately static per the client's fixed-order brief; disabled in `.theme-check.yml` with a comment (re-enable if nav moves to linklists).
- 5 `RemoteAsset` → Google Fonts (Mulish), per the design.
- 2 `UndefinedObject 'email'` → documented Shopify global in the reset-password template; linter false positive.

### Final state
- theme-check: **0 errors**
- Render smoke: **39/39 templates render clean**
- Structural: all section/snippet/asset references resolve; all 210 collection links + 16 page links verified; full required-template set present
- Functional: mega-menu open/switch/close, mobile drawer, hero slide dots, scroll rails, footer accordions, withdraw validation + `WD-XXXXXX` reference generation all pass

## Mobile audit (follow-up pass)

All 39 templates rendered at **390px** (phone) and **768px** (tablet): **zero horizontal overflow on every page at both widths**. Interactions verified on mobile: nav drawer, collection "Refine By" filter toggle, store-locator detail views, services hub→detail→booking, prescriptions tabs, gift-voucher calendar, product sticky buy bar.

Findings fixed (2):
| # | Finding | Fix |
|---|---------|-----|
| 6 | PSI badge overlapped the "Policies" footer accordion on every mobile page — a bug inherited from the design itself (desktop `-40px` pull-up never reset in mobile CSS) | Reset in `base.css` mobile block, with a comment |
| 7 | Product page: fixed mobile buy bar covered the last 82px of page content at scroll end | `padding-bottom` added under the bar's media query |

## Category build-out (follow-up pass)

Every one of the 210 category pages now has its own identity, not just the shared template:

- **Per-category breadcrumbs** — full parent trail (`Home / Medicines & Health / Pain Relief / Muscle & Joint Pain`), generated from the taxonomy into `snippets/category-breadcrumb.liquid`.
- **Per-category sub-nav chips** — departments show their groups, groups show their categories, categories show their siblings with the current one highlighted (`snippets/category-chips.liquid` + `category-chip.liquid`; previously every page showed the Medicines & Health tree). Generator: `setup/gen_category_nav.py`.
- **Per-category descriptions** — draft intro/SEO copy for all 210 collections in `collections.json`, provisioned via `descriptionHtml` (**draft copy — client to review**).
- **Department banner templates** — 8 new `collection.<handle>.json` templates (Vitamins, Beauty, Skincare, Toiletries, Mother & Baby, Fragrance, Gifting, Hot Offers) with design-voice banner copy; provisioning now assigns each templated collection its `templateSuffix`.
- **Wishlist + Loyalty Rewards Club pages** (per user decision) — on-brand pages at `/pages/wishlist` and `/pages/loyalty-rewards-club`; header/drawer wishlist icons and the footer loyalty link now point at them; both added to provisioning. No demo-content seeding (per user decision).
- **Every category page viewable locally** — `preview/categories/` holds a mock-rendered page per collection plus an A–Z index (`/preview/categories/index.html`).

Verified: 49/49 templates + 210/210 category previews render clean; all structural checks pass (210 collection links, 18 page links); theme-check 0 errors; leaf/group/department breadcrumbs and chip sets spot-checked; mobile overflow scan clean on sampled category pages.

## Mega-menu usability pass (follow-up)

Audit found the dropdowns were mouse-only. Now (all in `theme.js` + one CSS rule):
- **Keyboard**: tabbing onto a nav item opens its panel, Tab moves through the open panel's links, focus leaving the nav closes it, **Esc** closes. `aria-haspopup`/`aria-expanded` kept in sync.
- **Touch (tablets)**: first tap opens the panel instead of navigating, second tap follows the link, tapping outside closes. (Tap-fired synthetic hover/focus events are filtered out via `hover:` media queries and `:focus-visible`.)
- **Hover robustness**: 250ms close grace on mouseleave (no more snap-shut on accidental exits); the open menu's nav item stays highlighted green while browsing its panel.
- Hero carousel also gained the spec'd auto-rotate (6s default, editor setting, pauses on hover, stops on manual use, honors reduced-motion) — the "auto" half of the README's "auto/manual carousel" was never implemented in the design files.

## To go live (see `setup/README.md`)
1. Dev store + custom app token (`write_products`, `write_online_store_navigation`, `write_online_store_pages`, `write_content`).
2. `SHOP=… ADMIN_TOKEN=… node setup/provision.mjs all`
3. `shopify theme push --path shopify-theme`
4. Install the free **Search & Discovery** app (activates the filter UI already in the template).
5. Import products, **tagging each with its exact category title(s)** — tags are what populate the smart collections.
6. Assign homepage collection/slides in the editor.

## Open items (decisions or content someone must supply)
- **Legal placeholders** on Withdraw From Contract: trader name, registered address, PSI number, customer-service contacts, excluded-products list (pending legal review).
- **Checkout**: Shopify-hosted; brand it in admin (full checkout design needs Plus).
- **File uploads** (prescriptions, CV): rendered disabled; needs a forms app or custom app.
- **Wishlist**: header icon links to account (as designed); real wishlist needs an app.
- Real photography for striped-placeholder tiles; reviews platform if live review data is wanted.
- 'Arial Rounded MT Bold' renders on macOS/iOS; other platforms fall back to Arial. License a rounded webfont for full parity.

## Local preview
- `preview/` — every template mock-rendered to static HTML (open via the local server: `python3 -m http.server 8734` from project root, then `/preview/index.html`).
- The original HTML design references still run at `/pages/…` (unchanged).

---

# Audit + fix pass (9 Aug)

A full-site audit ran across five layers: theme-check, mock render of all 49 templates
and 293 category pages, a design-vs-theme heading parity check on all 26 design pages,
a Playwright visual sweep (desktop 1440 + mobile 390) and an interaction sweep that
clicks every control on the site.

## Product reviews removed — a review app now owns them

The theme was drawing **five-star ratings that no product had earned**: hardcoded
`★★★★★` rows on collection cards (grid and list), search results, the homepage sale
rail, and five invented review counts on the Gift Vouchers page.

All of it is gone. Ratings now render through one snippet, `snippets/product-rating.liquid`,
which reads the standard `reviews.rating` / `reviews.rating_count` product metafields that
Judge.me, Loox, Okendo and Shopify Product Reviews all write to. **If no app is installed,
or a product has no reviews yet, it renders nothing** — the theme never invents a rating.
`scratchpad/test_product_rating.mjs` locks that behaviour in (6 assertions).

The product page also gained an `#product-reviews` landing zone accepting an `@app` block,
so the review widget drops in from the theme editor and the star rating links down to it.

The homepage testimonial rail is *store* reviews (real Google reviews of the pharmacy),
not product ratings — left as-is and marked `data-testimonials`.

## Bugs fixed

| Bug | Fix |
|---|---|
| Footer Facebook/Instagram/TikTok rendered `href=""` on **every page** — links that silently reloaded the page | Hidden until a URL is set |
| Scroll rails showed a "next" arrow on rails with nothing to scroll | Both arrows now hide when they have nothing to do; re-checked on resize |
| Closed mobile drawer kept **16 links in the tab order** — keyboard users tabbed through an invisible menu | `visibility:hidden` when closed (still animates) |
| Store Locator "Search" and "Use my location" did nothing | Search filters the list live (name, address, Eircode, badge) with a no-results state; "Use my location" sorts nearest-first and only appears once stores have coordinates |
| Brands "Search brands" did nothing to the A–Z index | Live filter; empty letter groups collapse and their A–Z chips grey out; form still falls back to product search without JS |
| 25 `href="#"` controls (20 gift voucher, 4 PDP, 1 locator) | All now real `<button>` elements with `aria-pressed`/`aria-expanded`; **zero `href="#"` left in the theme** |
| Gift-voucher placeholder cards linked nowhere | Now link to `/collections/gifting` |

## Merchant editability

- **Hot Offers** was hardcoded — three tiles no one could edit. Now `offer` blocks with
  title, subtext, badge, button label + link, image, tile colour and badge colour.
- **Brand slider** was hardcoded and every tile pointed at `/pages/brands`. Now `brand`
  blocks, each linking to **its own brand collection**, with a logo picker.
- Both are wired into `templates/index.json`, so an existing store picks them up (presets
  alone only apply to newly added sections).
- NIVEA and Piz Buin were missing from the brand list despite appearing in the designs —
  added, so the manifest is now **293 collections** (88 brands).

## Still not built (needs content, a decision, or an app)

- **No products and no blog articles.** Provisioning creates collections, menus, pages
  and the blog; the catalogue import is the client's. All category pages are empty until then.
- **"Buy More, Save More"** volume pricing on the PDP — needs a discount app or Shopify Functions.
- **Store locator map** is a placeholder; store **coordinates** are unset (that's why
  "Use my location" is hidden — fill in lat/lng per store to switch it on).
- **File uploads** (prescription, CV) still route to the contact form.
- **Wishlist / Loyalty Rewards Club** are explainer pages only.
- **Cookie Policy** still carries placeholder wording pending the real text.
- The **mega menu is generated Liquid, not the Shopify navigation menu** — editing
  navigation in admin has no storefront effect; re-run `setup/gen_mega.py` after taxonomy changes.
- 293 collection descriptions are auto-generated draft copy for client review.

## Verification

theme-check 0 errors · 49/49 templates render clean · 293/293 category pages render clean ·
293 collection links + 18 page links all resolve · 6/6 rating snippet assertions ·
36/36 interaction checks · visual sweep clean at 1440 and 390 (no overflow, no broken
images, no JS errors) · 0 dead links site-wide.

---

# Shopify-ready pass

A pre-upload validation (`scratchpad/audit_shopify_ready.py`) now checks the cross-file
integrity that breaks a `theme push` or the theme editor but that theme-check does not
cover: every section type referenced by a JSON template exists; every block type and
setting id in those templates exists in that section's schema; `block_order` resolves;
every `{% render %}` snippet, `asset_url` and `| t` translation key resolves; schema
setting types are valid and ids unique; presets only use declared block types;
`settings_data.json` only sets declared settings; and `theme_info` is complete.

It found and fixed:

- **`theme_info` still pointed at `example.com`** — would have shown as the theme's
  documentation and support links in the merchant's theme editor.
- **The product page read two metafields nothing created.** The Ingredients and
  How To Use tabs render from `custom.ingredients` / `custom.how_to_use`, but no
  definition existed, so staff had no field to fill in and the tabs could never appear.
  `provision.mjs` now creates both definitions (`node provision.mjs metafields`).
- **Cart AJAX hardcoded `/cart/add.js`.** That breaks under a locale or market path
  prefix (`/en-ie/cart/add.js`) — silently, on every add-to-cart. The routes now come
  from Liquid via `window.mccRoutes`, with the old paths as fallback.

## Upload package

`./setup/package_theme.sh` builds `dist/mccormacks-theme.zip` (170 files, 11 MB) with the
seven theme folders at the archive root as Shopify requires — so the theme can go up via
**Online Store → Themes → Add theme → Upload zip** without the CLI. The linter config is
the only file excluded.

## Readiness

Everything that can be verified without a store is green: 0 pre-upload integrity problems ·
0 theme-check errors · 49/49 templates and 293/293 category pages render clean · all 293
collection and 18 page links resolve · 36/36 interaction checks · 6/6 rating-snippet
assertions · visual sweep clean at 1440px and 390px · 0 dead links.

What still requires the store itself: the product import (tags drive every category page),
a review app, the Search & Discovery app for filters, and the theme-editor settings listed
in `setup/README.md`.
