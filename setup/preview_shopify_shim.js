/* PREVIEW ONLY — never shipped in the theme.
 *
 * render_preview.mjs injects this as content_for_header, which is where a real
 * store gets window.Shopify from. It stands in for two things the local preview
 * has no access to:
 *
 *   1. Shopify.loadFeatures + Shopify.customerPrivacy — the Customer Privacy
 *      API the consent banner drives.
 *   2. The permission-gated pixels under Settings > Customer events, modelled
 *      as two fake pixels that refuse to fire until their category is granted.
 *
 * WHAT THIS DOES AND DOES NOT PROVE
 *
 *   It proves the theme's half: that the banner appears before any choice, that
 *   nothing is recorded until the visitor acts, that reject sends the same shape
 *   of call as accept, that the choice persists, and that it can be changed.
 *
 *   It cannot prove Shopify's half — that Shopify actually withholds a real
 *   pixel. The gating here is modelled, not observed. That has to be checked on
 *   a real store; the procedure is in setup/analytics/README.md.
 */
(function () {
  var KEY = 'preview_consent';
  var EMPTY = { analytics: '', marketing: '', preferences: '', sale_of_data: '' };

  function read() {
    try {
      var raw = window.localStorage.getItem(KEY);
      return raw ? JSON.parse(raw) : Object.assign({}, EMPTY);
    } catch (e) {
      return Object.assign({}, EMPTY);
    }
  }

  function write(consent) {
    try { window.localStorage.setItem(KEY, JSON.stringify(consent)); } catch (e) { /* private mode */ }
  }

  // Every attempt a "pixel" makes to fire is appended here, granted or not, so a
  // test can assert on the whole history rather than on a final state.
  window.__pixelLog = [];

  var customerPrivacy = {
    currentVisitorConsent: function () { return read(); },
    shouldShowBanner: function () {
      var c = read();
      // A visitor who has answered — either way — is not asked again.
      return c.analytics === '' && c.marketing === '' && c.preferences === '';
    },
    analyticsProcessingAllowed: function () { return read().analytics === 'yes'; },
    marketingAllowed: function () { return read().marketing === 'yes'; },
    preferencesProcessingAllowed: function () { return read().preferences === 'yes'; },
    saleOfDataAllowed: function () { return read().sale_of_data === 'yes'; },
    userCanBeTracked: function () { return read().analytics === 'yes' || read().marketing === 'yes'; },
    setTrackingConsent: function (payload, callback) {
      var next = {
        analytics: payload.analytics ? 'yes' : 'no',
        marketing: payload.marketing ? 'yes' : 'no',
        preferences: payload.preferences ? 'yes' : 'no',
        sale_of_data: payload.sale_of_data ? 'yes' : 'no',
      };
      write(next);
      window.__consentCalls = (window.__consentCalls || []).concat([payload]);
      document.dispatchEvent(new CustomEvent('visitorConsentCollected', { detail: next }));
      releasePixels();
      if (typeof callback === 'function') callback({ error: false });
    },
  };

  // Stand-ins for the pixels configured in Settings > Customer events. Each
  // declares the permission it needs, exactly as a real custom pixel does.
  var PIXELS = [
    { name: 'ga4', permission: 'analytics' },
    { name: 'meta', permission: 'marketing' },
  ];
  var fired = {};

  function releasePixels() {
    var consent = read();
    PIXELS.forEach(function (pixel) {
      var granted = consent[pixel.permission] === 'yes';
      window.__pixelLog.push({ pixel: pixel.name, granted: granted, at: 'release' });
      if (granted && !fired[pixel.name]) {
        fired[pixel.name] = true;
        window.__pixelLog.push({ pixel: pixel.name, granted: true, at: 'fired' });
      }
    });
  }

  window.Shopify = window.Shopify || {};
  window.Shopify.shop = 'mock.myshopify.com';
  window.Shopify.loadFeatures = function (features, callback) {
    // Async, like the real one, so anything that assumes synchronous
    // availability of customerPrivacy fails here too rather than only in production.
    window.setTimeout(function () {
      window.Shopify.customerPrivacy = customerPrivacy;
      callback(null);
    }, 0);
  };

  // On load, pixels attempt to fire and are gated by whatever is already stored.
  releasePixels();
})();
