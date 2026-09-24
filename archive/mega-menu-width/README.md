# Mega menu panel widths — unfinished, parked 24 Sep 2026

`mega-menu-width.patch` is work that was never committed. It was saved from
the `fable/mega-width` worktree (`McCormacks-Fable`, last edited 11 Sep 2026
00:18) before that folder was deleted. The branch itself was merged long ago;
only this edit was left over.

## What it was trying to do

Size each wide mega-menu panel to fit its columns, rather than using a
hand-picked width.

The four wide panels had fixed widths of 1380, 1000, 1240 and 1100px. Only
Medicines & Health's width was consistent with its column count. Skincare, for
example, put five groups into three 330px columns carrying about 167px of text,
so the right side of the panel read as empty.

The patch works the width out from the columns:
`cols × 200 + (cols − 1) × 24 + 2 × 30`. 200px is the widest label measured
across all eight panels at 1440, which is 194px ("Medicines & Health"). The
patch also drops the per-panel column minimums and gaps in favour of one gap
(24px) and one side padding (30px).

Resulting widths:

| Panel | Before | After |
|---|---|---|
| Medicines & Health | 1380 | 1380 |
| Vitamins | 1000 | 932 |
| Beauty | 1240 | 932 |
| Skincare | 1100 | 708 |

## State

- It was never rendered, verified or reviewed. It stopped mid-session, with
  both files edited and nothing committed.
- As of 24 Sep 2026 it applies cleanly to `main`. Neither file, nor
  `taxonomy.json`, has changed since it was written.
- `snippets/mega-menu.liquid` is generated. To use this, apply only the
  `setup/gen_mega.py` half and regenerate. Don't hand-apply the snippet half.
  (See "Generated snippets" in `setup/MAINTENANCE.md`.)

To try it:

```sh
git apply --include=setup/gen_mega.py archive/mega-menu-width/mega-menu-width.patch
python3 setup/gen_mega.py && npm run verify
```

Then check each panel at 1024 and 1440. Narrower panels change where the
narrow-panel alignment in `theme.js` has room to place them.
