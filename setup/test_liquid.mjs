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

console.log(`${passed}/${passed} liquid snippet checks passed`);
