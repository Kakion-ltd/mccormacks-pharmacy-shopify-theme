# McCormack's Pharmacy — Shopify theme

Online Store 2.0 theme for mccormackspharmacy.ie, built from the design
handoff now kept in `archive/design/`.

## Layout

| Folder | What it is |
|---|---|
| `shopify-theme/` | The theme. Shopify's own layout; `assets/` must stay flat. |
| `setup/` | Generators, taxonomy data, store provisioning, the preview renderer and `verify/` checks. See `setup/README.md`. |
| `preview/` | Rendered output of `npm run render`. Untracked; Vercel and GitHub Pages render it themselves at build time. |
| `artwork/` | Image masters, one folder per slot. Never deployed. See `artwork/README.md`. |
| `archive/` | Historical: build reports, the hifi HTML design handoff, superseded artwork. Kept in git, nothing reads it. |
| `STORE-SETUP.md` | Admin checklist for pages, collections, blog and menus. |
| `IMAGE-BRIEF.md` | Sizes and status of every image slot, for whoever supplies artwork. |

## Commands

```sh
npm install
npm run render     # theme -> preview/ (all pages, categories, endpoints); run first on a fresh clone
npm run render:diff  # what a theme change alters in the render, before overwriting preview/
npm run dev        # serve preview/ with Shopify-style routes
npm test           # Liquid render tests + theme-check
npm run verify     # re-renders, then Playwright and static checks against the running preview
npm run build      # preview/ -> _site/ for static hosting
npm run package    # dist/mccormacks-theme.zip for upload
```

`preview/`, `_site/`, `dist/` and `node_modules/` are regenerated and ignored.

`preview/` is per working tree. Sessions sharing one tree render into the
same folder, so whichever rendered last is what the dev server serves: a
race for a verify run, not a git problem. One worktree per session, as
`setup/MAINTENANCE.md` sets out, gives each its own `preview/`.
