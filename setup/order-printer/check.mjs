// Renders medicine-record.liquid against three mock orders and checks what the
// pharmacist would see. liquidjs, not Order Printer: it proves the logic, not
// Shopify's objects. The first real print on a test order proves those.
import { Liquid } from 'liquidjs';
import { readFileSync } from 'node:fs';
import assert from 'node:assert/strict';

const tpl = readFileSync(new URL('./medicine-record.liquid', import.meta.url), 'utf8');
const engine = new Liquid();

const nurofen = { title: 'Nurofen Plus 24 Tablets', quantity: 2, sku: 'NP24', variant: { title: 'Default Title' },
  product: { title: 'Nurofen Plus 24 Tablets', tags: ['Pain Relief', 'Pharmacist-Review'] } };
const vitamin = { title: 'Vitamin D3', quantity: 1, sku: 'VD3', variant: { title: '60' },
  product: { title: 'Vitamin D3', tags: ['Vitamins'] } };
const custom = { title: 'Gift hamper', quantity: 1, sku: '', product: null };
const order = (line_items, attributes = {}) => ({
  name: '#1042', created_at: '2026-09-28T10:15:00Z', email: 'a@example.com', note: '',
  customer: { name: 'A Customer', orders_count: 3 }, shipping_address: { address1: '1 Main St', city: 'Clonmel' },
  attributes, line_items,
});
const render = (o) => engine.parseAndRender(tpl, { order: o, shop: { name: "McCormack's Pharmacy" } });
const medRows = (html) => (html.split('Medicine lines')[1].split('</table>')[0].match(/<tr><td>/g) || []).length;

let html = await render(order([nurofen, vitamin], { 'Over 18 and will follow the leaflet': 'Yes' }));
assert.match(html, /Ticked: &ldquo;I confirm/);
assert.doesNotMatch(html, /NOT GIVEN/);
assert.equal(medRows(html), 1, 'one medicine line; the tag matches case-insensitively');
assert.match(html, /<strong>2<\/strong>/, 'medicine quantity shown');
assert.match(html, /Other items in the order[\s\S]*Vitamin D3/);
assert.match(html, /3, including this one/);

html = await render(order([nurofen, custom]));
assert.match(html, /NOT GIVEN/, 'missing declaration is flagged');
assert.match(html, /Gift hamper <strong>\(custom item/, 'custom item flagged');

html = await render(order([vitamin]));
assert.match(html, /no line tagged pharmacist-review/);
assert.equal(medRows(html), 0);

console.log('order printer template: 3 orders, all checks passed');
