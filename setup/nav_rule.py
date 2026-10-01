"""The empty-collection nav rule, in one place.

Both nav generators (gen_mega.py, gen_category_nav.py) emit the same test, so it
is defined here rather than written out twice -- the defect at the top of
MAINTENANCE.md is one thing living in two places, and a nav rule that disagrees
with itself between the desktop panel and the mobile drawer is exactly that.

THE RULE: hide a nav link only when we positively know its collection has
nothing published to the Online Store. `all_products_count == 0` is that
positive knowledge, and a nil count is NOT zero -- so a handle the theme does
not recognise renders as it always did, and the only thing that disappears is a
category we can see is empty. Hiding on nil would blank the whole nav the first
time a handle was mistyped.

Decided at render time, not at generate time: taxonomy.json stays the complete
map of the shop, this only decides what is worth showing today, and a category
comes back by itself the moment a product is tagged into it. Nothing to
regenerate, nothing to remember.

snippets/nav-hide.liquid is the same rule for the hand-written nav -- the
header, the pill row and the footer, whose links come from store menus rather
than from the taxonomy. Change one, change the other.
setup/verify/nav-empty.py checks both.
"""

END = '{%- endunless -%}'


def live(handle):
    """Open a block that renders only while `handle` has published products."""
    return "{%%- unless collections['%s'].all_products_count == 0 -%%}" % handle


def live_any(handles):
    """Open a block that renders while ANY of `handles` has published products.

    Liquid has no `or` over a list, so the counts are summed instead; a nil
    count contributes 0 through `plus`, which is the same safe direction as
    live() -- except here it means an unknown handle alone cannot keep a group
    alive, which is why a group's own handle is always first in the list.
    """
    if len(handles) == 1:
        return live(handles[0])
    sums = ' | '.join("plus: collections['%s'].all_products_count" % h for h in handles)
    return "{%%- assign shown = 0 | %s -%%}\n{%%- unless shown == 0 -%%}" % sums
