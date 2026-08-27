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

**Items A, B and C are now fixed** — see "Status" at the end. The rest stands as the map.

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

The empty state also links to `/collections/all`, which used to 404 in the preview.
That route is now served (see route gaps below), so the "Continue shopping" button
is exercisable.

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
| `/collections/all` | **Routed** | Was a real gap — the theme links here from `main-collection.liquid:296` via `routes.all_products_collection_url`, and the empty-collection state made it a live dead link. Now serves the generic collection render, matching Shopify's automatic all-products collection |
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


---

## Status — 27 August, after the fixture pass

### Done

| Item | Result |
|---|---|
| **B. Multi-variant** | Fixed. **Found the variant picker was broken.** |
| **A. Pagination** | Fixed. The `paginate` tag was stubbed, not just under-populated. |
| **C. Form states** | Fixed. All six form pages render success and error. |
| Generator drift | Fixed, and guarded. **All three generators had drifted, not one.** |

Suite grew from 261 to **347 assertions**: +35 variants, +11 pagination,
+40 form states, and 9 generated files checked against their generators.

### What the fixtures found

**The variant picker had never worked.** The variants JSON block sat *after* the
IIFE that reads it, so `getElementById` returned null on every product page.
Selecting a pack size changed no price, no SKU, and no hidden variant id — the form
would have submitted the first variant whatever the shopper chose, and threw into
the console every time. The markup was correct; the bug was execution order, which
is why only driving it in a browser could catch it.

That is the concrete cost of a coverage gap: not a hypothetical, a buy button that
added the wrong item, sitting behind a fixture nobody had written.

**Pagination was stubbed, not just unpopulated.** The harness's `paginate` tag
hardcoded `pages: 1` with empty `parts`, so no product count would ever have
produced a second page. It now parses `by n`, slices, rebinds
`collection.products` the way Shopify does inside a paginate block, and builds
`parts` with the same first/last/window shape.

**All three generators had drifted**, not just `gen_category_nav.py`.
`gen_brands.py` and `gen_mega.py` both emitted literal hexes where the committed
snippets had tokens. `gen_mega.py` was also broken outright — it fetched the design
handoff through a preview route that no longer serves it — and carried the last
hardcoded absolute project path, which broke when the directory was renamed.
`setup/verify/generators.py` now regenerates all three against a scratch copy and
diffs, so this cannot recur silently.

### Corrections to this document

The original said four public contact forms rendered no error state. **That was
wrong** — they use inline error blocks rather than the shared `form-errors` snippet,
and my marker only looked for the snippet. All six render both states.

One real inconsistency remains, not worth changing on its own: the theme has two
error presentations, the `form-errors` snippet (account pages, withdrawal,
back-in-stock) and inline blocks (the four public contact forms). Both work.

### Still open

Items D through G, and the three unrouted templates (`/collections/all`,
`/password`, `/gift_cards/<id>/<token>`), are unchanged and still listed above.

---

## Status — items D to G

| Item | Result |
|---|---|
| **D. Empty and filtered collections** | Fixed. Three fixtures: filtered-with-results, filtered-to-nothing, genuinely empty. |
| **E. Predictive search** | **Not a gap — my original entry was wrong.** See below. |
| **F. Logged-in customer** | Fixed. Signed-in renders for the two storefront `{% if customer %}` branches. |
| **G. Smaller states** | Mostly fixed: order shipping method, expired gift card. The rest are unchanged and explained below. |

### Correction to item E

The original entry said page, article and query suggestions never rendered.
**Two thirds of that was wrong.** `predictive-search.liquid` reads exactly three
resources — products, collections and queries — and **all three already rendered**:
collections on 10 pages, query suggestions in 10 of 11 suggest fixtures. It never
reads `pages` or `articles` at all, so those being empty in the mock is correct
rather than a gap.

Nothing needed fixing. The entry was a bad reading of the mock rather than a real
finding.

### What D actually protects

The useful distinction is between *filtered to nothing* and *empty*. They are
different messages — "No products match your filters" with a Clear all, versus
"No products here yet" with Continue shopping — and getting them the wrong way
round tells a shopper to clear filters they never set, or to give up on a
collection that is one click from showing results. Both directions are now
asserted, including that neither message appears on the other's page.

This becomes live when held item 2.2 (Search & Discovery) populates real filters.

### What remains in G, and why

| Path | Status |
|---|---|
| Express checkout buttons | Still live-only. `additional_checkout_buttons` cannot be mocked meaningfully — a stand-in would prove nothing about real payment providers. Stays on the dev-store list. |
| Subscriptions | `selling_plan_groups` is empty and the theme has no subscription UI to exercise. Nothing to cover until that is built. |
| Blog tag filtering | `current_tags` is null. Reachable only via `/blogs/<b>/tagged/<tag>`, which is not routed. Left with the other unrouted templates. |
| Related articles | Article `tags` are populated and render; the earlier entry conflated this with `blog.articles`. |
| Dispatch cutoff | Blank **by design** — fails closed, awaiting a real time from the client. Correct, not a gap. |

### The unrouted templates

`/collections/all` is now routed: the empty-collection state renders, so its
"Continue shopping" button was a live dead link rather than a theoretical gap.
`build_static_preview.py` was moved in step — it had parked the unrouted
`list-collections` template on `/collections/all`, which would have left the two
harnesses disagreeing about what that URL is.

`/password` and `/gift_cards/<id>/<token>` remain unrouted, as asked. Neither is
linked from any rendered page, so both are still theoretical.

Suite is now **415 assertions**.
