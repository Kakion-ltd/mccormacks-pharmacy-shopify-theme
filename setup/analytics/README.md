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

## 4. Consent — set each pixel's Permission, or the banner does nothing

The theme ships a consent banner (`snippets/consent-banner.liquid`) that drives
Shopify's Customer Privacy API. **The banner does not block anything by itself.**
What blocks a pixel is the Permission field on the pixel, which tells Shopify to
withhold it until that consent is granted. A pixel set to "Not required" fires
before the visitor has answered, banner or no banner.

So, in **Settings → Customer events**, for every pixel:

| Pixel | Permission |
|---|---|
| Meta Pixel (the custom pixel above) | **Marketing** |
| Google (installed by the Google & YouTube channel) | **Analytics** — check it, do not assume |
| Anything an app installs later | Whichever category it genuinely is |

Then **turn OFF Shopify's own cookie banner** (Settings → Customer privacy →
Cookie banner). Both it and the theme banner write the same consent state, so
either works — but with both enabled the visitor sees two.

Also set **Settings → Customer privacy → Region visibility** to include Ireland
and the EEA, so `shouldShowBanner()` returns true for the visitors who need it.

### Verifying in the browser that nothing fires before consent

On the dev store, in a **fresh incognito window** each time — consent persists,
so a second run in the same window proves nothing.

1. Open DevTools → **Network**, tick **Preserve log**, filter on:
   `connect.facebook.net|facebook.com/tr|google-analytics|googletagmanager|analytics.google`
2. Load the storefront. The banner should appear.
3. **Before touching it**, browse two or three pages, view a product, add to bag.
   The filter must stay **empty**. One request here means a pixel's Permission
   is wrong — the banner cannot save you.
4. In the console, confirm no choice is recorded yet:
   ```js
   Shopify.customerPrivacy.currentVisitorConsent()
   // { analytics: "", marketing: "", preferences: "", sale_of_data: "" }
   ```
5. Click **Reject all**. The filter must *still* be empty, and:
   ```js
   Shopify.customerPrivacy.currentVisitorConsent()
   // { analytics: "no", marketing: "no", preferences: "no", sale_of_data: "no" }
   ```
6. New incognito window. Click **Accept all**. Requests should now appear for
   both, and `analytics` / `marketing` should read `"yes"`.
7. New incognito window. **Choose → Analytics only → Save**. Google requests
   appear; **Meta requests must not**. This is the check that catches a pixel
   with the wrong Permission, because accept-all hides that mistake.
8. Click **Cookie settings** in the footer. The panel must reopen showing the
   choice actually stored, and changing it must take effect.

Step 7 is the one worth repeating after any app install, since apps add their
own pixels and choose their own default permission.

### What the local preview already covers

`npm run verify` runs 40 assertions against the banner: nothing fires or is
recorded before a choice, reject is styled identically to accept, no category is
pre-ticked, the choice persists across pages, the footer link reopens it with
stored state, `sale_of_data` is never granted, and an analytics-only grant
releases the analytics pixel while withholding the marketing one.

Those model Shopify's gating rather than observing it — the preview has no
Shopify backend. They prove the theme asks for the right thing; steps 1–8 above
prove Shopify honours it.
