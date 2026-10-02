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
   **not workable yet.** Refunding the medicine line and releasing the hold would
   be the steps, but Flow 2 still sees the refunded medicine line, finds no
   approval tag and holds the order again (see MAINTENANCE, "Refusing only the
   medicine"). Until Flow 2 is changed, refuse the whole order and tell the
   customer they can reorder the other items. Never add an approval tag to get
   round the guard: the tag is the record of who approved.
6. File the signed sheet by order number. Keep it 2 years.

**Printing for packing.** Staff print packing slips from **Order Printer's
packing slip only**. Shopify's own packing slip (Orders → Print packing slips,
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
