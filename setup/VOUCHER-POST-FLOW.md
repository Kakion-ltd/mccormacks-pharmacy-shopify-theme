# Building the posted-voucher alert: click by click

A voucher bought as **Printed and posted** needs a person to print it, put it in
a card and post it. Nothing about the order says so on its own: the voucher is a
gift card line like any other, and Shopify issues and emails the code whether or
not anyone posts anything. The only signal is the line item property the page
adds, `Delivery: Printed and posted`, and nobody reads line item properties
unprompted.

So one Flow tags the order and emails the shop. Nothing in this repo creates it —
Shopify Flow has no API for building workflows — so it is built by hand, like the
two in `PHARMACIST-HOLD-FLOWS.md`, and this file is the record of what was built.

**Companion to `PHARMACIST-HOLD-FLOWS.md`, not a replacement.** That file's Flow 1
still holds any order containing a medicine, including one that also holds a
voucher.

---

## 0. Check the gift card fulfilment setting first

The Flow below tells staff to post something. The **code** they print comes from
Shopify issuing the gift card, and Shopify issues it when the line item is
fulfilled. If the store never fulfils automatically, there is nothing to print
until someone fulfils it by hand.

1. Admin → **Settings** → **Checkout** → **Order processing**.
2. Under fulfilment, choose **"Automatically fulfill only the gift cards"**.

This is the one option that satisfies both this Flow and `PHARMACIST-HOLD-FLOWS.md`
step 0: gift cards are issued at once, and nothing else is fulfilled without a
person. Set to "Don't fulfill any of the order's line items automatically", every
voucher — emailed, posted or kept — sits unissued and no customer ever gets one.

---

## 1. The Flow: "Voucher: printed and posted"

Admin → **Apps** → **Flow** → **Create workflow**. Rename it at the top to
`Voucher: printed and posted`.

**Trigger**

1. **Select a trigger** → search `Order created` → select it.

**Condition: did anything on this order ask to be posted?**

2. Click **+** under the trigger → **Condition**.
3. **Add criteria** → pick `Order` → `Line items` → `Custom attributes` → `Key`.
   Flow sets the list operator to **At least one of**.
4. Operator **Equal to**, value `Delivery`.
5. In the same "at least one of" group, **add criteria** → `Value`,
   **Equal to**, `Printed and posted`. The group must require **all** of its
   criteria (AND), so the key and the value are matched on the same attribute —
   the same shape as the over-18 attribute check in `PHARMACIST-HOLD-FLOWS.md`.

   **If Flow does not offer `Custom attributes` under `Line items`** — the path
   has moved before — use `Order` → `Line items` → `Product` → `Title`,
   **Equal to**, `McCormack's Pharmacy Gift Voucher` instead, and accept that it
   also catches emailed vouchers. Then add a second condition on the order's line
   item properties inside the action's email body rather than as a filter, and say
   so here. Do not leave the condition matching every voucher without saying so:
   staff will stop trusting the tag within a week.

**Then path**, two actions:

6. **Add order tags**, tags: `voucher-post`
7. **Send internal email**
   - To: `sales@mccormackspharmacy.ie`
   - Subject: `Voucher to post — order {{order.name}}`
   - Body:

     ```
     Order {{order.name}} includes a gift voucher to be printed and posted.

     {% for line in order.lineItems %}{% for attr in line.customAttributes %}{% if attr.key == 'Delivery' and attr.value == 'Printed and posted' %}Voucher: {{ line.title }} ({{ line.variantTitle }})
     {% for a in line.customAttributes %}{{ a.key }}: {{ a.value }}
     {% endfor %}{% endif %}{% endfor %}{% endfor %}
     Buyer: {{order.customer.firstName}} {{order.customer.lastName}} — {{order.email}}

     The voucher code is on the order in admin, under the gift card line, once the
     line item is fulfilled. Print it, put it in a card, post it to the address
     above, then remove the voucher-post tag.
     ```

8. **Turn on workflow** (top right).

**Otherwise** stays empty: an emailed voucher and a send-to-me voucher need
nobody.

---

## 2. What staff do with a tagged order

1. Orders → filter by tag `voucher-post`.
2. Open it. The gift card code is on the gift card line once it is fulfilled.
3. Print the voucher, write the recipient name and the "From" line on the card,
   post it to the `Postal address` property on the line item.
4. **Remove the `voucher-post` tag.** Nothing removes it automatically: Flow has
   no "order tags added" trigger (see `PHARMACIST-HOLD-FLOWS.md`), and there is no
   fulfilment event left to hang it on once the gift card is already fulfilled.
   The tag is the worklist, and an unworked list is only useful if finished work
   leaves it.

---

## 3. Test it

With test mode on, buy one voucher each way and check Flow → the workflow →
**Recent runs**:

| Order | Expect |
|---|---|
| Voucher, **Printed and posted** | Tagged `voucher-post`, email to sales@ naming the address |
| Voucher, **By email** | No run, no tag |
| Voucher, **Send it to me** | No run, no tag |
| Voucher + a medicine, posted | Tagged `voucher-post` **and** held by Flow 1 — but the voucher itself is issued straight away (tested, order #1012) |

That last row was expected to be the awkward one and turned out not to be. On the
30 Sep test (order #1012) the gift card line was auto-fulfilled two seconds after
payment while the medicine line stayed held: "Automatically fulfill only the gift
cards" works per line item, not per order, so Flow's hold on the medicine does not
stop the voucher being issued. The customer gets the code immediately, staff have
something to print, and the pharmacist still reviews the medicine before it ships.
Re-check this if the fulfilment setting is ever changed.

Cancel every test order afterwards, and **deactivate the test gift cards**
(Products → Gift cards): cancelling an order does not void a gift card it issued,
so a cancelled test order can leave a live code with real balance on it.
