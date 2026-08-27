/**
 * Mock renderer: renders every theme template with stand-in Shopify data and
 * writes static HTML into preview/. Lets us eyeball and measure the theme
 * without a live store.
 *
 *   node setup/render_preview.mjs                 # 49 templates -> preview/
 *   node setup/render_preview.mjs --categories    # + one page per collection
 *
 * Lives in setup/ deliberately: an earlier copy sat in a temp dir and was lost.
 */
import { Liquid } from 'liquidjs';
import { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const PROJECT = dirname(HERE);
const THEME = join(PROJECT, 'shopify-theme');
const ASSETS = '/shopify-theme/assets';

const engine = new Liquid({
  root: [join(THEME, 'snippets'), join(THEME, 'sections'), THEME],
  extname: '.liquid',
  jsTruthy: true,
  strictFilters: false,
  strictVariables: false,
});

/* ---------- Shopify filters ---------- */
const money = (v) => (v == null || isNaN(v) ? v : `€${(v / 100).toFixed(2)}`);
const imgSrc = (img) => (typeof img === 'string' ? img : img && (img.src || img.url)) || '';

engine.registerFilter('asset_url', (v) => `${ASSETS}/${v}`);
engine.registerFilter('asset_img_url', (v) => `${ASSETS}/${v}`);
engine.registerFilter('file_url', (v) => `${ASSETS}/${v}`);
engine.registerFilter('img_url', (v) => imgSrc(v));
// liquidjs hands named filter arguments over as [key, value] pairs, not as one
// options object — Object.entries on them yields 0="as" 1="font".
engine.registerFilter('preload_tag', (url, ...args) => {
  const attrs = args
    .filter((a) => Array.isArray(a) && a.length === 2)
    .map(([k, v]) => ` ${k}="${attrEsc(v)}"`)
    .join('');
  return `<link rel="preload" href="${attrEsc(url)}"${attrs}>`;
});
// Shopify's perceived-brightness filter, 0-255. The theme uses it to pick legible text
// for whatever green a merchant sets, so the harness has to agree with Shopify's maths
// or the preview shows a different foreground to the real store.
engine.registerFilter('color_brightness', (v) => {
  const m = /^#?([0-9a-f]{6})$/i.exec(String(v ?? '').trim());
  if (!m) return 0;
  const n = parseInt(m[1], 16);
  const [r, g, b] = [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  return (r * 299 + g * 587 + b * 114) / 1000;
});
const hexToRgb = (v) => {
  const m = /^#?([0-9a-f]{6})$/i.exec(String(v ?? '').trim());
  if (!m) return null;
  const n = parseInt(m[1], 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
};
const relLum = ([r, g, b]) =>
  [r, g, b].map((c) => { c /= 255; return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; })
    .reduce((a, c, i) => a + c * [0.2126, 0.7152, 0.0722][i], 0);

engine.registerFilter('color_contrast', (a, b) => {
  const [x, y] = [hexToRgb(a), hexToRgb(b)];
  if (!x || !y) return 1;
  const [l1, l2] = [relLum(x), relLum(y)];
  return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
});
// Shopify darkens in HSL, so match that rather than scaling RGB — scaling RGB
// shifts the hue and the preview would drift from the real store.
engine.registerFilter('color_darken', (v, pct) => {
  const rgb = hexToRgb(v);
  if (!rgb) return v;
  const [r, g, b] = rgb.map((c) => c / 255);
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  let h = 0;
  const l = (max + min) / 2, d = max - min;
  const s = d === 0 ? 0 : d / (1 - Math.abs(2 * l - 1));
  if (d !== 0) {
    if (max === r) h = ((g - b) / d) % 6;
    else if (max === g) h = (b - r) / d + 2;
    else h = (r - g) / d + 4;
    h *= 60;
    if (h < 0) h += 360;
  }
  const nl = Math.max(0, l - Number(pct) / 100);
  const c = (1 - Math.abs(2 * nl - 1)) * s, x = c * (1 - Math.abs(((h / 60) % 2) - 1)), m2 = nl - c / 2;
  const seg = [[c, x, 0], [x, c, 0], [0, c, x], [0, x, c], [x, 0, c], [c, 0, x]][Math.floor(h / 60) % 6];
  return '#' + seg.map((p) => Math.round((p + m2) * 255).toString(16).padStart(2, '0')).join('').toUpperCase();
});
engine.registerFilter('money', money);
engine.registerFilter('money_with_currency', (v) => `${money(v)} EUR`);
engine.registerFilter('money_without_trailing_zeros', (v) => `€${Math.round(v / 100)}`);
engine.registerFilter('money_without_currency', (v) => (v == null || isNaN(v) ? v : (v / 100).toFixed(2)));
engine.registerFilter('handleize', (v) => String(v ?? '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''));
engine.registerFilter('handle', (v) => String(v ?? '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''));
engine.registerFilter('url_encode', (v) => encodeURIComponent(String(v ?? '')));
engine.registerFilter('json', (v) => JSON.stringify(v));
engine.registerFilter('t', (v) => String(v));
engine.registerFilter('stylesheet_tag', (v) => `<link rel="stylesheet" href="${v}">`);
engine.registerFilter('script_tag', (v) => `<script src="${v}"></script>`);
engine.registerFilter('payment_type_svg_tag', () => '<svg width="38" height="24"></svg>');
engine.registerFilter('placeholder_svg_tag', () => '<svg class="placeholder"></svg>');
engine.registerFilter('within', (v) => v);
engine.registerFilter('link_to', (v, u) => `<a href="${u}">${v}</a>`);
engine.registerFilter('highlight', (v) => v);
engine.registerFilter('weight_with_unit', (v) => `${v}g`);
engine.registerFilter('metafield_text', (v) => (v && v.value) || v || '');
// Shopify renders these from the store's enabled payment providers. The mock shows a
// labelled stand-in so placement is reviewable; the real buttons only appear on a store.
engine.registerFilter('payment_button', () =>
  '<div data-mock-express style="height:48px;border-radius:10px;border:1.5px dashed #b9c2b3;' +
  'display:flex;align-items:center;justify-content:center;font-size:12.5px;font-weight:700;' +
  'letter-spacing:.06em;text-transform:uppercase;color:#697262;background:#f4f6f1;">' +
  'Shop Pay / Apple Pay &middot; live store only</div>');

// image_url: keeps the width so image_tag can build a srcset from it
engine.registerFilter('image_url', (img, ...rest) => {
  const opts = {};
  for (let i = 0; i < rest.length; i++) {
    const a = rest[i];
    if (Array.isArray(a)) opts[a[0]] = a[1];
    else if (a && typeof a === 'object') Object.assign(opts, a);
  }
  const base = imgSrc(img);
  if (!base) return '';
  if (!opts.width) return base;
  // encode height too: Shopify's image_tag derives width/height attributes from
  // the URL it is given, and we need those to appear for CLS verification.
  const ar = (img && img.width && img.height) ? img.width / img.height : null;
  const h = ar ? Math.round(opts.width / ar) : null;
  return `${base}?width=${opts.width}${h ? `&height=${h}` : ''}`;
});

const attrEsc = (s) => String(s ?? '').replace(/"/g, '&quot;');
engine.registerFilter('image_tag', (url, ...rest) => {
  const o = {};
  for (const a of rest) {
    if (Array.isArray(a)) o[a[0]] = a[1];
    else if (a && typeof a === 'object') Object.assign(o, a);
  }
  if (!url) return '';
  const base = String(url).split('?')[0];
  const baseW = Number(String(url).match(/width=(\d+)/)?.[1] || 0);
  const baseH = Number(String(url).match(/height=(\d+)/)?.[1] || 0);
  let srcset = '';
  if (o.widths) {
    srcset = String(o.widths).split(',').map((w) => `${base}?width=${w.trim()} ${w.trim()}w`).join(', ');
  }
  const at = [`src="${url}"`];
  if (srcset) at.push(`srcset="${srcset}"`);
  if (o.sizes) at.push(`sizes="${attrEsc(o.sizes)}"`);
  at.push(`alt="${attrEsc(o.alt ?? '')}"`);
  if (o.width || baseW) at.push(`width="${o.width || baseW}"`);
  if (o.height || baseH) at.push(`height="${o.height || baseH}"`);
  if (o.loading) at.push(`loading="${o.loading}"`);
  if (o.fetchpriority) at.push(`fetchpriority="${o.fetchpriority}"`);
  // Shopify emits a preload link for image_tag preload:true — mirror it so the
  // rendered preview can be checked for it.
  let preloadLink = '';
  if (o.preload) {
    preloadLink = `<link rel="preload" as="image" href="${url}"` +
      (srcset ? ` imagesrcset="${srcset}"` : '') +
      (o.sizes ? ` imagesizes="${attrEsc(o.sizes)}"` : '') +
      (o.fetchpriority ? ` fetchpriority="${o.fetchpriority}"` : '') + '>';
  }
  if (o.class) at.push(`class="${attrEsc(o.class)}"`);
  if (o.id) at.push(`id="${attrEsc(o.id)}"`);
  if (o.style) at.push(`style="${attrEsc(o.style)}"`);
  return `${preloadLink}<img ${at.join(' ')}>`;
});

/* ---------- Shopify tags ---------- */
// Block tags need parseStream in liquidjs 10 — collecting raw tokens and
// rendering them later throws "getPosition".
const blockTag = (endName, wrap) => ({
  parse(tagToken, remainTokens) {
    this.tpls = [];
    const stream = this.liquid.parser.parseStream(remainTokens);
    stream.on(`tag:${endName}`, () => stream.stop())
      .on('template', (tpl) => this.tpls.push(tpl))
      .on('end', () => { throw new Error(`${endName} not found`); });
    stream.start();
  },
  *render(ctx, emitter) {
    const inner = yield this.liquid.renderer.renderTemplates(this.tpls, ctx);
    emitter.write(wrap ? wrap(inner) : '');
  },
});

// schema holds JSON, not Liquid — swallow the tokens without parsing them.
engine.registerTag('schema', {
  parse(tagToken, remainTokens) {
    let t;
    while ((t = remainTokens.shift())) if (t.name === 'endschema') return;
  },
  render() { return ''; },
});

engine.registerTag('style', blockTag('endstyle', (s) => `<style>${s}</style>`));
engine.registerTag('javascript', blockTag('endjavascript', (s) => `<script>${s}</script>`));
engine.registerTag('stylesheet', blockTag('endstylesheet', (s) => `<style>${s}</style>`));

engine.registerTag('form', {
  parse(tagToken, remainTokens) {
    this.args = tagToken.args;
    this.tpls = [];
    const stream = this.liquid.parser.parseStream(remainTokens);
    stream.on('tag:endform', () => stream.stop())
      .on('template', (tpl) => this.tpls.push(tpl))
      .on('end', () => { throw new Error('endform not found'); });
    stream.start();
  },
  *render(ctx, emitter) {
    const st = this.args.match(/style:\s*'([^']*)'/);
    ctx.push({ form: { posted_successfully: false, errors: null } });
    const inner = yield this.liquid.renderer.renderTemplates(this.tpls, ctx);
    ctx.pop();
    emitter.write(`<form method="post"${st ? ` style="${st[1]}"` : ''}>${inner}</form>`);
  },
});

engine.registerTag('paginate', {
  parse(tagToken, remainTokens) {
    this.tpls = [];
    const stream = this.liquid.parser.parseStream(remainTokens);
    stream.on('tag:endpaginate', () => stream.stop())
      .on('template', (tpl) => this.tpls.push(tpl))
      .on('end', () => { throw new Error('endpaginate not found'); });
    stream.start();
  },
  *render(ctx, emitter) {
    ctx.push({ paginate: { pages: 1, current_page: 1, items: 8, parts: [], next: null, previous: null } });
    emitter.write(yield this.liquid.renderer.renderTemplates(this.tpls, ctx));
    ctx.pop();
  },
});

// Section groups (sections/*.json) carry the header and footer.
engine.registerTag('sections', {
  parse(tagToken) { this.name = tagToken.args.replace(/['"]/g, '').trim(); },
  *render(ctx, emitter) {
    const file = join(THEME, 'sections', `${this.name}.json`);
    if (!existsSync(file)) return;
    const group = JSON.parse(readFileSync(file, 'utf8'));
    const order = group.order || Object.keys(group.sections || {});
    for (const id of order) {
      const sec = group.sections[id];
      if (!sec) continue;
      emitter.write(yield renderSection(sec.type, sec.settings || {},
        { order: sec.block_order || [], blocks: sec.blocks || {} }, ctx.getAll()));
    }
  },
});

engine.registerTag('section', {
  parse(tagToken) { this.name = tagToken.args.replace(/['"]/g, '').trim(); },
  *render(ctx, emitter) {
    emitter.write(yield renderSection(this.name, {}, {}, ctx.getAll()));
  },
});

/* ---------- mock data ---------- */
const mockImage = (name, w = 1000, h = 1000) => ({
  src: `${ASSETS}/${name}`, url: `${ASSETS}/${name}`, width: w, height: h,
  alt: '', aspect_ratio: w / h,
});

const COLLECTION_INDEX = Object.fromEntries(
  JSON.parse(readFileSync(join(PROJECT, 'setup/collections.json'), 'utf8')).map((c) => [c.handle, c]));

const CATALOGUE = [
  { t: 'fabÜ Skin Hair Nails Glow 60 Capsules', col: 'skin-hair-nails', v: 'fabÜ', img: 'prod-fabu-glow.jpg', p: 1995, was: 2495, ty: 'Vitamins' },
  { t: 'Cetrine Allergy 10mg 30 Tablets', col: 'hayfever-allergy', v: 'Cetrine', img: 'prod-cetrine.jpg', p: 799, was: null, ty: 'Allergy' },
  { t: 'Revive Active 30 Sachets', col: 'energy-wellbeing', v: 'Revive Active', img: 'prod-revive.jpg', p: 6499, was: 6999, ty: 'Supplements' },
  { t: 'Optibac Every Day MAX 30 Capsules', col: 'probiotics-digestive-health', v: 'Optibac', img: 'prod-optibac-max.jpg', p: 2799, was: null, ty: 'Probiotics' },
  { t: 'Nurofen 200mg Ibuprofen 24 Tablets', col: 'pain-relief', v: 'Nurofen', img: 'prod-nurofen.jpg', p: 649, was: null, ty: 'Pain Relief' },
  { t: 'CeraVe Hydrating Cleanser 236ml', col: 'cleanser', v: 'CeraVe', img: 'prod-cerave-cleanser.jpg', p: 1350, was: null, ty: 'Skincare' },
  { t: 'Sudocrem Antiseptic Healing Cream 125g', col: 'baby-skincare', v: 'Sudocrem', img: 'prod-sudocrem.jpg', p: 799, was: 899, ty: 'Baby' },
  { t: 'Vitamin D3 1000IU 60 Capsules', col: 'everyday-multivitamins', v: 'McCormack’s', img: 'prod-vitd.jpg', p: 999, was: null, ty: 'Vitamins' },
  // Fixture for the pharmacy gate. A codeine-containing analgesic is pharmacist-only
  // in Ireland, so it is the honest example of a product that must never be
  // one-click added from a grid, a search suggestion or a recommendation.
  { t: 'Nurofen Plus 200mg/12.8mg 24 Tablets', col: 'pain-relief', v: 'Nurofen', img: 'prod-nurofen.jpg', p: 1099, was: null, ty: 'Pain Relief', tg: ['pharmacist-only'] },
  // Fixture for the sold-out path. Without one, the out-of-stock product page and its
  // back-in-stock capture render in no preview and are verified by nobody.
  { t: 'Difflam Sore Throat Spray 30ml', col: 'sore-throat', v: 'Difflam', img: 'prod-cetrine.jpg', p: 1299, was: null, ty: 'Sore Throat', oos: true },
];

// Harness-only FAQ fixture. NOT customer copy and never shipped: the theme's FAQ
// metafield is empty by design and its content needs pharmacist sign-off. This
// exists so the mechanism is exercised — that it renders, that an entry missing
// half a pair is dropped rather than half-rendered, that an internal link
// survives, and that the JSON-LD stays valid when an answer contains quotes.
CATALOGUE[0].faq = [
  { question: 'HARNESS FIXTURE - does the accordion render?',
    answer: '<p>Fixture answer with an <a href="/pages/shipping">internal link</a>.</p>' },
  { question: 'HARNESS FIXTURE - does "quoting" keep the JSON valid?',
    answer: '<p>Fixture answer containing "double quotes" and an apostrophe.</p>' },
  { question: 'HARNESS FIXTURE - is a half-filled entry dropped?', answer: '   ' },
];

const handleOf = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
// Minimal collection stub for product.collections — the PDP breadcrumb reads
// .first.url and .first.title from it.
const collectionRef = (handle) => {
  const c = COLLECTION_INDEX[handle];
  return { handle, title: c ? c.title : handle, url: `/collections/${handle}` };
};
const mockVariant = (i) => ({
  id: 40000000 + i, title: 'Default', price: CATALOGUE[i].p, compare_at_price: CATALOGUE[i].was,
  available: !CATALOGUE[i].oos, sku: `SKU-${i}`,
  inventory_quantity: CATALOGUE[i].oos ? 0 : 12, featured_image: null,
  store_availabilities: [],
  requires_shipping: true, options: ['Default'], selected: i === 0,
});
const products = CATALOGUE.map((c, i) => ({
  id: 30000000 + i, title: c.t, handle: handleOf(c.t), vendor: c.v, type: c.ty,
  url: `/products/${handleOf(c.t)}`, price: c.p, price_min: c.p, price_max: c.p,
  compare_at_price: c.was, compare_at_price_max: c.was, available: !c.oos,
  featured_image: mockImage(c.img, 700, 700), images: [mockImage(c.img, 700, 700)],
  media: [{ media_type: 'image', preview_image: mockImage(c.img, 700, 700), id: i, alt: c.t }],
  variants: [mockVariant(i)], first_available_variant: mockVariant(i),
  selected_or_first_available_variant: mockVariant(i), has_only_default_variant: true,
  options_with_values: [], tags: c.tg || [], selling_plan_groups: [],
  description: '<p>Product description.</p>',
  content: '<p>Product description.</p>',
  collections: c.col ? [collectionRef(c.col)] : [],
  metafields: { reviews: {}, custom: c.faq ? { faq: { value: c.faq } } : {} },
}));

const mockCollection = {
  id: 1, title: 'Medicines & Health', handle: 'medicines-health', url: '/collections/medicines-health',
  description: '<p>Everyday healthcare for the whole family.</p>',
  products, products_count: products.length, all_products_count: products.length,
  image: mockImage('cat-vitamins.jpg', 1440, 500), featured_image: mockImage('cat-vitamins.jpg', 1440, 500),
  filters: [
    { label: 'Brand', type: 'list', param_name: 'filter.p.vendor', active_values: [],
      values: [
        { label: 'fabÜ', value: 'fab', count: 4, active: false, url_to_add: '?filter.p.vendor=fab', url_to_remove: '?' },
        { label: 'Nurofen', value: 'nur', count: 2, active: true, url_to_add: '?filter.p.vendor=nur', url_to_remove: '?' },
      ] },
    { label: 'Price', type: 'price_range', param_name: 'filter.v.price', active_values: [], values: [],
      range_max: 10000, min_value: { value: null, param_name: 'filter.v.price.gte' },
      max_value: { value: null, param_name: 'filter.v.price.lte' }, url_to_remove: '?' },
  ],
  sort_options: [{ name: 'Best selling', value: 'best-selling' }, { name: 'Price, low to high', value: 'price-ascending' }],
  sort_by: 'best-selling', default_sort_by: 'best-selling',
};

const articles = [0, 1, 2, 3].map((i) => ({
  id: i, title: `Health Hub article ${i + 1}`, handle: `article-${i}`, url: `/blogs/health-hub/article-${i}`,
  excerpt: 'Advice from our pharmacists.', content: '<p>Article body.</p>',
  image: mockImage('cat-suncare.jpg', 860, 531), author: 'Pharmacist',
  published_at: '2026-05-01', tags: ['Advice'], comments_count: 0,
}));

const collectionsList = JSON.parse(readFileSync(join(PROJECT, 'setup/collections.json'), 'utf8'));

const globals = {
  shop: {
    name: "McCormack's Pharmacy", email: 'info@example.com', url: 'https://mock.myshopify.com',
    secure_url: 'https://mock.myshopify.com', domain: 'mock.myshopify.com',
    enabled_payment_types: ['visa', 'master', 'american_express', 'paypal', 'apple_pay', 'google_pay'],
    money_format: '€{{amount}}', privacy_policy: { url: '/pages/privacy-policy' },
  },
  cart: {
    item_count: 2, total_price: 4990, items_subtotal_price: 4990, original_total_price: 5490, total_discount: 500,
    items: [0, 2].map((i, n) => ({
      key: `a:${n}`, title: CATALOGUE[i].t, quantity: 1, final_price: CATALOGUE[i].p,
      final_line_price: CATALOGUE[i].p, original_price: CATALOGUE[i].was, line_price: CATALOGUE[i].p,
      price: CATALOGUE[i].p, image: mockImage(CATALOGUE[i].img, 700, 700), url: products[i].url,
      product: products[i], variant: mockVariant(i), variant_id: 40000000 + i,
      product_id: 30000000 + i, product_title: CATALOGUE[i].t,
      vendor: CATALOGUE[i].v, variant_title: null, sku: `SKU-${i}`, options_with_values: [],
    })),
    empty: false, note: '', attributes: {}, currency: { iso_code: 'EUR', symbol: '€' },
  },
  collection: mockCollection,
  collections: Object.fromEntries(collectionsList.map((c) => [c.handle, {
    ...mockCollection, handle: c.handle, title: c.title, url: `/collections/${c.handle}`,
    description: c.description_html || '', image: null, featured_image: null,
  }])),
  product: products[0],
  products: new Proxy({}, { get: (_, k) => (typeof k === 'string' ? products[0] : undefined) }),
  recommendations: { performed: true, products_count: 4, products: products.slice(0, 4) },
  predictive_search: { performed: false, terms: '', resources: { products: [], collections: [], queries: [], pages: [], articles: [] } },
  blog: { title: 'Health Hub', handle: 'health-hub', url: '/blogs/health-hub', articles, articles_count: 4, all_tags: ['Advice'], tags: [] },
  article: articles[0],
  articles, search: { performed: true, terms: 'vitamins', results: products, results_count: products.length, results_url: '/search' },
  customer: null, gift_card: { balance: 5000, initial_value: 5000, code: 'XXXX-XXXX', expired: false, enabled: true, currency: 'EUR', qr_identifier: '', pass_url: null, url: '#' },
  page: { title: 'Page', handle: 'page', content: '<p>Page content.</p>' },
  order: { name: '#1001', created_at: '2026-05-01', line_items: [], financial_status: 'paid', fulfillment_status: 'fulfilled', shipping_address: {}, billing_address: {}, subtotal_price: 4990, total_price: 4990, shipping_methods: [], tax_lines: [], cancelled: false },
  linklists: {}, images: {}, current_tags: null, canonical_url: 'https://mock.myshopify.com/',
  page_title: "McCormack's Pharmacy", page_description: 'Ireland’s trusted family pharmacy.',
  template: { name: 'index', suffix: null, directory: null },
  request: { design_mode: false, page_type: 'index', host: 'mock.myshopify.com', origin: 'https://mock.myshopify.com', path: '/', locale: { iso_code: 'en' } },
  routes: {
    root_url: '/', cart_url: '/cart', cart_add_url: '/cart/add', cart_change_url: '/cart/change',
    collections_url: '/collections', all_products_collection_url: '/collections/all', search_url: '/search',
    account_url: '/account', account_login_url: '/account/login', account_logout_url: '/account/logout',
    account_register_url: '/account/register', account_addresses_url: '/account/addresses',
    account_recover_url: '/account/recover', predictive_search_url: '/search/suggest',
    product_recommendations_url: '/recommendations/products',
  },
  // On a real store this is where window.Shopify comes from, so the consent
  // shim belongs here rather than in the theme. See setup/preview_shopify_shim.js.
  content_for_header: '<!-- content_for_header -->\n<script>'
    + readFileSync(join(PROJECT, 'setup/preview_shopify_shim.js'), 'utf8')
    + '</script>',
  content_for_additional_checkout_buttons:
    '<div data-mock-express style="height:48px;border-radius:10px;border:1.5px dashed #b9c2b3;' +
    'display:flex;align-items:center;justify-content:center;font-size:12.5px;font-weight:700;' +
    'letter-spacing:.06em;text-transform:uppercase;color:#697262;background:#f4f6f1;">' +
    'Express checkout buttons &middot; live store only</div>',
  powered_by_link: '<a href="https://shopify.com">Shopify</a>',
  additional_checkout_buttons: false, scripts: [],
  settings: {}, // filled from settings_schema defaults
};

// {% render %} isolates scope in liquidjs, so snippets cannot see page globals
// unless they are engine globals. Shopify exposes these everywhere.
globals.additional_checkout_buttons = true;
engine.options.globals = globals;

/* settings_schema.json defaults -> settings */
const schemaJson = JSON.parse(readFileSync(join(THEME, 'config/settings_schema.json'), 'utf8'));
for (const group of schemaJson) {
  for (const s of group.settings || []) if (s.id) globals.settings[s.id] = s.default ?? '';
}
// Saved settings win over schema defaults, as they do on a real store — otherwise
// the preview shows defaults the merchant has already changed.
if (existsSync(join(THEME, 'config/settings_data.json'))) {
  const saved = JSON.parse(readFileSync(join(THEME, 'config/settings_data.json'), 'utf8'));
  Object.assign(globals.settings, saved.current || {});
}

/* ---------- section rendering ---------- */
const sectionSource = (type) => readFileSync(join(THEME, 'sections', `${type}.liquid`), 'utf8');
const schemaOf = (src) => {
  const m = src.match(/{%-?\s*schema\s*-?%}([\s\S]*?){%-?\s*endschema\s*-?%}/);
  if (!m) return {};
  try { return JSON.parse(m[1]); } catch { return {}; }
};
const defaultsFrom = (defs = []) => Object.fromEntries((defs).filter((s) => s.id).map((s) => [s.id, s.default ?? '']));

async function renderSection(type, settings, blocksSpec, extraGlobals = {}) {
  const src = sectionSource(type);
  const schema = schemaOf(src);
  const merged = { ...defaultsFrom(schema.settings), ...settings };

  let blocks = [];
  const blockDefs = schema.blocks || [];
  const defFor = (t) => blockDefs.find((b) => b.type === t) || { settings: [] };
  if (blocksSpec && blocksSpec.order && blocksSpec.order.length) {
    blocks = blocksSpec.order.map((id) => {
      const b = blocksSpec.blocks[id];
      return { id, type: b.type, settings: { ...defaultsFrom(defFor(b.type).settings), ...(b.settings || {}) }, shopify_attributes: '' };
    });
  } else if (schema.presets && schema.presets[0] && schema.presets[0].blocks) {
    blocks = schema.presets[0].blocks.map((b, i) => ({
      id: `b${i}`, type: b.type, settings: { ...defaultsFrom(defFor(b.type).settings), ...(b.settings || {}) }, shopify_attributes: '',
    }));
  } else if (blockDefs.length) {
    blocks = blockDefs.filter((d) => d.type !== '@app').map((d, i) => ({
      id: `b${i}`, type: d.type, settings: defaultsFrom(d.settings), shopify_attributes: '',
    }));
  }

  const section = { id: `sec-${type}`, settings: merged, blocks, blocks_count: blocks.length, index: 1, location: 'template' };
  return engine.parseAndRender(src, { ...globals, ...extraGlobals, section });
}

// request.page_type drives page-type-specific markup (JSON-LD, canonical hints).
// Without this every preview page claimed to be the homepage, and anything
// branching on page type silently rendered the wrong branch — or nothing.
const pageTypeOf = (name) => {
  if (name.startsWith('customers/')) return name;
  if (name.startsWith('collection')) return 'collection';
  if (name.startsWith('page')) return 'page';
  if (name === 'index') return 'index';
  if (name === 'list-collections') return 'list-collections';
  if (name === 'gift_card') return 'gift_card';
  return name; // product, cart, search, blog, article, 404, password
};

async function renderTemplate(name, extraGlobals = {}) {
  extraGlobals = {
    ...extraGlobals,
    request: { ...globals.request, page_type: pageTypeOf(name) },
    template: { name: pageTypeOf(name), suffix: null, directory: null },
  };
  // page.url/handle are real on Shopify and used in canonical + structured data.
  if (name.startsWith('page.')) {
    const handle = name.slice('page.'.length);
    extraGlobals.page = { ...globals.page, handle, url: `/pages/${handle}` };
  }

  // {% render %} isolates scope in liquidjs, so a snippet sees engine globals and
  // NOT the per-template values passed down the render tree. On Shopify these are
  // true globals, visible everywhere. Mirror that by swapping them in for the
  // duration of this template, then putting them back — otherwise anything a
  // snippet branches on (request.page_type, collection) is stuck at its default
  // and the wrong branch renders silently.
  const savedGlobals = {};
  for (const k of Object.keys(extraGlobals)) savedGlobals[k] = globals[k];
  Object.assign(globals, extraGlobals);
  try {
    return await renderTemplateInner(name, extraGlobals);
  } finally {
    Object.assign(globals, savedGlobals);
  }
}

async function renderTemplateInner(name, extraGlobals) {
  const jsonPath = join(THEME, 'templates', `${name}.json`);
  const liquidPath = join(THEME, 'templates', `${name}.liquid`);
  let body = '';
  if (existsSync(jsonPath)) {
    const tpl = JSON.parse(readFileSync(jsonPath, 'utf8'));
    for (const id of tpl.order) {
      const s = tpl.sections[id];
      body += await renderSection(s.type, s.settings || {}, { order: s.block_order || [], blocks: s.blocks || {} }, extraGlobals);
    }
  } else if (existsSync(liquidPath)) {
    body = await engine.parseAndRender(readFileSync(liquidPath, 'utf8'), { ...globals, ...extraGlobals });
  } else return null;

  const TITLES = {
    index: 'Home', product: 'Product', collection: 'Collection', cart: 'Cart',
    search: 'Search', blog: 'Health Hub', article: 'Article', page: 'Page',
    'list-collections': 'Collections', '404': 'Page not found', password: 'Opening soon',
    gift_card: 'Gift card',
  };
  const key = name.replace('customers/', '');
  const pretty = TITLES[key] || key.replace(/^(collection|page)\./, '').replace(/[-_]/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
  extraGlobals = { ...extraGlobals, page_title: extraGlobals.page_title || pretty };

  const layoutName = name === 'password' ? 'password' : 'theme';
  const layout = readFileSync(join(THEME, 'layout', `${layoutName}.liquid`), 'utf8');
  return engine.parseAndRender(layout, { ...globals, ...extraGlobals, content_for_layout: body });
}

/* ---------- main ---------- */
const outDir = (() => {
  const i = process.argv.indexOf('--html-out');
  return i > -1 ? process.argv[i + 1] : join(PROJECT, 'preview');
})();
mkdirSync(outDir, { recursive: true });

const templateNames = readdirSync(join(THEME, 'templates'))
  .filter((f) => f.endsWith('.json') || f.endsWith('.liquid'))
  .map((f) => f.replace(/\.(json|liquid)$/, ''));
const customerNames = existsSync(join(THEME, 'templates/customers'))
  ? readdirSync(join(THEME, 'templates/customers')).map((f) => `customers/${f.replace(/\.(json|liquid)$/, '')}`)
  : [];

let ok = 0, fail = 0;
const failures = [];
for (const name of [...templateNames, ...customerNames]) {
  try {
    const html = await renderTemplate(name);
    if (html == null) continue;
    const file = name.replace('/', '_') + '.html';
    writeFileSync(join(outDir, file), html);
    ok++;
  } catch (e) {
    fail++; failures.push(`${name}: ${String(e.message).slice(0, 140)}`);
  }
}
console.log(`${ok}/${ok + fail} templates render clean`);

// A second product page for the sold-out fixture. The buy box takes a different
// path when a variant is unavailable — disabled button plus the back-in-stock
// capture — and with only one product page rendered, that path shipped unseen.
{
  const oos = products.find((p) => p.available === false);
  if (oos) {
    const saved = { product: globals.product, request: globals.request };
    globals.product = oos;
    globals.request = { ...globals.request, page_type: 'product' };
    try {
      writeFileSync(join(outDir, 'product.oos.html'), await renderTemplate('product'));
      console.log(`sold-out product page: ${oos.handle}`);
    } finally {
      Object.assign(globals, saved);
    }
  }
}
failures.forEach((f) => console.log('  FAIL ' + f));

/* ---------- AJAX endpoints ----------
   Predictive search and cart recommendations are live-store endpoints: Shopify
   renders a section for each request. Pre-rendering their output for the mock
   catalogue lets serve_preview.py answer those requests locally, so the panel,
   the debounce, the keyboard handling and the restricted-product filtering can
   be exercised for real instead of only on a dev store. */
if (process.argv.includes('--endpoints')) {
  const slug = (t) => t.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  const matches = (p, q) => [p.title, p.vendor, p.type].join(' ').toLowerCase().includes(q);

  const suggestDir = join(outDir, '_suggest');
  mkdirSync(suggestDir, { recursive: true });
  // Terms chosen to cover: a plain hit, a vendor hit, a hit whose top result is
  // the restricted fixture, and a term with no matches at all.
  const TERMS = ['vit', 'vitamin', 'nurofen', 'cerave', 'skin', 'revive', 'baby', 'sudocrem', 'pain', 'allergy'];
  let sok = 0;
  for (const term of TERMS) {
    const q = term.toLowerCase();
    const hits = products.filter((p) => matches(p, q)).slice(0, 6);
    const colls = collectionsList.filter((c) => c.title.toLowerCase().includes(q)).slice(0, 3)
      .map((c) => ({ title: c.title, handle: c.handle, url: `/collections/${c.handle}` }));
    const html = await renderSection('predictive-search', {}, {}, {
      predictive_search: {
        performed: true, terms: term,
        resources: {
          products: hits, collections: colls, pages: [], articles: [],
          queries: hits.slice(0, 2).map((p) => ({
            text: p.title, styled_text: p.title.replace(new RegExp(`(${term})`, 'i'), '<b>$1</b>'),
            url: `/search?q=${encodeURIComponent(p.title)}`,
          })),
        },
      },
    });
    writeFileSync(join(suggestDir, `${slug(term)}.html`), html);
    sok++;
  }
  // Fallback for any term the mock catalogue does not cover.
  writeFileSync(join(suggestDir, '_none.html'), await renderSection('predictive-search', {}, {}, {
    predictive_search: { performed: true, terms: 'zzz', resources: { products: [], collections: [], queries: [], pages: [], articles: [] } },
  }));

  const recsDir = join(outDir, '_recs');
  mkdirSync(recsDir, { recursive: true });
  let rok = 0;
  for (const anchorProduct of products) {
    const html = await renderSection('cart-recommendations', {}, {}, {
      recommendations: {
        performed: true,
        products: products.filter((p) => p.id !== anchorProduct.id),
        products_count: products.length - 1,
      },
    });
    writeFileSync(join(recsDir, `${anchorProduct.id}.html`), html);
    rok++;
  }
  console.log(`${sok} predictive-search responses + ${rok} recommendation responses rendered`);
}

if (process.argv.includes('--categories')) {
  const catDir = join(outDir, 'categories');
  mkdirSync(catDir, { recursive: true });
  let cok = 0, cfail = 0;
  for (const c of collectionsList) {
    const tplName = existsSync(join(THEME, 'templates', `collection.${c.handle}.json`)) ? `collection.${c.handle}` : 'collection';
    try {
      const html = await renderTemplate(tplName, {
        collection: { ...mockCollection, handle: c.handle, title: c.title, url: `/collections/${c.handle}`,
          description: c.description_html || '', image: null, featured_image: null },
      });
      writeFileSync(join(catDir, `${c.handle}.html`), html);
      cok++;
    } catch (e) { cfail++; if (cfail < 4) console.log(`  CAT FAIL ${c.handle}: ${String(e.message).slice(0, 120)}`); }
  }
  console.log(`categories: ${cok} ok, ${cfail} failed of ${collectionsList.length}`);
}
