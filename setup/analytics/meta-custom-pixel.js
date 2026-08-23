/* ---------------------------------------------------------------------------
   Meta (Facebook) pixel — Shopify custom pixel.

   WHERE THIS GOES
     Shopify admin > Settings > Customer events > Add custom pixel.
     Name it "Meta Pixel". Paste this whole file. Set Permission to
     "Marketing" — this is what makes Shopify withhold the pixel until the
     consent banner records a marketing grant. "Not required" fires it before
     the visitor has answered, which is the failure the banner exists to
     prevent. Save, then Connect.

     Do NOT paste this into theme.liquid or Additional Scripts. Additional
     Scripts is being removed, and a pixel in the theme cannot see checkout
     or the thank-you page, which is where purchase fires.

   WHAT IT COVERS
     ViewContent   <- product_viewed
     AddToCart     <- product_added_to_cart   (fires for the theme's AJAX adds too)
     InitiateCheckout <- checkout_started
     Purchase      <- checkout_completed

   SET THIS BEFORE SAVING
     Replace PIXEL_ID below with the pixel from Meta Events Manager.

   NOTES
     Custom pixels run in a sandboxed iframe, so `window` here is not the
     storefront's window and the storefront cannot see this code. That is the
     point: it also means fbq's automatic PageView on load is the only page
     event, and everything else must be subscribed explicitly, as below.

     GA4 is NOT here. GA4, Merchant Center and Google Ads all come from the
     Google & YouTube channel app, which installs its own pixel — adding a
     second GA4 pixel would double-count every event.
--------------------------------------------------------------------------- */

const PIXEL_ID = 'REPLACE_WITH_META_PIXEL_ID';

/* Standard Meta base snippet. */
!(function (f, b, e, v, n, t, s) {
  if (f.fbq) return;
  n = f.fbq = function () {
    n.callMethod ? n.callMethod.apply(n, arguments) : n.queue.push(arguments);
  };
  if (!f._fbq) f._fbq = n;
  n.push = n;
  n.loaded = true;
  n.version = '2.0';
  n.queue = [];
  t = b.createElement(e);
  t.async = true;
  t.src = v;
  s = b.getElementsByTagName(e)[0];
  s.parentNode.insertBefore(t, s);
})(window, document, 'script', 'https://connect.facebook.net/en_US/fbevents.js');

fbq('init', PIXEL_ID);
fbq('track', 'PageView');

/* Money on Shopify's pixel events is always {amount, currencyCode}. */
const amount = (price) => (price && price.amount) || 0;
const currency = (price) => (price && price.currencyCode) || 'EUR';

analytics.subscribe('product_viewed', (event) => {
  const v = event.data.productVariant;
  if (!v) return;
  fbq('track', 'ViewContent', {
    content_type: 'product',
    content_ids: [String(v.id)],
    content_name: v.product && v.product.title,
    value: amount(v.price),
    currency: currency(v.price),
  });
});

analytics.subscribe('product_added_to_cart', (event) => {
  const line = event.data.cartLine;
  if (!line) return;
  fbq('track', 'AddToCart', {
    content_type: 'product',
    content_ids: [String(line.merchandise.id)],
    content_name: line.merchandise.product && line.merchandise.product.title,
    value: amount(line.cost && line.cost.totalAmount),
    currency: currency(line.cost && line.cost.totalAmount),
  });
});

analytics.subscribe('checkout_started', (event) => {
  const c = event.data.checkout;
  if (!c) return;
  fbq('track', 'InitiateCheckout', {
    content_type: 'product',
    content_ids: (c.lineItems || []).map((li) => String(li.variant.id)),
    num_items: (c.lineItems || []).reduce((n, li) => n + li.quantity, 0),
    value: amount(c.totalPrice),
    currency: currency(c.totalPrice),
  });
});

analytics.subscribe('checkout_completed', (event) => {
  const c = event.data.checkout;
  if (!c) return;
  fbq(
    'track',
    'Purchase',
    {
      content_type: 'product',
      content_ids: (c.lineItems || []).map((li) => String(li.variant.id)),
      num_items: (c.lineItems || []).reduce((n, li) => n + li.quantity, 0),
      value: amount(c.totalPrice),
      currency: currency(c.totalPrice),
    },
    // Deduplicates against Meta's Conversions API if that is ever added, and
    // guards against a shopper refreshing the thank-you page.
    { eventID: c.order && c.order.id ? String(c.order.id) : c.token }
  );
});
