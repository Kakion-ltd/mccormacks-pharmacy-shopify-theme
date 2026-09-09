# What cannot be verified without a store

The preview harness (`setup/render_preview.mjs`, `setup/serve_preview.py`) renders
the theme against mock data and answers a handful of AJAX endpoints from
pre-rendered files. Everything below is modelled, stubbed, or absent there. A
green `npm run verify` says nothing about any of it. Each item needs a dev store,
and the ones marked **decision** need a merchant answer before they can be checked.

## Checkout and payment

- Express checkout and dynamic checkout buttons: `payment_button`,
  `additional_checkout_buttons`, Shop Pay, Apple Pay, Google Pay. The harness
  draws a labelled placeholder.
- Automatic discounts, discount codes, `line_level_discount_allocations`,
  `cart.total_discount` from a real discount.
- Unit prices, selling plans and subscriptions, inventory policy for
  "continue selling when out of stock" (available true with quantity 0).
- The order status page and order confirmation.

## Search

- Real search ranking, the `q` parameter on `/search`, search filters and sort
  options, article and page results. The harness search page is one static
  render.
- Predictive search: prefix matching, `resources[type]`, `limit`,
  `unavailable_products`, and which query suggestions Shopify returns. The
  harness answers ten fixed terms by substring match and says "No matches" for
  everything else.
- Vendor and type listings at `/collections/vendors` and `/collections/types`,
  which is where `url_for_vendor` links.

## SEO and page metadata

- `canonical_url` — **checked 2026-09-09 on the dev store.** Collection page N
  canonicalises to `?page=N` and drops sort and filter params; a
  collection-scoped product URL and a `?variant=` URL canonicalise to the bare
  product URL; search and blog keep `page` and `q`. The list-collections page
  drops `page` entirely (`/collections?page=13` → `/collections`). Out-of-range
  pages return 200 with a self-canonical, so a `noindex` when
  `paginate.current_page > paginate.pages` is worth adding. The theme's own
  pagination links preserve active filters.
- `page_title` and `page_description` per resource. The harness derives the
  title from the template filename and uses one constant description.
- Sitemap, robots, structured data as Google actually reads it.

## Customer accounts — **decision**

- **Answered 2026-09-09 on the dev store: new customer accounts are on**
  (`customerAccountsVersion: NEW_CUSTOMER_ACCOUNTS`). Every `/account/*` URL
  redirects to shopify.com, so none of the seven `templates/customers/*` files
  renders. Either switch the store to classic accounts (Settings > Customer
  accounts) or accept that those templates, the account sidebar and the address
  forms are dead code on this store. The `customer` object still populates on
  the storefront after a hosted login, so the wishlist and loyalty forks work.
- Login, register, recover, reset, activate, logout, address create/edit/delete,
  `form.id` on address forms, `all_country_option_tags`, `format_address`
  ordering per country.
- Account pages with real data: orders table and its pagination, order line
  items, saved addresses. The harness renders these with a null customer.

## Forms

- What Shopify does on POST for every `{% form %}`: contact, customer
  (newsletter), login, register, address, storefront password. Redirects, the
  reCAPTCHA challenge page, `contact[tags]`, and the exact `form.errors` shape.
- The no-JavaScript submit of the product form to `/cart/add`.

## Markets, locales, currency — **decision**

- Whether the store enables markets or locales that add a path prefix. The
  theme has 657 hardcoded `href="/collections/..."` style paths in generated
  navigation (mega-menu, mobile-nav, breadcrumbs, footer) that are correct
  only at the root.
- `shop.money_format` and `money` filter output. The harness always prints
  `€x.xx`.
- `routes.*` under a prefix, `request.locale`, `localization`.

## Apps, editor, platform scripts

- App blocks (`@app`) and app embeds.
- Theme editor behaviour: `request.design_mode`, section and block events,
  `block.shopify_attributes`, presets applied when a merchant adds a section.
- `content_for_header`: Shopify's own scripts, the preview bar, Web Pixels,
  and whether consent genuinely withholds a pixel. See `../analytics/README.md`.
- Inline "Liquid error" output. Shopify prints it on the page; the harness
  swallows unknown filters and undefined variables silently.
- Output whitespace and head injection, seen 2026-09-09: Shopify emitted a
  leading newline from a snippet that opened with an undashed `{% comment %}`
  (liquidjs did not), so every alt text began with "\n" until the tags were
  dashed. `image_tag: preload: true` injected nothing into `content_for_header`,
  and a hand-written `<link rel="preload">` carrying `imagesrcset` was dropped
  from the served page; media-scoped preload links, as the hero slider writes
  them, do render. Filters inside a `for` expression are a syntax error on
  Shopify; theme-check catches that one.

## Assets and images

- CDN asset URLs and versioning from `asset_url`, and the self-hosted font
  becoming a cross-origin request to `cdn.shopify.com`.
- `image_url` transforms: crop, focal point, format negotiation, real
  `srcset` widths, and `image_picker` settings, which the harness represents
  as empty strings so the asset fallback always wins.

## Content the merchant supplies

- Menus from Navigation admin (`linklists`). The footer falls back to
  built-in columns until a named menu exists.
- Metafield definitions and the shape review apps write to
  `reviews.rating` and `reviews.rating_count`; `custom.faq`,
  `custom.ingredients`, `custom.how_to_use`.
- Collection images, product images per variant, video and 3D media.
- Real product handles. Fixture handles are invented from titles.
- Gift card page: `{% layout none %}`, QR code, wallet pass. The harness
  wraps it in the theme layout.
- The password page and blog comments.

## Harness blind spots found on the store

Each of these passed every local check and failed, or misbehaved, on the dev
store. They are the reason a green `npm run verify` is not a release signal.

1. A `text` setting with `"default": ""` is rejected at upload and takes the
   section and every template that uses it down with it. Now caught in
   `check.mjs`.
2. A lone `}` inside `{{ }}` ends the output tag on Shopify. Now caught in
   `check.mjs`.
3. Predictive search's `resources[limit]` is shared across result types unless
   `limit_scope=each` is sent. The harness answered with six products; the
   store answered with two.
4. `featured_image` on a collection with no image returns the first product's
   photo. The harness's collections had no products, so the asset fallback
   always rendered locally and never on the store.
5. `image_tag: preload: true` injects nothing into `content_for_header`, and a
   hand-written `<link rel="preload">` with `imagesrcset` is dropped from the
   page. Only media-scoped preload links render. The harness emitted all three.
6. Every alt text on the store began with a newline. The image-alt snippet
   opened with an undashed `{% comment %}`, and Shopify keeps the newline that
   liquidjs trims. It affected every product, collection and card image on the
   site and was invisible locally.

## Routes the harness does not model

- `/collections/<handle>/<tag>`, `?sort_by=`, `?filter.*`, `?page=` outside
  the paginated fixture, `?variant=` on a product.
- `/blogs/<blog>/tagged/<tag>`, `/account/orders/<id>`, `/account/logout`,
  `/account/recover`, `/account/reset`, `/account/activate`, `/challenge`,
  `/policies/*`, `/checkout`.

## Confirm with the client

- Free delivery threshold. The theme setting `free_shipping_threshold` is
  €65. Checked 9 September 2026 against three sources that disagreed: the live
  site said €65, the theme said €65, the client's own About copy said €60.
  €65 is taken as correct; the €60 in the About copy is the outlier. Confirm
  with the client before launch and correct whichever source is wrong.
