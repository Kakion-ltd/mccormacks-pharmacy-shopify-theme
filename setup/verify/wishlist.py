import sys
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8734"
RESTRICTED = "Nurofen Plus"
res = []
def ck(name, got, want=True): res.append((got == want, name, got))

with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True)
    for label, vp in (("desktop", {"width":1440,"height":900}), ("mobile", {"width":390,"height":844})):
        ctx = b.new_context(viewport=vp)          # fresh storage = nothing saved
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))

        # Empty state first.
        pg.goto(BASE + "/pages/wishlist", wait_until="networkidle"); pg.wait_for_timeout(400)
        ck(f"[{label}] empty state shown when nothing saved",
           pg.locator("[data-wish-empty]").is_visible())
        ck(f"[{label}] grid hidden when nothing saved",
           pg.locator("[data-wish-grid]").is_visible(), False)
        # Desktop shows the count in the header; the mobile header has no wishlist
        # icon by design, so the count lives on the link inside the nav drawer.
        badge = "a.hide-mobile [data-wish-count]" if label == "desktop" else ".mnav-drawer [data-wish-count]"
        if label == "mobile":
            pg.locator("[data-mnav-open-btn]").click(); pg.wait_for_timeout(350)
        ck(f"[{label}] count badge hidden at zero", pg.locator(badge).is_visible(), False)
        if label == "mobile":
            pg.keyboard.press("Escape"); pg.wait_for_timeout(300)

        # Save from a collection card.
        pg.goto(BASE + "/collections/medicines-health", wait_until="networkidle")
        card = pg.locator(".pcard").filter(has_text="Cetrine").first
        heart = card.locator("[data-wish-toggle]").first
        ck(f"[{label}] heart present on a product card", heart.count() == 1)
        ck(f"[{label}] heart starts unpressed", heart.get_attribute("aria-pressed"), "false")
        heart.dispatch_event("click"); pg.wait_for_timeout(250)
        ck(f"[{label}] heart reflects saved state", heart.get_attribute("aria-pressed"), "true")
        if label == "mobile":
            pg.locator("[data-mnav-open-btn]").click(); pg.wait_for_timeout(350)
        ck(f"[{label}] count badge appears once something is saved",
           pg.locator(badge).is_visible())
        ck(f"[{label}] count badge reads 1", pg.locator(badge).inner_text().strip(), "1")
        if label == "mobile":
            pg.keyboard.press("Escape"); pg.wait_for_timeout(300)

        # Save the restricted product too — the gate must survive the round trip.
        rcard = pg.locator(".pcard").filter(has_text=RESTRICTED).first
        rcard.locator("[data-wish-toggle]").first.dispatch_event("click")
        pg.wait_for_timeout(250)

        # Survives navigation.
        pg.goto(BASE + "/pages/wishlist", wait_until="networkidle"); pg.wait_for_timeout(700)
        ck(f"[{label}] grid shown after saving", pg.locator("[data-wish-grid]").is_visible())
        ck(f"[{label}] empty state hidden after saving",
           pg.locator("[data-wish-empty]").is_visible(), False)
        titles = pg.locator(".wish-card-title").all_text_contents()
        ck(f"[{label}] both saved products listed ({len(titles)})", len(titles) == 2)
        ck(f"[{label}] price rendered live from product JSON",
           any("7.99" in t for t in pg.locator(".wish-card-price").all_text_contents()))

        # THE GATE. Cards here are built in JS, so this is the one surface where
        # the Liquid check cannot run.
        rest = pg.locator(".wish-card").filter(has_text=RESTRICTED).first
        ck(f"[{label}] restricted product has NO quick-add on the wishlist",
           rest.locator("[data-add-id]").count(), 0)
        ck(f"[{label}] restricted product links to the PDP instead",
           "View product" in rest.inner_text())
        norm = pg.locator(".wish-card").filter(has_text="Cetrine").first
        ck(f"[{label}] unrestricted product still quick-adds",
           norm.locator("[data-add-id]").count(), 1)

        # Adding from the wishlist opens the drawer, like every other add surface.
        norm.locator("[data-add-id]").click(); pg.wait_for_timeout(900)
        ck(f"[{label}] add from wishlist opens the cart drawer",
           pg.locator("[data-cd-drawer]").is_visible())
        pg.keyboard.press("Escape"); pg.wait_for_timeout(300)

        # Remove.
        pg.locator(".wish-card").filter(has_text=RESTRICTED).first.locator(".wish-remove").click()
        pg.wait_for_timeout(500)
        ck(f"[{label}] removing a card updates the list",
           len(pg.locator(".wish-card-title").all_text_contents()), 1)

        # A deleted product must not leave a dead card.
        pg.evaluate("localStorage.setItem('mcc_wishlist', JSON.stringify({v:1, items:['cetrine-allergy-10mg-30-tablets','a-product-that-was-deleted']}))")
        pg.reload(wait_until="load"); pg.wait_for_timeout(900)
        ck(f"[{label}] a deleted product is dropped, not shown broken",
           len(pg.locator(".wish-card-title").all_text_contents()), 1)
        ck(f"[{label}] the dead handle is pruned from storage",
           pg.evaluate("JSON.parse(localStorage.getItem('mcc_wishlist')).items.length"), 1)

        # Corrupt storage must not take the page down.
        pg.evaluate("localStorage.setItem('mcc_wishlist', 'not json at all')")
        pg.reload(wait_until="load"); pg.wait_for_timeout(700)
        ck(f"[{label}] corrupt storage falls back to empty",
           pg.locator("[data-wish-empty]").is_visible())

        ck(f"[{label}] no JS errors", errs, [])
        ctx.close()
    b.close()

for ok, n, g in res:
    print(("  ok  " if ok else "  FAIL") + f"  {n}" + ("" if ok else f"   (got {g!r})"))
bad = [r for r in res if not r[0]]
print(f"\n{len(res)-len(bad)}/{len(res)} wishlist checks passed")
sys.exit(1 if bad else 0)
