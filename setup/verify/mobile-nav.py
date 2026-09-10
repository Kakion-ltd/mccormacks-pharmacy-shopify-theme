import sys
from playwright.sync_api import sync_playwright
res=[]
def ck(n,g,w=True): res.append((g==w,n,g))
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_page(viewport={"width":390,"height":844})
    errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto("http://localhost:8734/", wait_until="networkidle")

    ck("page does not scroll behind a closed drawer",
       pg.evaluate("getComputedStyle(document.body).overflow"), "visible")
    pg.locator("[data-mnav-open-btn]").click(); pg.wait_for_timeout(350)
    ck("drawer opens", pg.locator(".mnav-drawer").is_visible())
    ck("body scroll locked while open",
       pg.evaluate("getComputedStyle(document.body).overflow"), "hidden")
    ck("focus moved into the drawer",
       pg.evaluate("!!document.querySelector('.mnav-drawer').contains(document.activeElement)"))
    ck("only the root panel is visible",
       pg.locator("[data-mnav-panel]:visible").count(), 1)

    # Drill: department -> group -> leaves
    row = pg.locator('.mnav-row', has_text="Medicines & Health").first
    ck("department name still links to the department",
       row.locator("a.mnav-link").get_attribute("href"), "/collections/medicines-health")
    row.locator("[data-mnav-into]").click(); pg.wait_for_timeout(300)
    ck("department panel opens", pg.locator('[data-mnav-panel="medicines-health"]').is_visible())
    ck("root hidden after drilling", pg.locator('[data-mnav-panel="root"]').is_visible(), False)
    ck("shop-all link present",
       pg.locator('[data-mnav-panel="medicines-health"] .mnav-all').inner_text().strip(),
       "Shop all Medicines & Health")
    ck("18 groups listed",
       pg.locator('[data-mnav-panel="medicines-health"] > .mnav-list > .mnav-row').count(), 18)

    pg.locator('[data-mnav-panel="medicines-health"] .mnav-row', has_text="Pain Relief").first \
      .locator("[data-mnav-into]").click(); pg.wait_for_timeout(300)
    ck("group panel opens", pg.locator('[data-mnav-panel="pain-relief"]').is_visible())
    leaves = pg.locator('[data-mnav-panel="pain-relief"] .mnav-link').all_text_contents()
    ck("leaf reachable that was unreachable before",
       any("Baby & Children Pain Relief" in t for t in leaves))

    # Back, one level at a time
    pg.locator('[data-mnav-panel="pain-relief"] [data-mnav-back]').click(); pg.wait_for_timeout(300)
    ck("back returns to the department", pg.locator('[data-mnav-panel="medicines-health"]').is_visible())
    pg.keyboard.press("Escape"); pg.wait_for_timeout(300)
    ck("Escape steps back to root, not straight out", pg.locator('[data-mnav-panel="root"]').is_visible())
    ck("drawer still open at root", pg.locator(".mnav-drawer").is_visible())
    pg.keyboard.press("Escape"); pg.wait_for_timeout(350)
    ck("Escape at root closes the drawer", pg.locator(".mnav-drawer").is_visible(), False)
    ck("scroll lock released", pg.evaluate("getComputedStyle(document.body).overflow"), "visible")

    # Reopen lands at root, not where we left off
    pg.locator("[data-mnav-open-btn]").click(); pg.wait_for_timeout(300)
    pg.locator('.mnav-row', has_text="Skincare").first.locator("[data-mnav-into]").click()
    pg.wait_for_timeout(250)
    pg.locator("[data-mnav-open-btn]").click(); pg.wait_for_timeout(350)   # the hamburger is the X now
    pg.locator("[data-mnav-open-btn]").click(); pg.wait_for_timeout(300)
    ck("reopening starts at the root again", pg.locator('[data-mnav-panel="root"]').is_visible())

    # Flat department has no third level
    pg.locator('.mnav-row', has_text="Vitamins & Supplements").first.locator("[data-mnav-into]").click()
    pg.wait_for_timeout(300)
    ck("flat department lists its leaves directly",
       pg.locator('[data-mnav-panel="vitamins"] .mnav-link').count(), 18)
    ck("flat department offers no further drilling",
       pg.locator('[data-mnav-panel="vitamins"] [data-mnav-into]').count(), 0)

    # No-children departments are plain links
    pg.locator('[data-mnav-panel="vitamins"] [data-mnav-back]').click(); pg.wait_for_timeout(250)
    sale = pg.locator('.mnav-row', has_text="Sale").first
    ck("Sale has no chevron promising a submenu", sale.locator("[data-mnav-into]").count(), 0)

    # Disclosure, not a modal: the drawer hangs under the header, which stays usable.
    btn = pg.locator("[data-mnav-open-btn]")
    ck("hamburger reads as the close control while open", btn.get_attribute("aria-expanded"), "true")
    ck("hamburger label switched", btn.get_attribute("aria-label"), "Close menu")
    ck("X icon shown, bars hidden", pg.evaluate("[document.querySelector('.mnav-ico-close').getBoundingClientRect().height > 0, document.querySelector('.mnav-ico-open').getBoundingClientRect().height]"), [True, 0])
    ck("page scrolled to the top on open", pg.evaluate("window.scrollY"), 0)
    ck("drawer top meets the header bottom",
       pg.evaluate("Math.round(document.querySelector('.mnav-drawer').getBoundingClientRect().top) >= Math.round(document.querySelector('.hdr-search-row').getBoundingClientRect().bottom)"))
    ck("search input still visible and on top",
       pg.evaluate("(() => { const i = document.querySelector('.hdr-search-form input'); const r = i.getBoundingClientRect(); return r.height > 0 && document.elementFromPoint(r.left + 40, r.top + r.height / 2) === i; })()"))
    ck("main and footer inert while open", pg.evaluate("document.querySelector('main').inert && document.querySelector('footer').inert"))
    btn.click(); pg.wait_for_timeout(350)
    ck("hamburger tap closes the drawer", pg.locator(".mnav-drawer").is_visible(), False)
    ck("main released", pg.evaluate("document.querySelector('main').inert"), False)
    ck("label back to Menu", btn.get_attribute("aria-label"), "Menu")
    # Open from mid-page: the drawer still sits under the header at rest
    pg.evaluate("window.scrollTo(0, 600)"); pg.wait_for_timeout(400)
    btn.click(); pg.wait_for_timeout(400)
    ck("opening mid-page scrolls to the top", pg.evaluate("window.scrollY"), 0)
    ck("drawer top consistent after a mid-page open",
       pg.evaluate("Math.round(document.querySelector('.mnav-drawer').getBoundingClientRect().top)"),
       pg.evaluate("Math.round(document.querySelector('main').getBoundingClientRect().top)"))

    # A real navigation still works
    pg.locator('.mnav-row', has_text="Brands").first.locator("a.mnav-link").click()
    pg.wait_for_load_state("networkidle")
    ck("tapping a name navigates", pg.url.endswith("/pages/brands"))
    ck("no JS errors", errs, [])
    b.close()
for ok,n,g in res: print(("  ok  " if ok else "  FAIL")+f"  {n}"+("" if ok else f"   (got {g!r})"))
bad=[r for r in res if not r[0]]
print(f"\n{len(res)-len(bad)}/{len(res)} mobile nav checks passed")
sys.exit(1 if bad else 0)
