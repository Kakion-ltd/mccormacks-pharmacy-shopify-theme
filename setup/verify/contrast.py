"""Text contrast on the brand greens.

The theme shipped white text on #82C914 at 2.04:1 against a 4.5:1 WCAG AA
requirement, on ADD TO BAG and every other primary button. The foreground is now
derived from perceived brightness in theme.liquid, so it survives a merchant
changing the colour — this asserts the result rather than the mechanism.

Only real, visible, text-bearing elements are measured. Anything whose background
resolves to transparent is walked up to its painted ancestor, because that is what
a reader actually sees behind the glyphs.
"""
import sys
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8734"
PAGES = ["/", "/collections/medicines-health", "/products/cetrine-allergy-tablets",
         "/cart", "/pages/wishlist", "/pages/store-locator"]
AA = 4.5          # WCAG 2.1 AA, normal text
AA_LARGE = 3.0    # >=24px, or >=18.66px bold

# Reads every visible text node's own colour against the first painted background
# behind it, and reports anything that falls short.
PROBE = """() => {
  const lum = (r, g, b) => {
    const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
  };
  const parse = (c) => (c.match(/[\\d.]+/g) || []).map(Number);
  // Returns null when the nearest painted layer is an image or gradient: the real
  // contrast there depends on the artwork, which this cannot measure and must not guess.
  const painted = (el) => {
    for (let n = el; n && n !== document.documentElement; n = n.parentElement) {
      const cs = getComputedStyle(n);
      if (cs.backgroundImage && cs.backgroundImage !== 'none') return null;
      const p = parse(cs.backgroundColor);
      if (p.length >= 3 && (p[3] === undefined || p[3] > 0.95)) return p;
    }
    return [255, 255, 255];
  };
  const out = [];
  for (const el of document.querySelectorAll('a, button, span, p, h1, h2, h3, div, label, li')) {
    const txt = [...el.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent.trim()).join('');
    if (txt.length < 2) continue;
    const r = el.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) continue;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none' || +cs.opacity === 0) continue;
    const bg = painted(el);
    if (!bg) continue;
    const fg = parse(cs.color);
    if (fg[3] !== undefined && fg[3] < 0.95) continue;
    const [l1, l2] = [lum(fg[0], fg[1], fg[2]), lum(bg[0], bg[1], bg[2])];
    const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
    const size = parseFloat(cs.fontSize), weight = +cs.fontWeight || 400;
    const large = size >= 24 || (size >= 18.66 && weight >= 700);
    out.push({ txt: txt.slice(0, 40), ratio: +ratio.toFixed(2), large,
               fg: cs.color, bg: `rgb(${bg[0]}, ${bg[1]}, ${bg[2]})` });
  }
  return out;
}"""

fails, checked = [], 0
with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True)
    for label, vp in (("desktop", {"width": 1440, "height": 900}),
                      ("mobile", {"width": 390, "height": 844})):
        pg = b.new_context(viewport=vp).new_page()
        for path in PAGES:
            pg.goto(BASE + path, wait_until="networkidle")
            for r in pg.evaluate(PROBE):
                checked += 1
                if r["ratio"] < (AA_LARGE if r["large"] else AA):
                    fails.append((label, path, r))
    b.close()

for label, path, r in fails[:25]:
    print(f'FAIL  [{label}] {path}  {r["ratio"]}:1  "{r["txt"]}"  {r["fg"]} on {r["bg"]}')

print(f'\n{checked - len(fails)}/{checked} text elements meet WCAG AA'
      + (f' — {len(fails)} below threshold' if fails else ''))
sys.exit(1 if fails else 0)
