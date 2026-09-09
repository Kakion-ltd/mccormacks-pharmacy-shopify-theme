# Image & banner brief — McCormack's Pharmacy

For whoever is producing artwork. Everything here is measured from the built
theme, not estimated. Sizes are **source pixels to supply** (already 2× the
largest rendered slot — do not double them again).

---

## The house look

Irish family pharmacy, seven stores, trading since 1982. Reads as clinical
trust first, retail beauty second. Not a spa, not a supermarket.

**Palette** — imagery has to sit against these, and a banner's text panel is
drawn in them:

| Token | Hex | Where it lands on imagery |
|---|---|---|
| Primary green | `#82C914` | Buttons and chips over banners |
| Deep green | `#3F6B4F` | The hero's left-hand copy panel |
| Ink | `#2A2B2A` | All body text, incl. text set on primary green |
| Tint | `#E6F2D5` | Panel behind category banner copy |

Type is Mulish. **Do not bake text into any image** — every headline, button
and badge is live HTML over the top, and it is translated and re-flowed per
viewport. An image with a headline in it will collide with the real one.

**Composition rule that applies everywhere:** keep the subject off-centre-right
and leave the left third quiet. Copy panels sit left on the hero, the category
banners and the hot-offer tiles.

---

## Priority 1 — slots that are empty and visible

### A. Category / department banners — 12 needed
`1300 × 600` (2.17:1). Subject right, left third quiet.

**Supplied (Sep 2026):** Beauty, Fragrance, Gifting, Medicines & Health,
Mother & Baby, Sale, Skincare, Toiletries, Vitamins. Masters in
`artwork/category-banners/`.

Still **empty** and rendering a dashed placeholder:

- New In

Two more are **filled with a borrowed image** at the wrong aspect ratio:

- Hot Offers *(the 536×545 Mitchum hot-offer tile)*
- Bundles *(the hero travel shot)*

### B. Store photography — 7 needed
`1520 × 700` landscape. One exterior per store, shopfront and signage legible.
All seven currently show a grey map placeholder.

Clonmel · Ballylanders · Newbridge · Tullamore · Haggardstown (Dundalk) ·
Carrick Road (Dundalk) · Erris Pharmacy

### C. Homepage tiles — 2 needed
- **Menopause Support** hot-offer thumbnail — `600 × 600` (1:1), product-on-
  plain-ground. Renders as the square thumb on a compact offer row; the same
  crop spec as the popular-category tiles, so one artwork order covers both.
  (If Menopause is ever promoted to the spotlight slot, that wants the
  `1200 × 800` spotlight spec instead.)
- **About Us storefront** — `1520 × 700`. One hero shot for the About page.

### D. Brand logos — 6 needed
`350 × 240` max, **transparent PNG**, mark centred with even padding, dark
enough to read on white. Missing: NIVEA, Optibac, Revive Active, Mitchum,
Piz Buin, Nurofen. *(Supplied by the brands — usually a press-kit download
rather than a design job.)*

### E. Services card images — up to 9 optional
`800 × 600`. The In-Store Services page has nine service cards, all currently
text-only. They render fine without images; add them if you want the page to
carry weight.

---

## Priority 2 — supplied but under-resolution

These render today, so nothing is broken, but they are soft on a retina screen
or cropping badly. Ordered by how visible the problem is.

| Asset | Have | Need | Problem |
|---|---|---|---|
| `contact-us.png` | 299×299 | 658×658 | Less than half resolution, homepage |
| `instore-services.png` | 299×299 | 658×658 | Same |
| `common-conditions.jpg` | 299×299 | 658×658 | Same |
| `mitchum-hot-offers.jpg` | 536×545 | 600×600 | Near-square now fits its slot — the offer redesign shows it as a 72px row thumb, so resolution is fine too |
| `cat-suncare.jpg` | 860×531 | 1360×765 | Under-size, wrong aspect |
| `cat-vitamins.jpg` | 1440×500 | 1360×765 | 2.88:1 forced into 16:9 — heavy crop |
| Hero slides ×4 | 1440×500 | 1760×920 | 2.88:1 forced into 1.91:1 — heavy crop |
| `hero-summer-travel.jpg` | 1570×880 | 1760×920 | Marginally under |
| `brand-loreal/proven/sculpted.png` | 175×120 | 350×240 | Blurry at 2× |

The hero slides are the worst of these: the frame is `1760 × 920` desktop and
the images are 500px tall, so roughly half of each is discarded.

---

## Priority 3 — missing entirely, not currently a slot

- **Social share image (`og:image`)** — `1200 × 630`. The theme emits **no**
  `og:image` at all, so every link shared to WhatsApp, Facebook or Slack shows
  a bare text card. Logo on brand green, generous margins.
- **Favicon** — `512 × 512` PNG, plus a 32×32-legible mark. Not currently set.

Both need a small code change as well as the artwork; flag it back and it's a
few lines.

---

## Full size table

| Slot | Source px | Ratio | Notes |
|---|---|---|---|
| Hero slide (desktop) | 1760 × 920 | 1.91:1 | Left ~500px sits under the green copy panel |
| Hero slide (mobile) | 1100 × 850 | 1.30:1 | Optional but recommended — the desktop crop loses the subject on a phone |
| Category / sale banner | 1300 × 600 | 2.17:1 | Subject right |
| Feature tile | 1360 × 765 | 16:9 | Subject right and upper; bottom-left 55% × 55% is background only; theme darkens the bottom 60%; no text or badges; both tiles in a section share one image language. See the house rule below |
| Feature tile (mobile) | 800 × 800 | 1:1 | Optional. Same rule applied to its own bottom-left corner |
| Hot-offer spotlight | 1200 × 800 | 3:2 | Bleeds to the card's top, right and bottom edges; phones crop it to a 2:1 band, so keep the subject inside the central 2:1. Any background. See the house rule below |
| Hot-offer row thumbnail | 600 × 600 | 1:1 | Square thumb on the compact rows — same spec as the popular-category tile, one crop serves both |
| Service / other tile | 658 × 658 | 1:1 | Title and link sit below the image |
| Popular-category tile | 400 × 400 | 1:1 | Falls back to the collection's own image |
| Store photo | 1520 × 700 | 2.17:1 | |
| About storefront | 1520 × 700 | 2.17:1 | |
| Services card | 800 × 600 | 4:3 | |
| Brand logo | 350 × 240 max | — | Transparent PNG, contained not cropped |
| Product photo | 1200 × 1200 | 1:1 | White ground, pack centred, ~10% margin |
| Social share | 1200 × 630 | 1.91:1 | |

---

## House rule: homepage feature tiles

The two promo tiles under the hero. The theme sets the title in white on a
dark scrim in the bottom-left corner, so the image has to be composed for that
corner rather than fitted after the fact. Both tiles run through the same
treatment, so they only read as a pair if the artwork follows the same rule.

1. **Frame.** 1360 × 765 JPEG at quality 80, under 300 KB. Optional mobile
   crop 800 × 800 with the same rule applied to its own corner.
2. **Safe area.** The bottom-left corner, 55% of the width by 55% of the
   height, is background only. No product, face, text, badge, logo, or hard
   edge in it. The theme sets the title and button there.
3. **Subject.** Sits in the right half and upper two-thirds, with at least 8%
   clear on every edge. The frame is cropped by the browser at every width, so
   a subject that touches an edge will be cut.
4. **Brightness.** The theme darkens the bottom 60% of the frame. Supply the
   image at its true tone. No baked-in gradients, vignettes, or drop shadows.
5. **No text in the image.** No price flashes, "special offer" badges, or
   brand lockups. Copy belongs to the theme so it can be edited in the theme
   editor and read by screen readers.
6. **One language per section.** Both tiles use the same kind of image: both
   lifestyle photography, or both product on a flat brand-green ground. Never
   one of each.
7. **Check.** Before sending, cover the bottom-left 55% × 55% with a rectangle.
   If anything you would miss is under it, recompose.

`tile-vitamins.jpg` fails rules 2, 5 and 6 and needs a re-cut; there is no
master for it in `artwork/`, so ask the supplier for one with this rule.

## House rule: hot-offer images

Two slots, and the spotlight one changed shape in September 2026 when the
image stopped floating inside the card and started bleeding to its edge.

- **Spotlight:** 1200 × 800 JPEG (3:2). The panel fills the card's right 46%
  from top edge to bottom edge on desktop and becomes a full-width 2:1 band
  on a phone, so keep the subject inside the central 2:1 with 8% clear on
  every side. **Any background works.** The image's rectangle is never
  visible, so there is no longer a reason to export it on the tile's green
  or on a plain ground to match; a photographed surface, a gradient or a
  flat colour all read the same. The earlier advice to match the tile colour
  applied to the inset tile and is withdrawn.
- **Row thumbnail:** 600 × 600 (1:1), product on a plain ground, the same
  spec as the popular-category tile so one crop serves both. This one is
  still a visible square with a rounded corner, so its ground does show.
- No text, price flashes or badges in either. The Deal and Ends fields carry
  the offer in live text.

---

## Format and delivery

- **JPEG** for photography, quality ~80. **PNG** only for logos and anything
  needing transparency. Do not supply WebP — Shopify generates its own formats
  and sizes from whatever is uploaded, and a WebP source just limits what it
  can do.
- Under **300KB** per file. The two banners that were 3MB were the site's worst
  performance problem before they were re-exported.
- Everything except brand logos and product shots is **cropped by the browser
  with `object-fit: cover`**, so supply generous framing and never let the
  subject touch an edge.
- Product photography is loaded from Shopify's product records, not the theme —
  it comes with the catalogue rather than from this brief.

## Not needed

No icons (all inline SVG in the theme), no illustrations, no background
textures, no logo work — `mccormacks-logo.png` and the PSI mark are in place.

## Counts

**Genuinely missing: 27** — 12 category banners, 7 store photos, 2 homepage
tiles, 6 brand logos.
**Wanted but optional: 11** — 9 service cards, social share, favicon.
**Re-exports of existing artwork: 13.**

## Post-launch: rename theme assets to the slot convention

Deferred until the store is live. Theme asset names are inconsistent
(`banner-vitamins.jpg` is a hero slide, `cat-suncare.jpg` is a feature tile,
`contact-us.png` is an Other Services tile). The intended convention is
`<slot>-<subject>[-mobile].<ext>` with prefixes `hero-`, `banner-`, `tile-`,
`offer-`, `popular-`, `service-`, `store-`, `about-`, `logo-`, `prod-`,
`placeholder-`; masters in `artwork/` already follow it where they can.

Why not now: if the theme is installed and anything has been saved in the
theme editor, the store's copy of `templates/*.json` names the old files.
A push with renamed assets leaves those slots blank until each is re-picked.
Do it as one commit after launch, with the merchant's editor changes pulled
first (`shopify theme pull`), then `npm run render` and the full verify run.
Files touched: `templates/index.json`, the department collection templates,
hero-slider, feature-tiles, other-services, hot-offers, brand-slider,
page-brands, page-about, footer, buy-assurance, logo-src, sale-products,
`setup/render_preview.mjs`, `setup/serve_preview.py`, and this brief.
