# Maintenance warnings — McCormack's Pharmacy theme

Things a future maintainer can get wrong quietly. Each one is a value or a rule
that used to live in more than one place, and the note says where it lives now.

---

## Free delivery threshold — one setting, 62 former hardcodes

**Change it in one place: Theme settings → Brand → Free delivery threshold.**
Never type the amount into markup again.

Before this was consolidated, the number was written out in **62 places across
18 files**, and the cart page had its own copy in cents. Moving the setting
would have changed the bag drawer's progress bar and nothing else — the cart
page, the announcement strip and every "free delivery over" line would have gone
on advertising the old figure.

| File | Hardcodes | What they were |
|---|---|---|
| `setup/collections.json` | 39 | Collection description copy, pushed to the store by `provision.mjs` |
| `shopify-theme/sections/main-cart.liquid` | 4 | `assign free_delivery_threshold = 6500`, two copy lines, one comment |
| `shopify-theme/sections/main-product.liquid` | 2 | Trust strip and buy-box copy |
| `shopify-theme/sections/page-shipping.liquid` | 2 | Shipping policy copy |
| `shopify-theme/templates/collection.new-in.json` | 2 | Banner copy and FAQ answer |
| `shopify-theme/sections/announcement-bar.liquid` | 1 | Schema default for the centre text |
| `shopify-theme/snippets/trust-row.liquid` | 1 | Sitewide trust strip |
| `shopify-theme/templates/collection.beauty.json` | 1 | FAQ answer |
| `shopify-theme/templates/collection.bundles.json` | 1 | FAQ answer |
| `shopify-theme/templates/collection.fragrance.json` | 1 | FAQ answer |
| `shopify-theme/templates/collection.gifting.json` | 1 | FAQ answer |
| `shopify-theme/templates/collection.hot-offers.json` | 1 | FAQ answer |
| `shopify-theme/templates/collection.json` | 1 | FAQ answer (the fallback used by most of the 293 collections) |
| `shopify-theme/templates/collection.medicines-health.json` | 1 | FAQ answer |
| `shopify-theme/templates/collection.mother-baby.json` | 1 | FAQ answer |
| `shopify-theme/templates/collection.skincare.json` | 1 | FAQ answer |
| `shopify-theme/templates/collection.toiletries.json` | 1 | FAQ answer |
| `shopify-theme/templates/collection.vitamins.json` | 1 | FAQ answer |

### How it works now

- **Liquid copy** renders `{% render 'free-delivery-amount' %}`.
- **Merchant-editable copy** — announcement bar text, collection FAQ answers,
  collection banner text and collection descriptions — uses the token
  `[threshold]`, which the theme replaces at render time. Anyone writing new
  copy in the theme editor should type `[threshold]`, not a number.
- **Maths** (the cart page and drawer progress bars) reads
  `settings.free_shipping_threshold | at_least: 1 | times: 100`. The
  `at_least: 1` is load-bearing: the cart page divides by it, so a merchant
  entering `0` would otherwise throw a Liquid error. The setting is typed
  `number` for the same reason — as text, `€65` silently evaluated to zero.

### Checking it after a change

Set the threshold to something distinctive, re-render, and confirm the old
number is gone everywhere:

```sh
npm run render
grep -rl "€65" preview/          # should return nothing
```

---

## Restricted products — tag, not code

**Theme settings → Pharmacy → Restricted product tag** (default
`pharmacist-only`). Products carrying the tag lose the one-click add on every
listing, search result and recommendation, and link to the product page instead.

Two rules for anyone adding a new product grid or rail:

1. Compute the gate with `{% render 'product-restricted', product: p %}` and
   capture it. Do not re-implement the tag test inline; matching is
   case-insensitive and exact-per-tag for a reason.
2. Never build an add-to-cart surface in JavaScript that picks its own
   products. The cross-sell rail and the search suggestions both fetch
   *server-rendered sections* precisely so the filtering cannot be bypassed by
   client code.

**This is suppression, not a suitability check.** The product page's own Add to
bag is ungated. The collection FAQ used to claim customers are screened with
questions before adding restricted medicines to the basket; that claim was
removed in `0af9da9` because the theme cannot honour it. It goes back only when
a real questionnaire is built to the client's pharmacist specification.

---

## Analytics lives in the admin, not the theme

No tracking code belongs in `layout/theme.liquid` or Additional Scripts —
Additional Scripts is removed on 26 August 2026, and theme-level scripts cannot
observe checkout, so they can never report `begin_checkout` or `purchase`.

GA4 comes from the Google & YouTube channel; Meta from a custom pixel under
Settings → Customer events. See [`analytics/README.md`](./analytics/README.md).
Adding a second GA4 tag alongside the channel double-counts revenue.
