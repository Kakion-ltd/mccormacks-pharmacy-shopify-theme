"""Hero slider swipe.

Its own file because it needs a touch-enabled context: every other browser check
runs without touch, and turning it on globally would change how the mega-nav and
the hover states behave.

Synthetic TouchEvents rather than Playwright's touchscreen helper, which only taps.
The point of these checks is the discrimination — a swipe must move the slider, and
a vertical drag or a short flick must not — so the gesture has to be driven by hand.
"""
import sys
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8734"

res = []
def ck(name, got, want=True): res.append((got == want, name, got))

# Drives touchstart / two touchmoves / touchend across the slider. Returns nothing;
# the caller reads which pane ended up visible.
SWIPE = """([dx, dy]) => {
  const root = document.querySelector('[data-slider]');
  const r = root.getBoundingClientRect();
  const x0 = r.left + r.width * 0.5, y0 = r.top + r.height * 0.5;
  const fire = (type, x, y) => {
    const t = new Touch({ identifier: 1, target: root, clientX: x, clientY: y });
    root.dispatchEvent(new TouchEvent(type, {
      touches: type === 'touchend' ? [] : [t],
      changedTouches: [t], bubbles: true, cancelable: true,
    }));
  };
  fire('touchstart', x0, y0);
  fire('touchmove', x0 + dx * 0.4, y0 + dy * 0.4);
  fire('touchmove', x0 + dx, y0 + dy);
  fire('touchend', x0 + dx, y0 + dy);
}"""

# Same gesture, but started on a named element rather than the middle of the slider.
SWIPE_FROM = """([sel, dx, dy]) => {
  const root = document.querySelector('[data-slider]');
  const el = [...root.querySelectorAll(sel)].find(e => e.offsetParent !== null) || root;
  const r = el.getBoundingClientRect();
  const x0 = r.left + r.width * 0.5, y0 = r.top + r.height * 0.5;
  const fire = (type, x, y) => {
    const t = new Touch({ identifier: 1, target: el, clientX: x, clientY: y });
    el.dispatchEvent(new TouchEvent(type, {
      touches: type === 'touchend' ? [] : [t],
      changedTouches: [t], bubbles: true, cancelable: true,
    }));
  };
  fire('touchstart', x0, y0);
  fire('touchmove', x0 + dx * 0.4, y0 + dy * 0.4);
  fire('touchmove', x0 + dx, y0 + dy);
  fire('touchend', x0 + dx, y0 + dy);
  /* The browser follows touchend with a click on the element under the finger. */
  el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
}"""

# Which pane is on show, and what the dots claim — they must agree.
STATE = """() => {
  const root = document.querySelector('[data-slider]');
  const panes = [...root.querySelectorAll('[data-slide]')];
  const shown = panes.findIndex(p => p.style.display !== 'none');
  const dots = [...panes[shown].querySelectorAll('[data-dot-proxy]')];
  const lit = dots.findIndex(d => d.style.width === '22px');
  return { shown, lit, title: (panes[shown].querySelector('h1') || {}).textContent };
}"""

with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True)
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(BASE + "/", wait_until="networkidle")

    start = pg.evaluate(STATE)
    ck("slider starts on the first slide", start["shown"], 0)

    # A vertical drag is the page scrolling, not a slide change.
    pg.evaluate(SWIPE, [0, -160])
    ck("a vertical drag does not change slide", pg.evaluate(STATE)["shown"], 0)

    # Neither is a short horizontal flick, which is how a tap wobbles.
    pg.evaluate(SWIPE, [-20, 0])
    ck("a short flick does not change slide", pg.evaluate(STATE)["shown"], 0)

    # A real swipe left advances.
    pg.evaluate(SWIPE, [-140, 0])
    after = pg.evaluate(STATE)
    ck("swiping left advances a slide", after["shown"], 1)
    ck("the dots follow the swipe", after["lit"], 1)
    ck("the advanced slide is the next one", (after["title"] or "").strip(), "Feel Your Best")

    # And back.
    pg.evaluate(SWIPE, [140, 0])
    ck("swiping right goes back", pg.evaluate(STATE)["shown"], 0)

    # Wrapping, so a swipe never dead-ends.
    pg.evaluate(SWIPE, [140, 0])
    wrapped = pg.evaluate(STATE)
    ck("swiping back from the first wraps to the last", wrapped["shown"], 4)
    ck("the dots follow the wrap", wrapped["lit"], 4)

    # A mostly-vertical diagonal is still a scroll: the page must win ambiguous drags.
    pg.evaluate(SWIPE, [-60, -200])
    ck("a mostly-vertical diagonal does not change slide", pg.evaluate(STATE)["shown"], 4)

    # The subtle one: a swipe that begins on the SHOP button must move the slider and
    # must NOT follow the link. Without the suppressor the browser fires a click on
    # the anchor after touchend and the visitor is navigated away mid-gesture.
    # A navigation here destroys the execution context, so every read is guarded:
    # the failure this check exists for would otherwise surface as a crash with no
    # output rather than as a named, failing check.
    def state_or_none():
        try:
            return pg.evaluate(STATE)
        except Exception:
            return None

    before_url = pg.url
    try:
        pg.evaluate(SWIPE_FROM, ["a.hero-cta", -140, 0])
    except Exception:
        pass
    pg.wait_for_timeout(600)                     # let any navigation commit
    after = state_or_none()
    navigated = pg.url != before_url or after is None
    ck("a swipe starting on the button does not navigate", navigated, False)
    ck("a swipe starting on the button still changes slide",
       after is not None and after["shown"] != 4)

    # And a genuine tap still follows the link — the suppressor must not turn the
    # button into a decoration. Reloaded first so this stands on its own rather than
    # inheriting whatever the checks above left on screen.
    pg.goto(BASE + "/", wait_until="networkidle")
    home = pg.url
    pg.locator("a.hero-cta:visible").first.click()
    pg.wait_for_load_state("networkidle")
    ck("tapping the button still follows the link", pg.url != home)

    ck("no JS errors", errs, [])
    b.close()

for ok, name, got in res:
    if not ok:
        print(f"FAIL  {name}   (got {got!r})")
print(f"\n{sum(1 for r in res if r[0])}/{len(res)} hero swipe checks passed")
sys.exit(0 if all(r[0] for r in res) else 1)
