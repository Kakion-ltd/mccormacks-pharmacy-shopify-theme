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
import { readdirSync, readFileSync, statSync } from 'node:fs';
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
counts.ERROR += uploadErrors;
console.log(`\n${counts.ERROR} errors, ${counts.WARNING} warnings, ${counts.INFO} info`);
process.exit(counts.ERROR > 0 ? 1 : 0);
