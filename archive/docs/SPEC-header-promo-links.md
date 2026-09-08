# Spec: editable promotional links in the header

Status: proposal only — nothing here is built.
Decision context: the taxonomy build (`taxonomy.json` →
`setup/gen_category_nav.py`) stays the single source for the category tree,
because it is what keeps the desktop mega menu, the mobile drill-down drawer
and the breadcrumbs describing the same structure. This spec adds a small
merchant-editable layer alongside that tree for time-boxed links like a
Christmas Shop, without touching how categories are generated.

## The precedent already in the theme

The nav bar is not 100% taxonomy today. After the eight generated category
triggers, `sections/header.liquid` hardcodes two plain links — **Sale**
(highlighted: bold, `--c-primary-text`, `hov-green-dk`) and **Brands** — and
`snippets/mobile-nav.liquid` mirrors them as the first two rows of the
drawer, above the category drill-down. A "promo slot" is exactly this
pattern, made editable. That is why the cost below is low: the layout,
styling and mobile placement all exist; only the source of the links
changes.

## What the merchant gets

Header section blocks of one new type, **Promo link**:

| Setting | Type | Notes |
|---|---|---|
| Label | text | e.g. "Christmas Shop" |
| Link | url | collection, page, or external |
| Highlight | checkbox | renders in the Sale link's accent style |

Sale and Brands themselves convert into the first two of these blocks
(Sale with Highlight on), so there is one mechanism, not two. The merchant
can then retitle or remove them like any other promo link — which also
quietly fixes "Sale and Brands are hardcoded" from the audit.

## Where the links sit

- **Desktop (>1100px):** in the existing nav bar, after the last generated
  category trigger ("Gifting"), exactly where Sale and Brands sit today.
  Promo links never get a `data-mega-trigger`; hovering them closes any
  open mega panel (`data-mega-close`), as Sale does now.
- **Mobile drawer:** as `mnav-row` entries at the top of the drawer list,
  where Sale and Brands render today — above the category drill-down,
  because promo links are the reason a merchant sends people to the menu.
  Highlighted links use the existing `mnav-link-accent` class.
- **Not** in the announcement bar, and not as a second row: both would be
  design changes.

## How many

**Maximum 4 promo blocks** (`max_blocks: 4`), including Sale and Brands as
shipped. The nav bar at 1101–1200px already wraps close to the limit with
ten items plus the two buttons; two extra ~110px labels fit, a fifth risks
a two-row header on smaller laptops. The editor cap is the guard rail; no
CSS changes needed. If the merchant one day needs more, that is a design
conversation, not a settings change.

## What happens on mobile

The drawer list is generated at build time, but the promo rows are section
markup, not generated markup — `mobile-nav.liquid`'s Sale/Brands rows move
out of the snippet into the drawer template in `header.liquid`, looping the
same blocks. One source, both surfaces, zero drift. The drill-down panels
(all 37 of them) remain generated and untouched.

## Editor behaviour

- Blocks live on the header section, so they are edited in the theme
  editor's header group, present on every template.
- Reordering blocks reorders the links on both surfaces.
- Zero blocks renders zero promo links (the category tree is unaffected).
- Default blocks ship as Sale + Brands with today's URLs, so the theme
  looks identical until someone edits.

## What this deliberately does not do

- No editing of category links, mega panels, drill-downs or breadcrumbs —
  taxonomy remains the only source.
- No image/banner slots inside the mega menu panels. Feasible later (a
  block type carrying an image + link rendered into a panel's right rail),
  but it multiplies the surface area; out of scope until asked for.
- No scheduling (auto show/hide by date). Shopify has no native section
  scheduling; faking it in Liquid breaks on CDN caching. The merchant adds
  and removes the block manually.

## Cost

- Header section: block schema + desktop loop replacing the two hardcoded
  links: **~2h**
- Mobile drawer: move the two rows from the snippet into the block loop:
  **~1h**
- Seed default blocks in `header-group.json`, render-identity check against
  the preview pipeline, verify suite, editor QA on a dev store: **~2–3h**

**Total: about a day**, including verification. No build-script changes, no
taxonomy changes, no CSS changes.

## Risks

- The header renders on every template; the render-identity gate (byte-diff
  of the rendered preview) makes the conversion itself low-risk.
- `verify/mobile-nav.py` asserts drawer behaviour — it runs unchanged and
  would catch a broken drawer.
- The only genuinely new behaviour is "more than two promo links", which is
  bounded by the cap above.
