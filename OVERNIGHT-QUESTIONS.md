# Open questions — overnight run, 27 August 2026

Three items I stopped on rather than guess. Each says what I found, the options,
and what I would do.

---

## Q1. Canonical URLs cannot be observed without the dev store

**Status: Phase A item 1 is only partly answerable. This is the blocking one.**

The theme emits a single unmodified `{{ canonical_url }}` in
[theme.liquid:13](shopify-theme/layout/theme.liquid#L13). Whatever Shopify puts in
that variable is what ships — the theme adds no logic, no `rel="next"`/`rel="prev"`,
and no `noindex` anywhere.

So the answer to "what canonical is emitted on a paginated collection / filtered
collection / tag URL / search page" is **entirely Shopify's behaviour, not the
theme's**, and I could not verify it:

- The local preview harness hardcodes `canonical_url` to
  `'https://mock.myshopify.com/'` for every page
  ([render_preview.mjs:374](setup/render_preview.mjs#L374)), so the preview tells us
  nothing.
- Shopify's own documentation for `canonical_url` says only "The canonical URL for
  the current page" and does not state whether query parameters, filters, or search
  strings are included. I checked; it genuinely does not specify.

I am not willing to write "Shopify strips filter parameters from the canonical" into
a report from memory. That claim would drive real decisions about whether this theme
needs its own canonical logic, and if it were wrong the site would ship either a
duplicate-content problem or a pile of unnecessary code.

**What I need:** ten minutes on the dev store once it exists. Load each of the five
URL shapes and read the `<link rel="canonical">`. I have written the exact procedure
into `OVERNIGHT-REPORT.md` under "Canonical verification procedure" so it can be run
by anyone in one pass.

**Recommendation:** run that procedure before deciding whether any canonical work is
needed. My expectation is that Shopify handles the product-within-collection case
correctly and that pagination self-canonicalises, but expectation is not evidence,
and the filtered and tag-filtered cases are the ones most likely to need theme-level
handling.

---

## Q2. `product.url | within: collection` — fixed, but flagging the reasoning

**Status: I did fix this in Phase C. Reverting it is one commit if you disagree.**

[main-collection.liquid](shopify-theme/sections/main-collection.liquid) linked to
products through `product.url | within: collection` in 4 places, producing
`/collections/<handle>/products/<handle>`. Everywhere else in the theme — search
results, recommendations, the cart, the wishlist, predictive search — links to the
plain `/products/<handle>`. 14 plain links against 4 scoped ones.

I treated this as unambiguous and fixed it, because it is the better option under
*both* possible answers to Q1:

- If Shopify canonicalises the scoped URL to the plain one, then every internal link
  from a collection grid was pointing at a URL that only redirects the signal
  elsewhere. Linking to the canonical directly is strictly better.
- If Shopify does *not* canonicalise it, the theme was generating a duplicate URL for
  every product on all 293 collection pages, which is worse.

The usual reason to keep `within:` is that it gives the product page a `collection`
object for "back to collection" links or collection-aware breadcrumbs. **This theme
never reads it** — I checked; `sections/main-product.liquid` contains no reference to
the `collection` object, and the PDP has no breadcrumb. So the scoping bought nothing.

**If you want it back:** revert that single commit. Nothing else depends on it.

---

## Q3. Product FAQ metafield — the definition has to be created in the admin

**Status: mechanism built, cannot be activated from the theme.**

Phase B item 6 is built and rendering-ready, but a metafield *definition* lives in the
Shopify admin, not in theme code. I could not create it — the work order rules out
changing admin settings, and there is no store connected anyway.

The theme reads `product.metafields.custom.faq`. Before anything appears, someone has
to create that definition in **Settings → Custom data → Products**:

| Field | Value |
|---|---|
| Namespace and key | `custom.faq` |
| Name | Product FAQ |
| Type | **JSON** (not "JSON string") |
| Validation | none |

The expected shape, and what happens if it is wrong, is documented in
`setup/MAINTENANCE.md` under "Product FAQ". The theme fails closed: an absent,
empty, or unparseable value renders nothing and emits no schema, so a malformed
metafield cannot produce broken markup or invalid JSON-LD on a live page.

**I deliberately populated nothing**, per the work order. FAQ content on medicine
products is a pharmacist judgement, and FAQPage JSON-LD makes those answers eligible
to appear directly in Google results, which raises the stakes on the wording well
above ordinary product copy.

**Recommendation:** treat the first batch of FAQ content as requiring the same
pharmacist sign-off already pending on the collection FAQ answer (see the "AWAITING
PHARMACIST SIGN-OFF" section in `setup/MAINTENANCE.md`), and do not enable it on
pharmacist-only lines until the gating spec arrives from the client.
