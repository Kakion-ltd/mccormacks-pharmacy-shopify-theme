// theme-check runner. Kept in the repo so the same command works after a
// scratchpad wipe: `node check.mjs`.
import { themeCheckRun } from '@shopify/theme-check-node';
import { fileURLToPath } from 'node:url';

// fileURLToPath, not .pathname — the project path contains a space, which
// .pathname leaves percent-encoded and readdir cannot open.
const root = fileURLToPath(new URL('./shopify-theme/', import.meta.url));
const { offenses } = await themeCheckRun(root);

const SEV = ['ERROR', 'WARNING', 'INFO'];
const counts = { ERROR: 0, WARNING: 0, INFO: 0 };
for (const o of offenses) counts[SEV[o.severity] ?? 'INFO']++;

for (const o of offenses.slice().sort((a, b) => a.severity - b.severity)) {
  const rel = String(o.uri).replace(/^file:\/\//, '').replace(root, '');
  console.log(`${SEV[o.severity] ?? 'INFO'}  ${rel}:${(o.start?.line ?? 0) + 1}  ${o.check}  ${o.message}`);
}
// Two rules Shopify enforces at upload that theme-check and liquidjs do not. Both
// rejected files on the first push to the dev store while every local check was green.
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
const liquidFiles = (dir) => readdirSync(dir).flatMap((f) => {
  const p = join(dir, f);
  return statSync(p).isDirectory() ? liquidFiles(p) : p.endsWith('.liquid') ? [p] : [];
});
let uploadErrors = 0;
for (const file of liquidFiles(root)) {
  const src = readFileSync(file, 'utf8');
  const rel = file.replace(root, '');
  // Shopify's tokenizer ends an output tag at the first "}" that is not part of "}}".
  for (const m of src.matchAll(/\{\{(?:(?!\}\}).)*?\}(?!\})/gs)) {
    const line = src.slice(0, m.index).split('\n').length;
    console.log(`ERROR  ${rel}:${line}  ShopifyLoneBrace  a "}" inside {{ }} ends the output tag on Shopify; build the value with assign in a {% %} tag`);
    uploadErrors++;
  }
  // A text setting with default "" is rejected as "default can't be blank"; omit the key.
  const schema = src.match(/{%-?\s*schema\s*-?%}([\s\S]*?){%-?\s*endschema/);
  if (schema) {
    try {
      const j = JSON.parse(schema[1]);
      const walk = (defs, where) => {
        for (const d of defs || []) {
          if ((d.type === 'text' || d.type === 'textarea') && d.default === '') {
            console.log(`ERROR  ${rel}  ShopifyBlankDefault  setting "${d.id}"${where} has default "": Shopify rejects the schema; drop the default key`);
            uploadErrors++;
          }
          // A color setting's default must be a literal colour; a var() or token name is rejected at upload.
          if (d.type === 'color' && d.default !== undefined && !/^#[0-9a-fA-F]{6}$/.test(String(d.default))) {
            console.log(`ERROR  ${rel}  ShopifyColorDefault  color setting "${d.id}"${where} has default ${JSON.stringify(d.default)}: must be a hex literal`);
            uploadErrors++;
          }
        }
      };
      walk(j.settings, '');
      for (const b of j.blocks || []) walk(b.settings, ` in block ${b.type}`);
      // Preset values are validated the same way: a color setting set to var() in a preset fails upload too.
      const colorIds = new Set();
      for (const d of j.settings || []) if (d.type === 'color') colorIds.add(d.id);
      for (const b of j.blocks || []) for (const d of b.settings || []) if (d.type === 'color') colorIds.add(d.id);
      for (const p of j.presets || []) {
        const check = (settings, where) => {
          for (const [k, v] of Object.entries(settings || {})) {
            if (colorIds.has(k) && !/^#[0-9a-fA-F]{6}$/.test(String(v))) {
              console.log(`ERROR  ${rel}  ShopifyColorDefault  preset "${p.name}"${where} sets color "${k}" to ${JSON.stringify(v)}: must be a hex literal`);
              uploadErrors++;
            }
          }
        };
        check(p.settings, '');
        for (const b of p.blocks || []) check(b.settings, ` block ${b.type}`);
      }
    } catch { /* theme-check reports invalid JSON */ }
  }
}
// A product price must go through the shared compare-at path, so a reduced product is
// never shown at an apparent full price. Seven hand-copied cards drifted apart on exactly
// this, and six of them lost the strikethrough. Liquid: `X.price | money` needs
// `render 'product-compare-at', product: X` earlier in the same loop over X. JavaScript:
// `fmt(X.price)` / `formatMoney(X.price)` needs saleWas(X), saleWas(shownVariant(X)) or
// mccSaleWas(X) within 30 lines. Exemptions are prices that are not a product's own
// headline price; each must still match something, so a stale entry fails too.
const PRICE_EXEMPT = {
  'sections/main-product.liquid|current_variant': 'buy box: shows the selected variant\'s own compare-at, updated by mccSaleWas on change',
  'sections/main-product.liquid|variant': 'no-JS variant <select>: option text, not a card',
  'sections/main-order.liquid|shipping_method': 'shipping cost, not a product',
};
const exemptSeen = new Set();
const lineAt = (src, i) => src.slice(0, i).split('\n').length;
const jsFiles = readdirSync(join(root, 'assets')).filter((f) => f.endsWith('.js')).map((f) => join(root, 'assets', f));
for (const file of [...liquidFiles(root), ...jsFiles]) {
  const src = readFileSync(file, 'utf8');
  const rel = file.replace(root, '');
  for (const m of src.matchAll(/\b(\w+)\.price\s*\|\s*money\w*/g)) {
    const v = m[1];
    const key = `${rel}|${v}`;
    if (PRICE_EXEMPT[key]) { exemptSeen.add(key); continue; }
    const before = src.slice(0, m.index);
    const loopAt = Math.max(...[...before.matchAll(new RegExp(`\\{%-?\\s*for\\s+${v}\\s+in\\b`, 'g'))].map((f) => f.index), 0);
    const scope = before.slice(loopAt);
    if (!new RegExp(`render\\s+'product-compare-at',\\s*product:\\s*${v}\\b`).test(scope)) {
      console.log(`ERROR  ${rel}:${lineAt(src, m.index)}  PriceWithoutCompareAt  ${v}.price is shown without render 'product-compare-at', product: ${v} in the same loop: a reduced product would show at full price`);
      uploadErrors++;
    }
  }
  for (const m of src.matchAll(/\b(?:fmt|formatMoney)\(\s*(\w+)\.price\s*\)/g)) {
    const v = m[1];
    const line = lineAt(src, m.index);
    const near = src.split('\n').slice(Math.max(0, line - 31), line + 30).join('\n');
    if (!new RegExp(`\\b(?:mccSaleWas|saleWas)\\(\\s*(?:shownVariant\\(\\s*)?${v}\\s*\\)`).test(near)) {
      console.log(`ERROR  ${rel}:${line}  PriceWithoutCompareAt  ${v}.price is shown without saleWas(${v}) nearby: a reduced product would show at full price`);
      uploadErrors++;
    }
  }
}
for (const key of Object.keys(PRICE_EXEMPT)) {
  if (!exemptSeen.has(key)) {
    console.log(`ERROR  ${key.split('|')[0]}  PriceWithoutCompareAt  stale exemption for "${key.split('|')[1]}": nothing matches it any more, remove it`);
    uploadErrors++;
  }
}
// No medicine in a recommendation rail (1 Oct 2026). A pharmacist-review product has
// to be found and read, not suggested next to a moisturiser, and it is not promoted
// with a discount on the homepage either. The rule is settings.restricted_tag through
// snippets/product-restricted.liquid; each rail loop skips on it and counts first, so
// a rail emptied by the filter takes its heading with it.
//
// This is a tripwire, not a proof: it fails when a listed rail loses its guard, which
// is the regression that actually happens. It cannot see a NEW rail that never had one
// — same limit as PromoLabelMissing, and the same reason. setup/verify/rails.py drives
// the real pages and is what checks the behaviour.
const RAILS = [
  ['snippets/product-card.liquid', "render 'product-restricted'"],
  ['sections/main-product.liquid', "restricted == 'true'"],
  ['sections/main-collection.liquid', "restricted == 'true'"],
  ['sections/sale-products.liquid', "restricted == 'true'"],
  ['sections/page-gift-vouchers.liquid', "restricted == 'true'"],
  ['sections/cart-recommendations.liquid', "restricted == 'true'"],
];
for (const [f, needle] of RAILS) {
  if (!readFileSync(join(root, f), 'utf8').includes(needle)) {
    console.log(`ERROR  /${f}  RailShowsMedicine  no "${needle}": a pharmacist-review product would be recommended here`);
    uploadErrors++;
  }
}
// Free delivery is the threshold and nothing else (1 Oct 2026). The theme used to tell a
// bag holding a sale or offer item that free delivery "isn't available", but the
// checkout's free-shipping discount never excluded them, so the bag said one thing and
// the checkout did another. Keep the claim out of the theme until the checkout enforces
// it (setup/MAINTENANCE.md, "Free delivery and sale items").
for (const f of ['sections/main-cart.liquid', 'assets/theme.js', 'sections/page-shipping.liquid']) {
  const src = readFileSync(join(root, f), 'utf8');
  if (/sale or offer items|containing sale items|data-sale-or-offer/.test(src)) {
    console.log(`ERROR  /${f}  SaleExclusionClaim  the theme promises a free-delivery exclusion the checkout does not apply`);
    uploadErrors++;
  }
}
// The bag drawer's Checkout must stay reachable on a phone. Two halves, both found broken
// on the live store on 1 Oct 2026: the open drawer keeps [hidden], so it must stay a flex
// column under that attribute; without min-height: the scroll region will not shrink,
// so the drawer outgrows the screen and Checkout falls off the bottom; and the product
// page's sticky bar paints over the drawer (same z-index layer), so it must hide.
const DRAWER_REACH = [
  ['assets/base.css', '.cd-scroll { flex: 1 1 auto; min-height: 0; overflow-y: auto;', 'the drawer stops scrolling and Checkout goes off-screen'],
  ['assets/base.css', '.cd-drawer[hidden] { display: flex; }', 'the open drawer (which keeps [hidden]) falls back to display:block and never scrolls'],
  ['sections/main-product.liquid', 'body[data-cd-open] .mobile-buybar { visibility: hidden; }', 'the sticky bar covers the drawer\'s Checkout on a phone'],
];
for (const [f, needle, why] of DRAWER_REACH) {
  if (!readFileSync(join(root, f), 'utf8').includes(needle)) {
    console.log(`ERROR  /${f}  DrawerCheckoutUnreachable  no "${needle}": ${why}`);
    uploadErrors++;
  }
}
// The free delivery threshold must stay a TEXT setting. Shopify's `number` type cannot
// hold a decimal: it rounded 54.99 to 55, so every "free delivery over" line on the site
// read €55 while the shipping policy and the Shopify discount both said €54.99. Reverting
// the type would bring that back silently -- the theme editor would simply show 55 and
// nothing would fail. Text is only safe because free-delivery-cents sanitises it, so both
// halves are checked here: the type, and the parse that makes the type safe.
{
  const schema = readFileSync(join(root, 'config/settings_schema.json'), 'utf8');
  const m = schema.match(/\{[^{}]*"id":\s*"free_shipping_threshold"[^{}]*\}/s);
  if (!m) {
    console.log('ERROR  /config/settings_schema.json  ThresholdSettingMissing  no free_shipping_threshold setting');
    uploadErrors++;
  } else if (!/"type":\s*"text"/.test(m[0])) {
    console.log('ERROR  /config/settings_schema.json  ThresholdNotText  free_shipping_threshold is not type text: a number setting rounds 54.99 to 55');
    uploadErrors++;
  }
  const cents = readFileSync(join(root, 'snippets/free-delivery-cents.liquid'), 'utf8');
  for (const needle of ["remove: '€'", 'times: 100', 'round', 'at_least: 100']) {
    if (!cents.includes(needle)) {
      console.log(`ERROR  /snippets/free-delivery-cents.liquid  ThresholdParseWeakened  no "${needle}": a text threshold needs sanitising, or "€65" evaluates to zero`);
      uploadErrors++;
    }
  }
}
// assets/placeholder-shop-image.svg is referenced from setup/render_preview.mjs and from
// nothing in the theme, so an unused-asset sweep would call it dead. It is not: it is what
// `shopify://shop_images/` image_picker settings resolve to in the preview, and without it
// every page carrying one logs ERR_UNKNOWN_URL_SCHEME and funnel.py goes red on console
// errors. Deleting it would re-break that with no obvious connection to the deletion.
if (!existsSync(join(root, 'assets/placeholder-shop-image.svg'))) {
  console.log('ERROR  /assets/placeholder-shop-image.svg  ShopImagePlaceholderMissing  the preview resolves shopify://shop_images/ to this; without it funnel.py fails on console errors');
  uploadErrors++;
}
// The promo label ("3 for €10", "While stocks last") is a product metafield. It used to
// be on three of seven hand-copied cards; four of those copies are now the one shared
// card, so these three files are every surface that can show it: the shared card, the
// homepage Sale rail (its own design, see the snippet's header) and the product page's
// own price block. If one loses the render, that surface silently shows a multi-buy
// product with no sign there is an offer. See MAINTENANCE.md, "The promo label".
for (const f of ['snippets/product-card.liquid', 'sections/sale-products.liquid', 'sections/main-product.liquid']) {
  if (!readFileSync(join(root, f), 'utf8').includes("render 'product-promo-label'")) {
    console.log(`ERROR  /${f}  PromoLabelMissing  no render 'product-promo-label': an offer on this surface shows nothing`);
    uploadErrors++;
  }
}
// The Common Conditions page lists every store with its phone for "call to book". Liquid
// cannot read another template's blocks, so that list is a copy of the store locator's.
// It must name the same stores with the same address and phone, or a patient rings a
// number the locator has since corrected.
{
  const blocksOf = (t) => {
    const j = JSON.parse(readFileSync(join(root, 'templates', t), 'utf8').replace(/^\s*\/\*[\s\S]*?\*\//, ''));
    return Object.values(j.sections).flatMap((s) => (s.block_order || []).map((k) => s.blocks[k]))
      .filter((b) => b.type === 'store').map((b) => b.settings);
  };
  const key = (s) => `${s.name} | ${s.address} | ${s.phone}`;
  const loc = new Set(blocksOf('page.store-locator.json').map(key));
  const ccs = new Set(blocksOf('page.common-conditions.json').map(key));
  for (const s of loc) if (!ccs.has(s)) { console.log(`ERROR  templates/page.common-conditions.json  StoreDrift  store locator has "${s}", the Common Conditions page does not`); uploadErrors++; }
  for (const s of ccs) if (!loc.has(s)) { console.log(`ERROR  templates/page.common-conditions.json  StoreDrift  Common Conditions page has "${s}", the store locator does not`); uploadErrors++; }
}
counts.ERROR += uploadErrors;
console.log(`\n${counts.ERROR} errors, ${counts.WARNING} warnings, ${counts.INFO} info`);
process.exit(counts.ERROR > 0 ? 1 : 0);
