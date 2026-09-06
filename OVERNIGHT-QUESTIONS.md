# Overnight questions

Items stopped under the escalation rule, with findings, options and a
recommendation. Nothing below has been built.

## Item 3 — Trust bar blocks

**What I found.** The instruction was "convert to 3 blocks, each with text
plus an icon choice". Blocks belong to one section instance, but the trust
row is not one section: `snippets/trust-row.liquid` is rendered at the top
of **26 sections** — the homepage `trust-bar` section plus 25 interior-page
sections (about, contact, returns, shipping, every account page, and so
on). If the homepage section gets blocks, editing them changes the homepage
only; the other 25 copies keep the hardcoded copy. That recreates the exact
"theme contradicts itself" failure item 1 removed for phone numbers —
worse, because the stale claims ("7 stores", "20,000 customers") are the
content most likely to be edited.

**Options.**

1. **Global theme settings (recommended).** A "Trust bar" group in
   `settings_schema.json` with three fixed slots, each an icon select
   (truck / shamrock / star), a bold lead and a text field supporting the
   existing `[threshold]` token. The snippet reads `settings.*`, so one
   edit updates all 26 renders. Loses add/remove/reorder — but the mobile
   carousel animation (`trustSlide` keyframes, and `verify/trust-bar.py`)
   is hard-built for exactly three messages, so a variable count is a
   design change anyway, which I am told not to make.
2. **Blocks on the homepage section, snippet defaults elsewhere.** Follows
   the letter of the instruction; homepage becomes editable, 25 interior
   copies drift. Not recommended.
3. **Blocks plus moving the trust row out of the 25 interior sections into
   each of their templates.** Every page then has its own block instance —
   26 places to edit one claim. Worst of the three.

**Recommendation.** Option 1. It is a smaller change than option 2, keeps
every page consistent, and respects the three-message animation contract.
If you confirm, it is ~2 hours including the verify run.
