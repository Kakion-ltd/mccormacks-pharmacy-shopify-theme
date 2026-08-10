#!/usr/bin/env node
/**
 * Provision the McCormack's store from the design taxonomy.
 * Creates: category collections (smart, tag-based), navigation menus, pages, blog,
 * and the product metafield definitions the product page reads.
 *
 * Usage:
 *   SHOP=your-store.myshopify.com ADMIN_TOKEN=shpat_xxx node provision.mjs collections
 *   node provision.mjs menus | pages | blog | metafields | all
 *
 * Token needs scopes: write_products, write_online_store_navigation, write_online_store_pages,
 * write_content. (Product metafield definitions are covered by write_products.)
 * Idempotent: existing handles are skipped.
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const SHOP = process.env.SHOP;
const TOKEN = process.env.ADMIN_TOKEN;
const API = process.env.API_VERSION || '2025-01';
if (!SHOP || !TOKEN) {
  console.error('Set SHOP and ADMIN_TOKEN env vars.');
  process.exit(1);
}

async function gql(query, variables) {
  const res = await fetch(`https://${SHOP}/admin/api/${API}/graphql.json`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Shopify-Access-Token': TOKEN },
    body: JSON.stringify({ query, variables }),
  });
  const body = await res.json();
  if (body.errors) throw new Error(JSON.stringify(body.errors, null, 2));
  return body.data;
}

const userErrs = (payload) => {
  const errs = payload?.userErrors ?? [];
  if (errs.length) throw new Error(JSON.stringify(errs, null, 2));
};

const collections = JSON.parse(readFileSync(join(HERE, 'collections.json'), 'utf8'));
const taxonomy = JSON.parse(readFileSync(join(HERE, 'taxonomy.json'), 'utf8'));

const handleize = (s) =>
  s.normalize('NFKD').replace(/[̀-ͯ]/g, '')
    .toLowerCase().replace(/&/g, ' ').replace(/'/g, '')
    .replace(/[^a-z0-9]+/g, '-').replace(/-{2,}/g, '-').replace(/^-|-$/g, '');

// Collections with a design-specific template (templates/collection.<handle>.json)
const TEMPLATED_COLLECTIONS = new Set([
  'medicines-health', 'sale', 'new-in', 'bundles', 'hot-offers',
  'vitamins', 'beauty', 'skincare', 'toiletries', 'mother-baby', 'fragrance', 'gifting',
]);

// ---------------------------------------------------------------- collections
async function createCollections() {
  let created = 0, skipped = 0;
  for (const c of collections) {
    const existing = await gql(
      `query($h: String!) { collectionByHandle(handle: $h) { id } }`, { h: c.handle });
    if (existing.collectionByHandle) { skipped++; continue; }
    const data = await gql(
      `mutation($input: CollectionInput!) {
        collectionCreate(input: $input) { collection { id handle } userErrors { field message } }
      }`,
      {
        input: {
          title: c.title,
          handle: c.handle,
          templateSuffix: TEMPLATED_COLLECTIONS.has(c.handle) ? c.handle : null,
          descriptionHtml: c.description_html || '',
          ruleSet: {
            appliedDisjunctively: false,
            rules: [{
              column: c.level === 'brand' ? 'VENDOR' : 'TAG',
              relation: 'EQUALS',
              condition: c.title,
            }],
          },
        },
      });
    userErrs(data.collectionCreate);
    created++;
    console.log(`created /collections/${data.collectionCreate.collection.handle}`);
  }
  console.log(`collections: ${created} created, ${skipped} already existed`);
  console.log('NOTE: smart collections match products tagged with the exact category title.');
}

// ---------------------------------------------------------------- menus
async function createMenus() {
  const PAGES = { Brands: '/pages/brands', Services: '/pages/in-store-services' };
  const items = taxonomy.map((m) => {
    const url = PAGES[m.menu] || `/collections/${handleize(m.menu)}`;
    const children = [
      ...(m.groups || []).map((g) => ({
        title: g.title, type: 'HTTP', url: `/collections/${handleize(g.title)}`,
        items: g.items.map((i) => ({ title: i, type: 'HTTP', url: `/collections/${handleize(i)}` })),
      })),
      ...(m.flat || []).map((i) => ({ title: i, type: 'HTTP', url: `/collections/${handleize(i)}`, items: [] })),
    ];
    return { title: m.menu, type: 'HTTP', url, items: children };
  });

  const existing = await gql(`{ menus(first: 50) { nodes { handle } } }`);
  if (existing.menus.nodes.some((m) => m.handle === 'main-menu-mccormacks')) {
    console.log('menu main-menu-mccormacks already exists, skipping');
    return;
  }
  const data = await gql(
    `mutation($title: String!, $handle: String!, $items: [MenuItemCreateInput!]!) {
      menuCreate(title: $title, handle: $handle, items: $items) {
        menu { id handle } userErrors { field message }
      }
    }`,
    { title: "McCormack's Main Menu", handle: 'main-menu-mccormacks', items });
  userErrs(data.menuCreate);
  console.log('created menu:', data.menuCreate.menu.handle);
}

// ---------------------------------------------------------------- pages
const PAGES = [
  ['About Us', 'about-us'], ['Contact Us', 'contact-us'], ['Careers', 'careers'],
  ['Store Locator', 'store-locator'], ['In-Store Services', 'in-store-services'],
  ['Prescriptions', 'prescriptions'], ['Withdraw From Contract', 'withdraw-from-contract'],
  ['Cookie Policy', 'cookie-policy'], ['Privacy Policy', 'privacy-policy'],
  ['Terms and Conditions', 'terms-and-conditions'], ['Shipping & Free Delivery', 'shipping'],
  ['Returns & Refunds', 'returns'], ['Click & Collect', 'click-and-collect'],
  ['Registered Internet Supply Pharmacy', 'internet-supply-pharmacy'],
  ['Gift Vouchers', 'gift-vouchers'], ['Brands', 'brands'],
  ['Wishlist', 'wishlist'], ['Loyalty Rewards Club', 'loyalty-rewards-club'],
];

async function createPages() {
  let created = 0, skipped = 0;
  for (const [title, handle] of PAGES) {
    const existing = await gql(
      `query($q: String!) { pages(first: 1, query: $q) { nodes { handle } } }`,
      { q: `handle:${handle}` });
    if (existing.pages.nodes.length) { skipped++; continue; }
    const data = await gql(
      `mutation($page: PageCreateInput!) {
        pageCreate(page: $page) { page { id handle } userErrors { field message } }
      }`,
      { page: { title, handle, templateSuffix: handle, isPublished: true, body: '' } });
    userErrs(data.pageCreate);
    created++;
    console.log(`created /pages/${handle} (template page.${handle})`);
  }
  console.log(`pages: ${created} created, ${skipped} already existed`);
}

// ---------------------------------------------------------------- blog
async function createBlog() {
  const existing = await gql(`{ blogs(first: 50) { nodes { handle } } }`);
  if (existing.blogs.nodes.some((b) => b.handle === 'health-hub')) {
    console.log('blog health-hub already exists, skipping');
    return;
  }
  const data = await gql(
    `mutation($blog: BlogCreateInput!) {
      blogCreate(blog: $blog) { blog { id handle } userErrors { field message } }
    }`,
    { blog: { title: 'Health Hub', handle: 'health-hub' } });
  userErrs(data.blogCreate);
  console.log('created blog:', data.blogCreate.blog.handle);
}

// ---------------------------------------------------------------- metafields
// The product page renders Ingredients / How To Use tabs from these. Without the
// definitions they cannot be filled in from the product admin, so the tabs would
// never appear. (reviews.rating / reviews.rating_count are owned by the review app.)
const METAFIELDS = [
  {
    name: 'Ingredients', namespace: 'custom', key: 'ingredients', ownerType: 'PRODUCT',
    type: 'multi_line_text_field',
    description: 'Full ingredients list. Shown as the Ingredients tab on the product page.',
  },
  {
    name: 'How To Use', namespace: 'custom', key: 'how_to_use', ownerType: 'PRODUCT',
    type: 'multi_line_text_field',
    description: 'Directions for use. Shown as the How To Use tab on the product page.',
  },
];

async function createMetafields() {
  for (const def of METAFIELDS) {
    const existing = await gql(
      `query($ns: String!, $key: String!) {
        metafieldDefinitions(first: 1, namespace: $ns, key: $key, ownerType: PRODUCT) { nodes { id } }
      }`,
      { ns: def.namespace, key: def.key });
    if (existing.metafieldDefinitions.nodes.length) {
      console.log(`metafield ${def.namespace}.${def.key} already exists, skipping`);
      continue;
    }
    const data = await gql(
      `mutation($definition: MetafieldDefinitionInput!) {
        metafieldDefinitionCreate(definition: $definition) {
          createdDefinition { id key } userErrors { field message }
        }
      }`,
      { definition: { ...def, access: { admin: 'MERCHANT_READ_WRITE', storefront: 'PUBLIC_READ' } } });
    userErrs(data.metafieldDefinitionCreate);
    console.log('created metafield:', `${def.namespace}.${def.key}`);
  }
}

// ---------------------------------------------------------------- main
const cmd = process.argv[2] || 'all';
const steps = { collections: createCollections, menus: createMenus, pages: createPages, blog: createBlog, metafields: createMetafields };
try {
  if (cmd === 'all') {
    for (const fn of Object.values(steps)) await fn();
  } else if (steps[cmd]) {
    await steps[cmd]();
  } else {
    console.error(`unknown command: ${cmd} (use collections|menus|pages|blog|metafields|all)`);
    process.exit(1);
  }
} catch (e) {
  console.error('FAILED:', e.message);
  process.exit(1);
}
