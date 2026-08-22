# Tracking setup — McCormack's Pharmacy

Shopify **Basic**. Additional Scripts is being removed on **26 August 2026**, so
nothing goes there and nothing in this repo writes to it. Everything below is
either a first-party channel app or a custom pixel under
**Settings → Customer events**.

Both are admin tasks. The theme carries no analytics code, which is deliberate:
a script in `theme.liquid` cannot see checkout or the thank-you page, so it can
never report `begin_checkout` or `purchase`.

---

## 1. GA4, Merchant Center and Google Ads — Google & YouTube channel

Install the **Google & YouTube** channel app (first-party, free).

1. **Sales channels → Google & YouTube → Add channel**.
2. Connect the Google account that owns the GA4 property and Merchant Center.
3. Under **Settings → Google Analytics**, pick the GA4 property (or let it
   create one). This installs Shopify's own Google pixel under Customer events.
4. Under **Merchant Center**, verify and claim the domain, set the product feed
   target country to **Ireland** and language **English**.
5. Link **Google Ads** if paid search is planned — conversions then import from
   GA4 rather than needing a separate tag.

The channel emits `view_item`, `add_to_cart`, `begin_checkout` and `purchase`
itself. **Do not add a second GA4 tag** — a manual gtag in a custom pixel
alongside this one double-counts every event and inflates revenue.

### Why `add_to_cart` fires from this theme

The theme adds to cart through the Cart AJAX API (`/cart/add.js`), from the
product form, the collection quick-add and the cross-sell rail. Shopify raises
the `product_added_to_cart` customer event from that API call server-side, so
every add path is covered without the theme emitting anything. Adds that are
suppressed for restricted products correctly produce no event, because no add
happens.

---

## 2. Meta — custom pixel

**Settings → Customer events → Add custom pixel**, named `Meta Pixel`.
Paste [`meta-custom-pixel.js`](./meta-custom-pixel.js) and replace `PIXEL_ID`.

Leave **Permission** set to *Analytics* so the pixel honours the consent banner
(Phase 5). Set **Data sale** according to the privacy stance agreed with the
client.

Do not also install the Facebook & Instagram channel's pixel — same
double-counting problem as GA4.

---

## 3. Verifying the four events end to end

This **needs a dev store**; it cannot be checked in the local preview, which has
no checkout. Run through it once on the dev store and once on production before
launch.

| Event | Where to trigger | GA4 check | Meta check |
|---|---|---|---|
| `view_item` / `ViewContent` | Open any product page | Realtime → event count | Events Manager → Test events |
| `add_to_cart` / `AddToCart` | Add from PDP, then from a collection tile, then from the cart cross-sell rail | 3 events, correct `value` each time | same |
| `begin_checkout` / `InitiateCheckout` | Click Checkout in the bag drawer, then again from the cart page | 2 events, `value` = subtotal | same |
| `purchase` / `Purchase` | Complete an order with a Bogus Gateway card (`1`, any future expiry, any CVC) | Revenue matches the order total exactly once | `eventID` present |

Tools: **GA4 → Admin → DebugView** (install the *Google Analytics Debugger*
extension first), and **Meta Events Manager → Test events**.

Three things worth checking specifically, because they are the usual failures:

1. **`purchase` fires once, not twice.** Refresh the thank-you page and confirm
   the count does not increase.
2. **Revenue excludes tax and shipping consistently** with however the client
   reports it — decide which, then keep it.
3. **Currency is EUR** on every event, not the visitor's local currency.

---

## 4. Consent (Phase 5, not yet built)

Shopify's native cookie banner plus the Customer Privacy API. Until it is in
place, both pixels above run unconditionally, which is not acceptable for an
Irish store at launch. The banner must be live **before** launch traffic
arrives — see the plan's Phase 5.
