# Artwork

Image masters and staging. Nothing in here is deployed: the theme reads only
the flat `shopify-theme/assets/` folder, and the preview build ignores this
tree. One folder per slot, sized per `IMAGE-BRIEF.md`.

| Folder | Slot | Supply at |
|---|---|---|
| `hero-slides/` | Homepage hero slider | 1600 × 1000 transparent PNG cut-out; photographic slides 1760 × 920 + 1100 × 850 `-mobile` |
| `category-banners/` | Department collection banners | 1300 × 600 |
| `feature-tiles/` | Homepage feature tiles | 1360 × 765 |
| `hot-offers/` | Homepage hot-offer tiles | 1032 × 774 |
| `popular-categories/` | Homepage popular category tiles | 400 × 400 min |
| `service-cards/` | In-Store Services page cards | 800 × 600 |
| `store-photos/` | Store locator exteriors | 1520 × 700 |
| `other-services/` | Homepage "Other Services" tiles | 658 × 658 |
| `brand-logos/` | Brand slider and Brands page | 350 × 240 transparent PNG |
| `about/` | About page storefront | 1520 × 700 |
| `products/` | Mock product shots used by the preview | 1200 × 1200 |
| `../archive/artwork-superseded/` | Replaced artwork kept for reference | |

Folders are created when the first master arrives; an empty slot has no folder yet.
Files ending `-master` are the higher-resolution originals behind an existing
under-size export (see IMAGE-BRIEF priority 2).

A master keeps the same stem as its export: `category-banners/banner-beauty.png`
becomes `shopify-theme/assets/banner-beauty.jpg`. Export to JPEG at quality
about 80, under 300 KB, PNG only where transparency is needed.

Two hero masters carry a `banner-` stem because the deployed files do
(`banner-vitamins.jpg` is hero slide 2). Renaming to the slot convention is a
post-launch job, see IMAGE-BRIEF.md.
