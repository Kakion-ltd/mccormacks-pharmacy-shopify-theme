# Overnight report — theme editor customisability work

Seven build items were requested, in order, plus one spec. Six built and
verified, one escalated (item 3, see `OVERNIGHT-QUESTIONS.md`), spec
delivered (`SPEC-header-promo-links.md`). The live rendering is unchanged:
every item was gated on theme-check (0 errors), `npm test`, the full
`npm run verify` suite, and a render-identity check — `npm run render`
regenerates all 363 preview pages from the theme, and after each item the
diff was either empty or reviewed line-by-line and limited to invisible
editor hooks (details below). Final state: all suites green, render diff
empty, homepage / gift vouchers / footer visually confirmed identical at
desktop and mobile widths, including the footer accordion behaviour.

## What changed, commit by commit

- `d68b2b7` **Sync preview renders** — housekeeping. Yesterday's hand-
  mirrored preview edits drifted from the renderer's own output by
  whitespace; regenerated so the render-identity gate starts from a clean
  no-op.

- `abf47c1` **Item 1: logo picker + contact settings.** Brand settings gain
  a `logo` image_picker and an `email` text setting (default: current
  address). All six hardcoded logo references (header ×2, footer, password
  page, gift card, JSON-LD structured data) now go through a `logo-src`
  snippet that prefers the picked image and falls back to the bundled
  asset. All 12 stray `tel:` links, 5 `mailto:` links and their visible
  text now read `settings.phone` / `settings.email` (34 literal swaps).
  Not touched, deliberately: PSI regulatory contacts (`internetsupply@psi.ie`,
  the PSI phone number) and per-section schema defaults such as
  `help_phone` and per-store phone numbers, which are merchant data.
  theme-check calls a conditional logo src RemoteAsset; five scoped
  disable comments mark the false positives. Render: byte-identical.

- `2554cb1` **Item 2: brand-green literals.** Investigation first: the
  audit's "5 in base.css" turned out to be the documented fallback layer —
  theme.liquid injects the settings-driven custom properties *after*
  base.css precisely so they win (the file comments say so). Those are
  correct and untouched. The genuine bypasses were five: the hot-offers
  badge-text fallback (now `settings.color_dark`), the active row in the
  legal and account sidebars (now `var(--c-dark)`/`var(--c-accent)`), and
  two JS border highlights on gift-voucher fields and product gallery
  thumbnails (now `'var(--c-primary)'`). The hot-offers schema/preset
  colour defaults feed settings rather than bypass them and stay. Render:
  17 pages changed in exactly those five expressions, same computed
  colours.

- **Item 3: trust bar — NOT BUILT, escalated.** The trust row is rendered
  by 26 sections, not one; per-section blocks would make the homepage
  editable while 25 interior copies stay frozen. Options and a
  recommendation (global theme settings) are in `OVERNIGHT-QUESTIONS.md`.

- `65ae8b2` **Item 4: category pills → blocks.** Seven pills become
  blocks (label + link), carried as both the section preset and the
  homepage template's block data. Capped at 10 to protect the single-row
  layout. Render: 7 lines gain the editor's block-attribute hook (a space
  inside the tag), nothing else.

- `5564d36` **Item 5: footer columns → menu pickers.** Four column blocks,
  each a heading + `link_list` picker, seeded in the footer group. Until
  the named menus exist in the admin, each column falls back to the
  theme's built-in links (the old pipe-string, kept as the onboarding
  fallback — the same pattern the theme already uses for image assets), so
  nothing changes today. Render: every page's four column divs gain the
  editor hook; links, headings and accordion slugs byte-identical.

  **What you need to create in Shopify admin** (Online Store → Navigation),
  four menus with these exact handles:
  - `footer-shop`: All Brands → /pages/brands · New In → /collections/new-in
    · Bundles → /collections/bundles · Gift Vouchers → /pages/gift-vouchers
    · Sale → /collections/sale
  - `footer-customer-care`: About Us → /pages/about-us · Contact Us →
    /pages/contact-us · Loyalty Rewards Club → /pages/loyalty-rewards-club
    · Blog → /blogs/health-hub
  - `footer-shipping-returns`: Shipping & Free Delivery → /pages/shipping ·
    Returns & Refunds → /pages/returns · Click & Collect →
    /pages/click-and-collect
  - `footer-policies`: Terms & Conditions → /pages/terms-and-conditions ·
    Privacy Policy → /pages/privacy-policy · Cookie Policy →
    /pages/cookie-policy · Registered Internet Supply Pharmacy →
    /pages/internet-supply-pharmacy · Withdraw From Contract →
    /pages/withdraw-from-contract

  Each menu takes over its column the moment it exists; the built-in
  fallback then never renders again.

- `bfbfefc` **Item 6: gift voucher denominations → blocks.** Six amounts
  (€10–€150) become blocks with amount, optional tag ("Popular", "Most
  gifted") and a preselected flag; the hero voucher preview now follows
  the preselected block instead of a hardcoded €50. Seeded as preset and
  template data. Render: buttons identical bar the editor hook.

- `52a966d` **Item 7: generic sections.** `rich-text`, `image-with-text`
  and `newsletter` — written in this theme's idiom (shared section shell,
  rounded-MT headings, promo-strip CTA, collection-banner card with the
  standard image placeholder, the footer's newsletter form and dark band).
  Text defaults are blank (no shipped copy, per the hard limits); all
  three have presets so they appear in the editor's Add section list; none
  is referenced by any template, so nothing rendered changes. Each was
  smoke-rendered with populated and empty settings. Custom-liquid was
  deliberately not added.

- **Item 8: header nav spec** — `SPEC-header-promo-links.md`. Taxonomy
  stays the source of the category tree; up to 4 editable promo-link
  blocks sit where the hardcoded Sale/Brands links sit today (desktop nav
  bar + top of the mobile drawer), with Sale/Brands converting into the
  first two blocks. Estimated at about a day.

## Verification detail

- theme-check: 0 errors, 5 warnings — the same 5 as before the work
  (3 pre-existing AssetPreload in hero-slider, 2 pre-existing
  UndefinedObject in main-reset-password).
- `npm test`: 53/53 liquid snippet checks, theme-check exit 0.
- `npm run verify`: all 16 checks pass after every item — includes the
  trust-bar carousel geometry, mobile nav, consent, variants, forms,
  contrast (the 63 accepted white-on-lime entries are the pre-existing
  `button_text_white` acceptance, unchanged), and 26 clean page loads.
- Render identity: after the final item, `npm run render` produces a zero-
  file diff against the committed previews. Mid-run diffs were only the
  reviewed, invisible changes described per item.
- Visual: homepage, gift-vouchers page and footer screenshotted at 1440px
  and 390px; mobile footer accordion clicked and confirmed to open its
  column (5 links).

## Not done, and why

- **Item 3** — escalated (above).
- Items 9–11 from the audit (padding settings, neutral tokenisation,
  product-page blocks, font pickers, i18n) — excluded by instruction.
- Consent banner, restricted-product suppression, pharmacy compliance
  copy, variant picker — untouched, per the hard limits. (Item 1 routed
  the *contact details* rendered on two legal pages through settings; the
  copy itself is byte-identical.)

## Loose ends worth knowing

- The `link_list` defaults mean the footer editor shows the four menu
  handles as text until the menus exist; that is the onboarding state, not
  an error.
- The three new generic sections have never rendered on a real page; when
  one is first added on a dev store, give it a quick look in the editor.
- `settings_data.json` was not extended with the new `email` setting — the
  schema default covers it, and the merchant's first save will persist it.
