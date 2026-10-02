// Renders medicine-record.liquid against mock orders and checks what the
// pharmacist would see. liquidjs, not Order Printer: it proves the logic, not
// Shopify's objects. Real prints prove those: #1024 (2 Oct 2026) showed
// order.attributes, customer.orders_count and line_item.product.tags all work.
import { Liquid } from 'liquidjs';
import { readFileSync } from 'node:fs';
import assert from 'node:assert/strict';

const tpl = readFileSync(new URL('./medicine-record.liquid', import.meta.url), 'utf8');
const engine = new Liquid();

const nurofen = { title: 'Nurofen Plus 24 Tablets', quantity: 2, sku: 'NP24', variant: { title: 'Default Title' },
  product: { title: 'Nurofen Plus 24 Tablets', tags: ['Pain Relief', 'Pharmacist-Review'] } };
const savlon = { title: 'Savlon Antiseptic Cream', quantity: 1, sku: '', variant: { title: '30g' },
  product: { title: 'Savlon Antiseptic Cream', tags: ['pharmacist-review'] } };
const vitamin = { title: 'Vitamin D3', quantity: 1, sku: 'VD3', variant: { title: '60' },
  product: { title: 'Vitamin D3', tags: ['Vitamins'] } };
const custom = { title: 'Gift hamper', quantity: 1, sku: '', product: null };
// Properties as the theme writes them (snippets/pharmacy-questionnaire.liquid).
const answered = { ...nurofen, properties: {
  '1. Are you over 18?': 'Yes',
  '2. Who is it for?': 'Myself; My partner',
  _questionnaire: 'Painkillers', _questionnaire_version: 'painkillers-2026-10-01',
  _answered_at: '2026-10-01T20:05:00Z', _pharmacist_review: 'required' } };
const order = (line_items, attributes = {}, extra = {}) => ({
  name: '#1042', created_at: '2026-09-28T10:15:00Z', email: 'a@example.com', note: '',
  customer: { name: 'A Customer', orders_count: 3 },
  shipping_address: { name: 'A Customer', address1: '1 Main St', city: 'Clonmel', zip: 'E91 X000', country: 'Ireland' },
  attributes, line_items, ...extra,
});
const yes = { 'Over 18 and will follow the leaflet': 'Yes' };
const render = (o) => engine.parseAndRender(tpl, { order: o, shop: { name: "McCormack's Pharmacy" } });
const section = (html, h) => html.split(h)[1].split('</table>')[0];
const medRows = (html) => (section(html, 'Medicine lines').match(/<tr><td>/g) || []).length;

// A medicine with a ticked declaration, and an ordinary item.
let html = await render(order([nurofen, vitamin], yes));
assert.match(html, /Ticked: &ldquo;I confirm/);
assert.doesNotMatch(html, /NOT GIVEN/);
assert.equal(medRows(html), 1, 'one medicine line; the tag matches case-insensitively');
assert.match(html, /<strong>2<\/strong>/, 'medicine quantity shown');
assert.match(html, /Other items in the order[\s\S]*Vitamin D3/);
assert.match(html, /3, including this one/);
assert.match(html, /1 Main St, Clonmel, E91 X000, Ireland</, 'address has no stray commas');
assert.match(html, /No questions answered for this line/, 'a medicine with no questionnaire says so');
assert.match(html, /Refused, medicine only/, 'mixed order offers refusing the medicine alone');

// Missing declaration, and a custom item.
html = await render(order([nurofen, custom]));
assert.match(html, /NOT GIVEN\. The customer reached checkout/, 'missing declaration is flagged');
assert.match(html, /Gift hamper <strong>\(custom item/, 'custom item flagged');

// A declaration value other than exactly "Yes" is not a tick.
for (const v of ['yes', 'true', 'No']) {
  html = await render(order([nurofen], { 'Over 18 and will follow the leaflet': v }));
  assert.match(html, new RegExp(`NOT GIVEN: the declaration reads &ldquo;${v}&rdquo;`), `declaration "${v}" flagged`);
  assert.doesNotMatch(html, /Ticked:/);
}

// No medicine: one line, no sheet; a custom item there is still called out.
html = await render(order([vitamin]));
assert.match(html, /#1042: no medicine in this order, so no PSI record is needed\./);
assert.doesNotMatch(html, /Pharmacist review|Signature|custom item/);
html = await render(order([vitamin, custom]));
assert.match(html, /It has 1 custom item: check none is a medicine/);

// Questionnaire answers print under their medicine; hidden stamps only as the footer.
html = await render(order([answered, vitamin], yes));
const meds = section(html, 'Medicine lines');
assert.match(meds, /1\. Are you over 18\?: <strong>Yes<\/strong>/);
assert.match(meds, /2\. Who is it for\?: <strong>Myself; My partner<\/strong>/);
assert.match(meds, /Questionnaire: Painkillers \(painkillers-2026-10-01\), answered 01 October 2026/);
assert.doesNotMatch(meds, /_pharmacist_review|_answered_at|required/, 'hidden stamps are not printed as answers');
assert.ok(meds.indexOf('Are you over 18') < meds.indexOf('Who is it for'), 'answers in question order');

// Two medicines: both listed, each with its own answers, whole-order refusal only.
html = await render(order([answered, savlon], yes));
assert.equal(medRows(html), 2);
assert.match(section(html, 'Medicine lines'), /Savlon[\s\S]*No SKU[\s\S]*No questions answered/, 'second medicine, blank SKU named');
assert.doesNotMatch(html, /Other items in the order/);
assert.doesNotMatch(html, /Refused, medicine only/, 'nothing to release when every line is a medicine');

// Empty fields say so rather than print blank.
html = await render(order([nurofen], yes, { email: '', customer: null, shipping_address: null }));
assert.match(html, /Customer<\/th><td>Not given/);
assert.match(html, /No email &middot; No phone on the order/);
assert.match(html, /No delivery address \(collection\)/);
assert.match(html, /No customer account\./);
html = await render(order([nurofen], yes, { customer: { name: 'A Customer', phone: '+353 52 000 0000' } }));
assert.match(html, /Not shown on this print: check the customer's page/, 'missing order count named');
assert.match(html, /a@example\.com &middot; \+353 52 000 0000/, 'falls back to the customer phone');
html = await render(order([nurofen], yes, { note: 'HELD for pharmacist review' }));
assert.match(html, /Order note<\/th><td>HELD for pharmacist review/);

// Packing slip: the hold banner, and refunded lines left off.
const slipTpl = readFileSync(new URL('./packing-slip.liquid', import.meta.url), 'utf8');
engine.registerFilter('t', (k) => k);                       // Order Printer's translations
engine.registerFilter('format_address', (a) => (a ? a.address1 || '' : ''));
const slip = (o) => engine.parseAndRender(slipTpl, { order: { order_name: o.name, ...o }, shop: { name: "McCormack's Pharmacy" } });
const BANNER = /AWAITING PHARMACIST APPROVAL/;
const items = (html) => html.split('<tbody>')[1];

html = await slip(order([nurofen, vitamin], yes, { tags: ['awaiting-pharmacist'] }));
assert.match(html, BANNER, 'held medicine order is bannered');
assert.ok(html.indexOf('AWAITING') < html.indexOf('packing_slip_template.title'), 'banner is at the top');
html = await slip(order([nurofen], yes, { tags: [] }));
assert.match(html, BANNER, 'bannered on the product tag even if Flow never tagged the order');
html = await slip(order([nurofen, vitamin], yes, { tags: ['awaiting-pharmacist', 'Pharmacist-Approved-FM'] }));
assert.doesNotMatch(html, BANNER, 'approved order is not bannered');
html = await slip(order([nurofen], yes, { tags: 'no-declaration, pharmacist-approved-fm' }));
assert.doesNotMatch(html, BANNER, 'approval found when tags come as one string');
html = await slip(order([vitamin], {}, { tags: [] }));
assert.doesNotMatch(html, BANNER, 'no medicine, no banner');
html = await slip(order([{ ...nurofen, current_quantity: 0 }, vitamin], yes, { tags: ['pharmacist-refused-fm'] }));
assert.doesNotMatch(html, BANNER, 'medicine refused on its own: rest packs without a banner');
assert.doesNotMatch(items(html), /Nurofen/, 'refunded line is not listed for packing');
assert.match(items(html), /Vitamin D3/);
html = await slip(order([{ ...nurofen, current_quantity: 1 }], yes, { tags: [] }));
assert.match(items(html), /<td style="text-align: left;">1<\/td>/, 'quantity shown is what is left after a part refund');

console.log('order printer templates: 12 records and 7 packing slips, all checks passed');
