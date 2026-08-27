"""Generated files must match what their generator produces.

Three snippets in this theme are generated from taxonomy and design-handoff data.
All three had drifted the same way: a sitewide edit corrected the generated file,
nobody touched the generator, and the next regeneration would have silently put the
old value back. The contrast fix was reverted this way once already and was caught
only because a WCAG check happened to cover that element.

This runs each generator against a scratch copy of the theme and diffs the result.
It never writes into shopify-theme/, so it is safe to run at any time.

A failure means one of two things, and the message says which:
  - the generator is behind a hand edit  -> fix the generator, regenerate
  - the generator changed               -> regenerate and commit the output
"""
import difflib
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
THEME = ROOT / "shopify-theme"

# generator -> the snippets it owns
GENERATORS = {
    "gen_brands.py": ["brand-az.liquid"],
    "gen_mega.py": ["mega-menu.liquid"],
    "gen_category_nav.py": [
        "category-breadcrumb.liquid", "category-breadcrumb-data.liquid",
        "category-chips.liquid", "category-chip.liquid",
        "category-level.liquid", "collection-rank.liquid", "mobile-nav.liquid",
    ],
}

failures = []
checked = 0

with tempfile.TemporaryDirectory() as tmp:
    backup = pathlib.Path(tmp) / "snippets"
    shutil.copytree(THEME / "snippets", backup)

    for gen, outputs in GENERATORS.items():
        proc = subprocess.run([sys.executable, str(ROOT / "setup" / gen)],
                              capture_output=True, text=True, cwd=ROOT)
        if proc.returncode != 0:
            tail = (proc.stderr or proc.stdout).strip().splitlines()[-1:] or ["(no output)"]
            failures.append(f"{gen} FAILED TO RUN: {tail[0]}")
            continue

        for name in outputs:
            checked += 1
            produced = (THEME / "snippets" / name).read_text(encoding="utf-8")
            committed = (backup / name).read_text(encoding="utf-8")
            if produced != committed:
                diff = list(difflib.unified_diff(
                    committed.splitlines(), produced.splitlines(),
                    fromfile=f"committed/{name}", tofile=f"generated/{name}", lineterm="", n=0))
                failures.append(
                    f"{name} DRIFTED from {gen}\n"
                    + "\n".join("      " + d for d in diff[:8])
                    + (f"\n      … {len(diff) - 8} more diff lines" if len(diff) > 8 else ""))

    # Always restore, pass or fail: this check must never leave the theme modified.
    for f in backup.iterdir():
        shutil.copy2(f, THEME / "snippets" / f.name)

for f in failures:
    print(f"FAIL  {f}")

if failures:
    print(f"\n{checked - len(failures)}/{checked} generated files match their generator")
    print("\nA generated file and its generator have diverged. Fix the GENERATOR,")
    print("not the generated file, or the next regeneration reverts the change again.")
    sys.exit(1)

print(f"{checked}/{checked} generated files match their generator")
