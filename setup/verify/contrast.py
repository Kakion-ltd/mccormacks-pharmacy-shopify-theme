"""Text contrast on the brand greens.

The theme shipped white text on #82C914 at 2.04:1 against a 4.5:1 WCAG AA
requirement, on ADD TO BAG and every other primary button. The foreground is
derived from perceived brightness in theme.liquid, so it survives a merchant
changing the colour — this asserts the result rather than the mechanism.

The `button_text_white` setting can override that back to white, which is a
deliberate brand choice and is currently ON. Those elements are reported as
ACCEPTED rather than passed: the count stays visible on every run, so the cost
is never silently absorbed, but it does not fail the suite. Everything not
explained by that setting still fails normally.

Only real, visible, text-bearing elements are measured. Anything whose background
resolves to transparent is walked up to its painted ancestor, because that is what
a reader actually sees behind the glyphs. A gradient ancestor is measured at every
colour stop and the worst ratio is reported; a url() image is skipped.
"""
import os
import re
import sys
from playwright.sync_api import sync_playwright

BASE = f"http://localhost:{os.environ.get('PORT', '8734')}"
PAGES = ["/", "/collections/medicines-health", "/products/cetrine-allergy-10mg-30-tablets",
         "/cart", "/pages/wishlist", "/pages/store-locator", "/pages/brands",
         "/pages/gift-vouchers", "/pages/prescriptions"]
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
  // Returns the painted layer(s) behind an element. A solid colour is one entry. A
  // linear gradient is every colour stop, so contrast is measured at each end and
  // the worst wins: the hero copy panel fades from one green to another and a
  // solid-only check read it as unmeasurable and skipped the largest text on the
  // homepage. A url() image is still null: the real contrast there depends on the
  // artwork, which this cannot measure and must not guess.
  const stops = (img) => {
    const m = img.match(/linear-gradient\((.*)\)$/s);
    if (!m) return null;
    const cols = [...m[1].matchAll(/rgba?\(([^)]+)\)/g)].map((x) => parse(x[1]));
    // A translucent stop shows whatever is painted beneath; that composite is not
    // measured here, so the gradient is treated like an image and skipped.
    if (cols.some((c) => c[3] !== undefined && c[3] < 0.95)) return null;
    return cols.length >= 2 ? cols : null;
  };
  const painted = (el) => {
    for (let n = el; n && n !== document.documentElement; n = n.parentElement) {
      const cs = getComputedStyle(n);
      if (cs.backgroundImage && cs.backgroundImage !== 'none') {
        const g = stops(cs.backgroundImage);
        if (g && !cs.backgroundImage.includes('url(')) return { gradient: true, layers: g };
        return null;
      }
      const p = parse(cs.backgroundColor);
      if (p.length >= 3 && (p[3] === undefined || p[3] > 0.95)) return { gradient: false, layers: [p] };
    }
    return { gradient: false, layers: [[255, 255, 255]] };
  };
  const out = [];
  for (const el of document.querySelectorAll('a, button, span, p, h1, h2, h3, div, label, li')) {
    const txt = [...el.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent.trim()).join('');
    if (txt.length < 2) continue;
    const r = el.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) continue;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none' || +cs.opacity === 0) continue;
    // The harness's express-checkout stand-in never ships; do not fail the suite on it.
    if (el.closest('[data-mock-express]')) continue;
    const painted_bg = painted(el);
    if (!painted_bg) continue;
    const fg = parse(cs.color);
    if (fg[3] !== undefined && fg[3] < 0.95) continue;
    const l1 = lum(fg[0], fg[1], fg[2]);
    // Worst stop wins: text has to be legible at every point of a gradient.
    let worst = null;
    for (const bg of painted_bg.layers) {
      const l2 = lum(bg[0], bg[1], bg[2]);
      const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
      if (!worst || ratio < worst.ratio) worst = { ratio, bg };
    }
    const size = parseFloat(cs.fontSize), weight = +cs.fontWeight || 400;
    const large = size >= 24 || (size >= 18.66 && weight >= 700);
    out.push({ txt: txt.slice(0, 40), ratio: +worst.ratio.toFixed(2), large, gradient: painted_bg.gradient,
               fg: cs.color, bg: `rgb(${worst.bg[0]}, ${worst.bg[1]}, ${worst.bg[2]})`,
               stops: painted_bg.gradient ? painted_bg.layers.map((b) => `rgb(${b[0]}, ${b[1]}, ${b[2]})`) : null });
  }
  return out;
}"""

TOKENS = """() => {
  const cs = getComputedStyle(document.documentElement);
  return { primary: cs.getPropertyValue('--c-primary').trim(),
           on_primary: cs.getPropertyValue('--c-on-primary').trim() };
}"""

def rgb(hex_or_rgb):
    """'#82C914' or 'rgb(130, 201, 20)' -> (130, 201, 20)."""
    t = hex_or_rgb.strip()
    if t.startswith("#"):
        t = t[1:]
        return tuple(int(t[i:i + 2], 16) for i in (0, 2, 4))
    return tuple(int(n) for n in re.findall(r"\d+", t)[:3])

fails, accepted, checked = [], [], 0
tokens = {}
with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True)
    for label, vp in (("desktop", {"width": 1440, "height": 900}),
                      ("mobile", {"width": 390, "height": 844})):
        pg = b.new_context(viewport=vp).new_page()
        for path in PAGES:
            pg.goto(BASE + path, wait_until="networkidle")
            if not tokens:
                tokens = pg.evaluate(TOKENS)
            for r in pg.evaluate(PROBE):
                checked += 1
                if r["ratio"] >= (AA_LARGE if r["large"] else AA):
                    continue
                # Explained by the brand override, and only by it: white ink sitting on
                # exactly the configured primary. Anything else is a genuine failure.
                on_primary_is_white = rgb(tokens.get("on_primary") or "#000") == (255, 255, 255)
                if (on_primary_is_white
                        and rgb(r["fg"]) == (255, 255, 255)
                        and rgb(r["bg"]) == rgb(tokens["primary"])):
                    accepted.append((label, path, r))
                else:
                    fails.append((label, path, r))
    b.close()

for label, path, r in fails[:25]:
    where = f'gradient stop {r["bg"]} of {" -> ".join(r["stops"])}' if r.get("gradient") else r["bg"]
    print(f'FAIL  [{label}] {path}  {r["ratio"]}:1  "{r["txt"]}"  {r["fg"]} on {where}')
gradients = sum(1 for _, _, r in fails if r.get("gradient"))
if gradients:
    print(f'{gradients} of those sit on a gradient and were invisible to the solid-only check')

passed = checked - len(fails) - len(accepted)
print(f'\n{passed}/{checked} text elements meet WCAG AA')
if accepted:
    worst = min(r["ratio"] for _, _, r in accepted)
    print(f'{len(accepted)} ACCEPTED — white on {tokens["primary"]} by the '
          f'button_text_white setting, worst {worst}:1 against a 4.5:1 requirement.')
    print('  Set button_text_white to "auto" in the theme editor to clear these.')
if fails:
    print(f'{len(fails)} below threshold and not explained by that setting')
sys.exit(1 if fails else 0)
