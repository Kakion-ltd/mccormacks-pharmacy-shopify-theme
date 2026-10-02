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

    # The pre-payment disclosure used to be asserted here, on the modal. It was removed
    # from the modal on 1 Oct 2026 and the three checks moved to medicine-declaration.py,
    # which asserts it on the bag page where the copy now lives — the last screen before
    # payment. Moved, not dropped: the customer still has to be told before paying that a
    # pharmacist reviews after payment and an unsuitable order is refunded.

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

    # 7. Tag-driven sets (30 Sep 2026). The questions no longer have to come from a
    # metaobject: a tagged medicine gets a built-in set chosen by tag. Three branches,
    # and the one that must NOT gate is as important as the two that must.
    ed = ctx.new_page()
    ed.goto(BASE + "/products/questions-ed", wait_until="networkidle")
    check("[ed] 18 questions: the old site's 14, tidied, plus 4 from our draft",
          ed.locator("[data-pq-q]").count(), 18)
    check("[ed] no product form (the no-JS gate still holds)",
          ed.locator("form[data-ajax-add]").count(), 0)
    check("[ed] no answer blocks the sale",
          ed.evaluate("[...document.querySelectorAll('[data-pq-q]')].every(q => !q.dataset.blocking)"))
    check("[ed] every question is required",
          ed.evaluate("[...document.querySelectorAll('[data-pq-q]')].every(q => q.dataset.required === 'true')"))
    ed.close()

    # The default pair is no longer anyone's default (1 Oct 2026); it is reachable as
    # questionnaire-default and keeps the only yes_no_details question, so it is still
    # exercised here. Its Yes reveals the details box.
    dp = ctx.new_page()
    added["body"] = None
    dp.route("**/cart/add.js", handle_add)
    dp.route("**/cart.js", handle_cart)
    dp.goto(BASE + "/products/questions-default", wait_until="networkidle")
    check("[default] two questions", dp.locator("[data-pq-q]").count(), 2)
    dp.locator("[data-open-questionnaire]").first.click()
    dp.wait_for_timeout(150)
    check("[default] details box hidden before an answer",
          dp.locator("[data-pq-details]").first.is_hidden())
    dp.locator("[data-pq-q][data-kind=yes_no_details] input[value=Yes]").check()
    check("[default] Yes reveals the details box",
          dp.locator("[data-pq-details]").first.is_visible())
    dp.locator("[data-pq-details-input]").fill("warfarin")
    dp.locator("[data-pq-q][data-kind=yes_no_details] input[value=No]").check()
    check("[default] No hides it again and clears what was typed",
          dp.locator("[data-pq-details]").first.is_hidden()
          and dp.locator("[data-pq-details-input]").input_value() == "")
    # Submit with the over-18 tick missing: must not post.
    dp.locator("[data-pq-submit]").click()
    dp.wait_for_timeout(250)
    check("[default] unticked over-18 blocks the add", added["body"] is None)
    dp.locator("[data-pq-q][data-kind=confirm] input[type=checkbox]").check()
    dp.locator("[data-pq-q][data-kind=yes_no_details] input[value=Yes]").check()
    # Yes with an empty box must not get through: a bare "Yes" tells the pharmacist a
    # customer is on something without saying what. (Required since 30 Sep 2026.)
    dp.locator("[data-pq-submit]").click()
    dp.wait_for_timeout(250)
    check("[default] Yes with no detail blocks the add", added["body"] is None)
    check("[default] and says what is missing",
          "which ones" in dp.locator("[data-pq-q][data-kind=yes_no_details] [data-pq-error]").inner_text())
    dp.locator("[data-pq-details-input]").fill("warfarin")
    dp.locator("[data-pq-submit]").click()
    dp.wait_for_timeout(300)
    dprops = (added["body"] or {}).get("properties", {})
    check("[default] both answers reach the line item", len(dprops) >= 2)
    check("[default] the detail is recorded with the Yes",
          any("Yes" in v and "warfarin" in v for v in dprops.values()))
    dp.close()

    # Every set in the snippet (1 Oct 2026). The fixtures are generated from the
    # snippet's own `when` list, so a set added there is checked here unasked.
    import re
    snippet = open(os.path.join(os.path.dirname(__file__), "../../shopify-theme/snippets/pharmacy-question-set.liquid")).read()
    for name in re.findall(r"when '([^']+)'", snippet):
        sp = ctx.new_page()
        sp.goto(BASE + f"/products/questions-{name}", wait_until="networkidle")
        n = sp.locator("[data-pq-q]").count()
        check(f"[{name}] has questions", n > 0)
        check(f"[{name}] the button says ADD TO BAG",
              sp.locator("[data-gated-buybox] [data-gate-label]").inner_text().strip(), "ADD TO BAG")
        check(f"[{name}] no product form", sp.locator("form[data-ajax-add]").count(), 0)
        check(f"[{name}] no answer blocks the sale",
              sp.evaluate("[...document.querySelectorAll('[data-pq-q]')].every(q => !q.dataset.blocking)"))
        check(f"[{name}] every question is required",
              sp.evaluate("[...document.querySelectorAll('[data-pq-q]')].every(q => q.dataset.required === 'true')"))
        sp.close()

    # Painkillers: the one set with an option list. Ages are tick-all-that-apply with no
    # "None of the above", and the ticks reach the line item joined, with the stamps.
    pk = ctx.new_page()
    added["body"] = None
    pk.route("**/cart/add.js", handle_add)
    pk.route("**/cart.js", handle_cart)
    pk.goto(BASE + "/products/questions-painkillers", wait_until="networkidle")
    check("[painkillers] three questions", pk.locator("[data-pq-q]").count(), 3)
    check("[painkillers] who-for offers the five age bands, and nothing else",
          pk.locator("[data-pq-q][data-kind=multi] input").evaluate_all("e => e.map(i => i.value)"),
          ["Under 2", "2–5", "6–11", "12–17", "18+"])
    pk.locator("[data-open-questionnaire]").first.click()
    pk.wait_for_timeout(150)
    pk.locator("[data-pq-q][data-kind=yes_no] input[value=Yes]").check()
    pk.locator("[data-pq-q][data-kind=multi] input[value='2–5']").check()
    pk.locator("[data-pq-q][data-kind=multi] input[value='18+']").check()
    pk.locator("[data-pq-submit]").click()
    pk.wait_for_timeout(250)
    check("[painkillers] the leaflet tick is required", added["body"] is None)
    pk.locator("[data-pq-q][data-kind=confirm] input").check()
    pk.locator("[data-pq-submit]").click()
    pk.wait_for_timeout(300)
    pprops = (added["body"] or {}).get("properties", {})
    check("[painkillers] both age ticks recorded", "2–5; 18+" in pprops.values())
    check("[painkillers] leaflet confirmation recorded", "I confirm" in pprops.values())
    check("[painkillers] pharmacist-review stamp", pprops.get("_pharmacist_review"), "required")
    check("[painkillers] version names the set", pprops.get("_questionnaire_version"), "painkillers-2026-10-01")
    pk.close()

    # A set tag wins over questionnaire-none, so giving a medicine questions is one tag
    # added; and a set tag naming no set fails closed rather than opening the product.
    np_ = ctx.new_page()
    np_.goto(BASE + "/products/questions-none-plus", wait_until="networkidle")
    check("[none + painkillers] the set wins", np_.locator("[data-pq-q]").count(), 3)
    np_.close()
    uk = ctx.new_page()
    uk.goto(BASE + "/products/questions-unknown", wait_until="networkidle")
    check("[unknown set] shows the unavailable notice", uk.locator("[data-gated-unavailable]").count() > 0)
    check("[unknown set] no way to add", uk.evaluate(
        "!document.querySelector('form[action*=\"/cart/add\"], form[data-ajax-add], [data-open-questionnaire], [data-pq-modal]')"))
    uk.close()

    # A medicine with no set tag asks nothing: Fergal's default since 1 Oct 2026.
    nt = ctx.new_page()
    nt.goto(BASE + "/products/nurofen-tablets-12pk", wait_until="networkidle")
    check("[no set tag] no questionnaire", nt.locator("[data-pq-modal]").count(), 0)
    check("[no set tag] ordinary buy box", nt.locator("form[data-ajax-add] [data-pdp-submit]").count() > 0)
    nt.close()

    # questionnaire-none: a medicine that deliberately asks nothing (Curanail). It must
    # get an ordinary buy box — not the gate, and not the fail-closed notice.
    nq = ctx.new_page()
    nq.goto(BASE + "/products/questions-none", wait_until="networkidle")
    check("[none] no questionnaire at all", nq.locator("[data-pq-modal]").count(), 0)
    check("[none] ordinary buy box", nq.locator("form[data-ajax-add] [data-pdp-submit]").count() > 0)
    check("[none] not the fail-closed notice", nq.locator("[data-gated-unavailable]").count(), 0)
    nq.close()

    # 8. The modal's own usability, added 1 Oct 2026. These are not the gate — the gate
    # is checks 1-7 — but they are the difference between a gate someone can get
    # through and one they abandon, which on a medicine is the same lost sale either
    # way. Run on the 18-question set, where every one of them actually bites.
    ux = ctx.new_page()
    ux.goto(BASE + "/products/questions-ed", wait_until="networkidle")
    opener = ux.locator("[data-gated-buybox] [data-open-questionnaire]")
    # Seen: ADD TO BAG. Heard: the hidden words too, plus aria-haspopup, so the button
    # says it opens something even where a screen reader drops the pop-up hint.
    check("the button shows ADD TO BAG",
          opener.locator("[data-gate-label]").inner_text().strip(), "ADD TO BAG")
    check("the button's spoken name says it opens the questions, and it is a dialog opener",
          [opener.text_content().strip(), opener.get_attribute("aria-haspopup")],
          ["ADD TO BAG, opens health questions", "dialog"])
    check("the hidden words take no space", opener.locator("[data-gate-hint]").bounding_box()["width"] <= 1)
    bar = ux.locator(".mobile-buybar [data-open-questionnaire]")
    check("the mobile bar says and speaks the same",
          [bar.locator("[data-buybar-label]").text_content().strip(), bar.text_content().strip()],
          ["ADD TO BAG", "ADD TO BAG, opens health questions"])
    opener.scroll_into_view_if_needed()
    opener.click()
    ux.wait_for_timeout(250)

    # Header counter and the tick are the same fact, read from the answers.
    check("counter starts at none answered",
          ux.locator("[data-pq-progress]").inner_text().strip(), "0 of 18 answered")
    ux.evaluate("""() => {
      [...document.querySelectorAll('[data-pq-q]')].slice(0, 2).forEach(q => {
        const y = [...q.querySelectorAll('input')].find(i => i.value === 'Yes');
        y.checked = true; y.dispatchEvent(new Event('change', { bubbles: true }));
      });
    }""")
    check("counter follows the answers",
          ux.locator("[data-pq-progress]").inner_text().strip(), "2 of 18 answered")
    check("answered questions wear a tick", ux.locator(".pq-q.pq-answered").count(), 2)

    # Head and foot do not scroll away, so the count and the submit stay reachable
    # eighteen questions down.
    ux.evaluate("document.querySelector('[data-pq-body]').scrollTop = 4000")
    ux.wait_for_timeout(150)
    check("header stays put while the questions scroll", ux.locator(".pq-head").is_visible())
    check("submit stays put while the questions scroll", ux.locator("[data-pq-submit]").is_visible())

    # Submitting with gaps: the first unanswered question is scrolled to AND focused,
    # and the message it shows is the one its inputs point at with aria-describedby.
    ux.locator("[data-pq-submit]").click()
    ux.wait_for_timeout(400)
    check("focus lands on the first unanswered question", ux.evaluate("""() => {
      const q = document.activeElement.closest('[data-pq-q]');
      return q ? [...document.querySelectorAll('[data-pq-q]')].indexOf(q) : -1; }"""), 2)
    check("it says what is wrong",
          ux.locator("[data-pq-error]:visible").first.inner_text().strip(),
          "Please answer this question.")
    check("the message is wired to the inputs with aria-describedby", ux.evaluate("""() => {
      const i = document.querySelector('[data-pq-q] input');
      return (i.getAttribute('aria-describedby') || '').split(' ')
        .some(id => document.getElementById(id)); }"""))

    # Focus trap. The first focusable in the card is the close X and the last is the
    # submit button, so a wrap in either direction proves nothing escapes to the page.
    ux.evaluate("document.querySelector('[data-pq-submit]').focus()")
    ux.keyboard.press("Tab")
    check("Tab past the submit wraps to the close button",
          ux.evaluate("document.activeElement.classList.contains('pq-x')"))
    ux.keyboard.press("Shift+Tab")
    check("Shift+Tab off the close button wraps to the submit",
          ux.evaluate("document.activeElement.hasAttribute('data-pq-submit')"))

    # Every option is a 44px target; Yes/No is 52.
    check("no option row is under a 44px tap target", ux.evaluate("""() => Math.min(
      ...[...document.querySelectorAll('.pq-opt')].map(e => e.getBoundingClientRect().height)) >= 44"""))

    # Escape closes it and hands focus back to the button that opened it.
    ux.keyboard.press("Escape")
    ux.wait_for_timeout(200)
    check("Escape closes the modal", ux.locator("[data-pq-modal]").is_hidden())
    check("focus returns to the button that opened it",
          ux.evaluate("!!document.activeElement.closest('[data-open-questionnaire]')"))

    # Section headings are prepared and dormant. This asserts the dormancy: the day a
    # set starts emitting group:: lines, this check fails and whoever did it has to
    # come back here and say so. The counter above is the thing at risk — a heading
    # that got counted as a question would put "0 of 22" on an 18-question set.
    check("no set emits a section heading yet", ux.locator(".pq-group").count(), 0)
    ux.close()

    # The gated page is full screen on a phone, a centred panel on the desktop.
    for vw, want_full in ((375, True), (1200, False)):
        mp = b.new_context(viewport={"width": vw, "height": 812}).new_page()
        mp.goto(BASE + "/products/questions-ed", wait_until="networkidle")
        mp.evaluate("document.querySelector('[data-open-questionnaire]').click()")
        mp.wait_for_timeout(250)
        box = mp.locator(".pq-card").bounding_box()
        check(f"[{vw}px] the card {'fills the screen' if want_full else 'is a centred panel'}",
              box["width"] >= vw - 1, want_full)
        mp.close()

    # Scripting actually off (2 Oct 2026): the button now says ADD TO BAG, so the gate is
    # checked as a no-JS visitor meets it — the notice shows, and clicking the button
    # posts nothing anywhere.
    nj_ctx = b.new_context(java_script_enabled=False, viewport={"width": 1200, "height": 900})
    nj = nj_ctx.new_page()
    posts = []
    nj.on("request", lambda r: posts.append(r.url) if r.method == "POST" else None)
    nj.goto(BASE + "/products/questions-ed")
    check("[no JS] notice says why the button does nothing",
          nj.locator("[data-gated-buybox] .pdp-noscript-gate").is_visible())
    check("[no JS] no form anywhere that could add it",
          nj.locator("form[action*='/cart/add']").count(), 0)
    nj.locator("[data-gated-buybox] [data-open-questionnaire]").click()
    nj.wait_for_timeout(300)
    check("[no JS] clicking ADD TO BAG posts nothing", posts, [])
    check("[no JS] and stays on the page", nj.url, BASE + "/products/questions-ed")
    nj_ctx.close()

    b.close()

bad = [r for r in results if not r[0]]
for ok, name, got in results:
    print(("  ok  " if ok else "FAIL  ") + name + ("" if ok else f"  (got {got!r})"))
print(f"\n{len(results) - len(bad)}/{len(results)} passed")
sys.exit(1 if bad else 0)
