"""Trust bar — the rotating Free Delivery / Irish Owned / Trusted row.

Its own file because it is the one component whose behaviour is decided almost
entirely by viewport width, and because two of these need a reduced-motion context
that would change every other check in the suite.

The bug that prompted it: translateX(-100%) resolves against the border box, so the
horizontal padding on the animated row made every step overshoot by that amount. The
second message sat 40px left of centre and the third 80px, on every phone. It looked
like a design choice rather than a fault, which is exactly why it survived.
"""
import sys
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8734"
CAROUSEL = (320, 390, 430, 768, 1024, 1150)   # widths that rotate
COLUMNS = (1151, 1280, 1440)                  # widths that show all three at once

res = []
def ck(name, got, want=True): res.append((got == want, name, got))

# Freezes the animation and steps the transform by hand, reporting where each message
# lands relative to the clipping window. Message i must sit flush at step i.
OFFSETS = """() => {
  const inner = document.querySelector('.trust-inner');
  const wrap  = document.querySelector('.trust-mob-wrap');
  inner.style.animation = 'none';
  const wr = wrap.getBoundingClientRect();
  const out = [];
  for (const t of ['translateX(0)', 'translateX(-100%)', 'translateX(-200%)']) {
    inner.style.transform = t;
    out.push([...inner.children].map(k => Math.round(k.getBoundingClientRect().left - wr.left)));
  }
  inner.style.animation = ''; inner.style.transform = '';
  return out;
}"""

STATE = """() => {
  const inner = document.querySelector('.trust-inner');
  const wrap  = document.querySelector('.trust-mob-wrap');
  const cs = getComputedStyle(inner), wr = wrap.getBoundingClientRect();
  const inView = (k) => {
    const r = k.getBoundingClientRect();
    return r.right > wr.left + 1 && r.left < wr.right - 1
        && r.bottom > wr.top + 1 && r.top < wr.bottom - 1;
  };
  return {
    anim: cs.animationName,
    visible: [...inner.children].filter(inView).length,
    lines: [...inner.children].map(k => k.querySelector('span').getClientRects().length),
    overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
  };
}"""

with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True)

    for w in CAROUSEL:
        pg = b.new_context(viewport={"width": w, "height": 700}).new_page()
        pg.goto(BASE + "/", wait_until="networkidle")
        steps = pg.evaluate(OFFSETS)
        ck(f"[{w}] every message lands flush, not drifted",
           [steps[i][i] for i in range(3)], [0, 0, 0])
        st = pg.evaluate(STATE)
        ck(f"[{w}] it rotates", st["anim"], "trustSlide")
        ck(f"[{w}] exactly one message is on show", st["visible"], 1)
        ck(f"[{w}] no horizontal page scroll", st["overflow"], False)
        pg.close()

    for w in COLUMNS:
        pg = b.new_context(viewport={"width": w, "height": 700}).new_page()
        pg.goto(BASE + "/", wait_until="networkidle")
        st = pg.evaluate(STATE)
        ck(f"[{w}] it does not rotate", st["anim"], "none")
        ck(f"[{w}] all three are on show", st["visible"], 3)
        # The reason the carousel runs to 1150 rather than the theme's usual 900:
        # below this the longest message wrapped while its icon stayed centred.
        ck(f"[{w}] no message wraps to a second line", st["lines"], [1, 1, 1])
        pg.close()

    # Reduced motion: stop, but do not hide two thirds of the content.
    ctx = b.new_context(viewport={"width": 390, "height": 800}, reduced_motion="reduce")
    pg = ctx.new_page()
    pg.goto(BASE + "/", wait_until="networkidle")
    st = pg.evaluate(STATE)
    ck("[reduced motion] nothing animates", st["anim"], "none")
    ck("[reduced motion] all three messages are readable", st["visible"], 3)
    ctx.close()

    # ...and the same preference must not restack the desktop row.
    ctx = b.new_context(viewport={"width": 1440, "height": 800}, reduced_motion="reduce")
    pg = ctx.new_page()
    pg.goto(BASE + "/", wait_until="networkidle")
    st = pg.evaluate(STATE)
    ck("[reduced motion, desktop] the row is untouched", st["visible"], 3)
    ck("[reduced motion, desktop] still one line each", st["lines"], [1, 1, 1])
    ctx.close()

    # Something to stop it with, for anyone reading at their own pace.
    pg = b.new_context(viewport={"width": 1024, "height": 700}).new_page()
    pg.goto(BASE + "/", wait_until="networkidle")
    pg.locator(".trust-mob-wrap").first.hover()
    pg.wait_for_timeout(150)
    ck("hovering pauses the rotation",
       pg.evaluate("() => getComputedStyle(document.querySelector('.trust-inner')).animationPlayState"),
       "paused")
    pg.close()
    b.close()

for ok, name, got in res:
    if not ok:
        print(f"FAIL  {name}   (got {got!r})")
print(f"\n{sum(1 for r in res if r[0])}/{len(res)} trust bar checks passed")
sys.exit(0 if all(r[0] for r in res) else 1)
