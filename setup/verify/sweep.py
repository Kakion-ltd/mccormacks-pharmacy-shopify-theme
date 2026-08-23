import sys
from playwright.sync_api import sync_playwright
BASE = "http://localhost:8734"
PAGES = ["/", "/collections/medicines-health", "/collections/skincare", "/products/x",
         "/cart", "/search?q=vitamins", "/pages/shipping", "/pages/contact-us",
         "/pages/store-locator", "/blogs/health-hub", "/pages/services",
         "/pages/prescriptions", "/account/login"]
bad = []
with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True)
    for label, vp in (("1440", {"width":1440,"height":900}), ("390", {"width":390,"height":844})):
        pg = b.new_page(viewport=vp)
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        for path in PAGES:
            errs.clear()
            pg.goto(BASE + path, wait_until="networkidle")
            pg.wait_for_timeout(150)
            ow = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
            if ow > 1:
                bad.append(f"{label} {path}: horizontal overflow {ow}px")
            broken = pg.evaluate(
                "Array.from(document.images).filter(i=>i.complete&&i.naturalWidth===0&&!i.classList.contains('img-fallback')).length")
            if broken:
                bad.append(f"{label} {path}: {broken} broken images")
            # the search input must still exist and be usable after the header rewrap
            if pg.locator("[data-ps-input]").count() != 1:
                bad.append(f"{label} {path}: search input missing")
            for e in errs:
                bad.append(f"{label} {path}: JS {e}")
        pg.close()
    b.close()
print("\n".join(bad) if bad else "26 page-loads clean: no overflow, no broken images, no JS errors, search input present on every page")
sys.exit(1 if bad else 0)
