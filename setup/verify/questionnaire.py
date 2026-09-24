"""Pharmacist-questionnaire gate: the invariants that make it a real gate.

Runs against the gated fixture product (Viagra Connect). Checks, in order:
  1. No-JS gate — the gated buy box has no /cart/add form at all, so a scripting-off
     visitor cannot add the medicine. The add button is type=button.
  2. The button opens the questionnaire modal.
  3. Submitting with a required question unanswered does not post to the cart.
  4. A blocking answer (a contraindication) disables submit and shows the notice.
  5. A valid, non-blocking submission posts to /cart/add.js with the answers as
     line-item properties, including the hidden _pharmacist_review / version stamps.

The cart endpoints are stubbed so the check exercises the theme's own payload
building without a live store.
"""
import json
import os
import sys
from playwright.sync_api import sync_playwright

BASE = f"http://localhost:{os.environ.get('PORT', '8734')}"
URL = BASE + "/products/viagra-connect-sildenafil-50mg-tablets-8-pack"

results = []
def check(name, got, want=True):
    results.append((got == want, name, got))

with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width": 1200, "height": 900})
    pg = ctx.new_page()

    # Capture what the page tries to POST to the cart, and answer it like Shopify would.
    added = {"body": None}
    def handle_add(route):
        added["body"] = json.loads(route.request.post_data or "{}")
        route.fulfill(status=200, content_type="application/json",
                      body=json.dumps({"items": [{"id": added["body"].get("id"), "quantity": added["body"].get("quantity")}]}))
    def handle_cart(route):
        route.fulfill(status=200, content_type="application/json",
                      body=json.dumps({"item_count": 1, "items": []}))
    pg.route("**/cart/add.js", handle_add)
    pg.route("**/cart.js", handle_cart)

    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="networkidle")

    # 1. No-JS gate: no cart-add form anywhere on the gated page.
    check("no /cart/add form on the gated page",
          pg.evaluate("!document.querySelector('form[action*=\"/cart/add\"], form[data-ajax-add]')"))
    check("add button is type=button (inert without JS)",
          pg.evaluate("document.querySelector('[data-gated-buybox] [data-open-questionnaire]')?.type") == "button")

    # 2. Opening the modal.
    check("modal starts hidden", pg.locator("[data-pq-modal]").is_hidden())
    pg.locator("[data-gated-buybox] [data-open-questionnaire]").click()
    check("modal opens on click", pg.locator("[data-pq-modal]").is_visible())

    # 3. Submitting with nothing answered must not post.
    pg.locator("[data-pq-submit]").click()
    pg.wait_for_timeout(150)
    check("empty submit does not post to cart", added["body"] is None)
    check("an error is shown on empty submit", pg.locator("[data-pq-error]:visible").count() > 0)

    # Helper: tick every required question with a safe answer, radios -> Yes/None etc.
    def answer_safely():
        pg.evaluate("""() => {
          document.querySelectorAll('[data-pq-q]').forEach(q => {
            const kind = q.dataset.kind;
            if (kind === 'yes_no') { const y=[...q.querySelectorAll('input')].find(i=>i.value==='Yes'); if(y){y.checked=true;} }
            else if (kind === 'multi') { const n=q.querySelector('[data-pq-none]'); if(n){n.checked=true; n.dispatchEvent(new Event('change',{bubbles:true}));} }
            else if (kind === 'confirm' || kind === 'choice') { const c=q.querySelector('input'); if(c){c.checked=true;} }
          });
        }""")

    # 4. A blocking answer (tick a real contraindication) disables submit.
    answer_safely()
    pg.evaluate("""() => {
      const q = [...document.querySelectorAll('[data-pq-q]')].find(q => (q.dataset.blocking||'').length > 5);
      const opt = q.querySelector('input[type=checkbox]:not([data-pq-none])');
      const none = q.querySelector('[data-pq-none]'); if(none) none.checked=false;
      opt.checked = true; opt.dispatchEvent(new Event('change',{bubbles:true}));
    }""")
    check("blocking notice shows for a contraindication", pg.locator("[data-pq-blocked]").is_visible())
    check("submit is disabled while blocked", pg.locator("[data-pq-submit]").is_disabled())
    pg.locator("[data-pq-submit]").click(force=True)
    pg.wait_for_timeout(150)
    check("blocked submit does not post to cart", added["body"] is None)

    # 5. Clear the block, answer safely, submit — must post answers as properties.
    answer_safely()
    pg.locator("[data-pq-submit]").click()
    pg.wait_for_timeout(300)
    body = added["body"] or {}
    props = body.get("properties", {})
    check("valid submit posts to cart", body != {})
    check("posts a variant id", isinstance(body.get("id"), int) and body.get("id") > 0)
    check("answers are attached as line-item properties", len(props) >= 6)
    check("every question label is recorded",
          sum(1 for k in props if k[0].isdigit()) >= 6)
    check("pharmacist-review stamp present", props.get("_pharmacist_review") == "required")
    check("questionnaire version recorded", bool(props.get("_questionnaire_version")))
    check("modal closes after a successful add", pg.locator("[data-pq-modal]").is_hidden())

    check("no page errors", errs == [])

    # 6. Fail closed: a gated product whose questionnaire is deleted or empty must show
    # the "not available" notice and offer NO way to add — not drop back to a buy box.
    for handle in ("gated-deleted", "gated-empty"):
        p2 = ctx.new_page()
        p2.goto(BASE + "/products/" + handle, wait_until="networkidle")
        check(f"[{handle}] shows the unavailable notice",
              p2.locator("[data-gated-unavailable]").count() > 0)
        check(f"[{handle}] renders no gated buy box",
              p2.locator("[data-gated-buybox]").count() == 0)
        # This product's own add paths must be gone. ([data-add-id] on the page is the
        # cross-sell rail — other products — and is left out of the check on purpose.)
        check(f"[{handle}] no product form, opener or modal", p2.evaluate(
            "!document.querySelector('form[action*=\"/cart/add\"], form[data-ajax-add], [data-open-questionnaire], [data-pq-modal]')"))
        check(f"[{handle}] mobile buybar add is disabled",
              p2.evaluate("[...document.querySelectorAll('.mobile-buybar button')].every(b => b.disabled || b.dataset.qtyStep !== undefined)"))
        p2.close()

    b.close()

bad = [r for r in results if not r[0]]
for ok, name, got in results:
    print(("  ok  " if ok else "FAIL  ") + name + ("" if ok else f"  (got {got!r})"))
print(f"\n{len(results) - len(bad)}/{len(results)} passed")
sys.exit(1 if bad else 0)
