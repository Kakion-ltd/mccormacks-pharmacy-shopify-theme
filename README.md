# McCormack's Pharmacy — Shopify theme

Online Store 2.0 theme for mccormackspharmacy.ie, built from the design
handoff in `design/`.

## Layout

| Folder | What it is |
|---|---|
| `shopify-theme/` | The theme. Shopify's own layout; `assets/` must stay flat. |
| `setup/` | Generators, taxonomy data, store provisioning, the preview renderer and `verify/` checks. See `setup/README.md`. |
| `preview/` | Rendered output of `npm run render`. Committed because Vercel and GitHub Pages deploy it without Node. |
| `artwork/` | Image masters, one folder per slot. Never deployed. See `artwork/README.md`. |
| `design/` | The original hifi HTML handoff and its images. Reference only; `gen_mega.py` reads the homepage file. |
| `docs/` | Build reports, the coverage map and the header-promo spec. |
| `STORE-SETUP.md` | Admin checklist for pages, collections, blog and menus. |
| `IMAGE-BRIEF.md` | Sizes and status of every image slot, for whoever supplies artwork. |

## Commands

```sh
npm install
npm run render     # theme -> preview/ (all pages, categories, endpoints)
npm run dev        # serve preview/ with Shopify-style routes
npm test           # Liquid render tests + theme-check
npm run verify     # Playwright and static checks against the running preview
npm run build      # preview/ -> _site/ for static hosting
npm run package    # dist/mccormacks-theme.zip for upload
```

`_site/`, `dist/` and `node_modules/` are regenerated and ignored.
