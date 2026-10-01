# Building the posted-voucher alert: click by click

> ## NOT NEEDED — vouchers are online only (client decision, 1 Oct 2026)
>
> **Do not build this Flow.** The client decided on 1 Oct 2026 that vouchers are
> online only, and the "Printed and posted" method was removed from the voucher
> page the same day — the button, the `Postal address` field and the
> `Delivery: Printed and posted` value all went with it. Nothing in the theme can
> produce an order this Flow would match, so building it would create a workflow
> that never runs and a `voucher-post` tag nobody ever sees.
>
> **It was never built.** No workflow by this name exists in the store; this file
> was written ahead of it and the decision landed first. So there is nothing to
> turn off, delete or clean up — just do not build it.
>
> The file is kept rather than deleted because it is the record of a decision that
> was reversed, and because the click-by-click steps are the work if printed
> vouchers ever come back. **If they do:** restore the method on the voucher page
> first (the hidden `Delivery` input, the button and the address field), then build
> this, then put back the §3 and §4 rows removed on 1 Oct.
>
> Everything below describes a store that no longer exists. Read it as history.

---

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
| Voucher, **By email** | No run, no tag |
| Voucher, **Send it to me** | No run, no tag |

The two rows that exercised the posted path were removed on 1 Oct 2026 with the
method itself; there is no longer any way to place such an order. What remains is
only worth running if someone builds the Flow anyway, to confirm it stays quiet.

One finding from the 30 Sep test (order #1012) outlives the posted method and is
worth keeping: the gift card line was auto-fulfilled two seconds after payment while
a medicine line on the same order stayed held. **"Automatically fulfill only the gift
cards" works per line item, not per order**, so Flow 1's hold on a medicine does not
stop a voucher being issued. The customer gets the code immediately and the pharmacist
still reviews the medicine. Re-check this if the fulfilment setting is ever changed.

Cancel every test order afterwards, and **deactivate the test gift cards**
(Products → Gift cards): cancelling an order does not void a gift card it issued,
so a cancelled test order can leave a live code with real balance on it.

---

## 4. Testing the emailed voucher itself — two orders, click by click

§3 tests the Flow. This tests the thing the Flow is not involved in: Shopify
issuing a voucher **to someone other than the buyer**, now and on a date. Nothing
in the preview can reach it — `gift-voucher.py` proves the right properties are
posted, and there the harness stops. Shopify's side of the bargain needs a store.

### Before either order

1. **Settings → Checkout → Order processing** must read **"Automatically fulfill
   only the gift cards"**. On "Don't fulfill any of the order's line items
   automatically" no voucher is ever issued and both tests fail for a reason that
   has nothing to do with them. This is §0 of this file and the most common way
   to waste a test order.
2. **Settings → Payments → Shopify Payments → Manage → Test mode** on.
3. A **second inbox you control**, different from the buyer's. The whole point is
   that the voucher goes somewhere the buyer is not; with one address, every
   outcome looks like success.
4. Note the store's timezone (**Settings → General**). Order B turns on it.
5. Check `€10` is sellable: the page should show it, and checkout must ask for
   money. **"Your order is free. No payment is required." means the variant is
   inventory-tracked**, not that the voucher is free — see MAINTENANCE, "the gift
   card product, by handle".

### Order A — €10, By email, Send now

1. `/pages/gift-vouchers` → amount **€10**.
2. Method: **By email** (already selected — the only other option is "Send it to me").
3. Recipient name: `Test Recipient A`.
4. Recipient email: the second inbox.
5. Delivery date: leave **Send now** (the default).
6. Message: `Order A — send now`. Keep it identifiable; it is how you tell the two
   emails apart.
7. **Add voucher to bag**, then read the bag line **before paying**. It must show
   `Delivery: By email`, `Recipient name`, `Recipient email` and `Message`, and no
   `__shopify_*` — those start with an underscore and are hidden on purpose. A typo
   in the address is unrecoverable once Shopify has sent to it; this is the last
   place to catch one.
8. Checkout with the test card `4242 4242 4242 4242`, any future expiry, any CVC.

**What should arrive**

| Where | What |
|---|---|
| Recipient inbox | The **New gift card** notification: the code, a €10 balance, your message, addressed to `Test Recipient A`. Within a minute or two — the gift card line auto-fulfils (two seconds on order #1012) |
| Buyer inbox | The **order confirmation**, plus a **Gift card receipt** — a copy of the card confirming who it went to |
| Recipient inbox | **No sender name anywhere.** There is no "from" in that email and no property that could put one there. If the client expects one, the message is the only place it can live |

**In admin**

- Orders → the order → the gift card line → **Properties**: `Delivery: By email`,
  `Recipient name`, `Recipient email`, `Message`. **`Send on` must be absent.**
- The gift card line reads **Fulfilled**. That is what issued the card; an
  unfulfilled line means §0 above is wrong.
- Products → **Gift cards** → the new card: its **Recipient** is the recipient,
  **not the buyer**. This is the single check that proves the whole mechanism —
  buyer in that field means Shopify did not recognise the properties.

### Order B — €10, By email, Pick a date = tomorrow

Same as A, with two changes: Delivery date → **Pick a date** → tomorrow's date, and
message `Order B — scheduled`.

**Place it late in the evening, Irish time.** That is the only window where the
timezone bug this guards against shows up: a date built with `toISOString()` rolls
to the next day after 23:00 BST, and the voucher arrives a day early. The page uses
local date parts (`iso()`) and sends `__shopify_offset` so Shopify resolves the date
as the customer meant it. Placed at midday, a wrong answer and a right one look the same.

**What should happen**

| Where | What |
|---|---|
| Recipient inbox | **Nothing today.** That is the result |
| Buyer inbox | Order confirmation, plus a **Gift card receipt** stating **when it is scheduled to send** |
| Admin, order | The gift card line carries `Send on: <tomorrow's date>`. Check the date is **tomorrow**, not today and not the day after |
| Admin, gift card | The card exists with its €10 balance and names the recipient. What is deferred is the recipient's email, not the card |

Then **tomorrow**, confirm the New gift card email arrives at the recipient inbox,
with the Order B message.

### Afterwards

1. Cancel both orders (refund, test mode).
2. **Deactivate both gift cards** — Products → Gift cards → each → Deactivate.
   Cancelling an order does **not** void a card it issued.
3. Order B's scheduled send is the loose end. **It is not documented whether
   deactivating a card stops a send already scheduled**, so either let it arrive
   (the inbox is yours) or deactivate today and record here what actually happened.
   Do not assume either way in this file until someone has watched it.
