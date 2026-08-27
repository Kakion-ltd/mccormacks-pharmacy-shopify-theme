# Harness coverage — what renders nowhere

A deliberate pass over fixture and route coverage, prompted by three real paths that
had been found one at a time: `selling_plan_groups`, the sold-out product, and
`product.collections` plus the collection-scoped product route.

The pattern behind all three: **a code path that renders in no preview is verified by
nobody, and ships on assumption.** Every check in `npm run verify` runs against
rendered output, so anything absent from that output is untested no matter how many
checks exist.

Method: 365 rendered pages searched for the markup each branch produces; the mock
globals cross-referenced against every Liquid conditional that reads them; every
Shopify route family requested against the preview server; and theme settings checked
for blank values that gate a branch.

**Not fixed** — this is the map, so the fixtures can be built in priority order rather
than reactively.

---

## 1. Renders nowhere — ranked by what it would cost to be wrong

### A. Pagination — nothing beyond page 1 has ever rendered

`{% paginate collection.products by 24 %}` with 10 mock products means
`paginate.pages` is always 1. **Never rendered:** the page-number links, next/prev,
`paginate.parts`, and any `?page=` URL.

This is the highest-value gap, and it is directly in front of the open canonical
question. Q1 item 2 asks whether Shopify canonicalises page 2 back to page 1 — and
the theme's pagination markup has never been seen in a browser at all. Whatever the
dev store says about canonicals, the controls that produce those URLs are unverified.

**Fixture needed:** a collection with 25+ products, or `by 4` in a test render.

### B. Multi-variant products — the entire variant picker

Every mock product sets `has_only_default_variant: true`, so the
`{%- unless product.has_only_default_variant -%}` block never renders: no option
`<select>`, no selected state, and none of the JS that swaps variant on change.

A pharmacy sells a great many products in multiple sizes and strengths. This is
probably the single largest untested surface in the theme.

**It also silently covers a feature built last night.** The variant-name half of
`snippets/image-alt.liquid` depends on `image.attached_to_variant?`, which no mock
image sets. The rule "product title plus variant name where the image is
variant-specific" has never produced a variant name in any preview. The product-title
half is verified; the variant half is not.

**Fixture needed:** one product with 2–3 variants, images attached to variants, and
`options_with_values` populated.

### C. Every form success and error state

`form.posted_successfully?` is `false` and `form.errors` is `null` everywhere, so
across 6 contact forms, the newsletter signup, and back-in-stock, **no success
confirmation and almost no error state has ever rendered.** Only 2 pages show any
error block at all.

These matter more than usual here: the back-in-stock and prescription forms are the
two places where a customer hands over personal data and needs to see it landed.

**Fixture needed:** render key form templates twice, once with
`form: { posted_successfully: true }` and once with `form: { errors: … }`.

### D. Empty and filtered collection states

Every mock collection holds the same 10 products and `filters[].active_values` is
always `[]`. Never rendered:

- "No products here yet" (empty collection)
- "No products match your filters" / "Clear all filters" (filtered to nothing)
- active filter chips and `filter.url_to_remove`

The empty state also **links to `/collections/all`, which 404s in the preview** (see
route gaps below), so even if it rendered, the link would be broken locally.

Held item 2.2 (Search & Discovery) will populate these filters, so this becomes more
pressing once products are mapped.

### E. Predictive search: everything except products

`predictive_search.resources` mocks `queries`, `pages` and `articles` as `[]`.
Collection suggestions do render (10 pages), but **page, article and query
suggestions never have.**

### F. Logged-in customer states

`customer: null` across the storefront. The three account templates do render logged
in, but every `{% if customer %}` branch on a *storefront* page — the wishlist empty
state's "My account" vs "Create an account" fork, the repeat-prescriptions "Sign in to
see your repeat items" line — renders only its logged-out half.

### G. Smaller ones, same class

| Path | Why it never renders |
|---|---|
| Express checkout buttons | `additional_checkout_buttons: false` — known, live-only, already flagged |
| Subscriptions | `selling_plan_groups: []` — the one you already knew about |
| Order shipping method line | `shipping_methods: []` on the order template |
| Blog tag filtering | `current_tags: null` |
| Related articles on an article | `articles: []` |
| Gift card expired / spent states | `gift_card.expired` is always `false`; the page renders, its states do not |
| Dispatch cutoff line | `settings.dispatch_cutoff` is blank **by design** — fails closed, awaiting a real time from the client. Correct, not a gap |

---

## 2. Route gaps

Every Shopify route family, requested against the preview server:

| Route | Status | Verdict |
|---|---|---|
| `/collections/all` | **404** | **Real gap.** The theme links here from `main-collection.liquid:296` via `routes.all_products_collection_url` |
| `/password` | **404** | **Real gap.** `password.json` template exists and renders to `preview/password.html`, but nothing serves it |
| `/gift_cards/<id>/<token>` | **404** | **Real gap.** `gift_card.liquid` renders to `preview/gift_card.html`, but nothing serves it |
| `/policies/<handle>` | 404 | Not a gap — the theme uses `/pages/privacy-policy` and never links to `/policies/` |
| `/challenge` | 404 | Not a gap — Shopify-provided, not themed |
| `/404`, `/nonexistent` | 404 | Correct: serves the 404 template with a 404 status |
| everything else tested | 200 | `/`, collections, tag URLs, collection-scoped products, products, pages, blogs, article, cart, search, all 6 account routes |

Three templates therefore render into `preview/` but are unreachable by URL, so no
Playwright check can ever visit them.

---

## 3. Recommended order

1. **Pagination** — sits directly in front of the open canonical question
2. **Multi-variant product** — largest untested surface, and it covers the unverified
   half of the alt-text work
3. **Form success/error states** — where customers hand over data
4. **Empty and filtered collection** — becomes pressing when 2.2 lands
5. **The three dead routes** — cheap; three lines in `serve_preview.py`
6. Everything in G, as convenient

1–3 are each roughly one fixture plus one render variant. None needs a dev store.

---

## 4. The rule worth keeping

**A branch that renders in no preview is not covered by any check, however many
checks there are.** The suite currently reports 261 passing assertions across 365
pages, and every item above sits outside all of them.

When adding a branch, the question is not "did I test it" but "does it appear in
rendered output at all" — if not, the fixture is part of the work, not a follow-up.
