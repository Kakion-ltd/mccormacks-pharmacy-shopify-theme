# Building the pharmacist hold: click by click

**Status: built 28 Sep 2026, test plan passed on the live store 30 Sep 2026**
(see MAINTENANCE, "The pharmacist hold follows the tag"). Both Flows and the
Order Printer template were built from this file, with "Notify merchant" ticked
on all three hold actions (the steps below now say so). The over-18 tick box is
live. The template was revised on 2 Oct 2026 (questionnaire answers, one-line
page for orders with no medicine, a third refusal option): paste it again.

Built by hand in Shopify admin. Nothing in the repo creates these. The reasons
behind each choice are in `MAINTENANCE.md`, under "The pharmacist hold follows
the tag". Checked against Shopify's help pages on 28 Sep 2026. Labels in Flow
can drift, so if a button reads slightly differently, follow the meaning, and
fix this file afterwards.

Build in this order: check fulfilment, the Order Printer template, Flow 1, Flow 2, then test.

Two strings must be typed exactly, lower case, no spaces around them:

- product tag `pharmacist-review`
- cart attribute key `Over 18 and will follow the leaflet`

---

## 0. Check the store does not fulfil orders automatically

A hold is useless if the order is marked fulfilled the moment it is paid.

1. Admin → **Settings** → **Checkout**. (Shopify's help page says **Settings →
   General**. Use whichever of the two has the section.)
2. Scroll to **Order processing**.
3. Under fulfilment, **"Automatically fulfill the order's line items" must NOT
   be selected.** Choose **"Automatically fulfill only the gift cards"**.

   Either option protects the hold, but only that one also lets gift vouchers
   work: Shopify issues and emails a gift card when its line item is fulfilled,
   so under "Don't fulfill any of the order's line items automatically" no
   voucher is ever emailed until a person fulfils it by hand. That was the state
   until 30 Sep 2026, when the gift vouchers page started selling a real gift
   card — see `VOUCHER-POST-FLOW.md` step 0 and MAINTENANCE.md, "Gift vouchers:
   the page sells a real gift card, by handle". A medicine is not a gift card, so
   nothing about the hold changes.
4. If you changed it, click **Save**.

While you are in Order processing, leave "Automatically archive the order" as it
is. Archiving does not delete anything.

---

## 1. The Order Printer template (the signed record)

1. Admin → **Apps** → **Order Printer** (install "Shopify Order Printer" from
   the App Store if it is not there; it is free, by Shopify).
2. **Templates** → **Create a template**.
3. **Name:** `Medicine order record (PSI 2.5)`.
4. In **Edit code**, delete anything there and paste the whole of
   `setup/order-printer/medicine-record.liquid`.
5. **Save**.
6. Open any existing order, print it with this template (from the order:
   **More actions** / **Print** → Order Printer → this template) and check it fills
   in. A test order with a medicine is best (see step 4).

---

## 2. Flow 1: "Pharmacist hold: medicine orders"

Admin → **Apps** → **Flow** → **Create workflow**. Rename it at the top to
`Pharmacist hold: medicine orders`.

**Trigger**

1. **Select a trigger** → search `Order created` → select it.

**Condition A: does the order hold a medicine?**

2. Click **+** under the trigger → **Condition**.
3. **Add criteria** → pick `Order` → `Line items` → `Product` → `Tags`.
   Flow sets the list operator to **At least one of**.
4. Operator **Equal to**, value `pharmacist-review`.
5. Click **Done** or close the panel.

**Condition B, on the THEN branch of A: did the customer tick the box?**

6. On A's **Then** path, click **+** → **Condition**.
7. **Add criteria** → `Order` → `Custom attributes` → `Key`. List operator
   **At least one of**, operator **Equal to**, value
   `Over 18 and will follow the leaflet`.
8. In the same "at least one of" group, **add criteria** → `Value`, **Equal to**,
   `Yes`. The group must require **all** of its criteria (AND), so the key and the
   value are matched on the same attribute.

**B's Then path (declaration given)**, add three actions in this order:

9. **Hold fulfillment order**
   - Reason: **Other**
   - Reason notes: `Pharmacist review (PSI 2.5)`
   - Notify merchant: **ticked** (as built; the customer "under review" email
     is still undecided).
10. **Add order tags**, tags: `awaiting-pharmacist`
11. **Update order note**, note (this replaces the note, so it starts with the
    customer's own):

    ```
    {{order.note}}

    HELD for pharmacist review (PSI 2.5): this order contains a medicine. Do not send until a pharmacist approves it.
    ```

**B's Otherwise path (no declaration)**, the same three actions plus a flag
tag. Write the note once, in full; a second "Update order note" in the same
run would overwrite the first.

12. **Hold fulfillment order**, same settings as step 9.
13. **Add order tags**, tags: `awaiting-pharmacist` and `no-declaration`
14. **Update order note**, note:

    ```
    {{order.note}}

    HELD for pharmacist review (PSI 2.5): this order contains a medicine. Do not send until a pharmacist approves it.

    NO DECLARATION: the customer did not tick the over-18 / leaflet box (they reached checkout without the bag page). Get the confirmation from the customer before approving, and write how and when on the printed record.
    ```

A's **Otherwise** path stays empty: no medicine, no hold.

15. **Turn on workflow** (top right).

---

## 3. Flow 2: "Pharmacist hold: release guard"

Flow has no "order tags added" trigger, so a tag cannot release an order by
itself. The pharmacist releases the hold in admin; this Flow checks that the
approval tag is there, and puts the hold back if it is not.

**Create workflow**, rename to `Pharmacist hold: release guard`.

**Trigger**

1. **Select a trigger** → `Fulfillment order holds released`.

**Condition A: is this a medicine order?**

2. **+** → **Condition** → `Fulfillment order` → `Order` → `Line items` →
   `Product` → `Tags`, **At least one of**, **Equal to** `pharmacist-review`.

**Condition B, on A's Then path: has a pharmacist approved it?**

3. **+** → **Condition** → `Fulfillment order` → `Order` → `Tags`,
   **At least one of**, **Starts with** `pharmacist-approved-`.

**B's Then path (approved):**

4. **Remove order tags**, tags: `awaiting-pharmacist`

**B's Otherwise path (released without approval):**

5. **Hold fulfillment order**, Reason **Other**, Reason notes
   `Released without a pharmacist-approved tag: held again (PSI 2.5)`,
   Notify merchant ticked.
6. **Add order tags**, tags: `released-without-approval`

7. **Turn on workflow**.

### 3a. Change to Flow 2: let a medicine-only refusal release the rest

**Not built yet (written 2 Oct 2026).** Why: a refunded medicine line is still a
line item, so Condition A above still matches after the pharmacist refunds it,
and Flow 2 holds the order again. The change makes Condition A count only
medicine lines still to be supplied. Nothing else in Flow 2 changes, and Flow 1
is untouched.

1. Admin → **Apps** → **Flow** → open `Pharmacist hold: release guard`.
2. **Turn off workflow** (top right) while you edit, so a release in the
   meantime is not judged by a half-edited condition. Note the time: any order
   released while it is off is not guarded, so check `awaiting-pharmacist`
   orders released in that window afterwards.
3. Click **Condition A**. It reads `Line items` → `Product` → `Tags`, **At least
   one of**, **Equal to** `pharmacist-review`.
4. Inside the same `Line items` group (not a new condition, and not at the top
   level), **Add criteria** → `Line items` → `Current quantity`, operator
   **Greater than**, value `0`.
5. Set that `Line items` group to require **all** of its criteria (AND), so the
   tag and the quantity are judged on the **same** line item. Read it back: it
   must say, in effect, "at least one line item whose product is tagged
   `pharmacist-review` AND whose current quantity is greater than 0". If the two
   criteria sit in separate groups, an order with one refunded medicine and one
   ordinary item would still match, and nothing would change.
6. **Save**, then **Turn on workflow**.

What now happens on release:

| Order on release | Condition A | Result |
|---|---|---|
| Medicine still on the order, approval tag | matches | B: `awaiting-pharmacist` removed (as before) |
| Medicine still on the order, no approval tag | matches | B: held again, `released-without-approval` (as before) |
| Every medicine line refunded, other items left | **no match** | Released; nothing tagged or removed |

So after a medicine-only refusal Flow 2 removes nothing: the pharmacist takes
`awaiting-pharmacist` off by hand (step 4 below).

**Test it before relying on it** (Shopify Payments test mode, as in step 5):

1. Order one medicine and one ordinary item. It is held and tagged.
2. **Refund** the medicine line only, quantity in full, **Restock** ticked.
3. Add `pharmacist-refused-test`, remove `awaiting-pharmacist`, **Release hold**.
4. Expect: stays released, **no** `released-without-approval`; Flow → this
   workflow → **Recent runs** shows Condition A false.
5. Repeat with a medicine order released with no tag and nothing refunded:
   still held again (the guard still works).
6. Cancel both with restock.

If step 4 still re-holds the order, `Current quantity` does not drop on a
refund in Flow: stop, put the guide's refusal back to "whole order", and record
what Recent runs showed.

---

## 4. What the pharmacist does with a held order

1. Orders → filter **Tagged with** `awaiting-pharmacist`.
2. Open the order. Read **Additional details** for "Over 18 and will follow the
   leaflet: Yes". If the order is tagged `no-declaration`, get the confirmation
   from the customer first.
3. Click the customer's name and look at their earlier orders.
4. Print the order with **Medicine order record (PSI 2.5)**. The customer's
   questionnaire answers print under each medicine line. Tick, sign, date, and
   tick one decision.
5. **Approve:** add the tag `pharmacist-approved-<initials>` (e.g.
   `pharmacist-approved-fm`), then **Release hold** on the order. Flow 2 removes
   `awaiting-pharmacist`.
   **Refuse, whole order:** cancel the order with a full refund and restock, and
   add `pharmacist-refused-<initials>`.
   **Refuse, medicine only** (a mixed order whose other items should still go):
   **not workable until step 3a is built and its test passes.** Until then
   Flow 2 still sees the refunded medicine line, finds no approval tag and holds
   the order again: refuse the whole order and tell the customer they can
   reorder the other items. Once 3a is in: **Refund** the medicine line(s) only,
   quantity in full, **Restock** ticked; add `pharmacist-refused-<initials>`;
   remove `awaiting-pharmacist`; **Release hold**. Never add an approval tag to
   get round the guard: the tag is the record of who approved.
6. File the signed sheet by order number. Keep it 2 years.

**Printing for packing.** Staff print packing slips from **Order Printer's
packing slip only** (`setup/order-printer/packing-slip.liquid`, pasted over
Order Printer's Packing slip template). A held medicine order's slip opens with
"AWAITING PHARMACIST APPROVAL — DO NOT PACK"; once approved and released, print
it again and the banner is gone. Shopify's own packing slip (Orders → Print packing slips,
set up in Settings → Shipping and delivery) **must not be used for picking or
packing**: it cannot read product tags or order tags, so it cannot show the
"awaiting pharmacist approval" warning, and a held order's slip looks like any
other. Order Printer's pick list leaves held items out (see MAINTENANCE), so a
held order on its own prints an empty pick list: that is the hold working, not a
fault.

REVIEWER: waiting on the pharmacist. The initials scheme, who may approve, and
whether they want a stamp or a PSI number on the sheet.

---

## 5. Test with the Bogus Gateway (before Shopify Payments)

1. Settings → **Payments** → add a third-party provider → **(for testing)
   Bogus Gateway** → activate.
2. Check out from the **development theme's preview** (the tick box is only on
   that theme until it is published). Card number `1` succeeds, `2` fails; any
   name, any future expiry, any CVV.
3. Place each of these and read the result in Flow → the workflow → **Recent
   runs**:

| Order | Expect |
|---|---|
| Medicine, through the bag, box ticked | On hold, `awaiting-pharmacist`, note without "NO DECLARATION" |
| Medicine via `/cart/<variant id>:1` | On hold, `awaiting-pharmacist` + `no-declaration` |
| Non-medicine only | Not held, no tags |
| Medicine + non-medicine | Whole order on hold |
| Admin draft order with a medicine, marked paid | On hold, `no-declaration` |
| Release a held order **without** the approval tag | Held again, `released-without-approval` |
| Add `pharmacist-approved-xx`, release | Stays released, `awaiting-pharmacist` removed |

4. Print one with the Order Printer template.
5. Cancel every test order with **restock**, then deactivate the Bogus Gateway.

Shop Pay, Apple Pay and Google Pay only exist once Shopify Payments is on; check
they are missing from a medicine's page and bag then.
