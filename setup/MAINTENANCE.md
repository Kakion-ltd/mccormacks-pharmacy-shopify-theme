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

## AWAITING PHARMACIST SIGN-OFF: the "Do I need a prescription?" FAQ answer

**Status: not approved. This is a compliance statement, not marketing copy, and
it stands on every one of the 293 collection pages.**

The previous answer claimed customers must answer suitability questions before
adding pharmacist-only medicines to the basket, and that a pharmacist reviews
those answers before approving the order. The theme has no such mechanism, so
the claim was removed in `0af9da9` and replaced with:

> All items in this collection can be bought without a GP prescription.
> Prescription-only medicines are not sold online in Ireland — you can submit a
> prescription for dispensing instead, and collect it in store or have it
> delivered.

**Known concern with the replacement, raised and not yet resolved:** "can be
bought without a GP prescription" may read as more permissive than intended.
Pharmacy-only (P) medicines still require pharmacist involvement even though no
GP prescription is needed, and the sentence does not say so. It draws the line
at *prescription-only*, when the line that matters to a customer is *pharmacist
involvement*.

Do not treat this wording as settled, and do not reuse it elsewhere on the site,
until a pharmacist has approved it. Where it appears:

- `shopify-theme/sections/main-collection.liquid` — the FAQ block schema default
- `shopify-theme/templates/collection.json` — the fallback most collections use
- `shopify-theme/templates/collection.{beauty, fragrance, gifting, hot-offers,
  medicines-health, mother-baby, skincare, toiletries, vitamins}.json`

Eleven places in total. Changing only the schema default leaves the saved block
copy live, which is how the original claim survived a previous edit.

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

## Store data — the opening hours format is load-bearing

Opening hours are read by Google, not just displayed, so the **Store block →
Opening hours** field takes one machine-readable format. Seven lines, one per
day, in day order, 24-hour and zero-padded:

```
Mon|09:00-18:30
Tue|09:00-18:30
Wed|09:00-18:30
Thu|09:00-18:30
Fri|09:00-18:30
Sat|09:00-18:00
Sun|closed
```

A lunch closure takes two ranges: `Wed|09:00-13:00,14:00-18:00`.

The displayed hours are derived from this — consecutive identical days are
grouped into "Mon–Fri" and times are rendered as "9.00am – 6.30pm" — so **do not
write display labels into the field**. `snippets/store-hours.liquid` is the only
parser; both display sites and the JSON-LD go through it, so they cannot drift.

Anything unparseable, and any missing day, reads as **closed**. That is the safe
direction: publishing a pharmacy as open when it is shut sends someone on a
wasted journey. It also means a typo fails quietly, so check the store page after
editing.

Bank holidays are deliberately not expressed. They move each year and schema.org
wants specific dates; the page carries a standing note instead.

### Two other store fields worth knowing

- **Business name (for Google)** — optional per-store override. The schema
  defaults to "McCormack's Pharmacy — <store name>", which is a guess at the
  trading name. Where a branch trades under something else it must be set here
  to match the Google Business Profile exactly, or Google will not connect the
  listing to the page.
- **Eircode** — emitted as `postalCode`. The eircodes currently in the template
  were lifted mechanically out of the free-text address field, where they were
  already present. The address field still contains them, which is fine for
  display.

**Store data is confirmed as of 23 August 2026** — names, addresses, eircodes,
phones, emails and all seven sets of opening hours. The hours were checked
against the mechanically converted design data and every one matched, so the
earlier conversion introduced no errors.

Two corrections came with the confirmation: Carrick Road's address was missing
"Carrick Road" itself, and Belmullet trades as **Erris Pharmacy**, which is now
its visible name with Belmullet as the badge.

`business_name` is set explicitly on all seven rather than left to the
constructed "shop name — store name" fallback. Six of them therefore emit the
same schema `name`, "McCormack's Pharmacy", distinguished by address — which is
how a multi-location business is normally represented, and matches the Google
Business Profiles. Do not reintroduce a "— Clonmel" style suffix: it was our
invention, not a real trading name.

**Bank holidays follow Sunday hours** at every store (Newbridge and Haggardstown
11:00–17:00, the rest closed). This is stated in the page copy and deliberately
NOT in `openingHoursSpecification`, which has no way to express "bank holidays"
— only specific dates via `specialOpeningHoursSpecification`. The consequence
worth knowing: on a bank holiday Monday, Google will show that store's normal
Monday hours. Fixing that properly means publishing a dated exception list each
year.

**Still outstanding: latitude and longitude for all seven.** Until every store
has both, the locator's "Use my location" button stays disabled — that is
deliberate, since sorting by distance with partial coordinates would put stores
in a confidently wrong order.

---

## Dispatch cutoff and Click & Collect — both fail closed

`snippets/buy-assurance.liquid` renders the reassurance beside the Add to bag
button and in the cart. Two of its lines are deliberately absent until real data
exists, because the alternative is promising something the store cannot do.

**Dispatch cutoff** — Theme settings → Pharmacy → Same-day dispatch cutoff.
Blank by default, and blank means the line does not render at all. Before
setting it, know that **12 collection FAQ answers independently say "before
3pm"**. Those are separate copy and will not follow this setting. Either set it
to match them, or tokenise them the way `[threshold]` works — do not leave the
two disagreeing, which is exactly the failure the delivery threshold had.

**Click & Collect** — no setting, deliberately. The line renders from
`variant.store_availabilities`, which Shopify populates only where local pickup
is actually enabled for that product's location. Configure pickup per location
in Shopify admin and the line appears by itself, naming the store when there is
one and counting them when there are several. Leave pickup off and the page
never mentions collection. The count is Shopify's, never ours.

The cart's separate "Click & Collect — free" button is an information link to
`/pages/click-and-collect`. It sits directly under Checkout, so it reads as a
checkout alternative — **if local pickup is never enabled, that button is
misleading and should be removed**, not left as decoration.

---

## Consent — the banner is not what blocks the pixels

`snippets/consent-banner.liquid` records a choice through Shopify's Customer
Privacy API. **It does not block anything.** What blocks a pixel is the
**Permission** field on that pixel in Settings → Customer events. A pixel set to
"Not required" fires before the visitor has answered and the banner is then
decoration — the exact failure the banner exists to prevent.

Two rules:

1. Every pixel added from now on — including ones apps install — needs its
   Permission set to the category it genuinely belongs to.
2. **Never** reimplement consent with a cookie, a `localStorage` flag, or a
   `<script>` guard in the theme. Shopify replays the events a gated pixel
   missed once consent arrives; a theme-side guard just drops them, and drops
   them invisibly.

Shopify's own cookie banner must stay **off**, or visitors see two.

Re-verify after any app install: `setup/analytics/README.md` §4, step 7 — grant
analytics only and confirm the marketing pixel stays silent. Accept-all hides a
wrong Permission; a partial grant exposes it.

---

## Analytics lives in the admin, not the theme

No tracking code belongs in `layout/theme.liquid` or Additional Scripts —
Additional Scripts is removed on 26 August 2026, and theme-level scripts cannot
observe checkout, so they can never report `begin_checkout` or `purchase`.

GA4 comes from the Google & YouTube channel; Meta from a custom pixel under
Settings → Customer events. See [`analytics/README.md`](./analytics/README.md).
Adding a second GA4 tag alongside the channel double-counts revenue.
