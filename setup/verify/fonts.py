import os
import re
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
BASE = f"http://localhost:{os.environ.get('PORT', '8734')}"
out=[]
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_page(viewport={"width":1440,"height":900})
    reqs=[]
    pg.on("request", lambda r: reqs.append(r.url))
    pg.goto(BASE+"/", wait_until="networkidle")
    pg.wait_for_timeout(400)

    third = [u for u in reqs if "fonts.googleapis" in u or "fonts.gstatic" in u]
    out.append(("no third-party font requests", len(third)==0, third))

    font_reqs = [u for u in reqs if u.endswith(".woff2")]
    out.append(("each self-hosted woff2 requested once, Mulish and Nunito",
                sorted(u.rsplit("/", 1)[1].split("?")[0] for u in font_reqs)
                == ["mulish-variable.woff2", "nunito-variable.woff2"], font_reqs))

    loaded = pg.evaluate("""async () => {
      await document.fonts.ready;
      return {
        w400: document.fonts.check('400 16px Mulish'),
        w700: document.fonts.check('700 16px Mulish'),
        w800: document.fonts.check('800 16px Mulish'),
        w900: document.fonts.check('900 16px Mulish'),
        n700: document.fonts.check('700 16px Nunito'),
        n800: document.fonts.check('800 16px Nunito'),
        families: [...document.fonts].map(f => f.family + ':' + f.weight),
      };
    }""")
    for w in ("w400","w700","w800","w900"):
        out.append((f"Mulish {w[1:]} available", loaded[w], loaded[w]))
    for w in ("n700","n800"):
        out.append((f"Nunito {w[1:]} available", loaded[w], loaded[w]))
    out.append(("two @font-face registered", len(loaded["families"])==2, loaded["families"]))

    # The body must actually be painted in Mulish, not the fallback.
    used = pg.evaluate("getComputedStyle(document.body).fontFamily")
    out.append(("body uses Mulish first", used.startswith("Mulish") or "Mulish" in used.split(",")[0], used))

    # Headings must be painted in Nunito's own faces: the platform font Chrome actually
    # drew with, not just the family the CSS asked for. Arial Rounded, which this
    # replaced, passed a computed-style check on a Mac while Windows drew Arial.
    cdp = pg.context.new_cdp_session(pg); cdp.send("DOM.enable"); cdp.send("CSS.enable")
    # The first visible one: the hero's other slides are h2s too, hidden, with nothing drawn.
    pg.evaluate("[...document.querySelectorAll('main h2')].find(e => e.offsetParent && e.getBoundingClientRect().width)?.setAttribute('data-font-probe', '')")
    root = cdp.send("DOM.getDocument", {"depth": -1})["root"]["nodeId"]
    nid = cdp.send("DOM.querySelector", {"nodeId": root, "selector": "[data-font-probe]"})["nodeId"]
    drawn = [f["familyName"] for f in cdp.send("CSS.getPlatformFontsForNode", {"nodeId": nid})["fonts"]]
    out.append(("headings are drawn in self-hosted Nunito", drawn and all(n.startswith("Nunito") for n in drawn), drawn))

    # The five out-of-subset glyphs must still be visible via the fallback stack.
    vis = pg.evaluate("""() => {
      const probe = document.createElement('span');
      probe.style.cssText='position:absolute;left:-9999px;font-family:Mulish,system-ui,sans-serif;font-size:40px';
      document.body.appendChild(probe);
      const r = {};
      for (const ch of ['\\u2192','\\u2605','\\u26a0','\\u2713','\\u2714']) {
        probe.textContent = ch;
        r['U+' + ch.codePointAt(0).toString(16).toUpperCase()] = probe.getBoundingClientRect().width;
      }
      probe.remove();
      return r;
    }""")
    out.append(("all 5 out-of-subset glyphs render with width", all(v>0 for v in vis.values()), vis))
    pg.close(); b.close()

# --font-heading is the one place the heading face is named. A typed-out copy of the
# old stack came back once within a day of being removed (the pharmacy questionnaire).
theme = Path(__file__).resolve().parents[2] / "shopify-theme"
typed = [f"{f.relative_to(theme)}:{i}" for f in theme.rglob("*.*") if f.suffix in (".liquid", ".css", ".js")
         for i, line in enumerate(f.read_text(errors="ignore").splitlines(), 1)
         # a stack, so the @font-face descriptor (font-family: 'Nunito';) is not counted
         if re.search(r"font-family:\s*['\"]?(Arial Rounded|Nunito['\"]?\s*,)", line)]
out.append(("no heading font typed out instead of var(--font-heading)", not typed, typed))

bad=[o for o in out if not o[1]]
for name, ok, detail in out:
    print(("  ok  " if ok else "  FAIL") + f"  {name}" + ("" if ok else f"   {detail}"))
print(f"\n{len(out)-len(bad)}/{len(out)} font checks passed")
sys.exit(1 if bad else 0)
