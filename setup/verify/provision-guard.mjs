// provision.mjs must refuse the real store without --real-store. Every run here
// uses an unknown command, so nothing can reach the network even if the guard breaks.
import { spawnSync } from 'node:child_process';
import assert from 'node:assert/strict';

const run = (shop, ...args) => spawnSync('node', ['setup/provision.mjs', 'no-such-step', ...args],
  { env: { ...process.env, SHOP: shop, ADMIN_TOKEN: 'x' }, encoding: 'utf8' });

for (const shop of ['mccormackpharmacy.myshopify.com', 'www.mccormackspharmacy.ie', 'McCormackPharmacy.myshopify.com']) {
  const r = run(shop);
  assert.equal(r.status, 2, `${shop}: refused`);
  assert.match(r.stderr, /REFUSED[\s\S]*CREATES AND PUBLISHES/);
}
const dev = run('some-dev-store.myshopify.com');
assert.equal(dev.status, 1, 'a dev store passes the guard (then fails on the unknown step)');
assert.match(dev.stderr, /unknown command/);

console.log('provision guard: real store refused 3 ways, dev store allowed');
