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
console.log(`\n${counts.ERROR} errors, ${counts.WARNING} warnings, ${counts.INFO} info`);
process.exit(counts.ERROR > 0 ? 1 : 0);
