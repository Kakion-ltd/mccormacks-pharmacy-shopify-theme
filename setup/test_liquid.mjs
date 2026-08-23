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

const SHOP = { secure_url: 'https://mccormacks.ie', url: 'https://mccormacks.ie' };
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

console.log(`${passed}/${passed} liquid snippet checks passed`);
