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

### The one live submission that settles the contact forms (untested)

Seven `form 'contact'` posts ship in this theme — back-in-stock, contact page,
withdraw-from-contract, services booking, careers, and both prescription forms —
and **not one has ever been submitted on a store.** `setup/verify/back-in-stock.py`
passes against `render_preview.mjs`, whose `form` tag emits a bare
`<form method="post">` with no action and no `form_type`: it proves the markup, and
can prove nothing about transport. Nobody knows the mail arrives, where it lands, or
what it looks like.

One submission answers all of it. Do it on back-in-stock, because that form carries
the most hidden fields and so exercises the most of what is unknown.

**1. Record the expected recipient first, so the test can fail.** Read it before
submitting, or an email that never arrives is indistinguishable from one that went
somewhere unwatched:

```
SHOP=mccormackpharmacy.myshopify.com ADMIN_TOKEN=shpat_xxx   # needs read_shop
curl -s -H "X-Shopify-Access-Token: $ADMIN_TOKEN" \
  "https://$SHOP/admin/api/2025-01/shop.json" \
  | python3 -c 'import sys,json; s=json.load(sys.stdin)["shop"]; print(s["email"], s["customer_email"])'
```

Without a token: **Settings → Notifications**, and note whether the address there is
the pharmacy's or a Shopify-default that nobody reads.

**2. Submit.** Any sold-out product on the store shows the capture — 659 of the 2,474
hold 0 units, so no fixture is needed. Use an address you can read, with a plus-tag
(`you+bis1@…`) so the test is identifiable in the mailbox afterwards.

**3. Then answer these four, and write the answers back into this file.**

| Question | What to look for |
| --- | --- |
| Does it deliver at all? | An email arrives. If none does, check spam, then whether Shopify's reCAPTCHA challenge page appeared instead of the redirect. |
| Who receives it? | Compare against the address recorded in step 1. If they differ, the theme is fine and the store setting is wrong. |
| Does the body survive? | `contact[body]` was added 11 Sep 2026 and is the field most likely to be rendered. It should carry product, SKU and link on its own lines. |
| Do the extra fields survive? | Whether `contact[form_type]`, `contact[product]`, `contact[sku]` and `contact[product_url]` appear in the email at all. **If they do not, every filtering plan in `MAINTENANCE.md` depends on the body text instead** — say so there. |

Also confirm the redirect returns to the product page with `?contact_posted=true` and
the success panel renders, rather than dumping the shopper on `/contact`.

Two known risks this is testing for. Until 11 Sep 2026 the form sent no
`contact[body]` at all, alone among the seven — a body-less contact post may be
dropped silently, which would have meant every request since launch vanished with no
error shown to the shopper. And `contact[tags]` does **not** apply here: tags belong
to `form 'customer'`, so nothing marks these server-side and filtering is a mail rule
on the body text or nothing.

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
- Collection images, video and 3D media. Product images per variant are now
  modelled locally (the CeraVe fixture gives each variant its own photo and the
  gallery follows the selection), but no store has been seen doing it.
- **`option.selected_value` when the first variant is sold out — ANSWERED 11 Sep 2026,
  on the store. It was a harness defect, not a production one.**

  Settled by creating a disposable `ZZ TEST` product with two options and its first
  variant (Tub / 177ml, EUR 14.50) deliberately unavailable, then loading it with no
  query string. Both the shipped code and the pre-fix code were pushed and measured.

      shipped (current_variant.options[opt_i])  picker: Tub / 454ml   form id: ...913227 (Tub / 454ml)
      pre-fix (option.selected_value)           picker: Tub / 454ml   form id: ...913227 (Tub / 454ml)

  Identical. So on real Shopify `option.selected_value` falls back to the first
  AVAILABLE variant - the third of the three readings sketched in the old note, and the
  only one that does not produce the defect. The picker never named the sold-out
  combination, and the no-JS select rendered it `disabled` and unselected.

  What this means: the theme was never wrong on Shopify about this, and the fix in the
  picker is belt-and-braces rather than a repair. **The harness was the thing lying** -
  it modelled `selected_value` as falling back to the first variant, which Shopify does
  not do. Worth keeping the fix regardless, because it depends on nothing undocumented.

  The test product was deleted afterwards; the catalogue is back to 2,474.

- Real product handles. Fixture handles are invented from titles.
- Gift card page: `{% layout none %}`, QR code, wallet pass. The harness
  wraps it in the theme layout.
- The password page and blog comments.

### The catalogue has no variants because the import flattened them (11 Sep 2026)

Checked against the Admin API: all 2,474 products have exactly one variant, so no
product page on the store has ever rendered a variant picker. That is not because the
client sells no ranges. It is because sizes arrived as **separate products**.

    Revive Active Original 7Pk                            EUR  17.99
    Revive Active Original 30Pk                           EUR  59.95
    Revive Active 3 Month Supply - 90 Sachets              EUR 127.99
    Revive Active 6 Month Supply -180 Sachets              EUR 249.99
    Revive Active Original 210 Sachets 7 Months Supply     EUR 299.99
    Revive Original 1 Year Supply 360 Sachets              EUR 479.99

Six sizes of one product, six handles, six PDPs. The same shape repeats across
Nicorette (strength x pack size), Dulcolax (4 pack sizes), Optibac S.Boulardii (16 and
40), Chanel No5 (35/50/100ml) and the rest of the Revive range.

A conservative grouping - strip trailing size and pack tokens, then look for collisions
- finds **115 families and 138 products that are sizes of another product, 5.6% of the
catalogue**. Treat that as a floor, not a count. The titles are not systematic: the same
range appears as "Revive Active Original 30Pk", "Revive Active 3 Month Supply" and
"Revive Original 1 Year Supply", with the brand prefix drifting between "Revive Active"
and "Revive". Nothing automated can regroup those reliably, which is itself the finding.

**This is a catalogue question for the client, not a theme one.** It changes what the
variant work is protecting against:

- The variant picker, its sold-out states and the `selected_value` question above are
  all currently theoretical on this store. Nothing exercises them.
- The real cost is on the storefront: six near-identical PDPs compete with each other in
  search and in collection grids, none carries a "choose your size" control, and a
  shopper comparing 30Pk against 90 sachets has to navigate between pages to do it.
- Re-grouping is a merchandising decision with SEO consequences (five of every six URLs
  would become variants rather than pages, so redirects matter), and it cannot be done
  from the theme.

Also worth putting to the client: **inventory is placeholder.** Of 2,474 products, 1,815
hold exactly 1 unit and 659 hold 0. Nothing holds more than one. So "in stock" on this
store means "someone set it to 1", and any check that depends on stock levels - the
sold-out fixture, back-in-stock, low-stock messaging - is reading scaffolding.

### Getting a multi-variant product onto the store

Nothing on the store exercises the variant picker, so the `option.selected_value`
question above cannot be settled there as things stand. Three ways, cheapest first.
None of them requires seeding design fixtures into the client catalogue, which is the
thing to avoid: `provision.mjs all` skips `products` deliberately, and the ten design
products would be indistinguishable from real stock once in.

1. **One disposable test product, clearly named.** Create a single product by hand or
   by API — title prefixed `ZZ TEST` so it sorts last and reads as scaffolding, status
   `draft` or unpublished from the Online Store channel so no shopper can reach it, with
   two options and the first variant's inventory at zero. A draft product still renders
   on a preview link, which is all the check needs. Delete it afterwards. This is the
   only option that produces the exact shape the defect needs without touching client
   data, and it is reversible by deletion.

2. **Temporarily zero one real variant's inventory.** Cheapest in effort, but there is
   no real product with two variants to do it to — see above — so this only becomes an
   option after (1) or (3). Noted because it is the obvious instinct and it does not
   work here.

3. **Add a second variant to one real product.** Smallest footprint on paper, worst in
   practice: it edits client catalogue data, the change is not cleanly reversible (the
   variant carries its own inventory and can be ordered), and if the client re-imports
   the catalogue the edit either vanishes or conflicts. Only worth it if the client
   confirms a product genuinely has variants that the import flattened.

Recommended: (1). Whichever is used, the product must have **two options** and its
**first variant unavailable**, because that is the state the defect needs, and it should
be deleted once the question is answered rather than left as permanent scaffolding.

## States that exist nowhere — not a missing check, a missing state

A third category, distinct from the two above. Some defects are invisible not
because no check looks for them and not because the harness models something
wrongly, but because **the condition that triggers them has never existed in any
data the theme has ever rendered** — locally or on the store. No check can fail
on a state that never occurs, so the surface looks verified from both sides while
being entirely untested.

The worked example, found 11 September 2026. The product page displayed one
variant's option values while its price, stock line and submitted id belonged to
a different one, so pressing Add To Bag bought a variant the page was not showing.
It needs one condition: a product whose FIRST variant is unavailable. That
condition had never existed anywhere.

- Every product on the store has a single variant. Checked 11 Sep 2026 by walking all
  2,474 products through the Admin API: **zero** have more than one. There is no
  exception, so no product page on the store has ever rendered a variant picker at all.
- The one multi-variant product in the fixtures, `vitamin-d3-1000iu-60-capsules`, has
  its first variant in stock; its sold-out variant is the third. It exists locally only
  — it is not on the store, so nothing on the store has ever rendered this shape.
- The one local multi-variant fixture was the same product, with the same shape.

So the store could not show it, the harness could not show it, and no amount of
checking either would have found it. It surfaced only when a fixture was built
specifically to hold the state: a second multi-variant product with its cheapest
variant sold out and first in the list. Four more defects fell out of the same
fixture at the same time, for the same reason — its other novelties (two options,
a combination no variant covers, genuinely different images per variant) were also
states nothing had ever rendered.

The lesson for anything added here: ask what state a surface needs in order to go
wrong, then ask whether that state exists in any fixture or on the store. If the
answer is no, the surface is untested however green the suite is, and the fix is a
fixture rather than a check. Known gaps of this shape, still unrendered anywhere:
a product with video or 3D media, a variant with no SKU, a product with more than
two options, and a cart line whose variant has a quantity rule.

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

### Nothing in the theme knows what a medicine is — **decision** (11 Sep 2026)

Two separate features claim to act on medicines. Neither can tell what one is,
and both are wrong in the same direction on the same products.

| Feature | Where | What it actually tests |
|---|---|---|
| Pharmacist lines in the buy box (PSI-registered, Ask a pharmacist, the PSI mark) | `snippets/buy-assurance.liquid` | `restricted_tag` on the product, **or** its type's department is `Pharmacy` |
| One-click add suppression on listings, search and rails | `snippets/product-restricted.liquid` | `restricted_tag` on the product |

Both resolve, on this catalogue, to the same question: **did the client file this
product under the Pharmacy department?** That is a merchandising fact, not a
clinical one, and the two are not the same set.

`restricted_tag` is set to `pharmacist-review`, which the client applies to all 521
Pharmacy-department products — so the tag arm and the type arm select nearly the
same products, and tightening either one alone changes nothing. Voduz Sun Savers
Mini Travel Set is the worked example: a suncare travel set, typed under
`Pharmacy > Travel Sickness`, showing "Ask a pharmacist before you buy" and the PSI
registration mark next to its Add to bag.

**This is the same gap as the questionnaire gating list.** The collection FAQ's
screening claim was pulled in `0af9da9` because the theme cannot honour it, and it
returns only when the client's pharmacist specifies which products need it. That
list — which products are actually medicines — is the same list both features
above are missing, and it is the client's to supply. It cannot be derived from the
catalogue: the department tree was built to merchandise a shop, and it puts a
suncare set and a pharmacy-only medicine on the same branch.

**What is needed:** a tag the client applies per product on clinical grounds,
distinct from `pharmacist-review`, which today means "sold in the pharmacy
department". Until then both features are over-inclusive by design, and no
condition either snippet can express will fix it — the signal is not in the data.

**Not yet counted:** how many of the 521 are non-medicines like the Voduz set. That
needs an Admin API token with `read_products`; the storefront is password-protected
and `/products.json` redirects. Ask for the count before quoting a number.

*Note on the prefix fix.* `buy-assurance.liquid` matched the department with
`slice: 0, 8`, a bare prefix, so a department merely beginning with the word — a
`Pharmacy Brands` — read as the pharmacy one. That is corrected to an exact
whole-segment match, agreeing with `product-restricted.liquid`, and covered in
`setup/test_liquid.mjs`. It is a real inconsistency and it is **not** what causes
the problem above; do not mistake it for a fix.

- Free delivery threshold. The theme setting `free_shipping_threshold` is
  €65. Checked 9 September 2026 against three sources that disagreed: the live
  site said €65, the theme said €65, the client's own About copy said €60.
  €65 is taken as correct; the €60 in the About copy is the outlier. Confirm
  with the client before launch and correct whichever source is wrong.
