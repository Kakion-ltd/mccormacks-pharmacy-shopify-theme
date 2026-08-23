import sys
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8734"
results = []
def check(name, got, want=True):
    results.append((got == want, name, got))

with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True)
    for label, vp in (("desktop", {"width":1440,"height":900}), ("mobile", {"width":390,"height":844})):
        ctx = b.new_context(viewport=vp)          # fresh storage = first-time visitor
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(BASE + "/", wait_until="networkidle")
        pg.wait_for_timeout(400)

        banner = pg.locator("[data-cc-banner]")
        check(f"[{label}] banner shows to a first-time visitor", banner.is_visible())

        # PRIOR CONSENT: nothing may have fired, and nothing may be stored.
        log = pg.evaluate("window.__pixelLog")
        check(f"[{label}] no pixel fired before a choice",
              [e for e in log if e["at"] == "fired"] == [])
        consent = pg.evaluate("window.Shopify.customerPrivacy.currentVisitorConsent()")
        check(f"[{label}] no consent recorded before a choice",
              all(v == "" for v in consent.values()))
        check(f"[{label}] setTrackingConsent not called before a choice",
              pg.evaluate("window.__consentCalls || []") == [])

        # EQUAL PROMINENCE: reject must not be visually weaker than accept.
        box = lambda sel: pg.locator(sel).bounding_box()
        a, r = box("[data-cc-accept]"), box("[data-cc-reject]")
        style = lambda sel: pg.evaluate(
            "s => { const e = document.querySelector(s); const c = getComputedStyle(e);"
            " return [c.backgroundColor, c.color, c.fontSize, c.fontWeight].join('|'); }", sel)
        check(f"[{label}] reject is the same height as accept", abs(a["height"] - r["height"]) < 1)
        check(f"[{label}] reject is styled identically to accept",
              style("[data-cc-accept]") == style("[data-cc-reject]"))

        # NO PRE-TICKED BOXES.
        pg.locator("[data-cc-manage]").click()
        pg.wait_for_timeout(200)
        checked = pg.evaluate(
            "Array.from(document.querySelectorAll('[data-cc-toggle]')).filter(i => i.checked).length")
        check(f"[{label}] no optional category is pre-ticked", checked == 0)

        # REJECT: records a choice, grants nothing, and dismisses the banner.
        pg.locator("[data-cc-reject]").click()
        pg.wait_for_timeout(300)
        check(f"[{label}] banner dismissed after reject", banner.is_visible(), False)
        log = pg.evaluate("window.__pixelLog")
        check(f"[{label}] still no pixel fired after reject",
              [e for e in log if e["at"] == "fired"] == [])
        consent = pg.evaluate("window.Shopify.customerPrivacy.currentVisitorConsent()")
        check(f"[{label}] reject stored as an explicit no",
              consent["analytics"] == "no" and consent["marketing"] == "no")
        check(f"[{label}] sale_of_data never granted", consent["sale_of_data"] == "no")

        # PERSISTENCE: a visitor who answered is not asked again.
        pg.goto(BASE + "/collections/skincare", wait_until="networkidle")
        pg.wait_for_timeout(400)
        check(f"[{label}] banner does not reappear after a choice",
              pg.locator("[data-cc-banner]").is_visible(), False)
        check(f"[{label}] no pixel fired on a later page either",
              [e for e in pg.evaluate("window.__pixelLog") if e["at"] == "fired"] == [])

        # CHANGEABLE: the footer link reopens it with stored state reflected.
        pg.locator("[data-cc-reopen]").click()
        pg.wait_for_timeout(300)
        check(f"[{label}] footer link reopens the banner",
              pg.locator("[data-cc-banner]").is_visible())
        check(f"[{label}] reopened panel shows the stored (rejected) state",
              pg.evaluate("Array.from(document.querySelectorAll('[data-cc-toggle]')).filter(i=>i.checked).length") == 0)

        # ACCEPT: only now may pixels fire.
        pg.locator("[data-cc-accept]").click()
        pg.wait_for_timeout(300)
        fired = sorted(e["pixel"] for e in pg.evaluate("window.__pixelLog") if e["at"] == "fired")
        check(f"[{label}] both pixels fire only after accept", fired == ["ga4", "meta"])
        payload = pg.evaluate("window.__consentCalls.at(-1)")
        check(f"[{label}] accept grants analytics+marketing+preferences",
              payload["analytics"] and payload["marketing"] and payload["preferences"])
        check(f"[{label}] accept still does not grant sale_of_data", payload["sale_of_data"], False)

        # GRANULAR: analytics only must not release the marketing pixel.
        ctx2 = b.new_context(viewport=vp)
        pg2 = ctx2.new_page()
        pg2.on("pageerror", lambda e: errs.append(str(e)))
        pg2.goto(BASE + "/", wait_until="networkidle")
        pg2.wait_for_timeout(400)
        pg2.locator("[data-cc-manage]").click()
        pg2.locator("#cc-analytics").check()
        pg2.locator("[data-cc-save]").click()
        pg2.wait_for_timeout(300)
        fired2 = sorted(e["pixel"] for e in pg2.evaluate("window.__pixelLog") if e["at"] == "fired")
        check(f"[{label}] analytics-only releases ga4 and withholds meta", fired2 == ["ga4"])
        ctx2.close()

        check(f"[{label}] no JS errors", errs == [])
        ctx.close()
    b.close()

for ok, name, got in results:
    print(("  ok  " if ok else "  FAIL") + f"  {name}" + ("" if ok else f"   (got {got!r})"))
failed = [r for r in results if not r[0]]
print(f"\n{len(results)-len(failed)}/{len(results)} consent checks passed")
sys.exit(1 if failed else 0)
