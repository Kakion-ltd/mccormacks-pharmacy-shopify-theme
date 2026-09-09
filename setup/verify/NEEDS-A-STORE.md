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

- `canonical_url`, including what Shopify sets on page 2 of a collection and
  on a collection-scoped product URL.
- `page_title` and `page_description` per resource. The harness derives the
  title from the template filename and uses one constant description.
- Sitemap, robots, structured data as Google actually reads it.

## Customer accounts — **decision**

- Whether the store uses classic or new customer accounts. With new customer
  accounts, every `templates/customers/*` file never renders and `/account`
  redirects off-site. The theme ships classic templates.
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

## Routes the harness does not model

- `/collections/<handle>/<tag>`, `?sort_by=`, `?filter.*`, `?page=` outside
  the paginated fixture, `?variant=` on a product.
- `/blogs/<blog>/tagged/<tag>`, `/account/orders/<id>`, `/account/logout`,
  `/account/recover`, `/account/reset`, `/account/activate`, `/challenge`,
  `/policies/*`, `/checkout`.
