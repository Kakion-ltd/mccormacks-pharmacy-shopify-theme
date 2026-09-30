"""The gift voucher form posts exactly the line item properties its method needs.

Shopify issues the voucher from those property names, so this is a money path with
no forgiving failure: a dropped `Recipient email` sends the voucher to the buyer
instead of the recipient, and a `Send on` more than 90 days out is refused by the
cart. Both are invisible in the markup — they are decided by which inputs JS leaves
enabled — so they need a browser.

  1. The amounts come from the product's variants, each button carrying its own
     variant id, with the preselected one in the hidden `id` field.
  2. By email posts the recipient fields and Shopify's `if_present` flag.
  3. Send it to me posts none of them, which is what makes Shopify issue to the buyer.
  4. Printed and posted posts Delivery + a postal address, and no recipient email.
  5. The date picker stops at 90 days, and writes `Send on` as local YYYY-MM-DD.
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

    # Picking an amount moves the hidden id with it, or the bag charges for another one.
    pg.click("[data-gv-pick='€150']")
    check("picking €150 moves the hidden id",
          pg.get_attribute("#gv-variant", "value"), ids[5])
    pg.click("[data-gv-pick='€50']")

    # 2. By email: the recipient set, plus Shopify's flag.
    pick(pg, "By email")
    pg.fill("[name='properties[Recipient name]']", "Aoife Byrne")
    pg.fill("[name='properties[Recipient email]']", "aoife@example.com")
    pg.fill("[name='properties[From]']", "Dad")
    pg.fill("[name='properties[Message]']", "Happy birthday")
    posted = pg.evaluate(POSTED)
    check("by email: recipient email posted", posted.get("properties[Recipient email]"), "aoife@example.com")
    check("by email: recipient name posted", posted.get("properties[Recipient name]"), "Aoife Byrne")
    check("by email: Shopify's send flag posted",
          posted.get("properties[__shopify_send_gift_card_to_recipient]"), "if_present")
    check("by email: timezone offset posted", "properties[__shopify_offset]" in posted)
    check("by email: no Delivery property", "properties[Delivery]" not in posted)
    check("by email: no postal address", "properties[Postal address]" not in posted)
    check("by email: email field is required",
          pg.get_attribute("[name='properties[Recipient email]']", "required") is not None)

    # 5. The date. Today, then the 90-day ceiling.
    pg.click(".gv-quick[data-gv-offset='7']")
    posted = pg.evaluate(POSTED)
    check("Send on is local YYYY-MM-DD",
          posted.get("properties[Send on]"), (date.today() + timedelta(days=7)).isoformat())
    pg.click("#gv-date-field")          # "Send immediately" lives inside the calendar
    pg.click("#gv-clear")
    check("cleared: no Send on posted", pg.evaluate(POSTED).get("properties[Send on]", ""), "")

    # Walk the calendar to its last month and confirm day 91 is not selectable.
    pg.click("#gv-date-field")
    for _ in range(14):
        if pg.get_attribute("#gv-next", "disabled") is not None:
            break
        pg.click("#gv-next")
    check("calendar stops advancing", pg.get_attribute("#gv-next", "disabled") is not None)
    limit = date.today() + timedelta(days=90)
    usable = pg.eval_on_selector_all(
        "#gv-days .gv-day:not(.gv-blank):not(.gv-past)", "els => els.map(e => e.textContent)")
    check("last month offers no day past the 90th",
          all(int(d) <= limit.day for d in usable), True)
    pg.click("#gv-done")

    # 3. Send it to me: a bare gift card line.
    pick(pg, "Send it to me")
    posted = pg.evaluate(POSTED)
    leaked = [k for k in posted if k.startswith("properties[")]
    check("send to me: posts no properties at all", leaked, [])
    check("send to me: still posts a variant and quantity",
          ("id" in posted and posted.get("quantity") == "1"), True)
    check("send to me: recipient block hidden", pg.is_hidden("[data-gv-who]"))
    check("send to me: postal address hidden too",
          pg.is_hidden("[data-gv-only='Printed and posted']"))

    # 4. Printed and posted: staff need the address, and the Flow keys off Delivery.
    pick(pg, "Printed and posted")
    pg.fill("[name='properties[Postal address]']", "1 Main St, Athlone, Co Westmeath, N37 AB12")
    posted = pg.evaluate(POSTED)
    check("printed: Delivery property posted",
          posted.get("properties[Delivery]"), "Printed and posted")
    check("printed: postal address posted",
          posted.get("properties[Postal address]"), "1 Main St, Athlone, Co Westmeath, N37 AB12")
    check("printed: recipient name still posted", posted.get("properties[Recipient name]"), "Aoife Byrne")
    check("printed: no recipient email, so Shopify does not email them",
          "properties[Recipient email]" not in posted)
    check("printed: no send flag", "properties[__shopify_send_gift_card_to_recipient]" not in posted)
    check("printed: no Send on", "properties[Send on]" not in posted)

    # Switching back must not leave the postal address behind on an emailed voucher.
    pick(pg, "By email")
    check("switching back drops the postal address",
          "properties[Postal address]" not in pg.evaluate(POSTED))

    check("no page errors", errs, [])
    b.close()

for ok, name, got in results:
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"  (got {got!r})"))
sys.exit(0 if all(ok for ok, _, _ in results) else 1)
