# Handoff: McCormack's Pharmacy Website

## Overview
Full redesign/rebuild of mccormackspharmacy.ie — an Irish retail pharmacy group's Shopify storefront. Covers homepage, the Medicines & Health mega-category template, checkout flow, account area, content pages (About/Contact/Careers, policies, blog), and a statutory Withdraw From Contract page.

## About the Design Files
The files in `pages/` are **design references built in HTML** (a proprietary component template format — `{{ }}` template holes and an inline `<script type="text/x-dc">` logic block are tooling artifacts, not framework code). They show intended layout, copy, colors, typography, and interaction behavior — they are not production code to copy directly.

The task is to **recreate these designs in Shopify** — Liquid templates/sections + a theme JS/CSS build — reproducing the visual design and interactions using Shopify's platform conventions (sections, blocks, metafields for content editors, cart/checkout AJAX API, customer account API), not by embedding this HTML as-is.

## Fidelity
**High-fidelity (hifi).** Final colors, typography, spacing, and copy are as intended for production. Recreate pixel-close using Shopify theme patterns.

## Design Tokens

**Colors**
- Primary green (brand/logo): `#82C914`
- Hover green: `#6ba30f`
- Dark green (headings, footer newsletter band, announcement bar): `#3f6b4f`
- Accent green (search button, hero panels, badges): `#92C83F`
- Pale green tint (promo strips): `#e6f2d5`
- Body text: `#2A2B2A`
- Muted text: `#5a6153` / `#8b9182`
- Borders: `#e6e7e4` / `#dfe1dc`
- Error: `#B3261E` on `#FBEAE9`
- Success: `#5E8A1F` border on `#EEF6E4`

**Typography**
- Headings: `'Arial Rounded MT Bold', Arial, sans-serif`, weight 700–800
- Body/UI: `'Mulish', system-ui, sans-serif`, weight 400–700
- Base body size 16px; H1 clamp(28px,3.2vw,42px); H2 clamp(21px,2.2vw,28px)

**Spacing / shape**
- Page container max-width: 1440px, side padding 30px (16px mobile)
- Card radius: 12–16px; buttons/pills: 9–10px or fully-rounded (999px) for CTAs
- Standard card shadow: `0 24px 44px rgba(0,0,0,.14)` (dropdowns), `0 20px 50px rgba(32,69,65,.16)` (hero)

## Screens / Views (see `pages/` for full markup)

- **McCormacks Homepage.dc.html** — hero slider (5 slides), feature category tiles, popular categories rail, hot offers grid, reviews carousel, brand logo slider, "Other Services" grid, footer.
- **Medicines & Health.dc.html** — category/collection template: filter sidebar (facets: type, brand), product grid, sort, FAQ, "You may also like" rail. Reused as the pattern for all ~145 sub-collections via filter state, not separate files.
- **Brands.dc.html** — brand index + brand detail (toggle view).
- **Cart - Checkout.dc.html** — cart / checkout / confirmation steps in one flow.
- **My Account.dc.html** — login / register / reset / dashboard / orders / order detail / prescriptions tabs.
- **Sale - Baby Categories.dc.html** — sale + baby category views.
- **Store Locator.dc.html** — store list + per-store detail.
- **In-Store Services.dc.html** — services hub + per-service booking detail.
- **Health Hub Blog.dc.html** — blog index + article template.
- **Prescriptions.dc.html** — submit / repeat prescription forms.
- **About Us.dc.html / Contact Us.dc.html / Careers.dc.html** — standalone content pages (split from a single combined page; each has real URLs now).
- **Withdraw From Contract.dc.html** — statutory right-of-withdrawal page: intro, eligibility rules, excluded-products notice (marked `[PLACEHOLDER]` pending legal review), return/refund policy, a validated enquiry form (client-side required-field + email checks, inline error states, success confirmation panel with reference number/timestamp), and a printable EU model cancellation form. **Trader legal name, registered address, customer service email/phone, and PSI Internet Supply List number are placeholders — must be filled before publishing.**
- **Cookie Policy / Privacy Policy / Terms and Conditions / Shipping / Returns / Click and Collect / Internet Supply Pharmacy / Gift Vouchers / New In / Bundles / Product - fabU Skin Glow / Search Results** — standard content/utility pages, same header/footer/nav shell.

## Global Navigation (applies to every page)
Announcement bar → header (logo, search, wishlist/cart/account icons, mobile hamburger drawer) → main nav bar with mega-menus:
- **Medicines & Health** — 19 category groups, 6-column mega-menu, full sub-item lists (see file for exact taxonomy — sourced from client's approved category doc).
- **Vitamins** — flat list, 18 items, no group headings.
- **Beauty** — 7 groups (Face, Eyes, Lips, Tanning, Nails, Makeup Brushes & Tools, Beauty Accessories).
- **Skincare** — 5 groups (Dermatological, Facial, Body, Problem Skin, Hands & Nails).
- **Toiletries, Mother & Baby, Fragrance, Gifting, Sale, Brands, Services** — smaller dropdowns, see markup.
Nav order left-to-right is fixed per client brief — do not reorder without confirming.

## Interactions & Behavior
- Mega-menu dropdowns open on hover (`onMouseEnter`), close on mouse-leave of the nav bar.
- Mobile: hamburger opens a slide-in drawer with flat nav list + Services/Store Locator/Account/Wishlist quick links.
- Homepage hero is a 5-slide auto/manual carousel with dot navigation.
- Horizontal scroll rails (categories, brands, reviews, hot offers) have prev/next arrow buttons that scroll by a fixed pixel amount; back-arrow hides at scroll position 0.
- Withdraw From Contract form: required-field + email-format validation on submit, per-field inline error messages, focuses first invalid field, shows a success panel with a generated reference code and timestamp on valid submit (no real backend — wire to your form handler / Shopify contact form app).
- Footer newsletter signup is a plain form (no backend wired — connect to Shopify's customer/newsletter API or an ESP).

## Assets
All images/icons referenced by the pages are in `assets/` (logos, product photos, category placeholders, PSI registration badge, social icons as inline SVG). Some category/product tiles use a placeholder diagonal-stripe pattern (`repeating-linear-gradient`) where real photography hasn't been supplied yet — replace with real product imagery before launch.

## Files
See `pages/` for every page listed above. `assets/` holds all referenced images.
