# Design → Shopify Theme Conversion Guide

You are porting high-fidelity HTML design references into a Shopify Online Store 2.0 theme.

**Design sources:** `pages/*.dc.html` (project root). **Theme root:** `shopify-theme/`.

## Reading the design files

Each `.dc.html` page: real markup lives inside `<x-dc>`. Ignore `<helmet>` (shared head) and the `<script type="text/x-dc">` block at the end EXCEPT to read its `renderVals()` for data arrays (slides, products, stores, FAQs…) and interaction intent. Template syntax in markup:
- `{{ hole }}` — dynamic value from the script's renderVals
- `<sc-if value="{{ x }}">…</sc-if>` — conditional
- `<sc-for list="{{ xs }}" as="x">…</sc-for>` — loop
- `onClick="{{ fn }}"` etc — event handlers (see behaviors catalog)
- `style-hover="…"` / `style-focus="…"` — hover/focus styles

## Conversion rules

1. **Keep the design markup as close to verbatim as possible** — inline styles included. This is a hifi port; pixel fidelity beats code beauty. Page-specific responsive CSS from the page's `<helmet><style>` goes in the section's `{% style %}` block (shared shell CSS is already in `assets/base.css` — don't duplicate it; check first).
2. **style-hover / style-focus → classes.** Reuse existing utilities in `assets/base.css` (`.hov-green`, `.hov-green-dk`, `.hov-bg-green`, `.hov-bg-green-dk`, `.hov-bg-accent` (bg #92C83F), `.hov-bg-accent-dk` (bg #7FB52F), `.hov-bg-dark`, `.hov-bg-tint`, `.hov-border-accent`, `.hov-slide`). For one-offs, add a scoped class in the section's `{% style %}`.
3. **Images:** `src="assets/foo.png"` → `src="{{ 'foo.png' | asset_url }}"` (all design images already copied to theme assets). Keep the striped `repeating-linear-gradient` placeholder divs where the design uses them. For product/collection images prefer Shopify objects (`product.featured_image | image_url: width: 600 | image_tag`) with the striped placeholder as the no-image fallback.
4. **Money:** `€19.95` → `{{ product.price | money }}` when driven by product data.
5. **Copy:** design copy is final. Bake it in as schema setting defaults where an editor would plausibly change it (headings, subtext); hardcode structural labels.
6. **JS behaviors** — `assets/theme.js` already handles these via data attributes (do NOT write new JS unless truly page-specific; page-specific JS goes in a `<script>` at the end of the section):
   - Scroll rails: `id` on the track; buttons `data-rail-btn data-rail-target="<id>" data-rail-by="<±px>"`; back-arrows also `data-rail-back data-rail-target="<id>"` (auto-hidden at scroll 0)
   - Slider: wrapper `data-slider`, panes `data-slide`, dot buttons `data-slide-dot`
   - Accordions: trigger `data-acc-toggle="key"`, content `data-acc-content="key" data-open="false"`
   - Tabs/views: `data-view-btn="key"` buttons + `data-view="key"` panels (first visible by default — set `style="display:none"` on the rest)
   - Add to cart: `<button data-add-id="{{ variant.id }}">` or a product form with `data-ajax-add`; header badge updates automatically
   - Mobile drawer / mega menu: header-only, already built.
7. **Sections & templates:** each design region → `sections/<name>.liquid` with `{% schema %}` (must include `"name"`, and `"presets": [{"name": "…"}]` so it's addable in the editor). Page templates are JSON (`templates/<type>.<suffix>.json`) referencing the sections. One-section-per-content-page is fine (`sections/page-about.liquid` + `templates/page.about-us.json`).
8. **Liquid correctness:** `{% schema %}` must be valid JSON, no Liquid inside it. Don't use `{% include %}` (use `{% render %}`). Snippets go in `snippets/`.
9. **Forms:** contact-style forms → `{% form 'contact' %}` (fields `contact[name]`, etc). Newsletter → `{% form 'customer' %}`. Client-side validation UX from the designs (inline errors, success panel) may be reproduced with a small section-local script.
10. **No external JS/CSS libraries.** Google Fonts Mulish is already loaded in the layout.

## URL map (design link → theme URL)

| Design href | Shopify URL |
|---|---|
| McCormacks Homepage.dc.html | `{{ routes.root_url }}` |
| Medicines & Health.dc.html | `/collections/medicines-health` |
| Sale - Baby Categories.dc.html | `/collections/sale` |
| New In.dc.html | `/collections/new-in` |
| Bundles.dc.html | `/collections/bundles` |
| Brands.dc.html | `/pages/brands` |
| Cart - Checkout.dc.html | `{{ routes.cart_url }}` |
| My Account.dc.html | `{{ routes.account_url }}` |
| Store Locator.dc.html | `/pages/store-locator` |
| In-Store Services.dc.html | `/pages/in-store-services` |
| Health Hub Blog.dc.html | `/blogs/health-hub` |
| Prescriptions.dc.html | `/pages/prescriptions` |
| About Us / Contact Us / Careers | `/pages/about-us`, `/pages/contact-us`, `/pages/careers` |
| Withdraw From Contract.dc.html | `/pages/withdraw-from-contract` |
| Cookie/Privacy/Terms | `/pages/cookie-policy`, `/pages/privacy-policy`, `/pages/terms-and-conditions` |
| Shipping / Returns / Click and Collect | `/pages/shipping`, `/pages/returns`, `/pages/click-and-collect` |
| Internet Supply Pharmacy.dc.html | `/pages/internet-supply-pharmacy` |
| Gift Vouchers.dc.html | `/pages/gift-vouchers` |
| Search Results.dc.html | `{{ routes.search_url }}` |
| Product - fabU Skin Glow.dc.html | product template (`/products/*`) |
| Category links in copy | `/collections/<handleized-title>` (lowercase, `&`→omit, non-alnum→`-`) |

## Category collections

`setup/collections.json` lists every collection handle. Nav/category links must use those handles.

## Design tokens

CSS variables are defined in base.css `:root` (--c-primary #82C914, --c-primary-hover #6BA30F, --c-dark #3F6B4F, --c-accent #92C83F, --c-tint #E6F2D5, --c-text, --c-muted, --c-border, --c-error, --c-success…). Inline hex values from the designs may stay as-is; use vars for NEW css you author.

## Definition of done per template

- Section file(s) + JSON template committed under `shopify-theme/`
- All `{{ }}` holes resolved to Liquid or removed; no `sc-if`/`sc-for`/`style-hover`/`onClick` left in output
- All hrefs mapped per URL table; all assets via `asset_url`
- Schema JSON valid; `{% style %}` used for page CSS
- Interactions from the design list reproduced (via theme.js data-attrs or a small section script)
