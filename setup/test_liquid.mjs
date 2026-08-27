/* Unit checks for the two snippets whose logic is a correctness rule rather
   than markup, and whose wrong branch fails silently:

     absolute-url       — a relative URL in JSON-LD invalidates the rich result
     product-restricted — a missed match puts a pharmacist-only medicine behind
                          a one-click add

   Both are pure: input in, string out. The full preview render cannot cover
   them, because the mock catalogue only ever produces one of the three URL
   shapes and Shopify's own //cdn form never appears locally.

   Run: npm test
*/
import assert from 'node:assert/strict';
import { Liquid } from 'liquidjs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const THEME = join(dirname(dirname(fileURLToPath(import.meta.url))), 'shopify-theme');
const engine = new Liquid({ root: join(THEME, 'snippets'), extname: '.liquid' });

const SHOP = { name: "McCormack's Pharmacy", secure_url: 'https://mccormacks.ie', url: 'https://mccormacks.ie' };
const render = (snippet, scope) =>
  engine.renderFileSync(snippet, { shop: SHOP, ...scope }).trim();

let passed = 0;
const check = (name, actual, expected) => {
  assert.equal(actual, expected, `${name}\n  expected: ${expected}\n  actual:   ${actual}`);
  passed++;
};

/* ---------- absolute-url ---------- */
check('protocol-relative CDN URL gains a scheme',
  render('absolute-url', { src: '//cdn.shopify.com/s/files/1/x.jpg?width=1200' }),
  'https://cdn.shopify.com/s/files/1/x.jpg?width=1200');

check('already-absolute URL is left alone',
  render('absolute-url', { src: 'https://cdn.shopify.com/s/files/1/x.jpg' }),
  'https://cdn.shopify.com/s/files/1/x.jpg');

check('root-relative URL gets the shop origin',
  render('absolute-url', { src: '/assets/logo.png' }),
  'https://mccormacks.ie/assets/logo.png');

check('explicit base overrides the shop URL',
  render('absolute-url', { src: '/assets/logo.png', base: 'https://example.test' }),
  'https://example.test/assets/logo.png');

/* ---------- product-restricted ---------- */
const gate = (tags, setting = 'pharmacist-only') =>
  render('product-restricted', { product: { tags }, settings: { restricted_tag: setting } });

check('exact tag match is restricted', gate(['pharmacist-only']), 'true');
check('untagged product is not restricted', gate(['vitamins', 'bestseller']), '');
check('no tags at all is not restricted', gate([]), '');

// A merchant capitalising the tag in admin must not silently open the gate.
check('capitalised tag still matches', gate(['Pharmacist-Only']), 'true');
check('mixed case in the setting still matches', gate(['pharmacist-only'], 'Pharmacist-Only'), 'true');

// A substring must not close the gate on an unrelated product.
check('tag containing the gate tag does not match', gate(['pharmacist-only-note']), '');
check('gate tag as a prefix of another tag does not match', gate(['pharmacist-onlyish']), '');

// Clearing the setting disables the check, as the setting's help text promises.
check('blank setting disables the gate', gate(['pharmacist-only'], ''), '');


/* ---------- store-hours ---------- */
const WEEK = [
  'Mon|09:00-18:30', 'Tue|09:00-18:30', 'Wed|09:00-18:30', 'Thu|09:00-18:30',
  'Fri|09:00-18:30', 'Sat|09:00-18:00', 'Sun|closed',
].join('\n');

const hours = (src, mode) => render('store-hours', { hours: src, mode });

check('consecutive identical days group, times render 12-hour',
  hours(WEEK, 'rows'),
  'Mon–Fri~9.00am – 6.30pm|Saturday~9.00am – 6.00pm|Sunday~Closed|');

check('a mid-week outlier splits the group',
  hours(['Mon|09:15-18:15', 'Tue|09:15-18:15', 'Wed|09:15-18:15', 'Thu|09:15-18:15',
         'Fri|09:15-18:45', 'Sat|09:15-18:15', 'Sun|closed'].join('\n'), 'rows'),
  'Mon–Thu~9.15am – 6.15pm|Friday~9.15am – 6.45pm|Saturday~9.15am – 6.15pm|Sunday~Closed|');

check('a lunch closure renders both ranges',
  hours('Mon|09:00-13:00,14:00-18:00\nTue|closed\nWed|closed\nThu|closed\nFri|closed\nSat|closed\nSun|closed', 'rows'),
  'Monday~9.00am – 1.00pm, 2.00pm – 6.00pm|Tue–Sun~Closed|');

check('noon and midnight do not become 0',
  hours('Mon|00:00-12:00\nTue|closed\nWed|closed\nThu|closed\nFri|closed\nSat|closed\nSun|closed', 'rows'),
  'Monday~12.00am – 12.00pm|Tue–Sun~Closed|');

// A missing or malformed day must read as closed, never as open.
check('a missing day is closed, and the week stays seven long',
  hours('Mon|09:00-17:00', 'rows'),
  'Monday~9.00am – 5.00pm|Tue–Sun~Closed|');

check('an unparseable range is closed, not open',
  hours('Mon|whenever\nTue|closed\nWed|closed\nThu|closed\nFri|closed\nSat|closed\nSun|closed', 'schema'),
  '');

check('schema emits one entry per open day',
  hours(WEEK, 'schema'),
  ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'].map(
    (d) => `{"@type":"OpeningHoursSpecification","dayOfWeek":"https://schema.org/${d}","opens":"09:00","closes":"18:30"}`
  ).join(',') + ',{"@type":"OpeningHoursSpecification","dayOfWeek":"https://schema.org/Saturday","opens":"09:00","closes":"18:00"}');

check('schema emits two entries for a split day',
  hours('Mon|09:00-13:00,14:00-18:00\nTue|closed\nWed|closed\nThu|closed\nFri|closed\nSat|closed\nSun|closed', 'schema'),
  '{"@type":"OpeningHoursSpecification","dayOfWeek":"https://schema.org/Monday","opens":"09:00","closes":"13:00"},'
  + '{"@type":"OpeningHoursSpecification","dayOfWeek":"https://schema.org/Monday","opens":"14:00","closes":"18:00"}');

check('a fully closed week emits no schema entries', hours('', 'schema'), '');


/* ---------- buy-assurance ----------
   Two of its lines are gated on data the local preview cannot produce: a
   dispatch cutoff nobody has confirmed yet, and pickup locations that only
   exist once Shopify local pickup is switched on. Both gates fail closed, so a
   passing preview proves nothing about them either way. */
engine.registerFilter('asset_url', (v) => `/assets/${v}`);

const assurance = (scope) => render('buy-assurance', { settings: {}, ...scope });
const pickup = (names) => ({
  store_availabilities: names.map((n) => ({ available: true, location: { name: n } })),
});

check('no dispatch line until a cutoff is set',
  assurance({}).includes('same-day dispatch'), false);
check('dispatch line appears once a cutoff is set',
  assurance({ settings: { dispatch_cutoff: '3pm' } }).includes('Order before'), true);
check('dispatch days default when not set',
  assurance({ settings: { dispatch_cutoff: '3pm' } }).includes('Monday to Friday'), true);
check('dispatch days are overridable',
  assurance({ settings: { dispatch_cutoff: '3pm', dispatch_days: 'Monday to Saturday' } })
    .includes('Monday to Saturday'), true);

check('no Click & Collect without pickup locations',
  assurance({ variant: { store_availabilities: [] } }).includes('Click &amp; Collect'), false);
check('no Click & Collect when the variant has no availability data at all',
  assurance({ variant: {} }).includes('Click &amp; Collect'), false);
check('one pickup location is named',
  assurance({ variant: pickup(['Clonmel']) }).includes('Click &amp; Collect</strong> from\n        Clonmel'), true);
check('several pickup locations are counted, not listed',
  assurance({ variant: pickup(['Clonmel', 'Newbridge', 'Tullamore']) }).includes('3 of our stores'), true);
// A location Shopify reports as unavailable must not be counted as collectable.
check('unavailable pickup locations are excluded from the count',
  assurance({ variant: { store_availabilities: [
    { available: true, location: { name: 'Clonmel' } },
    { available: false, location: { name: 'Belmullet' } },
  ] } }).includes('Click &amp; Collect</strong> from\n        Clonmel'), true);

check('PSI registration is always shown',
  assurance({}).includes('/pages/internet-supply-pharmacy'), true);
check('the PSI mark is on the product page but not the cart',
  [assurance({}).includes('psi-logo'), assurance({ compact: true }).includes('psi-logo')].join(),
  'true,false');

/* ---------- structured-data: ItemList and SearchAction ----------
   Both must stay silent when there is nothing real to describe. The preview
   cannot cover the empty cases: every mock collection has the same 10 products,
   so the "collection with no products" branch renders nowhere. */

const ld = (scope) => {
  const out = engine.renderFileSync('structured-data', {
    shop: SHOP, cart: { currency: { iso_code: 'EUR' } },
    routes: { search_url: '/search' }, ...scope,
  });
  return out;
};
const parseLd = (html, type) => {
  const blocks = [...html.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)]
    .map((m) => m[1]);
  const hit = blocks.find((b) => b.includes(`"${type}"`));
  return hit ? JSON.parse(hit) : null;   // throws on malformed JSON, which is the point
};

const COLLECTION = {
  title: 'Vitamins', url: '/collections/vitamins', handle: 'vitamins',
  products: [
    { title: 'Vitamin D3 1000IU', url: '/products/vitamin-d3-1000iu' },
    { title: 'Magnesium "high strength" 60s', url: '/products/magnesium-60s' },
  ],
};

const listHtml = ld({ request: { page_type: 'collection' }, collection: COLLECTION });
const list = parseLd(listHtml, 'ItemList');
check('ItemList is emitted on a collection that has products', list !== null, true);
check('ItemList counts the products on the page', list.numberOfItems, 2);
check('ItemList positions start at 1 and increment',
  list.itemListElement.map((i) => i.position).join(), '1,2');
check('ItemList URLs are absolute',
  list.itemListElement.every((i) => i.url.startsWith('https://')), true);
check('a quoted product title does not break the JSON',
  list.itemListElement[1].name, 'Magnesium "high strength" 60s');
check('ItemList carries no nested Product node',
  listHtml.includes('"@type": "Product"'), false);

check('no ItemList when the collection has no products',
  parseLd(ld({ request: { page_type: 'collection' },
               collection: { ...COLLECTION, products: [] } }), 'ItemList'), null);

const site = parseLd(ld({ request: { page_type: 'index' } }), 'WebSite');
check('SearchAction is emitted on the homepage', site !== null, true);
check('SearchAction target is absolute and carries the placeholder',
  site.potentialAction.target.urlTemplate,
  'https://mccormacks.ie/search?q={search_term_string}');
check('SearchAction query-input matches the placeholder name',
  site.potentialAction['query-input'], 'required name=search_term_string');
check('WebSite points at the Organization node emitted by the footer',
  site.publisher['@id'], 'https://mccormacks.ie#organization');
check('SearchAction follows routes.search_url, not a hardcoded /search',
  parseLd(ld({ request: { page_type: 'index' }, routes: { search_url: '/en/search' } }), 'WebSite')
    .potentialAction.target.urlTemplate,
  'https://mccormacks.ie/en/search?q={search_term_string}');
check('no SearchAction on a collection page',
  parseLd(listHtml, 'WebSite'), null);

/* ---------- product-primary-collection ----------
   Which parent the PDP breadcrumb and the related-products fallback use. Every
   fixture below lists the LOW-ranked collection first, so a pass proves the rank
   is doing the work rather than the iteration order happening to agree. */

const primary = (handles) =>
  engine.renderFileSync('product-primary-collection',
    { product: { collections: handles.map((h) => ({ handle: h })) } }).trim();

check('a leaf beats the department it sits under',
  primary(['vitamins', 'skin-hair-nails']), 'skin-hair-nails');
check('a depth-3 leaf beats a depth-2 leaf',
  primary(['cleanser', 'facial-skincare'].reverse()), 'cleanser');
check('a taxonomy group beats a brand',
  primary(['nurofen', 'pain-relief']), 'pain-relief');
check('a brand still wins over nothing else',
  primary(['nurofen']), 'nurofen');
check('an unknown handle loses to any ranked collection',
  primary(['not-a-real-collection', 'pain-relief']), 'pain-relief');
check('an unknown handle is still returned when it is all there is',
  primary(['not-a-real-collection']), 'not-a-real-collection');
check('no collections returns nothing', primary([]), '');
check('ties keep the earlier collection, so the result is stable',
  primary(['pain-relief', 'stomach-gastrointestinal']), 'pain-relief');

console.log(`${passed}/${passed} liquid snippet checks passed`);
