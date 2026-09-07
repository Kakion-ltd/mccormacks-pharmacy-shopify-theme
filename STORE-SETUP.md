# Store setup checklist — Shopify admin

Everything the theme expects to exist in the store's admin content. The
theme ships templates only; none of these are created by installing it.
Work top to bottom — each section only depends on the ones above it.
Handles must match exactly: Shopify generates a handle from the title, so
where the auto-handle differs from the required one, edit it under
**Edit website SEO → URL and handle** before saving.

## 1. Pages (Online Store → Pages)

For each: create the page, set the handle, then under **Theme template**
pick the listed template. Page body content lives in the theme sections,
so the admin page body can stay empty unless noted.

| # | Title to enter | Handle (must be exactly) | Template to assign |
|---|---|---|---|
| 1 | About Us | `about-us` | page.about-us |
| 2 | Brands | `brands` | page.brands |
| 3 | Careers | `careers` | page.careers |
| 4 | Click & Collect | `click-and-collect` | page.click-and-collect |
| 5 | Contact Us | `contact-us` | page.contact-us |
| 6 | Cookie Policy | `cookie-policy` | page.cookie-policy |
| 7 | Gift Vouchers | `gift-vouchers` | page.gift-vouchers |
| 8 | In-Store Services | `in-store-services` | page.in-store-services |
| 9 | Internet Supply Pharmacy | `internet-supply-pharmacy` | page.internet-supply-pharmacy |
| 10 | Loyalty Rewards Club | `loyalty-rewards-club` | page.loyalty-rewards-club |
| 11 | Prescriptions | `prescriptions` | page.prescriptions |
| 12 | Privacy Policy | `privacy-policy` | page.privacy-policy |
| 13 | Returns | `returns` | page.returns |
| 14 | Shipping | `shipping` | page.shipping |
| 15 | Store Locator | `store-locator` | page.store-locator |
| 16 | Terms & Conditions | `terms-and-conditions` | page.terms-and-conditions |
| 17 | Wishlist | `wishlist` | page.wishlist |
| 18 | Withdraw From Contract | `withdraw-from-contract` | page.withdraw-from-contract |

Watch the handles on 4, 9 and 16: titles with "&" or extra words
auto-handle differently (`click-collect`, `terms-conditions`), so check
each against the table before saving.

## 2. Collections (Products → Collections)

The three merchandising collections linked from the footer and homepage.
Create as manual or automated collections as preferred; the handle and
template are what the theme needs.

| # | Title | Handle | Template to assign |
|---|---|---|---|
| 1 | New In | `new-in` | collection.new-in |
| 2 | Bundles | `bundles` | collection.bundles |
| 3 | Sale | `sale` | collection.sale |

The full category tree (Medicines & Health, Vitamins, Skincare, and ~290
subcategories) is a separate import job driven by `setup/collections.json`
and `setup/taxonomy.json`, not a hand-created list — do not attempt it
from this checklist. The department templates
(collection.medicines-health, collection.beauty, etc.) attach to those
collections by handle the same way once they exist.

## 3. Blog (Online Store → Blog posts → Manage blogs)

| Title | Handle | Template |
|---|---|---|
| Health Hub | `health-hub` | blog (default — no assignment needed) |

The footer's Blog link and the article pages depend on this exact handle.

## 4. Navigation menus (Online Store → Navigation)

Four menus for the footer link columns. The **handle** is what the theme
reads; check it under the menu's title after saving. Until a menu exists,
its footer column shows the theme's built-in links, so nothing breaks if
this step lands last.

**Menu 1 — title: Footer Shop, handle `footer-shop`**
- All Brands → `/pages/brands`
- New In → `/collections/new-in`
- Bundles → `/collections/bundles`
- Gift Vouchers → `/pages/gift-vouchers`
- Sale → `/collections/sale`

**Menu 2 — title: Footer Customer Care, handle `footer-customer-care`**
- About Us → `/pages/about-us`
- Contact Us → `/pages/contact-us`
- Loyalty Rewards Club → `/pages/loyalty-rewards-club`
- Blog → `/blogs/health-hub`

**Menu 3 — title: Footer Shipping Returns, handle `footer-shipping-returns`**
- Shipping & Free Delivery → `/pages/shipping`
- Returns & Refunds → `/pages/returns`
- Click & Collect → `/pages/click-and-collect`

**Menu 4 — title: Footer Policies, handle `footer-policies`**
- Terms & Conditions → `/pages/terms-and-conditions`
- Privacy Policy → `/pages/privacy-policy`
- Cookie Policy → `/pages/cookie-policy`
- Registered Internet Supply Pharmacy → `/pages/internet-supply-pharmacy`
- Withdraw From Contract → `/pages/withdraw-from-contract`

The header and mega menu need **no** navigation setup — they are generated
from the theme's taxonomy, and the Sale/Brands promo links are theme
editor blocks on the header section.

## Not on this list, deliberately

- Product and category-collection import (`setup/` carries the data files).
- Theme settings (logo upload, colours, phone/email, trust bar messages) —
  all optional, editable any time under Theme settings; the defaults match
  the current design.
- Shopify store connection itself: the repo has no `shopify.theme.toml`
  or store credentials; theme push happens via `setup/package_theme.sh`
  and the CLI once a store exists.
