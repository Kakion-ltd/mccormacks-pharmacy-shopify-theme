"""The gift voucher form posts exactly the line item properties its method needs.

Shopify issues the voucher from those property names, so this is a money path with
no forgiving failure: a dropped `Recipient email` sends the voucher to the buyer
instead of the recipient, and a `Send on` more than 90 days out is refused by the
cart. Both are invisible in the markup — they are decided by which inputs JS leaves
enabled — so they need a browser.

  1. The amounts come from the product's variants, each button carrying its own
     variant id, with the preselected one in the hidden `id` field.
  2. By email posts the recipient fields and Shopify's `if_present` flag.
  3. Send it to me posts no recipient fields, which is what makes Shopify issue to
     the buyer.
  4. There are exactly two methods. "Printed and posted" was removed on 1 Oct 2026
     (client decision, vouchers are online only), so nothing on the page collects a
     postal address, offers to post anything, or says the word. The page also makes
     no claim about vouchers sold in the shops, in either direction.
  5. The date is two radios and a native input: `Send now` leaves it disabled so
     nothing is posted, `Pick a date` enables it between today and Shopify's 90-day
     ceiling. Switching method must not leave a `Send on` on a printed voucher.
  6. The gift card's OWN product page sells nothing — its buy box is a link to this
     page. A bare product form there would post a voucher with no recipient and
     Shopify would quietly issue it to the buyer.
  7. Nothing overlays another field, and every tab stop in the form is real. The
     calendar this replaced covered the Message field, could not be closed with
     Escape or a click outside, put its Done button below the fold at 375px, and
     left 29 focusable dead day buttons in a month view.
"""
import os
import sys
from datetime import date, timedelta
from playwright.sync_api import sync_playwright

BASE = f"http://localhost:{os.environ.get('PORT', '8734')}"

results = []
def check(name, got, want=True):
    results.append((got == want, name, got))

# What the browser would actually post: FormData drops every disabled input, which is
# the whole mechanism, so read it the same way the browser does rather than the DOM.
POSTED = """() => {
  const f = document.getElementById('gv-form');
  const out = {};
  new FormData(f).forEach((v, k) => { out[k] = v; });
  return out;
}"""

def pick(pg, method):
    pg.click(f"[data-gv-method='{method}']")

TODAY = date.today()
LIMIT = TODAY + timedelta(days=90)

with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1280, "height": 1000})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(BASE + "/pages/gift-vouchers", wait_until="networkidle")

    # 1. Amounts are the product's variants.
    ids = pg.eval_on_selector_all("[data-gv-id]", "els => els.map(e => e.dataset.gvId)")
    check("six denominations, each with its own variant", len(ids), 6)
    check("variant ids are distinct", len(set(ids)), 6)
    amounts = pg.eval_on_selector_all("[data-gv-pick]", "els => els.map(e => e.dataset.gvPick)")
    check("amounts, in order", amounts, ["€10", "€20", "€25", "€50", "€100", "€150"])
    preselected = pg.eval_on_selector_all(".gv-amt.gv-on", "els => els.map(e => e.dataset.gvId)")
    check("exactly one preselected", len(preselected), 1)
    check("hidden id matches the preselected button",
          pg.get_attribute("#gv-variant", "value"), preselected[0])

    # Two blocks decorate two denominations; the other four said nothing and were deleted.
    # A variant with no block renders a blank tag, which is why deleting them changed
    # no pixel — assert that, so nobody "restores" four inert blocks to fix a non-problem.
    tags = pg.eval_on_selector_all(
        "[data-gv-pick] span:nth-child(2)", "els => els.map(e => e.textContent.trim())")
    check("only the two tagged amounts carry a tag",
          [t for t in tags if t], ["Popular", "Most gifted"])

    # The summary must show the preselected amount from Liquid, not a hardcoded €50, or
    # changing which amount is preselected makes it lie whenever JS has not run.
    check("summary shows the preselected amount before any JS could change it",
          pg.eval_on_selector_all(".gv-summary [data-gv-amount]",
                                  "els => els.map(e => e.textContent.trim())"), ["€50", "€50"])

    # Picking an amount moves the hidden id with it, or the bag charges for another one.
    pg.click("[data-gv-pick='€150']")
    check("picking €150 moves the hidden id",
          pg.get_attribute("#gv-variant", "value"), ids[5])
    pg.click("[data-gv-pick='€50']")

    # 2. By email: the recipient set, plus Shopify's flag.
    pick(pg, "By email")
    pg.fill("[name='properties[Recipient name]']", "Aoife Byrne")
    pg.fill("[name='properties[Recipient email]']", "aoife@example.com")
    pg.fill("[name='properties[Message]']", "Happy birthday — Dad")
    posted = pg.evaluate(POSTED)
    check("by email: recipient email posted", posted.get("properties[Recipient email]"), "aoife@example.com")
    check("by email: recipient name posted", posted.get("properties[Recipient name]"), "Aoife Byrne")
    check("by email: Shopify's send flag posted",
          posted.get("properties[__shopify_send_gift_card_to_recipient]"), "if_present")
    check("by email: timezone offset posted", "properties[__shopify_offset]" in posted)
    check("by email: Delivery names the method", posted.get("properties[Delivery]"), "By email")
    check("by email: no postal address", "properties[Postal address]" not in posted)
    check("by email: email field is required",
          pg.get_attribute("[name='properties[Recipient email]']", "required") is not None)

    # There is no From field. It reached the bag and the order but never the recipient:
    # the gift card notification renders in gift_card scope, with no order and no line
    # item, so a line item property cannot appear in it at all.
    check("no From field, which could never reach the recipient",
          pg.query_selector("[name='properties[From]']") is None)
    check("the Message hint says to sign it instead",
          "know who it’s from" in pg.inner_text("[data-gv-who]"))

    # 5. The date: two radios and a native input. No calendar.
    check("the custom calendar is gone", pg.query_selector("#gv-cal") is None)
    check("the Today / Tomorrow / In a week chips are gone",
          len(pg.query_selector_all(".gv-quick")), 0)
    check("Send on is a native date input",
          pg.get_attribute("[name='properties[Send on]']", "type"), "date")
    check("the group announces as Delivery date",
          pg.inner_text(".gv-date legend").strip(), "Delivery date")

    check("Send now is the default", pg.is_checked("#gv-when-now"))
    check("send now: the date input is disabled", pg.is_disabled("#gv-send-on"))
    check("send now: no Send on posted", "properties[Send on]" not in pg.evaluate(POSTED))
    check("send now: the date field is not on screen", pg.is_hidden('[data-gv-when="pick"]'))

    pg.check("#gv-when-pick")
    check("pick a date: the field appears", pg.is_visible('[data-gv-when="pick"]'))
    check("pick a date: the input is enabled", pg.is_disabled("#gv-send-on"), False)
    check("min is today, in local date parts", pg.get_attribute("#gv-send-on", "min"), TODAY.isoformat())
    check("max is Shopify's 90-day ceiling", pg.get_attribute("#gv-send-on", "max"), LIMIT.isoformat())
    check("the date is required once asked for",
          pg.get_attribute("#gv-send-on", "required") is not None)
    # An empty required date has to stop the submit, not quietly behave as "send now".
    check("a blank date fails validation",
          pg.eval_on_selector("#gv-send-on", "e => e.checkValidity()"), False)

    want = (TODAY + timedelta(days=7)).isoformat()
    pg.fill("#gv-send-on", want)
    check("Send on is local YYYY-MM-DD", pg.evaluate(POSTED).get("properties[Send on]"), want)
    check("a valid date passes validation",
          pg.eval_on_selector("#gv-send-on", "e => e.checkValidity()"), True)

    # The browser refuses day 91 and yesterday, rather than leaving the cart to discover
    # them. The cart is still the guard; this is so the shopper finds out before paying.
    for label, d in [("day 91", LIMIT + timedelta(days=1)), ("yesterday", TODAY - timedelta(days=1))]:
        pg.fill("#gv-send-on", d.isoformat())
        check(f"{label} fails validation",
              pg.eval_on_selector("#gv-send-on", "e => e.checkValidity()"), False)
    pg.fill("#gv-send-on", want)

    # Back to Send now: the typed date may stay on screen, but it must not be posted.
    pg.check("#gv-when-now")
    check("back to Send now: the input is disabled again", pg.is_disabled("#gv-send-on"))
    check("back to Send now: no Send on posted", "properties[Send on]" not in pg.evaluate(POSTED))

    # 3. Send it to me: no recipient fields at all, which is what makes Shopify issue to
    #    the buyer. Delivery is the one property it posts, so the order still says so.
    pick(pg, "Send it to me")
    posted = pg.evaluate(POSTED)
    props = sorted(k for k in posted if k.startswith("properties["))
    check("send to me: Delivery is the only property", props, ["properties[Delivery]"])
    check("send to me: Delivery names the method", posted.get("properties[Delivery]"), "Sent to me")
    check("send to me: still posts a variant and quantity",
          ("id" in posted and posted.get("quantity") == "1"), True)
    check("send to me: recipient block hidden", pg.is_hidden("[data-gv-who]"))
    check("send to me: no send flag, so Shopify issues to the buyer",
          "properties[__shopify_send_gift_card_to_recipient]" not in posted)

    # 4. There are two methods, and no trace of a third.
    #
    #    Removed 1 Oct 2026, client decision: vouchers are online only. A leftover
    #    Postal address input would be a `required` field on a branch nothing can
    #    reach — the form would refuse to submit with nothing on screen explaining
    #    why — and leftover copy would promise a service that no longer exists.
    pick(pg, "By email")
    methods = pg.eval_on_selector_all("[data-gv-method]", "els => els.map(e => e.dataset.gvMethod)")
    check("exactly two methods, By email first", methods, ["By email", "Send it to me"])
    check("no postal address field anywhere on the page",
          pg.query_selector("[name='properties[Postal address]']") is None)
    check("no Delivery value offers posting",
          pg.eval_on_selector_all("input[name='properties[Delivery]']",
                                  "els => els.map(e => e.value)"), ["By email", "Sent to me"])
    # Copy, not just controls. The hero, the method intro, two How-it-works cards, the
    # About paragraph and two FAQ answers all described a posted voucher.
    #
    # "in store" and "at the counter" joined the list on 1 Oct 2026: the page may make
    # no claim about vouchers sold in the shops, in either direction. The FAQ's "It
    # can't be used in our shops" is deliberately phrased to say where this voucher
    # works without saying what the counter sells, and does not trip either word.
    #
    # The nav's "In-Store Services" is hyphenated, so it does not match "in store" —
    # if that ever changes, this check fails on the header rather than on this page,
    # and the word list is where to look.
    body = pg.inner_text("body").lower()
    for word in ["printed", "posted", "post it", "in a card", "postal",
                 "in store", "at the counter"]:
        check(f"the page never says {word!r}", word not in body)
    check("no 'Prefer to buy in store?' aside",
          "prefer to buy" not in body)

    # The date belongs to By email alone. Choosing a date and THEN switching method must
    # not leave a Send on behind — applyMethod enables every input its method owns,
    # including this one, so the radios have to get the last word.
    pick(pg, "By email")
    pg.check("#gv-when-pick")
    pg.fill("#gv-send-on", want)
    check("by email: the date is posted before switching",
          pg.evaluate(POSTED).get("properties[Send on]"), want)
    pick(pg, "Send it to me")
    check("send to me: no Send on even with Pick a date still checked",
          "properties[Send on]" not in pg.evaluate(POSTED))
    check("send to me: the date input is disabled", pg.is_disabled("#gv-send-on"))
    pick(pg, "By email")
    check("back on By email, the date is posted again",
          pg.evaluate(POSTED).get("properties[Send on]"), want)

    check("no page errors on the voucher page", errs, [])
    pg.close()

    # 6. The gift card's own product page sells nothing.
    #
    #    This branch was in no preview at all: the fixture was only ever reachable as
    #    `all_products`, never as `product`. It was also rendering as an ordinary
    #    product even once it was — liquidjs looks `product.gift_card?` up as a literal
    #    key, so `gift_card: true` alone left every gift-card branch false. The fixture
    #    carries 'gift_card?' now, like posted_successfully? and attached_to_variant?.
    pg = b.new_page(viewport={"width": 1280, "height": 1000})
    perrs = []
    pg.on("pageerror", lambda e: perrs.append(str(e)))
    pg.goto(BASE + "/products/gift-voucher", wait_until="networkidle")

    check("the buy box is a link to the voucher page",
          pg.get_attribute(".pdp-buybox a", "href"), "/pages/gift-vouchers")
    check("and it says what it does", pg.inner_text(".pdp-buybox a").strip(), "Buy a gift voucher")
    check("no add-to-cart form on the gift card's page",
          len(pg.query_selector_all("form[action*='/cart/add']")), 0)
    check("no PDP submit button", pg.query_selector("[data-pdp-submit]") is None)
    check("no questionnaire gate either", pg.query_selector("[data-open-questionnaire]") is None)
    # The mobile bar is the second add surface, and a [data-add-id] there would post
    # straight to /cart/add.js and skip the page entirely.
    check("the mobile bar links to the page too",
          pg.get_attribute(".mobile-buybar a", "href"), "/pages/gift-vouchers")
    check("no quick add in the mobile bar",
          pg.query_selector(".mobile-buybar [data-add-id]") is None)
    check("no page errors on the gift card product page", perrs, [])
    pg.close()

    # 7. Layout and keyboard, at desktop and at the narrowest phone.
    for w, h, label in [(1440, 900, "1440"), (375, 667, "375")]:
        pg = b.new_page(viewport={"width": w, "height": h})
        verrs = []
        pg.on("pageerror", lambda e: verrs.append(str(e)))
        pg.goto(BASE + "/pages/gift-vouchers", wait_until="networkidle")
        pg.check("#gv-when-pick")

        # Nothing floats over anything. The popup this replaced covered the Message field
        # at every width, and From as well once the fields stacked.
        overlaps = pg.evaluate("""() => {
          const els = [...document.querySelectorAll(
            '#gv-form [data-gv-who] > label, #gv-form .gv-date, #gv-form .gv-when, .gv-summary')]
            .filter(e => e.offsetParent !== null);
          const name = e => (e.textContent || '').trim().split('\\n')[0].slice(0, 30);
          const hits = [];
          for (let i = 0; i < els.length; i++) for (let j = i + 1; j < els.length; j++) {
            // Nesting is not overlap: the fieldset contains its own radios and field.
            if (els[i].contains(els[j]) || els[j].contains(els[i])) continue;
            const a = els[i].getBoundingClientRect(), c = els[j].getBoundingClientRect();
            if (a.right > c.left + 1 && c.right > a.left + 1 &&
                a.bottom > c.top + 1 && c.bottom > a.top + 1) hits.push(name(els[i]) + ' / ' + name(els[j]));
          }
          return hits;
        }""")
        check(f"{label}: no field overlays another", overlaps, [])

        # Every tab stop in the form is a real, visible, enabled control. The old day grid
        # left 29 focusable buttons that did nothing and were announced as buttons.
        dead = pg.evaluate("""() => {
          const f = document.getElementById('gv-form');
          return [...f.querySelectorAll('a[href], button, input:not([type=hidden]), textarea, select')]
            .filter(e => !e.disabled && e.tabIndex >= 0)
            .filter(e => e.offsetParent === null)
            .map(e => e.id || e.name || e.className || e.tagName);
        }""")
        check(f"{label}: no focusable control is off screen or hidden", dead, [])

        # Tab order follows the page. Asserted as DOM order against painted position rather
        # than by pressing Tab: a native date input has its own internal stops (day, month,
        # year), which is correct behaviour and makes a keystroke-by-keystroke sequence
        # brittle. The summary aside is excluded — it is deliberately out of document flow.
        outoforder = pg.evaluate("""() => {
          const f = document.getElementById('gv-form');
          const els = [...f.querySelectorAll('a[href], button, input:not([type=hidden]), textarea, select')]
            .filter(e => !e.disabled && e.offsetParent !== null && e.tabIndex >= 0)
            .filter(e => !e.closest('.gv-side'))
            .map(e => ({ n: e.id || e.name || e.getAttribute('data-gv-pick') || e.getAttribute('data-gv-method'),
                         t: Math.round(e.getBoundingClientRect().top),
                         l: Math.round(e.getBoundingClientRect().left) }));
          const bad = [];
          for (let i = 1; i < els.length; i++) {
            const a = els[i - 1], b = els[i];
            // Later in the DOM must not be higher up the page, nor left of a sibling on
            // the same row.
            if (b.t < a.t - 2 || (Math.abs(b.t - a.t) <= 2 && b.l < a.l - 2)) bad.push(a.n + ' then ' + b.n);
          }
          return bad;
        }""")
        check(f"{label}: tab order follows the page", outoforder, [])

        # The submit is the end of the run, so it has to be reachable from the last field.
        pg.focus("[name='properties[Message]']")
        pg.keyboard.press("Tab")
        check(f"{label}: Tab from the last field reaches Add voucher to bag",
              pg.evaluate("() => document.activeElement.textContent.trim()"), "Add voucher to bag")

        # A real radio group: one tab stop, and arrow keys move inside it. That is the
        # whole reason for using radios rather than three more aria-pressed buttons.
        pg.check("#gv-when-now")
        pg.focus("#gv-when-now")
        pg.keyboard.press("ArrowDown")
        check(f"{label}: arrow keys move within the radio group", pg.is_checked("#gv-when-pick"))
        # A radio group is ONE tab stop: sequential focus lands on the checked radio and
        # the next Tab leaves the group. `tabIndex` reads 0 on both, so this has to be
        # walked rather than read off the property.
        pg.check("#gv-when-now")
        pg.focus("[name='properties[Recipient email]']")
        pg.keyboard.press("Tab")
        check(f"{label}: Tab into the group lands on the chosen radio",
              pg.evaluate("() => document.activeElement.id"), "gv-when-now")
        pg.keyboard.press("Tab")
        check(f"{label}: one more Tab leaves the group, skipping the unchosen radio",
              pg.evaluate("() => document.activeElement.name"), "properties[Message]")

        # Escape has nothing to close, and must not clear what has been chosen.
        pg.check("#gv-when-pick")
        pg.fill("#gv-send-on", want)
        pg.keyboard.press("Escape")
        check(f"{label}: Escape leaves the chosen date alone",
              pg.input_value("#gv-send-on"), want)
        check(f"{label}: Escape leaves Pick a date checked", pg.is_checked("#gv-when-pick"))
        check(f"{label}: no page errors", verrs, [])
        pg.close()

    b.close()

for ok, name, got in results:
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"  (got {got!r})"))
print(f"\n{sum(1 for ok, _, _ in results if ok)}/{len(results)} checks passed")
sys.exit(0 if all(ok for ok, _, _ in results) else 1)
