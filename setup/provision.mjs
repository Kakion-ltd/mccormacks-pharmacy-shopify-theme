#!/usr/bin/env node
/**
 * Provision the McCormack's store from the design taxonomy.
 * Creates: category collections (smart, tag-based), navigation menus, pages, blog,
 * the product metafield definitions the product page reads, the fixture products
 * from setup/catalogue.json, and the questionnaire metaobject definitions.
 *
 * Usage:
 *   SHOP=your-store.myshopify.com ADMIN_TOKEN=shpat_xxx node provision.mjs collections
 *   node provision.mjs menus | pages | blog | metafields | products | metaobjects | all
 *
 * Token needs scopes: write_products, write_online_store_navigation, write_online_store_pages,
 * write_content, write_metaobject_definitions, write_inventory. (Product metafield
 * definitions are covered by write_products.)
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

// ---------------------------------------------------------------- products
// The ten fixture products the preview renders, so collection pages on the dev
// store are not empty. Images are pulled from the public Vercel preview. Tags carry
// the exact category titles the smart collections match on, plus the restricted
// tag on the codeine product. Idempotent by handle.
const CATALOGUE = JSON.parse(readFileSync(join(HERE, 'catalogue.json'), 'utf8'));
const IMAGE_BASE = process.env.IMAGE_BASE || 'https://mccormacks-pharmacy-shopify-theme.vercel.app/shopify-theme/assets';
const money = (cents) => (cents / 100).toFixed(2);

async function createProducts() {
  const byHandle = Object.fromEntries(collections.map((c) => [c.handle, c.title]));
  const loc = await gql(`{ locations(first: 1) { nodes { id name } } }`);
  const locationId = loc.locations.nodes[0]?.id;
  if (!locationId) throw new Error('no location found for inventory');
  let created = 0, skipped = 0;
  for (const c of CATALOGUE) {
    const handle = handleize(c.t);
    const existing = await gql(`query($q: String!) { products(first: 1, query: $q) { nodes { handle } } }`, { q: `handle:${handle}` });
    if (existing.products.nodes.length) { skipped++; continue; }
    const tags = [...(c.cols || []).map((h) => byHandle[h]).filter(Boolean), ...(c.tg || [])];
    const packs = Array.isArray(c.packs) && c.packs.length > 1 ? c.packs : null;
    const variants = (packs || [{ o: 'Default Title', p: c.p, was: c.was, oos: c.oos }]).map((pk) => ({
      optionValues: packs ? [{ optionName: c.optName, name: pk.o }] : [{ optionName: 'Title', name: 'Default Title' }],
      price: money(pk.p), compareAtPrice: pk.was ? money(pk.was) : null,
      inventoryPolicy: 'DENY',
      inventoryItem: { tracked: true },
      inventoryQuantities: [{ locationId, name: 'available', quantity: pk.oos ? 0 : 12 }],
    }));
    const input = {
      title: c.t, handle, vendor: c.v, productType: c.ty, status: 'ACTIVE', tags,
      descriptionHtml: `<p>${c.t} from ${c.v}.</p>`,
      productOptions: [{ name: packs ? c.optName : 'Title', values: (packs ? c.packs.map((p) => p.o) : ['Default Title']).map((n) => ({ name: n })) }],
      variants,
      files: [{ originalSource: `${IMAGE_BASE}/${c.img}`, contentType: 'IMAGE', alt: c.t }],
    };
    const data = await gql(
      `mutation($input: ProductSetInput!) {
        productSet(input: $input, synchronous: true) { product { id handle } userErrors { field message } }
      }`, { input });
    userErrs(data.productSet);
    created++;
    console.log(`created /products/${data.productSet.product.handle} (${variants.length} variant${variants.length > 1 ? 's' : ''}, tags: ${tags.join(', ')})`);
  }
  console.log(`products: ${created} created, ${skipped} already existed`);
}

// ---------------------------------------------------------------- metaobjects
// Definitions for the pharmacist questionnaire, per the spec: the pharmacist edits
// questions under Content > Metaobjects; a product is gated by referencing one
// questionnaire. Creating the definitions commits no copy and no questions.
const QUESTION_DEF = {
  type: 'pharmacy_question', name: 'Pharmacy question',
  displayNameKey: 'label',
  access: { admin: 'MERCHANT_READ_WRITE', storefront: 'PUBLIC_READ' },
  fieldDefinitions: [
    { key: 'label', name: 'Question', type: 'single_line_text_field', required: true },
    { key: 'kind', name: 'Kind', type: 'single_line_text_field', required: true,
      validations: [{ name: 'choices', value: JSON.stringify(['yes_no', 'choice', 'short_text', 'long_text']) }],
      description: 'yes_no, choice, short_text or long_text' },
    { key: 'options', name: 'Options', type: 'list.single_line_text_field', description: 'For choice questions only' },
    { key: 'optional', name: 'Optional', type: 'boolean', description: 'Every question is required unless ticked' },
    { key: 'blocking_answers', name: 'Blocking answers', type: 'list.single_line_text_field',
      description: 'Any of these answers stops the sale. yes or no for yes/no questions; exact option text for choice.' },
    { key: 'help', name: 'Help text', type: 'single_line_text_field' },
  ],
};
const QUESTIONNAIRE_DEF = (questionDefId) => ({
  type: 'pharmacy_questionnaire', name: 'Pharmacy questionnaire',
  displayNameKey: 'title',
  access: { admin: 'MERCHANT_READ_WRITE', storefront: 'PUBLIC_READ' },
  fieldDefinitions: [
    { key: 'title', name: 'Title', type: 'single_line_text_field', required: true },
    { key: 'intro', name: 'Intro', type: 'rich_text_field' },
    { key: 'questions', name: 'Questions', type: 'list.metaobject_reference', required: true,
      validations: [{ name: 'metaobject_definition_id', value: questionDefId }] },
    { key: 'max_quantity', name: 'Maximum quantity per order', type: 'number_integer' },
    { key: 'blocked_message', name: 'Message when a blocking answer is given', type: 'rich_text_field' },
    { key: 'version', name: 'Version', type: 'single_line_text_field', required: true,
      description: 'Bump when the questions change; recorded on every order line' },
  ],
});

async function metaobjectDefinitionId(type) {
  const d = await gql(`query($t: String!) { metaobjectDefinitionByType(type: $t) { id } }`, { t: type });
  return d.metaobjectDefinitionByType?.id || null;
}

async function createMetaobjects() {
  let qId = await metaobjectDefinitionId('pharmacy_question');
  if (qId) console.log('metaobject pharmacy_question already exists, skipping');
  else {
    const d = await gql(`mutation($def: MetaobjectDefinitionCreateInput!) {
      metaobjectDefinitionCreate(definition: $def) { metaobjectDefinition { id type } userErrors { field message } } }`, { def: QUESTION_DEF });
    userErrs(d.metaobjectDefinitionCreate);
    qId = d.metaobjectDefinitionCreate.metaobjectDefinition.id;
    console.log('created metaobject definition: pharmacy_question');
  }
  let sId = await metaobjectDefinitionId('pharmacy_questionnaire');
  if (sId) console.log('metaobject pharmacy_questionnaire already exists, skipping');
  else {
    const d = await gql(`mutation($def: MetaobjectDefinitionCreateInput!) {
      metaobjectDefinitionCreate(definition: $def) { metaobjectDefinition { id type } userErrors { field message } } }`, { def: QUESTIONNAIRE_DEF(qId) });
    userErrs(d.metaobjectDefinitionCreate);
    sId = d.metaobjectDefinitionCreate.metaobjectDefinition.id;
    console.log('created metaobject definition: pharmacy_questionnaire');
  }
  // Product metafields that point at a questionnaire and carry product-specific intro copy.
  const defs = [
    { name: 'Pharmacist questionnaire', namespace: 'pharmacy', key: 'questionnaire', ownerType: 'PRODUCT',
      type: 'metaobject_reference', validations: [{ name: 'metaobject_definition_id', value: sId }],
      description: 'Set this and the product can only be bought after answering the questionnaire.' },
    { name: 'Pharmacist notice intro', namespace: 'pharmacy', key: 'intro', ownerType: 'PRODUCT',
      type: 'rich_text_field', description: 'Product-specific wording shown above the questionnaire button.' },
  ];
  for (const def of defs) {
    const existing = await gql(
      `query($ns: String!, $key: String!) { metafieldDefinitions(first: 1, namespace: $ns, key: $key, ownerType: PRODUCT) { nodes { id } } }`,
      { ns: def.namespace, key: def.key });
    if (existing.metafieldDefinitions.nodes.length) { console.log(`metafield ${def.namespace}.${def.key} already exists, skipping`); continue; }
    const data = await gql(
      `mutation($definition: MetafieldDefinitionInput!) {
        metafieldDefinitionCreate(definition: $definition) { createdDefinition { id key } userErrors { field message } } }`,
      { definition: { ...def, access: { admin: 'MERCHANT_READ_WRITE', storefront: 'PUBLIC_READ' } } });
    userErrs(data.metafieldDefinitionCreate);
    console.log('created metafield:', `${def.namespace}.${def.key}`);
  }
}

// ---------------------------------------------------------------- main
const cmd = process.argv[2] || 'all';
const steps = { collections: createCollections, menus: createMenus, pages: createPages, blog: createBlog, metafields: createMetafields, products: createProducts, metaobjects: createMetaobjects };
try {
  if (cmd === 'all') {
    for (const fn of Object.values(steps)) await fn();
  } else if (steps[cmd]) {
    await steps[cmd]();
  } else {
    console.error(`unknown command: ${cmd} (use collections|menus|pages|blog|metafields|products|metaobjects|all)`);
    process.exit(1);
  }
} catch (e) {
  console.error('FAILED:', e.message);
  process.exit(1);
}
