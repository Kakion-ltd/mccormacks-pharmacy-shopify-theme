import sys
from playwright.sync_api import sync_playwright
BASE="http://localhost:8734"
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
    out.append(("self-hosted woff2 requested once", len(font_reqs)==1, font_reqs))

    loaded = pg.evaluate("""async () => {
      await document.fonts.ready;
      return {
        w400: document.fonts.check('400 16px Mulish'),
        w700: document.fonts.check('700 16px Mulish'),
        w800: document.fonts.check('800 16px Mulish'),
        w900: document.fonts.check('900 16px Mulish'),
        families: [...document.fonts].map(f => f.family + ':' + f.weight),
      };
    }""")
    for w in ("w400","w700","w800","w900"):
        out.append((f"Mulish {w[1:]} available", loaded[w], loaded[w]))
    out.append(("one @font-face registered", len(loaded["families"])==1, loaded["families"]))

    # The body must actually be painted in Mulish, not the fallback.
    used = pg.evaluate("getComputedStyle(document.body).fontFamily")
    out.append(("body uses Mulish first", used.startswith("Mulish") or "Mulish" in used.split(",")[0], used))

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

bad=[o for o in out if not o[1]]
for name, ok, detail in out:
    print(("  ok  " if ok else "  FAIL") + f"  {name}" + ("" if ok else f"   {detail}"))
print(f"\n{len(out)-len(bad)}/{len(out)} font checks passed")
sys.exit(1 if bad else 0)
