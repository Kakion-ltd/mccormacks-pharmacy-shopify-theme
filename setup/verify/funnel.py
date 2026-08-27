import sys
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8734"
RESTRICTED = "Nurofen Plus"
results = []
errors = []

def check(name, got, want=True):
    ok = (got == want)
    results.append((ok, name, got))
    return ok

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    for label, vp in (("desktop", {"width": 1440, "height": 900}),
                      ("mobile",  {"width": 390,  "height": 844})):
        page = browser.new_page(viewport=vp)
        page.on("pageerror", lambda e: errors.append(f"{label}: {e}"))
        page.on("console", lambda m: errors.append(f"{label} console.error: {m.text}")
                if m.type == "error" else None)

        # ---- A. Predictive search ----
        page.goto(BASE + "/", wait_until="networkidle")

        # The hero's <picture> mobile swap, asserted on whichever slide actually carries
        # a mobile crop rather than a fixed index — reordering slides in the editor must
        # not quietly turn this into a no-op. currentSrc rather than the markup: a
        # <source> that is present but never selected looks identical in the HTML and
        # serves the wrong file to every phone. Lazy slides are nudged to load in place;
        # clicking the slider here would be blocked by the consent banner, which by
        # design sits above everything until it is answered.
        FIND = ("() => [...document.querySelectorAll('.hero-img-el')]"
                "        .findIndex(i => i.parentElement.querySelector('source'))")
        WANT = ("() => { const i = document.querySelectorAll('.hero-img-el')[IDX];"
                "        const s = i.parentElement.querySelector('source');"
                "        const m = matchMedia('(max-width: 900px)').matches;"
                "        return (m ? s.getAttribute('srcset') : i.getAttribute('src'))"
                "                 .split('/').pop(); }")
        idx = page.evaluate(FIND)
        check(f"[{label}] a hero slide carries a mobile crop", idx >= 0)
        if idx >= 0:
            page.evaluate("() => { document.querySelectorAll('.hero-img-el')[%d].loading = 'eager'; }" % idx)
            page.wait_for_function(
                "() => { const i = document.querySelectorAll('.hero-img-el')[%d];"
                "        return i && i.complete && i.currentSrc; }" % idx, timeout=8000)
            got = page.evaluate(
                "() => document.querySelectorAll('.hero-img-el')[%d].currentSrc.split('/').pop()" % idx)
            check(f"[{label}] hero serves the right crop for the viewport",
                  got, page.evaluate(WANT.replace("IDX", str(idx))))

        inp = page.locator("[data-ps-input]")
        panel = page.locator("[data-ps-panel]")

        inp.fill("v")                      # below the 2-char floor
        page.wait_for_timeout(450)
        check(f"[{label}] 1 char does not open panel", panel.is_visible(), False)

        inp.fill("vit")
        page.wait_for_timeout(600)
        check(f"[{label}] panel opens on 3 chars", panel.is_visible())
        n = page.locator(".ps-item").count()
        check(f"[{label}] suggestions rendered ({n})", n > 0)
        check(f"[{label}] aria-expanded true", inp.get_attribute("aria-expanded") == "true")
        check(f"[{label}] 'see all' link present", page.locator(".ps-all").count() == 1)

        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(120)
        focused = page.evaluate("document.activeElement.className")
        check(f"[{label}] ArrowDown moves into list", "ps-item" in focused or "ps-all" in focused)

        page.keyboard.press("Escape")
        page.wait_for_timeout(150)
        check(f"[{label}] Escape closes panel", panel.is_visible(), False)

        inp.fill("zzz")
        page.wait_for_timeout(600)
        check(f"[{label}] no-match shows empty state",
              page.locator(".ps-empty").count() == 1)

        inp.fill("pain")
        page.wait_for_timeout(600)
        flag = page.locator(".ps-flag").count()
        check(f"[{label}] restricted suggestion flagged, not priced", flag >= 1)
        check(f"[{label}] no add button anywhere in panel",
              panel.locator("[data-add-id]").count() == 0)

        # (6,6) is outside the panel on both viewports; on mobile the panel is
        # full-width below the input, so a mid-screen click can land inside it.
        page.mouse.click(6, 6)
        page.wait_for_timeout(200)
        check(f"[{label}] click-away closes panel", panel.is_visible(), False)

        # ---- B. Restricted product on the collection grid ----
        page.goto(BASE + "/collections/medicines-health", wait_until="networkidle")
        card = page.locator(".pcard").filter(has_text=RESTRICTED).first
        check(f"[{label}] restricted card has NO quick-add",
              card.locator("[data-add-id]").count() == 0)
        check(f"[{label}] restricted card links to the PDP instead",
              card.get_by_text("View Product").count() >= 1)
        normal = page.locator(".pcard").filter(has_text="Cetrine").first
        check(f"[{label}] unrestricted card still quick-adds",
              normal.locator("[data-add-id]").count() >= 1)

        # ---- C/D. Drawer + cross-sell ----
        # The grid's add button is a hover affordance (opacity:0 until hover) and
        # a separate full-width button on mobile — dispatch the event rather than
        # fighting visibility, since what is under test is the handler, not CSS.
        normal.locator("[data-add-id]").first.dispatch_event("click")
        page.wait_for_timeout(1200)
        check(f"[{label}] drawer opens on add",
              page.locator("[data-cd-drawer]").is_visible())
        # Focus must land inside the drawer. It silently did not until the
        # visibility transition was changed to a delay.
        check(f"[{label}] focus moves into the drawer",
              page.evaluate("!!document.querySelector('[data-cd-drawer]').contains(document.activeElement)"))
        rail = page.locator("[data-cd-drawer] .crec")
        check(f"[{label}] cross-sell rail rendered in drawer", rail.count() == 1)
        titles = page.locator("[data-cd-drawer] .crec-title").all_text_contents()
        check(f"[{label}] rail excludes restricted product",
              all(RESTRICTED not in t for t in titles))
        check(f"[{label}] rail has cards ({len(titles)})", len(titles) > 0)
        ship = page.locator("[data-cd-ship-msg]").inner_text()
        check(f"[{label}] drawer free-delivery msg: {ship!r}", "delivery" in ship)

        # ---- D2. Buy-box assurance (3.3 / 3.4) ----
        page.goto(BASE + "/products/x", wait_until="networkidle")
        body = page.locator("body").inner_text()
        check(f"[{label}] PSI registration shown beside the buy box",
              page.locator("[data-buy-assurance] a[href='/pages/internet-supply-pharmacy']").count() >= 1)
        check(f"[{label}] pharmacist route shown beside the buy box",
              "Ask a pharmacist" in body)
        # Both of these are gated on data that does not exist yet. Rendering
        # either one today would be a claim the store cannot honour.
        check(f"[{label}] no dispatch cutoff until one is configured",
              "same-day dispatch" in body, False)
        # Scoped to the assurance block: the footer links to the same page
        # legitimately, as an information link rather than an offer.
        check(f"[{label}] no Click & Collect until Shopify pickup is enabled",
              page.locator("[data-buy-assurance] a[href='/pages/click-and-collect']").count(), 0)

        # ---- E. Threshold consistency ----
        page.goto(BASE + "/cart", wait_until="networkidle")
        page.wait_for_timeout(800)
        body = page.locator("body").inner_text()
        amounts = set()
        import re
        for m in re.finditer(r"(?:over|away from free delivery|OVER)\s*", body):
            pass
        for m in re.finditer(r"€(\d+)(?:\.00)?\b", body):
            amounts.add(m.group(0))
        check(f"[{label}] cart page mentions €65 threshold", "€65" in body or "€65.00" in body)
        check(f"[{label}] cart cross-sell rail present",
              page.locator(".crec").count() >= 1)
        cart_titles = page.locator(".crec-title").all_text_contents()
        check(f"[{label}] cart rail excludes restricted",
              all(RESTRICTED not in t for t in cart_titles))
        page.close()
    browser.close()

for ok, name, got in results:
    print(("  ok  " if ok else "  FAIL") + f"  {name}" + ("" if ok else f"   (got {got!r})"))
print()
print("js errors:", errors if errors else "none")
failed = [r for r in results if not r[0]]
print(f"{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed or errors else 0)
