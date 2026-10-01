"""Point the footer's shipping and returns links at the Shopify policy pages.

  python3 setup/offers/footer-menu-policies.py           # dry run
  python3 setup/offers/footer-menu-policies.py --write   # writes

WHY A STORE WRITE AND NOT A THEME CHANGE. sections/footer.liquid carries a
`col_data` fallback list of column links, and another session repointed three of
them at /policies/ URLs. That change is correct and completely inert: the footer
renders `linklists[block.settings.menu]` when the menu exists, and only falls
back to `col_data` when it is empty. On this store all four footer menus exist,
so the live links come from Navigation in admin and nothing in the theme can
move them. Verified on the rendered live page before writing this.

WHAT CHANGES, AND WHAT DELIBERATELY DOES NOT.

  Shipping & Free Delivery   /pages/shipping -> /policies/shipping-policy
  Returns & Refunds          /pages/returns  -> /policies/refund-policy

Terms & Conditions and Privacy Policy are already on /policies/ and are not
touched. Cookie Policy, Withdraw From Contract and Registered Internet Supply
Pharmacy stay on /pages/: Shopify has no policy slot for them, so there is
nowhere to point them.

CONTACT US STAYS ON /pages/contact-us. /policies/contact-information is the
statutory contact details -- a block of text with registration numbers and no
form. /pages/contact-us carries the contact form, which is what someone clicking
"Contact Us" in a footer wants. Sending them to the policy text instead would be
a regression dressed as consistency. The other session agrees; its own earlier
advice said the same and its repoint contradicted it.

menuUpdate replaces the whole item list, so every item is sent back, changed or
not. Anything left out would be deleted.
"""
import json
import os
import subprocess
import sys

SHOP = 'mccormackpharmacy.myshopify.com'
DRY = '--write' not in sys.argv

# menu handle -> {item title: new url}
CHANGES = {
    'footer-shipping-returns': {
        'Shipping & Free Delivery': '/policies/shipping-policy',
        'Returns & Refunds': '/policies/refund-policy',
    },
}


def gql(q, mutate=False):
    cmd = ['npx', 'shopify', 'store', 'execute', '-s', SHOP, '-q', q]
    if mutate:
        cmd.append('--allow-mutations')
    env = {**os.environ, 'CI': '1', 'SHOPIFY_CLI_NO_ANALYTICS': '1'}
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    for n, l in enumerate(r.stdout.splitlines()):
        if l.startswith('{'):
            d = json.loads('\n'.join(r.stdout.splitlines()[n:]), strict=False)
            break
    else:
        raise SystemExit(f'query failed:\n{r.stdout}\n{r.stderr}')
    if d.get('errors'):
        raise SystemExit(json.dumps(d['errors'], indent=1))
    return d.get('data', d)


def gql_item(i):
    """One MenuItemUpdateInput literal.

    Built field by field rather than by unquoting json.dumps: `type` is a MenuItemType
    ENUM, so it must appear as `type: HTTP` and not `type: "HTTP"`, which the API
    rejects with argumentLiteralsIncompatible. Strings still go through json.dumps so
    an apostrophe or ampersand in a title cannot break the query.
    """
    parts = ['id: %s' % json.dumps(i['id']),
             'title: %s' % json.dumps(i['title']),
             'type: %s' % i['type'],          # enum literal, unquoted
             'url: %s' % json.dumps(i['url'])]
    if i.get('items'):
        parts.append('items: [%s]' % ' '.join(gql_item(c) for c in i['items']))
    return '{%s}' % ', '.join(parts)


menus = {m['handle']: m for m in gql(
    '{ menus(first: 20) { nodes { id handle title items { id title type url tags '
    'items { id title type url tags } } } } }')['menus']['nodes']}

print('footer menu policy links | %s' % ('DRY RUN' if DRY else 'WRITING'))
changed_any = False

for handle, repoint in CHANGES.items():
    menu = menus.get(handle)
    if menu is None:
        raise SystemExit(f'no menu with handle {handle}')
    unknown = set(repoint) - {i['title'] for i in menu['items']}
    if unknown:
        raise SystemExit(f'{handle}: no item titled {sorted(unknown)} -- '
                         'the menu was renamed, fix the list rather than guessing')

    items, diffs = [], []
    for i in menu['items']:
        new_url = repoint.get(i['title'], i['url'])
        if new_url != i['url']:
            diffs.append((i['title'], i['url'], new_url))
        # menuUpdate replaces the list wholesale: send every item back, nested ones too
        entry = {'id': i['id'], 'title': i['title'], 'type': i['type'], 'url': new_url}
        if i.get('items'):
            entry['items'] = [{'id': c['id'], 'title': c['title'], 'type': c['type'],
                               'url': c['url']} for c in i['items']]
        items.append(entry)

    print(f'\n  {handle} ({len(menu["items"])} items, {len(diffs)} changing)')
    for i in menu['items']:
        mark = '  ->' if i['title'] in repoint and repoint[i['title']] != i['url'] else '    '
        print(f'  {mark} {i["title"]:<38} {i["url"]}')
        if mark.strip():
            print(f'       {"":<38} becomes {repoint[i["title"]]}')
    if not diffs:
        print('    nothing to change')
        continue
    changed_any = True
    if DRY:
        continue

    m = ('mutation { menuUpdate(id: %s, title: %s, handle: %s, items: [%s]) '
         '{ menu { id handle items { title url } } userErrors { field message } } }'
         % (json.dumps(menu['id']), json.dumps(menu['title']), json.dumps(handle),
            ' '.join(gql_item(i) for i in items)))
    res = gql(m, mutate=True)['menuUpdate']
    if res.get('userErrors'):
        raise SystemExit(f'{handle} failed: {res["userErrors"]}')
    print('    written. Read back:')
    for i in res['menu']['items']:
        print(f'      {i["title"]:<38} {i["url"]}')

if DRY and changed_any:
    print('\ndry run: nothing written. Re-run with --write.')
