"""Header between 1440 and 901 — the band the four-width sweep steps over.

sweep.py samples 1440, 1280, 1024 and 390. Three defects lived in the gaps and none
of them could fail a check there, because a wrapped header is *valid* layout: no
overflow, no broken image, no JS error. The sweep was green throughout.

What was wrong, and what each assertion below holds:

  - Nothing compressed between 1101 and 1271. The ten department links plus the two
    pills need 1273px, so the pills dropped to a second row at 1272 and the header
    grew 27px, with the only compression rule starting 171px lower down.
  - The compression rule itself wrapped the nav. It put 12px of padding on each of
    the ten plain text links - 240px - so "Brands" fell to a third row at 1068 and
    the header reached 186px, inside the band meant to prevent exactly that.
  - --hdr-pinned was three hardcoded values and feeds scroll-padding-top. Across
    this band it understated the real height by up to 72px, so the skip link and
    any focused control below the fold landed underneath the sticky bar. That one
    is not cosmetic, which is why it is asserted per width rather than sampled.

The sweep of widths is deliberately dense (every 8px, plus both sides of each
breakpoint). A step function is the failure mode here: the old bugs were each a
single band that happened to fall between two samples, and a coarse sweep would
step over the replacement just as cleanly.
"""
import os
import sys
from playwright.sync_api import sync_playwright

BASE = f"http://localhost:{os.environ.get('PORT', '8734')}"
# Every 8px across the desktop band, plus the exact breakpoint edges where a
# rule hands over and an off-by-one lands.
WIDTHS = sorted({w for w in range(904, 1441, 8)}
                | {901, 902, 903, 1099, 1100, 1101, 1271, 1272, 1279, 1280, 1281, 1440})

# One evaluate per width: row counts come from distinct offsetTop buckets, which is
# what "wrapped" actually means, and the declared height is compared against the
# measured one rather than against the number a media query hoped for.
STATE = """() => {
  const bar   = document.querySelector('.hdr-sticky');
  const root  = document.querySelector('[data-mega-root]');
  const nav   = root.querySelector(':scope > nav');
  const pills = root.querySelector(':scope > div:not([data-mega-panel])');
  // Clustered on vertical centre, not top: the row is align-items:center and the nav
  // links are 17px against the pills' 32px, so their tops differ by 8px while they sit
  // on the same line. Bucketing by top counts that as a wrap and fails everywhere.
  // A real wrap separates centres by a full row (27px+), far outside the tolerance.
  const rows  = (el, sel) => {
    const ks = [...el.querySelectorAll(sel)].filter(k => {
      const s = getComputedStyle(k), r = k.getBoundingClientRect();
      return s.display !== 'none' && s.visibility !== 'hidden' && r.width > 0 && r.height > 0;
    });
    const mids = ks.map(k => { const r = k.getBoundingClientRect(); return r.top + r.height / 2; })
                   .sort((a, b) => a - b);
    let n = 0;
    for (let i = 0; i < mids.length; i++) if (i === 0 || mids[i] - mids[i - 1] > 6) n++;
    return n;
  };
  const input = document.querySelector('[data-ps-input]');
  const c = document.createElement('canvas').getContext('2d');
  c.font = getComputedStyle(input).font;
  return {
    navRows:   rows(nav, ':scope > a'),
    // nav and pills as siblings: 1 means they share a line, 2 means the pills dropped
    barRows:   rows(root, ':scope > nav, :scope > div:not([data-mega-panel])'),
    height:    Math.round(bar.getBoundingClientRect().height),
    declared:  parseInt(getComputedStyle(document.documentElement)
                 .getPropertyValue('--hdr-pinned'), 10),
    inputW:    Math.round(input.getBoundingClientRect().width),
    placeholdW: Math.round(c.measureText(input.placeholder).width),
  };
}"""

bad = []
with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.goto(BASE + "/", wait_until="load")
    pg.wait_for_timeout(300)
    for w in WIDTHS:
        pg.set_viewport_size({"width": w, "height": 900})
        pg.wait_for_timeout(60)
        s = pg.evaluate(STATE)
        # The ten links stay on one line at every desktop width. This is the assertion
        # the 1068 three-row header would have failed.
        if s["navRows"] != 1:
            bad.append(f"{w}: department links wrapped to {s['navRows']} rows")
        # The pills share the line down to the point where they genuinely cannot, and
        # they drop exactly once - no dead band above it where nothing compensated.
        if w >= 1101 and s["barRows"] != 1:
            bad.append(f"{w}: pills dropped to their own row above 1101 (bar is {s['barRows']} rows)")
        if s["barRows"] > 2:
            bad.append(f"{w}: nav bar is {s['barRows']} rows")
        # theme.js measures the bar; anything the browser scrolls to clears it only if
        # this holds. 1px for sub-pixel rounding, nothing more.
        if abs(s["declared"] - s["height"]) > 1:
            bad.append(f"{w}: --hdr-pinned is {s['declared']}px, bar measures {s['height']}px")
        # The search placeholder is the header's one piece of running text; a column
        # cap that cut it mid-word is how the 1100 band was found.
        if s["placeholdW"] > s["inputW"]:
            bad.append(f"{w}: search placeholder needs {s['placeholdW']}px, input is {s['inputW']}px")
    # The observer must follow a live resize, not just the width the page loaded at -
    # a hardcoded value looks correct on load and drifts the moment the window moves.
    for w in (1440, 1200, 1050, 950, 1440):
        pg.set_viewport_size({"width": w, "height": 900})
        pg.wait_for_timeout(150)
        s = pg.evaluate(STATE)
        if abs(s["declared"] - s["height"]) > 1:
            bad.append(f"resize to {w}: --hdr-pinned is {s['declared']}px, bar measures {s['height']}px")
    pg.close()
    b.close()

print("\n".join(bad) if bad else
      f"{len(WIDTHS)} widths from 901 to 1440: department links on one line, pills drop "
      "once and only below 1101, --hdr-pinned matches the measured bar on load and on "
      "resize, search placeholder fits")
sys.exit(1 if bad else 0)
