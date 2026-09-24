# Store cleanup, 24 Sep 2026

Snapshots taken through the Admin API before these changes, so each can be undone.

**Menus.** The live theme reads only `footer-shop`, `footer-customer-care`,
`footer-shipping-returns` and `footer-policies` (`sections/footer-group.json`).
The four menus below came from the earlier Dawn-based theme ("Policies Preview",
still on the store, unpublished), which reads `main-menu`, `footer` and
`footer-shipping`. Publishing that theme again would show them empty.

- `footer-shipping`, `footer-services`: deleted.
- `main-menu`, `footer`: emptied. Shopify refuses to delete a store's default menus.
- Contents of all four: `deleted-menus.json`.
- `footer-policies`: Registered Internet Supply Pharmacy repointed from
  `/pages/internet-supply` to `/pages/internet-supply-pharmacy`. Before: `footer-policies-before.json`.

**Pages.** `/pages/pharmacist-review` body: its one "contact our pharmacy team" link
moved from `/pages/contact` to `/pages/contact-us`. Before: `pharmacist-review-body-before.html`.

Hidden (unpublished, not deleted; republish in admin to restore): `about`, `contact`,
`stores`, `delivery`, `services`, `internet-supply` (older twins of about-us,
contact-us, store-locator, shipping, in-store-services, internet-supply-pharmacy),
and ten stubs of about a dozen words each: `covid-19-vaccination`,
`flu-vaccine-clinic`, `blood-pressure-screening`, `inhaler-technique`,
`compression-hosiery`, `blister-packing-service`, `hampers-made-to-order`,
`smoking-cessation`, `photo-printing`, `request-an-appointment`.

Where they came from: none from this repo, whose first commit is 10 Aug 2026.
`contact` was created 15 Apr 2026; the other five on 25 Apr 2026 within two
seconds of each other; the ten stubs on 2 Aug 2026 within three seconds. That
timing points to a script, but the store records no author or app for pages.

Still live and not changed: `/pages/faq`, which is now linked from nowhere and
itself links to the hidden `delivery` and `internet-supply`.
