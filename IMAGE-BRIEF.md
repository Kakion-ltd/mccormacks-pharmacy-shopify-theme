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

Five are **completely empty** and currently render a dashed placeholder:

- Beauty
- Gifting
- Medicines & Health
- New In
- Toiletries

Seven more are **filled with a borrowed image** — a homepage hero slide or a
hot-offer tile reused at the wrong aspect ratio (1440×500 dropped into a
1300×600 frame crops ~30% off the top and bottom). Replace:

- Fragrance, Mother & Baby, Skincare *(currently hero slides)*
- Vitamins, Hot Offers, Sale *(Sale and Hot Offers share one file)*
- Bundles *(currently the hero travel shot)*

### B. Store photography — 7 needed
`1520 × 700` landscape. One exterior per store, shopfront and signage legible.
All seven currently show a grey map placeholder.

Clonmel · Ballylanders · Newbridge · Tullamore · Haggardstown (Dundalk) ·
Carrick Road (Dundalk) · Erris Pharmacy

### C. Homepage tiles — 2 needed
- **Menopause Support** hot-offer tile — `1032 × 774` (4:3), product-on-plain-
  ground, cut out or shot on a light surface. Sits on a coloured panel.
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
| `mitchum-hot-offers.jpg` | 536×545 | 1032×774 | Half resolution **and** square in a 4:3 frame |
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
| Feature tile | 1360 × 765 | 16:9 | Label and button bottom-left |
| Feature tile (mobile) | 800 × 800 | 1:1 | Optional |
| Hot-offer tile | 1032 × 774 | 4:3 | Floats right over a coloured panel, rounded corners |
| Service / other tile | 658 × 658 | 1:1 | Title and link sit below the image |
| Popular-category tile | 400 × 400 | 1:1 | Falls back to the collection's own image |
| Store photo | 1520 × 700 | 2.17:1 | |
| About storefront | 1520 × 700 | 2.17:1 | |
| Services card | 800 × 600 | 4:3 | |
| Brand logo | 350 × 240 max | — | Transparent PNG, contained not cropped |
| Product photo | 1200 × 1200 | 1:1 | White ground, pack centred, ~10% margin |
| Social share | 1200 × 630 | 1.91:1 | |

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
