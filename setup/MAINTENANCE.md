# Maintenance warnings — McCormack's Pharmacy theme

Things a future maintainer can get wrong quietly. Each one is a value or a rule
that used to live in more than one place, and the note says where it lives now.

---

## Read this first: parallel sessions — one worktree each, merged fast-forward only

Several Claude sessions work this repo at the same time, on different tasks.
They must not share a working tree or an index. Give each session its own
worktree on its own branch, and land work on `main` only as a fast-forward.
Do this **before** touching any file — not after something goes wrong. Three
sessions have now broken this rule, each one discovering it only once a commit
went in under the wrong message or an uncommitted edit vanished.

Two commands to set a session up, from the main checkout:

```sh
git worktree add ../mccormacks-<session> -b <session>/<topic> main
ln -s "$PWD/node_modules" ../mccormacks-<session>/node_modules   # render + tests need it; ignored since 9ef74a6
```

Work, render (`npm run render`) and test (`npm test`) inside that worktree,
commit there, then land it:

```sh
cd <main checkout> && git merge --ff-only <session>/<topic>   # refuses unless main fast-forwards
git push origin main
```

**Merge, then push, as separate steps.** Run the merge on its own, confirm it
succeeded, and only then run `git push` or `shopify theme push`. Never chain
them in one command, and never pipe the merge through `tail` or `head`: a pipe
reports the exit status of its last command, so `git merge … | tail -1 && push`
pushes even after the merge is refused. See "A refused merge did not stop the
push", below.

If the merge refuses, main has moved: back in the worktree run
`git rebase main && npm run render && npm test`, then merge again. Do not
`git push . HEAD:main` from the worktree; git refuses to update a branch that
is checked out elsewhere, which main always is.

The main checkout is only ever a clean copy of `main` that receives merges.
Never edit, `git reset`, `git stash` or `git add -A` there while another
session is active, and never `git checkout main` inside a worktree. When done:
`git worktree remove ../mccormacks-<session>` and `git branch -d` the branch.

Each session also runs its own preview server on its own port
(`python3 setup/serve_preview.py 8736`, not the default 8734) and stops it by
PID, never with `pkill -f serve_preview`, which kills every session's server.

**Point the checks at that port with `PORT`:** `PORT=8736 npm run verify`, or
`PORT=8736 python3 setup/verify/sweep.py` for one of them. Until 10 Sep 2026 this
paragraph was advice the suite could not honour — fourteen of the fifteen scripts
that open a socket hardcoded `localhost:8734`, so a session that followed the
instruction above had to run against the shared server anyway, or patch copies of
the checks. They all read `os.environ.get("PORT", "8734")` now. The default is
unchanged, so every existing invocation still hits 8734 and nothing in
`package.json` moved.

Worth knowing why that took a second pass to find: twelve of the fourteen were the
identical line `BASE = "http://localhost:8734"`, which makes the whole thing look
like one find-and-replace. It is not. `fonts.py` wrote it without spaces around the
`=`, and `mobile-nav.py` had no `BASE` constant at all — the URL sat inline in its
`pg.goto()`. Replacing the obvious line would have migrated thirteen scripts and
left `mobile-nav.py` silently on 8734, which only shows up when someone runs the
suite on a private port, which is exactly what this paragraph tells them to do.

### preview/ is untracked and per tree (10 Sep 2026)

`preview/` came out of git the same day. Every section change re-rendered
300-odd files, and any `git add preview` or `git add -A` swept up whatever
the other session had rendered; two commits landed with the wrong preview
contents that way. Vercel and the Pages workflow now run `npm run render`
themselves, so nothing rendered is tracked and there is nothing to sweep.

What remains is a disk race, not a git one. Sessions sharing a single tree
render into the same `preview/`, so the dev server serves whichever render
ran last, and a verify run can be checking the other session's theme. With a
worktree per session each tree has its own `preview/`, and the race is gone.
`npm run verify` re-renders first, so it always checks the tree it runs in.

The render-identity check (render, then an empty `git diff`) went with the
tracked folder. `npm run render:diff` is the replacement: it renders to a
temp folder and lists which pages differ from the last render, before
`npm run render` overwrites it.

### Why — three collisions so far

Each happened in a window when two sessions shared one tree, and each is the
kind of thing that turns up months later as "when did this change?"

**1. A hunk rode into the wrong commit (10 Sep 2026).** Session A changed the
chip rule in `base.css` to 40px and left it uncommitted while rendering
screenshots for approval. Session B, working on the button hover in the same
file, committed `base.css` by whole path (553851f, "Filled buttons hover lime
with dark ink"). The 40px chip rule went in with it. The code was right and
the commit message was about something else, so the history now says the
hover commit changed the chips. Nobody did anything wrong by their own
lights; the tree was shared.

**2. A commit step reset the shared index (10 Sep 2026).** To avoid the first
problem, session A committed only its own hunks by building a filtered patch,
applying it in a temporary worktree, and moving `main` there with
`update-ref`. That left the main tree's index stale, so it ran `git reset`
(mixed) to catch up. A mixed reset unstages everything in the index,
including anything session B had staged and not yet committed. Nothing was
lost, because staged files stay on disk, but B's staging silently vanished.
The same sequence also failed once midway (`git rm --cached node_modules`
after B had already fixed the ignore rule), which killed the chain before the
commit and left the temp worktree to be cleaned up by hand.

**3. An uncommitted edit was reset out from under a session (23 Sep 2026).**
A session (Sonnet 5) was mid-edit on `main-product.liquid` in the shared main
checkout — never committed, never even staged. A second session (Opus 5.5),
also working directly in the same shared checkout rather than its own
worktree, committed unrelated work to `main` around the same time. The
`main-product.liquid` edit vanished with no trace in that commit's file list
and no error on either side. Confirmed cause: the second session had applied a
measurement patch to the same file, saved it with `git diff`, then ran
`git checkout -- shopify-theme/sections/main-product.liquid` to revert it. The
saved patch showed the other session's edit had already been in the file, so the
checkout snapped both back to HEAD. The edit was redone and verified landed
before continuing. Two lessons: `git checkout -- <file>` in a shared tree
discards everyone's work in that file, not just yours; and a patch taken with
`git diff` contains every uncommitted hunk in the file, whoever wrote it.

All three vanish with a worktree per session: each index is private, each
commit is by whole file with nothing foreign in it, and `push . HEAD:main`
cannot overwrite anyone because it only fast-forwards.

### A refused merge did not stop the push (25 Sep 2026)

The eleventh cross-session incident, and the first where a failed step did not
stop what came after it. A worktree per session does not prevent this one.

A session landed a one-line fix to the contact page FAQ with a single chained
command: fast-forward merge, `git push`, `shopify theme push --only
sections/page-contact.liquid --allow-live` to the live theme, then remove the
worktree. Another session had landed a commit on main in the meantime, so the
merge was refused. The merge was written as `git merge --ff-only … | tail -1`,
and a pipe exits with the status of its last command. `tail` succeeded, so the
chain carried on. `git push` had nothing to send. The theme push uploaded the
main checkout's copy of the section, which did not contain the fix.

It did no harm only because main's copy of that file happened to match the
store already; the session had checked that minutes earlier. The same shape
would have put the wrong version on the live store if main's copy had differed
from the store in any way, for example if someone had fixed that file on the
store and the fix had not yet come back to git. The FAQ fix itself was rebased,
tested and landed properly afterwards (`cf8b707`).

The rule, now in the landing steps above: merge and push are separate steps,
and a push runs only after the merge is confirmed. Check the result of the
merge before running anything that goes out of the repo, whether that is
GitHub or the store. Don't let a pipe or a `;` stand between a step and the
check on it.

### Fetch before you say what main contains, and quote the sha (30 Sep 2026)

The rules above are about writing to `main` safely. This one is about **reading**
it, which turned out to be the commoner mistake: three sessions in one evening
each stated something false about `main`, and none of them was careless. A
worktree cannot tell you what `main` has, and neither can a fetch from ten
minutes ago.

- **A sha from an unmerged worktree is not an identifier anyone else can use.**
  One session asked another to confirm it had commit `e5a37d3` before pushing
  theme files. It was their own pre-rebase local commit; it had landed as
  `4df10c1`, and `e5a37d3` was an ancestor of nothing on `main`. The warning was
  right, the identifier could not be checked, and answering it meant checking
  the file contents instead.
- **A stale read asserted as current.** A session fetched, then did other work,
  then read `run-all.sh` and told another session their commit had not landed.
  It had, eight minutes earlier, and that session's own next commit already had
  it as a parent — it was standing on the thing it said was missing.
- **A merge refused twice** because `main` moved between the check and the merge
  (see the rebase step in the landing instructions above).

So, before you state anything about `main` — in a message to another session, in
a commit message, or to the person running the sessions:

```sh
git fetch origin && git log --oneline -3 origin/main
```

and **quote the sha you actually read**. "main is at 1c273bb" can be checked by
whoever you said it to; "my work is on main" cannot, and is what all three of
these sounded like. Read `origin/main`, not your branch and not the main
checkout, both of which can be behind or ahead.

To check a file rather than a commit, read it out of the ref instead of trusting
that your branch matches:

```sh
git show origin/main:setup/verify/run-all.sh | head -40
git merge-base --is-ancestor <sha> origin/main && echo "on main"
```

The order matters and is the part that gets skipped: the read has to come
*after* the fetch, in the same breath. A fetch at the top of a session and a
claim at the bottom of it is the second incident above, which was made by the
session that had just recommended this habit to someone else.

### The store has no worktree: one session writes to it at a time (25 Sep 2026)

Worktrees protect the repo. Nothing protects the store. Every session reaches
the same live catalogue through `shopify store execute`, and Shopify keeps no
branches, no merge and no refusal. The last write wins, silently.

On 25 September two sessions wrote to the catalogue within the same hour. One
was tagging products and fixing their types; the other was retyping products
and deleting collections. Between one session reading the store and writing
to it, the other had retyped Sidena, Calpol and Deep Heat and deleted 98
collections, including 25 the first session was about to unpublish. Nothing
was lost only because both sessions re-read each product just before writing
and refused to write if it had changed. That was luck of habit, not a
safeguard.

The rule:

- **One session at a time makes store writes.** That means any mutation:
  product tags, types or status, collections, publishing, metafields, theme
  pushes to the live theme, anything run with `--allow-mutations`.
- **A session that is going to write to the store says so first**, to the
  person running the sessions, and does not start until they confirm no other
  session is writing. It says again when it has finished.
- Every other session treats the store as read-only: reports, proposals and
  CSVs, with no writes.
- The session that writes still re-reads each record immediately before
  changing it, and stops if the record differs from what its plan expected.
  That check caught today's overlap; keep it as a second line of defence, not
  instead of the rule.

#### The CLI token is one file for the whole machine (30 Sep 2026)

`npx shopify store auth` is itself a write against a shared resource, so it
follows the one-writer rule above even though it touches no product.

There is **one token file per machine**, not one per session or per worktree:
`~/Library/Preferences/shopify-cli-store-nodejs/config.json`. Every session
reads it. Re-running `store auth` rewrites it, which replaces the access token
that every other session is holding — including one that is part way through a
batch of mutations. A session whose token is swapped out mid-run gets an auth
failure on its next call, having already written some of its records and not
the rest, which is the worst state to leave the catalogue in.

So: **do not re-run `store auth` while another session is writing**, and treat
adding a scope as a store write to be announced and queued like any other. This
matters more than it looks, because the reason to re-run it is usually that a
scope is missing, which is exactly when a session is impatient to get on.

#### An all-clear can be given in good faith while someone else is mid-write

Asking the person running the sessions is necessary and it is not sufficient.
On 30 Sep a session was told, truthfully as far as the person knew, that the
catalogue was clear: the session they had in mind had indeed finished. A
different session was three seconds into a `productUpdate`. By then there were
**seven worktrees**, and no human tracks seven.

Check as well as ask. This costs nothing and catches what the ask cannot:

```sh
pgrep -fl 'store execute.*allow-mutations'          # a mutation in flight right now
git worktree list                                   # how many sessions actually exist
```

and, for what already landed, ask the store what it changed most recently —
`products(first: 20, sortKey: UPDATED_AT, reverse: true)` with `updatedAt`. Two
of those three would have caught it on 30 Sep; the worktree list alone would
have shown a session nobody had mentioned.

**A clean `git status` in another worktree does not mean that session is idle.**
Store writes leave no trace in git until someone commits a before-state CSV, and
a session can write for an hour with nothing staged. Judge whether a session is
writing from the store and the process table, never from its working tree.

One more thing that follows from all of this: a session that is waiting should
say so to the others, and say when it starts and finishes. Sessions can message
each other directly, and on 30 Sep three of them queued themselves that way
without the person having to arbitrate.

---

## The recurring defect: one thing in two places, saying two things

This is the most common defect on this site. It isn't a bug in code: it's one
thing (a policy, a page, a link list, a value, some copy) that exists in two
places. Each copy was maintained by someone who didn't know about the other,
until the two disagreed. By 23 Sep 2026 it had come up nine times in one week.
Most sections of this file are one instance of it: the free delivery threshold
(62 copies), the prescription FAQ answer (11), the generated snippets (a
file and the script that writes it), and the product card (7 copies, below).

Neither copy looks wrong on its own. Each one reads fine, renders fine and
passes every check. You can only see the defect by putting the two copies side
by side, and nobody does that unless they know a second copy exists.

### Where the second copy hides on this site

- **Admin versus theme.** Shopify's policies (Settings → Policies, served at
  `/policies/*`) versus our page templates (`/pages/*`). Admin navigation
  menus versus the hardcoded fallback link list in `footer.liquid`. A
  metafield value versus a schema default.
- **A schema default versus the saved template JSON.** Changing a section's
  default does nothing to a block already saved in `templates/*.json`.
- **Two admin pages with different handles.** For example, `/pages/internet-supply`
  and `/pages/internet-supply-pharmacy`, both live, with different text.
- **A hardcoded link next to a menu link.** They start out pointing at the same
  place and drift apart when one of them changes.
- **A pasted component versus the one it was pasted from.** A product card, a
  trust strip, a price row copied into a new section instead of rendered from a
  shared snippet. See the next subsection.
- **Other themes on the store.** `Policies Preview` (#205141082443) is the
  previous developer's Dawn build. Don't take content from it and don't push to
  it. Our theme is #207567454539.

### Before changing anything that looks like content

1. Find every copy. Grep the theme for the URL, the handle and a distinctive
   phrase from the text. Then check the admin: Pages, Settings → Policies,
   Navigation, and metafields. Check the live store, not the preview: the
   preview has no admin pages, no `/policies/*` and no real menus.
2. Decide which copy is the source, and record here where it lives.
3. Every other place should link to or render from the source, not keep its
   own text.
4. If the copies differ and the text belongs to the client (legal, clinical or
   pricing), don't pick one. List the differences and ask the client, as with
   the legal pages below.

### Components get pasted, not shared (23 Sep 2026)

The same shape at component scale. By 23 Sep 2026 the product card existed as
**seven hand-copied versions**: the collection grid, the product page's
"Have You Checked" rail, the collection pages' "You might also like" rail, the
homepage Sale rail, the gift vouchers rail, the cart drawer suggestions and the
wishlist, plus the compact rows in the search dropdown and the product page's
side list. The rule for showing a reduced price existed **three times**: the Liquid
snippet `product-compare-at`, and two copies in JavaScript. **Six of the seven
cards were wrong in the same way, and so were both compact rows.** Only the
collection grid (and the search results page, a separate layout) used the
snippet. The rest showed the current price with no strikethrough and no SALE
badge, so a reduced product read as full price. The worst was the
homepage section titled "On Sale This Month". The trust strip's inline copies
and the free delivery threshold (62 copies, above) are the same pattern:
something that should be rendered from one place gets pasted instead, each
paste is right on the day, and the copies drift.

Review doesn't catch this, because each copy looks fine on its own. What
catches it is a check that knows the shared path exists and fails when a new
surface skips it. Where it lives now:

- **Liquid:** `snippets/product-compare-at.liquid` decides whether a price may be
  struck through, and returns the old price or nothing. Every card captures it
  as `was`.
- **JavaScript:** `saleWas()` in `assets/theme.js` is the same rule for cards
  built in the browser (wishlist, quick view). The product page's variant picker
  reaches it as `window.mccSaleWas`.
- **Markup:** `.sale-badge` and `.price-was` in `base.css`.
- **The check:** `PriceWithoutCompareAt` in `check.mjs`, which runs in `npm test`.
  In Liquid, `X.price | money` fails unless the same loop renders
  `product-compare-at` for `X`. In JavaScript, `fmt(X.price)` or
  `formatMoney(X.price)` fails unless `saleWas(X)`, `saleWas(shownVariant(X))`
  or `mccSaleWas(X)` appears within 30 lines. Prices that aren't a product card
  are listed in `PRICE_EXEMPT` with a reason. An exemption that no longer matches
  anything fails too, so the list can't go stale.

**A green check is not a guarantee.** The JavaScript side only looks at the 30
lines around each price, so a sale check far away from the price it belongs
to will fool it: a helper function, a value computed at the top of a long
render function, or a price formatted in one module and a `saleWas` call in
another. It also only recognises the call patterns above. A price written
another way, such as `Intl.NumberFormat` directly, a template literal, or a
variable not named after the product, isn't seen at all. The Liquid side is
stricter, but it only knows `.price | money`. A new money filter or a price
passed through a snippet would get past it. When you add a surface that shows
a product price, check the sale marking in the browser with a reduced
product; don't rely on the check alone.

The general rule: before writing a card, row or strip that already exists
somewhere else on the site, render the existing one or move it into a snippet.
If a component genuinely has to be copied, add a check for the part that must
not drift.

### The promo label is on three of the seven cards (30 Sep 2026)

The eighth instance of the pattern above, and this one is **deliberately
incomplete** — recorded here so the next person knows it is a gap, not an
oversight.

The old site shows a free-text promo line under the price ("3 for €10",
"While stocks last", "Free tanning mitt with every Tan Studio item"). 99 of the
147 offers on its Sale and Clearance pages carry one, so it is most of what
those pages actually say. Nothing in this theme had a counterpart. It is now
`snippets/product-promo-label.liquid`, one line reading the product metafield
`custom.promo_label`, with `.promo-label` in `base.css`.

**Rendered on three surfaces**, the ones the launch offers depend on:

- the collection grid (`sections/main-collection.liquid`, which is the Sale page)
- the homepage rail (`sections/sale-products.liquid`)
- the product page's own price block (`sections/main-product.liquid`)

**Not rendered on the other four card copies**, which will show a multi-buy
product with no sign there is an offer:

- the "You might also like" rail on collection pages (`main-collection.liquid`,
  the *second* card in that same file — it is pasted twice)
- "Have You Checked" and "You May Also Like" on the product page
  (`main-product.liquid`, likewise two more copies in one file)
- the cart drawer suggestions (`snippets/cart-drawer.liquid`)
- the wishlist and quick view, built in JavaScript from `assets/theme.js`, which
  would need the metafield in the product JSON before they could show anything

`PromoLabelMissing` in `check.mjs` (in `npm test`) fails if one of the three
loses its render. It does **not** catch a new surface that forgets to add one,
for the same reason `PriceWithoutCompareAt` needs its exemption list: there is no
way to tell a card that should show a label from a strip that should not. If you
add a surface that shows a price, ask whether it also shows the offer.

**The text is a claim with no expiry.** Nothing dates it — see "Seasonal rotation
is manual" below — so a "While stocks last" sits there until someone clears the
metafield. It is deliberately not derived from the price, the tags or the
compare-at: a multi-buy has no compare-at to read, and "while stocks last" is not
a discount at all.

### Open case: the legal pages (23 Sep 2026)

Privacy, terms, returns and shipping each exist twice: as a Shopify policy and
as a theme page. Only the privacy pair has the same text; the other three
differ in substance. **The source is `/policies/`**, because checkout, order
emails and Shopify's own consent banner always link there and a theme can't
change that. **Don't delete or redirect the `/pages/` versions yet.** The
client and their solicitor still have to confirm which text is correct.

On 24 Sep the places where a customer agrees to or is shown the terms were
moved to `/policies/`: the registration checkbox (`main-register.liquid`),
the phone-only bottom-bar link in `footer.liquid`, and the footer Policies
menu (Terms, Privacy). Registration and checkout now point at the same
documents.

Links in the theme that still point at the `/pages/` versions are in
`back-in-stock.liquid`, `page-prescriptions.liquid`, `page-services.liquid`,
`page-cookie-policy.liquid`, `legal-sidebar.liquid` and `product-faq.liquid`.
The footer's Shipping & Returns menu still links `/pages/shipping` and
`/pages/returns`. Move them when the solicitor has confirmed the text.

The `/policies/*` pages are styled by the block headed "Shopify policy pages"
in `base.css`. Shopify writes that markup itself; the theme only gets the class
names.

---

## Free delivery threshold — one setting, 62 former hardcodes

**Change it in one place: Theme settings → Brand → Free delivery threshold.**
Never type the amount into markup again.

Before this was consolidated, the number was written out in **62 places across
18 files**, and the cart page had its own copy in cents. Moving the setting
would have changed the bag drawer's progress bar and nothing else — the cart
page, the announcement strip and every "free delivery over" line would have gone
on advertising the old figure.

| File | Hardcodes | What they were |
|---|---|---|
| `setup/collections.json` | 39 | Collection description copy, pushed to the store by `provision.mjs` |
| `shopify-theme/sections/main-cart.liquid` | 4 | `assign free_delivery_threshold = 6500`, two copy lines, one comment |
| `shopify-theme/sections/main-product.liquid` | 2 | Trust strip and buy-box copy |
| `shopify-theme/sections/page-shipping.liquid` | 2 | Shipping policy copy |
| `shopify-theme/templates/collection.new-in.json` | 2 | Banner copy and FAQ answer |
| `shopify-theme/sections/announcement-bar.liquid` | 1 | Schema default for the centre text |
| `shopify-theme/snippets/trust-row.liquid` | 1 | Sitewide trust strip |
| `shopify-theme/templates/collection.beauty.json` | 1 | FAQ answer |
| `shopify-theme/templates/collection.bundles.json` | 1 | FAQ answer |
| `shopify-theme/templates/collection.fragrance.json` | 1 | FAQ answer |
| `shopify-theme/templates/collection.gifting.json` | 1 | FAQ answer |
| `shopify-theme/templates/collection.hot-offers.json` | 1 | FAQ answer |
| `shopify-theme/templates/collection.json` | 1 | FAQ answer (the fallback used by most of the 293 collections) |
| `shopify-theme/templates/collection.medicines-health.json` | 1 | FAQ answer |
| `shopify-theme/templates/collection.mother-baby.json` | 1 | FAQ answer |
| `shopify-theme/templates/collection.skincare.json` | 1 | FAQ answer |
| `shopify-theme/templates/collection.toiletries.json` | 1 | FAQ answer |
| `shopify-theme/templates/collection.vitamins.json` | 1 | FAQ answer |

### How it works now

- **Liquid copy** renders `{% render 'free-delivery-amount' %}`.
- **Merchant-editable copy** — announcement bar text, collection FAQ answers,
  collection banner text and collection descriptions — uses the token
  `[threshold]`, which the theme replaces at render time. Anyone writing new
  copy in the theme editor should type `[threshold]`, not a number.
- **Maths** (the cart page and drawer progress bars) reads
  `settings.free_shipping_threshold | at_least: 1 | times: 100`. The
  `at_least: 1` is load-bearing: the cart page divides by it, so a merchant
  entering `0` would otherwise throw a Liquid error. The setting is typed
  `number` for the same reason — as text, `€65` silently evaluated to zero.

### Checking it after a change

Set the threshold to something distinctive, re-render, and confirm the old
number is gone everywhere:

```sh
npm run render
grep -rl "€65" preview/          # should return nothing
```

---

## AWAITING PHARMACIST SIGN-OFF: the "Do I need a prescription?" FAQ answer

**Status: not approved. This is a compliance statement, not marketing copy, and
it stands on every one of the 293 collection pages.**

The previous answer claimed customers must answer suitability questions before
adding pharmacist-only medicines to the basket, and that a pharmacist reviews
those answers before approving the order. The theme has no such mechanism, so
the claim was removed in `0af9da9` and replaced with:

> All items in this collection can be bought without a GP prescription.
> Prescription-only medicines are not sold online in Ireland — you can submit a
> prescription for dispensing instead, and collect it in store or have it
> delivered.

**Known concern with the replacement, raised and not yet resolved:** "can be
bought without a GP prescription" may read as more permissive than intended.
Pharmacy-only (P) medicines still require pharmacist involvement even though no
GP prescription is needed, and the sentence does not say so. It draws the line
at *prescription-only*, when the line that matters to a customer is *pharmacist
involvement*.

Do not treat this wording as settled, and do not reuse it elsewhere on the site,
until a pharmacist has approved it. Where it appears:

- `shopify-theme/sections/main-collection.liquid` — the FAQ block schema default
- `shopify-theme/templates/collection.json` — the fallback most collections use
- `shopify-theme/templates/collection.{beauty, fragrance, gifting, hot-offers,
  medicines-health, mother-baby, skincare, toiletries, vitamins}.json`

Eleven places in total. Changing only the schema default leaves the saved block
copy live, which is how the original claim survived a previous edit.

---

## Restricted products — tag, not code

**Theme settings → Pharmacy → Restricted product tag.** The schema default is
`pharmacist-only`; this store's setting is **`pharmacist-review`**. Products
carrying the tag lose the one-click add on every listing, search result and
recommendation, and link to the product page instead. On the preview theme only
(branch `psi25/order-review`, not yet live), the tag also removes Buy it now and
the express buttons, and puts the over-18 tick on the bag page ("The over-18
tick on the bag page", below).

**The same tag triggers the pharmacist hold** (Shopify Flow, "The pharmacist hold
follows the tag" below). So the tag means "this is a medicine" to two systems:
the theme reads it from the setting, the Flow reads it as a literal string. If
the setting is ever renamed, change the Flow condition in the same sitting, or
medicines will skip the hold. Since 25 Sep 2026 it is applied from the HPRA
register, not by department (see "Licensed medicines outside Pharmacy tagged"
and the retag notes further down).

Two rules for anyone adding a new product grid or rail:

1. Compute the gate with `{% render 'product-restricted', product: p %}` and
   capture it. Do not re-implement the tag test inline; matching is
   case-insensitive and exact-per-tag for a reason.
2. Never build an add-to-cart surface in JavaScript that picks its own
   products. The cross-sell rail and the search suggestions both fetch
   *server-rendered sections* precisely so the filtering cannot be bypassed by
   client code.

   **The wishlist page is the one exception**, because the visitor picks the
   products and they are held in their own browser. It pays for that by
   re-testing the tag client-side against the same setting, passed down in
   markup as `data-wish-restricted-tag`, and the tags come from Shopify's own
   `/products/<handle>.js`, not from anything stored locally. Change the
   setting and both gates move together. If you touch that surface, keep the
   test — it is the only thing standing between a saved pharmacist-only
   medicine and a one-click add.

**In the theme this is suppression, not a suitability check.** The tag hides the
one-click add on grids; it does not ask the customer anything, and it leaves the
product page's Add to bag open. The *questions* are a separate mechanism, the
pharmacist questionnaire below, driven by a metafield. The *review* of every
medicine order is the Flow hold, driven by this tag. A medicine always needs the
tag; it needs a questionnaire only if the pharmacist wants questions asked.

---

## Pharmacist questionnaire — the suitability gate

**Theme:** `sections/main-product.liquid` + `snippets/pharmacy-questionnaire.liquid`.
A product is gated when it carries the `pharmacy.questionnaire` metafield (a
reference to a `pharmacy_questionnaire` metaobject the pharmacist edits) **or**
when its tags pick a built-in set ("Questions before purchase follow the tag",
below, 30 Sep 2026). Neither, ordinary buy box. See `setup/provision.mjs` for the metaobject/metafield
definitions and `setup/verify/questionnaire.py` for the guarantees below.

Three things that are load-bearing and easy to break:

1. **The no-JS gate is the absence of a form.** A gated product renders **no**
   `{% form 'product' %}` and no accelerated-checkout button — with JavaScript off
   there is nothing to POST, so the medicine cannot be added at all. Do not
   "simplify" the gated branch back into the normal product form; that reopens the
   exact hole (Inish's own gate leaves it open). Answers post via `/cart/add.js` as
   line-item properties.

2. **It fails closed.** Gating keys off the metafield's *presence* (`pharma_mf`), not
   its resolved value, so a deleted questionnaire or one with zero questions shows a
   "not available" notice rather than dropping back to a buy box. Keep that
   distinction if you touch the branch logic.

3. **The gate holds the order AFTER payment, not before checkout.** There is no
   Shopify-native way to block checkout from the theme; the model is: customer pays,
   a pharmacist reviews the order (and the answers, where there were questions), and
   dispatch is held until they approve — or the order is refused and refunded. **The
   hold follows the `pharmacist-review` tag, not the questionnaire**: see the next
   section. The hidden `_pharmacist_review` line-item property the questionnaire
   stamps only says "answers are attached to this line"; it is not what holds the
   order. This is the same model Inish use
   and it is the right one, **but it means the customer pays before the decision is
   made.** So whoever writes customer-facing copy must make that sequence clear
   *before* payment: you pay now, a pharmacist reviews, an unsuitable order is
   cancelled and refunded. That disclosure currently lives next to the Submit button
   in `snippets/pharmacy-questionnaire.liquid` (`.pq-consent-note`). If the flow or
   the copy changes, keep the two in step, and get the wording pharmacist/client
   signed off like any other medical copy.

---

## Questions before purchase follow the tag (30 Sep 2026)

**Fergal's decision, 30 September 2026: use the old website's approach, not our
drafted question sets.** The draft in `PHARMACIST-QUESTIONS.md` proposed 25
products in 8 sets, with answers that stop a sale. What the old website actually
does — recorded question by question in `old-site-questionnaires.md` — is
narrower: one 14-question set on the five erectile dysfunction products, two tick
boxes on every other medicine, and **no answer anywhere stops a sale**. He chose
that. The draft sets are not built and are kept only as the proposal they were.

So the questions now come from two places, and the metafield is no longer the
only one:

| Source | Chosen by | Who edits it |
|---|---|---|
| `pharmacy.questionnaire` metaobject | set on the product | the pharmacist, in admin |
| `snippets/pharmacy-question-set.liquid` | product tag | us, in the theme |

**A metaobject on the product still wins**, so anything below can be overridden
per product later without touching the theme.

The tags, read in `sections/main-product.liquid`:

- `questionnaire-ed` — the old site's 14 erectile dysfunction questions. On
  Viagra Connect 4 and 8 pack, Cialis 4Pk and 8Pk, Sidena 50mg 4 Pack.
- `questionnaire-none` — a tagged medicine that deliberately asks nothing. On
  Curanail only, because the old site asks nothing there either.
- neither, but carrying the restricted tag — the default pair: "I am over 18
  years of age" (a tick) and "Are you taking any other medication?" (Yes/No,
  where Yes reveals a free-text box for the detail).

**Why the theme and not a metaobject.** Three reasons, in order of weight. The
sets are now the same across a whole group, so a per-product record is a copy of
the same thing 320 times, and the recurring defect this file opens with. A newly
tagged medicine has to be covered the moment it is tagged, with nobody
remembering a second step — the tag is what the hold already keys off, so one
act covers both. And the store's API token has no metaobject scope
(see "Store API access"), so 320 metaobject entries could not be created from
here anyway.

**What is load-bearing:**

1. **No answer blocks.** Neither built-in set sets `blocking_answers`, because
   Fergal's decision is that the pharmacist reads the answers on the order and
   decides. The blocking machinery is still in the framework and still tested —
   do not remove it, the metaobject path uses it.
2. **Every built-in question is required.** All 14 on an ED product, both on
   every other medicine. The free-text detail box is the one exception: it is
   optional, so a customer who answers Yes and types nothing still gets through,
   and the pharmacist sees a bare "Yes". If that is not good enough, make it
   required — it is one flag in `pharmacy-question-field`.
3. **It is the same gate.** A tag-gated product renders no `{% form 'product' %}`
   either, so the no-JS hole stays shut. `setup/verify/questionnaire.py` checks
   all three branches, including that `questionnaire-none` gets an **ordinary**
   buy box and not the fail-closed notice — a medicine silently gated is as much
   a defect here as a medicine silently open.
4. **Both tick boxes now exist.** The bag page already asks for an over-18
   declaration (below), and the default set asks again on the product page. That
   is deliberate: the bag attribute is what Flow reads, the line-item property is
   what the pharmacist reads per medicine. If one is ever dropped, check which
   system was reading it first.

### Tested on the live store, 30 Sep 2026

Two test orders on the live theme, with Shopify Payments in test mode:

- **#1005, a medicine** (Anusol Cream 23G). Both answers landed on the line
  item, including the free-text detail; the bag's declaration landed as the
  order attribute `Over 18 and will follow the leaflet` = `Yes`; Flow tagged it
  `awaiting-pharmacist`, put the fulfillment order ON_HOLD and wrote the note.
  No `no-declaration` tag, which is the tick box working — orders #1003 and
  #1004, placed on 29 Sep before it went live, both carry it.
- **#1006, a non-medicine** (Aveeno Body Wash). No questions on the page, no
  declaration on the bag, no line-item properties, no tags, not held.

**The erectile dysfunction set has not been tested end to end on the store**,
because the five products are still off the Online Store. The 18 questions are
checked in `setup/verify/questionnaire.py` and render from the same snippet the
two orders above exercised, but no ED order has been placed. Do it when they go
on sale.

### The ED set: 18 questions, and where each came from (30 Sep 2026)

The set started as the old site's 14. **Fergal's further instruction the same
day: where the old site's questions are incomplete, our approved draft
(`PHARMACIST-QUESTIONS.md`, set 1) fills the gap.** So it is now 18, and which
is which matters if anyone ever re-checks the wording against the old site:

| Question | Source |
|---|---|
| 1–3, 5–14 | the old site's own wording, tidied only |
| 4 | **our draft**, wording supplied by Fergal. The old site's question 4 broke off mid-sentence ("…under a doctor's care for any of the following") with no list after it. The replacement names what the list should have held: heart attack, stroke, unstable angina or severe heart failure in the last 6 months; chest pain or breathlessness on light exercise; low blood pressure; severe liver disease. |
| 15 | **our draft**, set 1 question 1 — is this for a man aged 18 or over with erectile dysfunction. The old site asks this nowhere; it relies on a tick box instead. |
| 16 | **our draft**, set 1 question 7 — any medicine for blood pressure or the prostate. The old site's question 10 asks only about alpha-blockers, so a man on, say, amlodipine answers No to it truthfully. |
| 17 | **our draft**, set 1 question 3 — any medicine for HIV. The old site names only ritonavir and saquinavir. |
| 18 | **our draft**, set 1 question 8 — sickle cell disease, leukaemia, myeloma, a bleeding disorder, an active stomach ulcer. The old site asks none of these. |

Tidying, on the same instruction and with no change of meaning: three spellings
(riocigaut → riociguat, protsate → prostate, non-artertic → non-arteritic); the
space before the question mark in 1, 2, 3 and 5; the missing space after a comma
in 5, 9 and 13; "e.g" → "e.g." in 9; and the bracket question 12 opened and
never closed.

**Our draft's stops did not come with the questions.** In the draft, six of set
1's eight answers stop a sale. Here they do not: Fergal's decision is that
nothing blocks, so questions 4 and 15–18 are Yes/No like the rest and the
pharmacist reads the answer. Question 15 is the one to watch — a customer can
answer "No, this is not for a man aged 18 or over" and still reach checkout. The
over-18 declaration that actually gets recorded is the bag-page tick box, which
Flow reads (below); the ED set has no `confirm` tick of its own, unlike the
default pair.

`setup/old-site-questionnaires.md` keeps the **verbatim, uncorrected** original
and must stay that way: it records what the old site asks, not what we ask. It
also carries the one thing Fergal has not answered — the set is written for
sildenafil and served unchanged on Cialis, which is tadalafil.

---

## The pharmacist hold follows the tag, not the questionnaire (25 Sep 2026)

PSI guidance (Internet Supply of Non-Prescription Medicines, section 2.5) says a
registered pharmacist must personally review and authorise **every** order for a
medicine before it is supplied. The first design held only orders carrying the
questionnaire's `_pharmacist_review` line property. No product has a questionnaire
(no `pharmacy_questionnaire` metaobject exists on the store) and most medicines
never will, so that design held nothing. The hold now keys off the product tag
every medicine carries.

**Built on the store 28 Sep 2026. Fully tested on the live store 30 Sep 2026.**
Both Flows are live in Shopify, built by hand from
`setup/PHARMACIST-HOLD-FLOWS.md` (nothing in this repo creates them), and
Shopify Order Printer is installed with the "Medicine order record (PSI 2.5)"
template. **One difference from the guide: "Notify merchant" is ticked on all
three hold actions** (Flow 1's two branches and Flow 2's re-hold).

**The test plan passed.** Seven test orders, #1001 to #1007, with Shopify
Payments in test mode; all cancelled with restock afterwards. What each one
proved:

| Order | What it showed |
|---|---|
| #1003, #1004 | Placed 29 Sep, before the tick box was live: both arrived without the declaration and Flow tagged them `no-declaration`, as designed |
| #1005 | A medicine with the tick box live: held, tagged `awaiting-pharmacist`, note written, declaration on the order, questionnaire answers on the line item, **no** `no-declaration` |
| #1005, again | Released **without** an approval tag: Flow 2 held it again and tagged it `released-without-approval` |
| #1003, again | `pharmacist-approved-test` added, then released: Flow 2 removed `awaiting-pharmacist` and let it go |
| #1006 | A non-medicine: no questions, no declaration, no tags, not held |
| #1007 | An erectile dysfunction product: all 18 answers on the line item, held and tagged |

The store does not fulfil orders automatically (step 0 of the build file); the
test orders confirm it.

**The over-18 tick box is live** (pushed 30 Sep 2026 with the questionnaire
work), so a medicine order placed through the bag page now arrives with the
declaration. The routes that skip the bag page still arrive without it and are
still tagged `no-declaration` — that is the Flow failing safe, not a fault.
The pre-payment line telling the customer a pharmacist reviews the order and
may cancel and refund it is live too, in the questionnaire modal.

The design:

- **Flow 1, "Pharmacist hold: medicine orders".** Trigger Order created (every
  channel, and a completed draft order). If at least one line item's product tag
  equals `pharmacist-review` (exact text, lower case: Flow compares literally,
  the theme does not), it holds the fulfillment orders, tags the order
  `awaiting-pharmacist` and writes the note. If the order also lacks the custom
  attribute `Over 18 and will follow the leaflet` = `Yes`, it adds
  `no-declaration` and says so in the same note.
- **Write the note once per branch.** "Update order note" replaces the note, and
  `{{order.note}}` is the note as it was when the order was created. A second note
  action in the same run would overwrite the first, so the no-declaration branch
  writes the held text and the flag text together.
- **Flow 2, "Pharmacist hold: release guard".** Flow has **no "Order tags added"
  trigger** (checked 28 Sep 2026; there is one for customer tags only), so a tag
  cannot release an order. The pharmacist adds `pharmacist-approved-<initials>`
  and clicks Release hold. Flow 2 (trigger "Fulfillment order holds released")
  removes `awaiting-pharmacist` if a tag starting `pharmacist-approved-` is
  there, and otherwise holds the order again and tags it
  `released-without-approval`. Flow cannot see which staff member added a tag;
  the initials in the tag are what name the approver.
- **REVIEWER: waiting on the pharmacist.** Who may approve and the initials
  scheme.
- **NOTIFICATIONS: partly decided.** "Notify merchant" is on for every hold,
  so the store's staff notification recipients hear when an order is held or
  re-held. Still open: whether the customer gets an "under review" email. Not
  built.

**The 2-year record.**

- **At launch: signed hardcopy.** The pharmacist prints each held order with the
  Order Printer template `setup/order-printer/medicine-record.liquid` ("Medicine
  order record (PSI 2.5)"), ticks over 18, aware of the leaflet and quantity
  reasonable given previous orders, marks approved or refused, signs and dates
  it, and files it by order number for 2 years. The sheet shows the order, the
  medicine lines and quantities, the customer's declaration (or "NOT GIVEN"),
  other items (custom items flagged) and the customer's order count. The
  template is edited in the repo, checked with `node
  setup/order-printer/check.mjs` (part of `npm test`), and pasted into Order
  Printer again. A copy edited only in Order Printer is the second copy this file
  warns about.
- **Later upgrade: archive mailbox.** Flow sends a record email on approval and
  refusal to a mailbox under a locked retention policy (Google Vault retention
  rule, or Microsoft 365 retention with preservation lock). An ordinary mailbox,
  an unsigned PDF, a Google Sheet or the Shopify order itself can be edited or
  deleted and do not meet "unalterable". Not built.

HANDOVER.md and PHARMACIST-QUESTIONS.md said "built, not yet tested" from 28
Sep; both were corrected on 30 Sep when the test plan passed. If the Flows,
the tick box or the questionnaire change again, change all three in the same
sitting — this is the "one thing in two places" defect this file opens with,
and it has three copies.

What this covers and what it does not:

- It covers every tagged medicine, whichever way it reached the bag: product page,
  questionnaire, wishlist or a saved cart.
- It does not cover a draft order's **custom line item**: it has no product, so
  no tag. Staff must add medicines to a draft order as the product, never as a
  custom item.
- It is only as good as the tagging. An untagged medicine skips the hold **and**
  the one-click suppression. That is why the product upload sheet asks "Is it
  a medicine?" and the handover tells staff to answer Yes for any product with a
  licence number on the pack (PA, PPA, TR, EU/1/, or VPA for pet medicines):
  whoever imports the sheet tags every Yes. Sudocrem (licensed GSL, PA0436/054/001)
  was untagged on 25 Sep 2026 because the register match marked it "unsure".
- It does **not** meet the rest of section 2.5 on its own: recording that the
  purchaser is over 18, knows to follow the pack's instructions and is buying a
  reasonable quantity; keeping each transaction record for two years in a
  permanent, unalterable form; and spotting repeat requests for medicines liable
  to misuse (laxatives, painkillers, antihistamines). How those are satisfied is
  the client's decision. The hold and the signed record above cover all of it
  but the last, and the tick box adds the customer's own declaration once it
  is live; repeat requests are still open.

### The over-18 tick on the bag page (28 Sep 2026)

**Preview theme only.** This lives on branch `psi25/order-review` (preview
theme 208803529035) and is not on main or the live theme. The two checks named
below exist on that branch.

A bag holding a medicine (the restricted tag, via `product-restricted`) shows a
required tick box inside the checkout form: "I confirm I'm over 18 and will use
this medicine as the leaflet says." Ticked, it saves the cart attribute
`Over 18 and will follow the leaflet` = `Yes`, which shows on the order under
Additional details. **The key is load-bearing**: step 4 of the Flow matches it
by exact text. Rename one, rename both. The box's wording and the line under it
("A pharmacist reviews every medicine order…") are customer-facing medical copy
and need pharmacist sign-off like the questionnaire's; don't put this theme live
before the Flow is on, or that line is untrue.

The tick is a soft gate. It is only as honest as the customer, and anything
that reaches checkout without the bag page skips it. The theme closes the
routes it owns:

- **Buy it now** is not rendered on a medicine's product page.
- **Express buttons** (Shop Pay, Apple Pay, Google Pay, PayPal) are not rendered
  on the bag page or in the drawer when the bag holds a medicine. They are not
  submit buttons, so a `required` tick box would not stop them.
- **The drawer** sends a medicine bag to the bag page instead of checkout.
  `/cart.js` has no tags, so it fetches `/cart?section_id=main-cart` and looks
  for `[data-medicine-declaration]`. It fails closed: until the answer comes,
  or if it fails, the drawer shows "Review bag and check out".

The routes it cannot close on Basic: cart links (`/cart/<variant>:<qty>`), a
direct `/checkout`, Buy again in new customer accounts, admin draft orders, and
any other sales channel. Those orders arrive without the attribute, and the
Flow tags them `no-declaration` (step 5). `setup/verify/medicine-declaration.py`
checks the theme half; the preview's medicine bag is `/cart?fixture=medicine`.

### A `no-declaration` order is the fail-safe working, not a defect (30 Sep 2026)

Order **#1012** arrived tagged `no-declaration` hours after the tick box went
live, which reads like a regression and is not one. It was a test order placed
by a script that posted to `/cart/add.js` and then went straight to `/checkout`.
The bag page was never loaded, so the tick box was never drawn, so nothing could
send the attribute. Nothing was broken; a route that the theme does not own was
used.

All four routes were probed against the live store the same evening:

| Route | Tick box |
|---|---|
| Bag page, medicine | shown, `required`, blocks submit, express buttons gone |
| Bag page, medicine **and** a gift voucher | shown |
| Straight to `/checkout`, bag page never loaded | never drawn — this is what #1012 did |
| `/cart/<variant>:<qty>` permalink | lands on checkout directly, never drawn |

Live `main-cart.liquid` was byte-identical to `main` throughout, so this is the
documented limit above, reached, rather than anything having moved.

**Before treating a `no-declaration` order as a bug, ask which route it took.**
The tag exists precisely because these routes cannot be closed from the theme on
this plan: it marks the order so a pharmacist gets the confirmation from the
customer by hand. A real customer reaches checkout through the bag page or the
drawer, and both are closed. The ones that remain are a typed URL, a saved
permalink, Buy again, a draft order or another sales channel.

The only thing that could refuse such an order outright is a Cart or Checkout
Validation Function, which is a Shopify app and is believed to need Plus — check
that against the plan before anyone promises it, and do not assume the theme can
be made to cover it.

---

## Store data — the opening hours format is load-bearing

Opening hours are read by Google, not just displayed, so the **Store block →
Opening hours** field takes one machine-readable format. Seven lines, one per
day, in day order, 24-hour and zero-padded:

```
Mon|09:00-18:30
Tue|09:00-18:30
Wed|09:00-18:30
Thu|09:00-18:30
Fri|09:00-18:30
Sat|09:00-18:00
Sun|closed
```

A lunch closure takes two ranges: `Wed|09:00-13:00,14:00-18:00`.

The displayed hours are derived from this — consecutive identical days are
grouped into "Mon–Fri" and times are rendered as "9.00am – 6.30pm" — so **do not
write display labels into the field**. `snippets/store-hours.liquid` is the only
parser; both display sites and the JSON-LD go through it, so they cannot drift.

Anything unparseable, and any missing day, reads as **closed**. That is the safe
direction: publishing a pharmacy as open when it is shut sends someone on a
wasted journey. It also means a typo fails quietly, so check the store page after
editing.

Bank holidays are deliberately not expressed. They move each year and schema.org
wants specific dates; the page carries a standing note instead.

### Two other store fields worth knowing

- **Business name (for Google)** — optional per-store override. The schema
  defaults to "McCormack's Pharmacy — <store name>", which is a guess at the
  trading name. Where a branch trades under something else it must be set here
  to match the Google Business Profile exactly, or Google will not connect the
  listing to the page.
- **Eircode** — emitted as `postalCode`. The eircodes currently in the template
  were lifted mechanically out of the free-text address field, where they were
  already present. The address field still contains them, which is fine for
  display.

**Store data is confirmed as of 23 August 2026** — names, addresses, eircodes,
phones, emails and all seven sets of opening hours. The hours were checked
against the mechanically converted design data and every one matched, so the
earlier conversion introduced no errors.

Two corrections came with the confirmation: Carrick Road's address was missing
"Carrick Road" itself, and Belmullet trades as **Erris Pharmacy**, which is now
its visible name with Belmullet as the badge.

`business_name` is set explicitly on all seven rather than left to the
constructed "shop name — store name" fallback. Six of them therefore emit the
same schema `name`, "McCormack's Pharmacy", distinguished by address — which is
how a multi-location business is normally represented, and matches the Google
Business Profiles. Do not reintroduce a "— Clonmel" style suffix: it was our
invention, not a real trading name.

**Bank holidays follow Sunday hours** at every store (Newbridge and Haggardstown
11:00–17:00, the rest closed). This is stated in the page copy and deliberately
NOT in `openingHoursSpecification`, which has no way to express "bank holidays"
— only specific dates via `specialOpeningHoursSpecification`. The consequence
worth knowing: on a bank holiday Monday, Google will show that store's normal
Monday hours. Fixing that properly means publishing a dated exception list each
year.

**Latitude and longitude are set for all seven** (Store block → Latitude /
Longitude, in `page.store-locator.json` since `04b27a6`, 23 Sep 2026). They
place each store on the map and drive "Use my location" sorting.

If a store is added, enter its coordinates when it is created: the "Use my
location" button renders once *any* store has coordinates, not only when *every*
store does, so a store saved without them would sort in a confidently wrong place.

---

## Store API access — check it, do not guess it (24 Sep 2026)

Two sessions on 24 Sep reported different access levels for the same store.
What is actually granted on `mccormackpharmacy.myshopify.com`, as of that date:

- **App:** "Shopify CLI Connector App" (`shopify-cli-connector-app`), installed
  by `npx shopify store auth`.
- **Scopes:** `read_products`, `write_products`, `read_publications`,
  `write_publications`, `read_online_store_pages`, `write_online_store_pages`,
  `write_online_store_navigation` (which also grants
  `read_online_store_navigation`) and `read_orders`, nothing else. The first two
  cover products and collections (rules, vendors, types). The publications pair,
  added later on 24 Sep, lets a new collection be published to the Online Store.
  The pages and navigation scopes, added the same evening for the footer and page
  cleanup (`archive/store-cleanup-2026-09-24/`), cover pages and menus. None of
  them reach customers, themes or settings.
- **`read_orders` was added after this section was written (found 30 Sep 2026).**
  Until then this list ended "nothing else" and said the scopes never reach
  orders, and a session that believed it would have handed a test plan back to a
  human for no reason. Read the grant, don't read this paragraph: the query below
  is the only answer that is current. `read_orders` is read-only — an order still
  cannot be created, tagged, cancelled or refunded from here, and neither gift
  cards (`read_gift_cards`/`write_gift_cards`) nor settings are granted, so
  deactivating a gift card and changing order processing are both admin jobs.
- **Sales channel:** Online Store is `gid://shopify/Publication/341524873547`.
- **User:** matthew@kakion.com (not the account owner).
- **Token:** `~/Library/Preferences/shopify-cli-store-nodejs/config.json` on
  this Mac, an access token that lasts about 24 hours plus a refresh token.
  Never print that file unredacted.

Scopes change when someone re-runs `store auth` with a different `--scopes`
list. Once the app is installed, adding a scope can pass without a visible
prompt. So ask the store what it has granted:

```sh
npx shopify store execute -s mccormackpharmacy.myshopify.com \
  -q '{ currentAppInstallation { accessScopes { handle } } }'
```

`store execute` refuses mutations unless `--allow-mutations` is passed, so
read-only work cannot write by accident. `setup/provision.mjs` does not use this
token: it takes a separate Admin API token through `ADMIN_TOKEN`.

### provision.mjs refuses the real store (28 Sep 2026)

`setup/provision.mjs` was written to seed a dev store. Every step creates and
publishes something: `products` creates the preview's fixture products with
stock and publishes them, and `all` creates collections, menus, pages and the
blog and publishes them. Until 28 Sep its fixtures included "Nurofen Plus
200mg/12.8mg 24 Tablets", a codeine product that is not on the store, so one
`node setup/provision.mjs products` against the real store would have put a
codeine medicine on sale.

- **It now refuses** when `SHOP` matches `mccormackpharmacy` or
  `mccormackspharmacy` (the store handle and the domain are spelled
  differently), and exits with code 2 unless `--real-store` is given. With the
  flag it warns and waits 10 seconds before doing anything. The flag is not
  permission: the one-writer rule above still applies.
- **The fixture is now "Nurofen Tablets 12Pk"** (ibuprofen, a real product,
  tagged), still the preview's only tagged medicine. `funnel.py`,
  `quick-view.py`, `wishlist.py` and `serve_preview.py` find it by that name.
  No codeine product belongs in `catalogue.json`.
- `setup/verify/provision-guard.mjs` (in `npm test`) checks the refusal
  without touching the network.

---

## The store is online only — the shops do not use Shopify POS (26 Sep 2026)

The pharmacy's shops run their own tills, not Shopify POS. The store sells
through the website alone, so a product's "Point of Sale" channel does
nothing, and a product published only to Point of Sale is on no channel that
sells.

- **The 70 products the `Anas-product-image-upload` app created on 23 Sep**
  were published to Point of Sale only. That channel was removed on 26 Sep;
  they are now active but on no sales channel, and nobody can buy them until
  they are published to the Online Store. Before state in
  `archive/store-cleanup-2026-09-26/app-products-channels-before.csv`.
- **Most other products are still published to Point of Sale** alongside the
  Online Store and Shop. That is harmless and was left alone.
- **Wording:** do not describe a product as "sold in the shops" or "on the
  tills" because of its Shopify channel; say whether it is on the website.
  Draft status takes a product off the website; it has no effect on the
  shops' own tills.
- Channel IDs: Online Store `341524873547`, Point of Sale `341524971851`,
  Shop `341525004619` (all `gid://shopify/Publication/…`).

### Medicines are sold on the Online Store only (27 Sep 2026)

The PSI's Internet Supply List registers one website, and PSI guidance 2.1
wants the EU common logo on every page that sells medicines. The Shop app
shows neither, and it skips the pharmacist questionnaire and quick-add block
too. So:

- **Every product tagged `pharmacist-review` is off the Shop channel** (334
  removed on 27 Sep; before state in
  `archive/store-cleanup-2026-09-27/medicines-channels-before.csv`). A newly
  tagged product must come off Shop as well: tagging does not do it.
- Medicines are still published to Point of Sale, which the shops do not use,
  so it sells nothing.
- Non-medicines stay on Shop; that is a commercial choice, not a compliance
  one.

### The primary domain must be www.mccormackspharmacy.ie

Our Internet Supply List entry (10001884, McCormack's Pharmacy, 23 Bolton
Street, Clonmel) names the website as `https://www.mccormackspharmacy.ie`.
The common logo in the footer links to that entry, so the store's primary
domain must be `www.mccormackspharmacy.ie`. Launching on any other domain
(the `.myshopify.com` one, a new domain, or the bare `mccormackspharmacy.ie`
as primary) means the logo vouches for a different website. Either keep the
domain or have the PSI update the entry first.

### PSI 2.1 on the site

Section 2.1 asks for four things. Only one has to be on every page:

- **The EU common logo, on every page that relates to the sale of medicines,**
  linking to our Internet Supply List entry. It is in the footer
  (`sections/footer.liquid`), which is on every storefront page.
- **The PSI's contact details, a link to psi.ie, and a statement that a
  record of each transaction is kept for 2 years** need to be on the website
  once. They live on `/pages/internet-supply-pharmacy` only, which 2.1
  allows. That page is linked from the footer's Policies menu. Do not delete
  or unpublish it; it is the only place they appear.

A footer line repeating those three was added and removed again on 27 Sep
2026: 2.1 does not ask for it. Shopify's checkout does not use the theme, so
the logo is not there either, and on Basic nothing can be added to the
checkout steps.

---

## Dispatch cutoff and Click & Collect — both fail closed

`snippets/buy-assurance.liquid` renders the reassurance beside the Add to bag
button and in the cart. Two of its lines are deliberately absent until real data
exists, because the alternative is promising something the store cannot do.

**Dispatch cutoff** — Theme settings → Pharmacy → Same-day dispatch cutoff.
Blank by default, and blank means the line does not render at all. Before
setting it, know that **11 collection FAQ answers independently say "before
3pm"**: every collection template except Bundles and Sale, counted on the repo and
the live theme on 28 Sep 2026 (the settings help text still says 12). Those are separate copy and will not follow this setting. Either set it
to match them, or tokenise them the way `[threshold]` works — do not leave the
two disagreeing, which is exactly the failure the delivery threshold had.

**Click & Collect** — no setting, deliberately. The line renders from
`variant.store_availabilities`, which Shopify populates only where local pickup
is actually enabled for that product's location. Configure pickup per location
in Shopify admin and the line appears by itself, naming the store when there is
one and counting them when there are several. Leave pickup off and the page
never mentions collection. The count is Shopify's, never ours.

The cart's separate "Click & Collect — free" button is an information link to
`/pages/click-and-collect`. It sits directly under Checkout, so it reads as a
checkout alternative — **if local pickup is never enabled, that button is
misleading and should be removed**, not left as decoration.

---

## Consent — the banner is not what blocks the pixels

`snippets/consent-banner.liquid` records a choice through Shopify's Customer
Privacy API. **It does not block anything.** What blocks a pixel is the
**Permission** field on that pixel in Settings → Customer events. A pixel set to
"Not required" fires before the visitor has answered and the banner is then
decoration — the exact failure the banner exists to prevent.

Two rules:

1. Every pixel added from now on — including ones apps install — needs its
   Permission set to the category it genuinely belongs to.
2. **Never** reimplement consent with a cookie, a `localStorage` flag, or a
   `<script>` guard in the theme. Shopify replays the events a gated pixel
   missed once consent arrives; a theme-side guard just drops them, and drops
   them invisibly.

Shopify's own cookie banner must stay **off**, or visitors see two.

Re-verify after any app install: `setup/analytics/README.md` §4, step 7 — grant
analytics only and confirm the marketing pixel stays silent. Accept-all hides a
wrong Permission; a partial grant exposes it.

---

## Analytics lives in the admin, not the theme

No tracking code belongs in `layout/theme.liquid` or Additional Scripts —
Additional Scripts is removed on 26 August 2026, and theme-level scripts cannot
observe checkout, so they can never report `begin_checkout` or `purchase`.

GA4 comes from the Google & YouTube channel; Meta from a custom pixel under
Settings → Customer events. See [`analytics/README.md`](./analytics/README.md).
Adding a second GA4 tag alongside the channel double-counts revenue.

---

## Colour is now a token system — do not paste hex into a template

Every brand green comes from a CSS custom property. `layout/theme.liquid` computes
them from the four theme-editor settings and writes a `:root` block after
`base.css`; `base.css` holds the same values as defaults so the theme still renders
if a setting is cleared.

| Token | What it is |
|---|---|
| `--c-primary` | The lime, `#82C914`. A **background** colour. |
| `--c-primary-text` | The lime as an **ink**, darkened until it passes AA (`#4C750B`). |
| `--c-dark` | Forest `#3F6B4F`. |
| `--c-accent` | Yellow-green `#92C83F`. |
| `--c-on-primary` / `--c-on-accent` / `--c-on-dark` | The text colour that sits **on** each of those. Computed, never fixed. |

Before this, the four settings were read by nothing: `base.css` declared the tokens
with literal hexes and 637 inline styles hardcoded their own copies. Changing
"Primary green" in the editor did nothing at all.

**Two rules.**

1. **Never write a brand hex into a template.** Use the token. A pasted hex will not
   follow the editor and will not follow a contrast fix.
2. **Text on a green takes the matching `--c-on-*` token**, and text on white takes
   `--c-primary-text`, never `--c-primary`.

### Why the on-* tokens are computed

The theme shipped white text on the lime at **2.04:1**, against a 4.5:1 WCAG AA
requirement — on ADD TO BAG, Checkout, and every primary button. The lime as an ink
on white was the same 2.04:1, affecting every price, link and category name: 355
failing elements in total.

The foreground is now derived from perceived brightness (`color_brightness`), and
`--c-primary-text` is the brand hue darkened in a loop until `color_contrast` clears
4.5. That means a merchant who picks a *dark* green in the editor gets white text
back automatically, and one who picks a pale green keeps dark text. **Do not replace
these with literals** — that reintroduces the bug the next time a colour changes.

The same derivation is inlined in `sections/hot-offers.liquid`, where the tile and
badge colours are picked per block in the editor and cannot use a shared token.

`npm run verify` fails if any text on any audited page drops below AA. Text over a
background *image* is skipped, because contrast there depends on artwork the checker
cannot measure — the hero headline is not covered and needs a human eye.

### The muted greys moved too

`#8B9182` (3.25:1), `#A7ADA0` (2.30:1) and `#5E8A1F` (4.09:1) were also below AA and
were darkened along the same hue to `#717769`, `#727969` and `#58821D`.

---

## Back-in-stock capture — it captures, it does not notify

`snippets/back-in-stock.liquid` renders on a product page only when the variant is
unavailable. Before it, a sold-out product was a dead end: a disabled button and no
way to recover the session.

**Nothing in this theme watches inventory.** A submission posts to Shopify's contact
endpoint and becomes one email, carrying the product title, SKU and a link back to the
page in both the `contact[*]` fields and the message body. **A person has to work that
mailbox.** If nobody does, the customer is never contacted and the copy becomes a lie.

### The email is the only record

There is no Shopify admin inbox for contact-form submissions. **Shopify stores nothing
when this form is posted** — no customer, no admin entry, no list to export, nothing to
search later. Delete the email and the request is gone with no way to recover it and no
way to know it existed. Anyone told to "work through the requests when stock arrives" is
working through a mailbox, and that is the entire system.

Two consequences worth planning for before launch:

- Whoever owns that mailbox should not delete these until the customer is contacted.
  Archive or label instead. A mail rule on `form_type: back-in-stock` in the body gives
  them a folder; there is no Shopify-side filter available, because contact forms create
  no record to filter on.
- Seven contact forms in this theme land in the same mailbox — back-in-stock, contact,
  withdraw-from-contract, services booking, careers, and both prescription forms. Six
  set a `contact[form_type]` to tell them apart; withdraw-from-contract sets none.

`contact[tags]` does **not** mark a stock request. Tags only apply to `form 'customer'`
(the newsletter forms in `footer.liquid` and `newsletter.liquid`), where they tag a real
customer record. A contact form has no record to tag.

The wording says so explicitly — "not an automatic alert — a person from the pharmacy
gets in touch". Do not soften that to "we'll email you when it's back" unless the
client has installed a real alerting app (Back in Stock, Klaviyo), at which point
this snippet should be removed rather than left alongside it.

Confirm with the client who owns that mailbox before launch, and see
`setup/verify/NEEDS-A-STORE.md` for the one live submission that proves it delivers —
**untested as of 2026-09-11.**

---

## Stock at launch: in-stock products continue selling, out-of-stock stay off (30 Sep 2026)

The store's stock counts are placeholders, not a stocktake. On 30 September 1,760 of
the 1,761 tracked variants with any stock at all were at a count of exactly 1 (one was
at 3). With "continue selling when out of stock" off, every one of them would have gone
to "Out of stock" after a single order, and the site would have emptied itself in its
first week of trading.

**The client's launch decision, and the rule from here on:**

- **A product that is in stock continues selling.** Any variant with tracking on and a
  count above 0 has `inventoryPolicy: CONTINUE`, so its count can go to 0 and below
  without the site taking it off sale. The count itself is left alone.
- **A product that is out of stock stays off.** Any variant at 0 or below keeps
  `inventoryPolicy: DENY`, so it shows "Out of stock" and cannot be added. **Keelan
  turns those back on himself** by setting a real count; nobody else changes them, and
  nothing in this repo flips them in bulk.
- **Untracked products are left alone.** Tracking off already means always available,
  so the policy on them does nothing either way.

Applied on 30 Sep to 1,761 variants across 1,761 products (every product on this store
is single-variant). Before state, the full before/after snapshot of all 2,425 variants,
and a per-variant write log are in `archive/store-cleanup-2026-09-30/`. The 594 at 0 and
the 70 untracked were not touched; a re-read of the whole catalogue afterwards confirmed
no count and no tracking flag moved.

This is the launch position, not a permanent one. Once the counts mean something,
turning `CONTINUE` back off is what stops the store overselling — see the stock rule
above and do not treat "continue selling" as the settled state of this store.

### The bag accepts an out-of-stock product; checkout is what refuses it (30 Sep 2026)

**`/cart/add.js` on this store enforces no stock ceiling at all.** A variant that is
tracked, at a count of 0, with `inventoryPolicy: DENY` and `sellableOnlineQuantity: 0` —
a product the page correctly draws as "Out of stock" — is still accepted into the bag by
a direct POST, and so is a quantity of 9,999. Checked on 30 Sep against four such
products, including ones untouched by that day's change, and reproduced on the live
storefront as well as through `theme dev`, so it is neither a consequence of turning
`CONTINUE` on nor a proxy artefact.

**Checkout refuses it, and that is the enforcement point.** Taking such a bag to
`/checkout` lands on Shopify's `stock-problems` step, headed "There was a problem with
our checkout" with an "Out of stock" section, the line marked **SOLD OUT** — and the
line is removed from the cart. Confirmed on the live store, 30 Sep:

| Bag, built by a direct POST | `/cart/add.js` | `/checkout` | Cart after |
|---|---|---|---|
| 1 × out of stock (count 0, `DENY`) | 200 | `stock-problems` | 1 → **0** |
| out of stock **+** in stock | both 200 | `stock-problems` | 2 → **1**, only the in-stock line |
| 50 × out of stock | 200 | `stock-problems` | 50 → **0** |
| **12 × a `CONTINUE` product on a count of 1** | 200 | **proceeds normally** | stays **12** |

That last row is the one the launch change depends on: **a continue-selling product
sells above its count through checkout, not just on the product page.** If checkout ever
starts refusing those, the change in "Stock at launch" above has stopped working.

So **an out-of-stock product cannot be bought.** What is left is a customer-experience
problem, not an oversell risk:

- **The disabled button is the only thing keeping an out-of-stock product out of the
  bag.** `variant.available` is false in Liquid, so the buy button renders disabled and
  reads "OUT OF STOCK", and the quick-add button is not rendered at all. That is enough
  for anyone using the site normally, and not enough if a page is stale or a request is
  made by hand. Someone who gets there sees an error-headed checkout rather than a clear
  "this is sold out" on the product page they came from.
- **The "can't add more" sentence in `theme.js` (`cartError`, 422) is unreachable on
  this store**, because nothing returns 422. It is correct code with nothing to fire it;
  leave it in place rather than deleting it, because it becomes reachable the moment
  inventory is enforced.
- **Polish item, not a launch blocker: why `DENY` at 0 is not enforced at the bag.**
  Most likely a location that does not stock these items — Shopify only enforces a
  ceiling where the inventory item has a level at a location the online store can draw
  from. Confirming it needs `read_inventory`, which the CLI Connector App does not have
  (see "Store API access"), so it has to be checked in the admin: open one of the
  0-count products and see whether its inventory says it is stocked at the location at
  all.

The store is protected against selling stock it does not have. It is not protected
against a customer reaching checkout with something it cannot sell them.

### The empty stock-problems checkout is refused, and unreachable anyway (30 Sep 2026)

A bag holding **only** an out-of-stock product loses its one line at
`stock-problems`, which leaves a checkout with no items, a **€0.00 total** and
"Your order is free. No payment is required." **Tested on the live store on
30 Sep: Shopify refuses it, and no order is created.** Two separate things stop it.

**1. A customer cannot reach the button.** `stock-problems` puts up a modal —
"Out of stock / These items are no longer available and will be removed from your
cart", the line marked **SOLD OUT** — whose only control is **Return to store**.
It has no close control, **Escape does not close it, and neither does clicking the
backdrop.** A hit test at the centre of **Complete order** lands on the modal's
overlay `div`, not the button. The button is enabled in the DOM, which is what
made it look reachable at first; it is not.

**2. The submission is refused even when forced.** Clicking **Complete order**
through the overlay, with every required field filled (email, name, address, city,
county, postal code), does not create an order. The form answers

> **Shipping not available** — Your order cannot be shipped to the selected
> address. Review your address to ensure it's correct and try again, or select a
> different address.

and stays on `stock-problems`. The store's latest order was **#1012 both before and
after**, so nothing was created: no order, therefore no hold, no tags, no note, and
no staff notification or customer email. The same address on a checkout holding a
real product raises no such error, so the refusal follows the empty order rather
than the address.

**Why it was worth settling.** An empty order would carry no line item tagged
`pharmacist-review`, so Flow 1's Condition A could not match and it would **not**
be held — it would land in the admin as an ordinary order with nothing in it, for
staff to puzzle over. Order #1006 (a non-medicine) already shows that Otherwise
path. That risk does not arise, because the order cannot be created.

**The one case not covered:** the refusal surfaces as a *shipping rate* failure, so
it rests on the order having nothing shippable in it. A €0 order that needed no
shipping at all might behave differently. Nothing on this store is in that position
today — gift cards are the only non-shippable line and they are never out of stock —
but if a digital or no-shipping product is ever added, retest this.

Reproduce with `setup/verify/continue-selling.py`'s two variants and the table
above. An order is a store write: read "The store has no worktree: one session
writes to it at a time" before placing one, and cancel whatever you create.

### Checking it needs the real store, and `theme dev` fights back

`setup/verify/continue-selling.py` is the check. Inventory policy is one of the things
`setup/verify/NEEDS-A-STORE.md` lists as unverifiable in the mock preview, so it has to
run against the real catalogue, and the storefront is behind the password page. It
drives `npx shopify theme dev` instead:

```sh
npx shopify theme dev --store mccormackpharmacy.myshopify.com --path shopify-theme --port 9292
python3 setup/verify/continue-selling.py
```

**One quirk will waste an afternoon if you meet it cold.** `theme dev` answers
`/cart.js` and `/cart/*.js` with a `Clear-Site-Data` header. Chromium acts on it, the
proxy loses its own storefront-password session, and the *second* cart write of a run
comes back 502 and everything after it 401. The theme surfaces that as its generic
"could not update your bag" line, which reads exactly like a real defect in the bag and
is not one. Two things in the check keep it honest, and both are load-bearing:

- **The header is stripped from every response**, not just the cart ones — section
  renders and the recommendations endpoint carry it too, and any one of them is enough.
- **A 401, 502 or other 5xx is never scored.** A poisoned session does not recover
  within a run, so the whole run restarts with a fresh browser context, up to four
  times. In practice one restart per run is normal and three runs in three then pass.

**Only a 422 is the store refusing an add.** Do not "fix" the script by scoring a 401
or a 502 as a failure, and do not remove the restart.

A run against the real storefront, once the password comes off, needs none of this.

---

## Product FAQ — the definition lives in the admin, not in the theme

`snippets/product-faq.liquid` renders a per-product FAQ and emits FAQPage JSON-LD
from the same data. **The theme ships it empty.** Nothing appears until two things
happen: someone creates the metafield definition, and someone writes approved
content into it.

### Creating the definition

**Settings → Custom data → Products → Add definition**

| Field | Value |
|---|---|
| Namespace and key | `custom.faq` |
| Name | Product FAQ |
| Type | **JSON** — not "JSON string", and not a list of rich text |

The value is a list of question/answer pairs:

```json
[
  {
    "question": "How long does a course last?",
    "answer": "<p>Fourteen days. See our <a href=\"/pages/returns\">returns policy</a>.</p>"
  }
]
```

Answers may contain HTML so internal links work. Only staff with admin access can
write a metafield, so this is the same trust level as a product description — but
it does mean a broken tag in an answer is a broken tag on the page.

### It fails closed, in three ways

- Absent, empty, or not a list → renders nothing, emits no schema.
- An entry missing either half → that entry is skipped entirely. A question with no
  answer is worse than no question, and an empty `acceptedAnswer` is invalid
  structured data.
- Nothing left to show → the whole section is omitted rather than left as an empty
  heading.

### Before populating it — pharmacist sign-off

FAQPage markup makes these answers eligible to appear **directly in Google's
results**, lifted away from the page and from any surrounding context. An answer
that reads as reasonable next to a product photo can read very differently as a
standalone snippet under a search query.

On a pharmacy that is a higher bar than ordinary product copy. Treat the first batch
as needing the same sign-off already pending on the collection FAQ answer (see
"AWAITING PHARMACIST SIGN-OFF" above), and do not populate pharmacist-only lines
until the gating spec arrives from the client.

`npm run verify` checks the mechanism — that content renders, that a half-filled
entry is dropped from both the page and the schema, that internal links survive,
and that quotes in an answer keep the JSON-LD valid. It does not and cannot check
whether an answer is *correct*.

---

## White text on the brand green — a recorded decision, not a defect

`button_text_white` was set to **"Always white"** in the theme editor. That was asked
for, after the trade-off was laid out, and it is the original design handoff's
appearance. **As of 23 Sep 2026 it is back on "Automatic"** on both the live theme
(#207567454539) and the repo's `settings_data.json`, so nothing is currently accepted
under it and the buttons use dark ink. What follows applies whenever it is switched
back on.

What it costs, measured: **63 text elements sit at 2.04:1 against a WCAG AA
requirement of 4.5:1** — every primary button, the consent banner's Accept and
Reject, and the category chips. `setup/verify/contrast.py` reports these as
**ACCEPTED** on every run: they are counted and printed, with the worst ratio, but
they do not fail the suite. Anything not explained by this setting still fails
normally, so the check has not been weakened — only this one decision is carved out,
and it stays visible.

**To reverse it, change nothing in the code.** Set `button_text_white` to
"Automatic" in the theme editor and the accessible pairing returns, computed from
whatever primary colour is set. There is no hard-coded white anywhere.

**If it is ever revisited**, the two things worth knowing:

- There is no green in this hue that carries both white and dark ink. Darkening
  `#82C914` raises white and lowers ink, and they cross around `#5E910E` where
  *neither* reaches 4.5:1. The choice is genuinely binary: keep the lime and use
  dark ink (6.98:1), or move to `#53820D` or darker and keep white (4.60:1).
- The consent banner's buttons are in the accepted set. Everything else here is
  commerce; that one is the mechanism by which a visitor exercises a legal choice,
  and it is the element most worth carving back out if only one is.

### The bug this surfaced

Flipping the token exposed a real mismatch that had been invisible: `.crec-add` and
`.wish-add` set `background: var(--c-accent)` but `color: var(--c-on-primary)`. It
passed for as long as both tokens happened to resolve to the same ink, and broke the
moment one changed. Both now use `--c-on-accent`. **When adding a rule, take the ink
from the same family as the surface** — an on-token that does not match its
background is a latent failure waiting for an unrelated setting to move.

---

## Gift vouchers: the page sells a real gift card, by handle (30 Sep 2026)

Until 30 Sep the gift vouchers page was a mockup. "Add voucher to bag" was an
`<a href="/cart">`: it added nothing, and none of the recipient fields had a
`name`, so nothing they held could reach an order even in principle. Seven
products named "Mccormacks Pharmacy E-Gift Card €10…€100" were live, published
and sellable at the same time, and **not** gift cards (`isGiftCard: false`) — a
customer could pay for one and receive no code. They were set to DRAFT on
30 Sep, not deleted; the before state is in `before-fakes.json` alongside the
build, and their amounts (10/20/30/40/50/75/100) were never the page's.

How it works now:

- **One real gift card product, handle `gift-voucher`**, six denominations
  (€10, €20, €25, €50, €100, €150). The page finds it with
  `all_products['gift-voucher']`. Rename the handle and the page stops selling.
- **The amounts on the page are that product's variants**, not the section's
  blocks. An `amount` block only decorates a variant it matches by price — its
  tag and its preselected flag — and a block matching no variant draws no button
  and is named in design mode. Six blocks plus six variants is the defect at the
  top of this file, and here it fails as a button that charges for a variant
  that does not exist.
- **The delivery method decides which line item properties are posted**, and it
  does it with `disabled`, so the browser leaves the others out of the post and
  no JS runs at submit time. `By email` posts `Recipient email`, `Recipient
  name`, `Message`, `Send on`, `__shopify_offset` and
  `__shopify_send_gift_card_to_recipient: if_present`, which is what makes
  Shopify email the recipient itself. `Send it to me` posts none of them, which
  is what makes Shopify issue to the buyer. (A third method, `Printed and
  posted`, posted `Delivery: Printed and posted` plus `Postal address` and no
  recipient email. **Removed 1 Oct 2026** — vouchers are online only. This
  paragraph describes 30 Sep; see "Printed and posted was removed the same day",
  below, for what ships.)
- **The names are Shopify's, exactly.** Rename one and Shopify stops recognising
  it and the voucher quietly goes to the buyer instead. This is the same
  load-bearing-key trap as the over-18 attribute the Flow matches.
- **`Send on` is capped at 90 days**, because Shopify refuses to schedule a gift
  card further out, and it is written from local date parts — never
  `toISOString()`, which would move an Irish evening in summer time to the next
  day and send the voucher early.
- **`setup/verify/gift-voucher.py`** checks all of the above through a browser,
  by reading what `FormData` would actually post. The properties are decided by
  which inputs are enabled, so nothing in the markup alone can show it.
- **The preview needs its fixture.** `all_products['gift-voucher']` in
  `render_preview.mjs` is harness-only and not in `catalogue.json`. Without it
  the page renders its "not on sale" notice and the buy form appears in no
  preview at all — which is how a dead Add-to-bag link survived as long as it did.

**`productVariantsBulkCreate` does not apply gift card defaults (30 Sep 2026).**
`giftCardProductSet` documents that it "applies gift card variant defaults
(non-taxable, no shipping required, inventory untracked)". The ordinary variant
mutations do not, even on a product whose `isGiftCard` is true. Two denominations
added with `productVariantsBulkCreate` came out **inventory-tracked with a DENY
policy and a quantity of nobody's setting**, so `availableForSale` was false. They
looked right in every check that did not name the field: price, title, position,
`taxable: false` and `requiresShipping: false` were all correct, because those two
*are* inherited. Only `tracked` was not.

What that looks like from the shop is the part worth remembering: `/cart/add.js`
accepted the variant happily — it refuses nothing, see "No cart stock ceiling" —
the bag showed €10, and checkout then dropped the line and said **"Your order is
free. No payment is required."** A voucher that cannot be bought, reported as a
free order, with no error anywhere naming stock.

So: after any variant write on the gift card product, check `availableForSale` and
`inventoryItem.tracked`, not just price and title. The six denominations must all
read `availableForSale: true, tracked: false, requiresShipping: false,
taxable: false`. Use `giftCardProductSet` where it fits; it is the only mutation
that gets this right by itself.

Two things this page cannot do from the repo, both admin jobs:

- **Gift cards must be activated on the store before a gift card product can
  exist.** `productCreate` and `giftCardProductSet` both refuse with
  `GIFT_CARDS_NOT_ACTIVATED` until someone does it in Products → Gift cards, and
  there is no mutation for it. `shop.features.giftCards` is `true` regardless,
  so it is not the flag to test.
- **Expiry and order processing are settings.** A gift card is issued and emailed
  when its line item is fulfilled, so if Order processing is set to "Don't
  fulfill any of the order's line items automatically" — which
  `PHARMACIST-HOLD-FLOWS.md` step 0 asks for — **no voucher is ever emailed**
  until staff fulfil it by hand. "Automatically fulfill only the gift cards" is
  the setting that satisfies both. Five-year expiry is set under Settings → Gift
  cards; the page's copy promises five years and nothing in the theme enforces it.

**The pharmacist hold and the voucher do not collide — tested 30 Sep 2026.** It was
written here first that a voucher bought alongside a medicine would not be issued
until the pharmacist released the order. That was wrong, and order **#1012** settled
it: the gift card line was auto-fulfilled two seconds after payment, so the voucher
was issued and sent, while the medicine line stayed unfulfilled and the order sat
`ON_HOLD` with `awaiting-pharmacist` and `no-declaration`. "Automatically fulfill
only the gift cards" acts per line item and runs independently of Flow's hold on the
rest of the order.

So the customer gets their voucher straight away and the pharmacist still reviews the
medicine. The voucher product carries no `pharmacist-review` tag, so a voucher on its
own is never held at all.

---

## The voucher's date picker was 88 lines; it is now an `<input type="date">` (1 Oct 2026)

`page-gift-vouchers.liquid` shipped a hand-rolled calendar: a field button, three
quick chips (Today / Tomorrow / In a week) and a popup with month navigation, a day
grid, a "Send immediately" reset and a Done button. **Two radios and a native date
input replaced all of it.** `Send now` is the default and leaves the input `disabled`;
`Pick a date` enables it, with `min` today and `max` at Shopify's 90-day ceiling.

What the custom control cost, all of it measured in a browser rather than argued:

| | Before | After |
|---|---|---|
| Custom JS in the section | 134 code lines | 79 |
| The date control's share of it | 77 | 23 |
| Date markup | 35 lines | 14 |
| Date CSS | 16 rules | 3 |
| Covered another field when open | Message at 1440; Message **and** From at 375 | nothing |
| Closed with Escape | no | n/a, nothing to close |
| Closed with a click outside | no | n/a |
| Footer buttons at 375×667 | Done at y=726, "Send immediately" at y=729, both **below a 667px fold** | n/a |
| Focusable buttons that did nothing | 29 (every past day in the month) | 0 |
| Accessible name of the control | "Send immediately" | "Delivery date" (fieldset + legend) |

Counted with blank lines and `//` comments stripped, before and after, from the
`<script>` block in the section. **55 lines of JavaScript went.** The file itself only
shrank 657 → 592, because roughly forty lines of comment went in where the code came
out — the numbers above are the code, not the diff.

Four things worth keeping in mind before anyone reaches for a picker again:

- **`min`/`max` are set from JS on load, not from Liquid.** `{{ 'now' | date: … }}`
  renders server-side into a CDN-cached page, so a Liquid `min` carries the *shop's*
  timezone and goes stale at midnight. `iso()` survives for exactly the reason it
  always existed — local date parts, never `toISOString()`, which moves an Irish
  summer evening to the next day.
- **`max` is a courtesy, not the guard.** Shopify refuses to schedule a gift card
  more than 90 days out and the cart is what enforces it; its error reaches the
  shopper through `showCartMessage`. Dawn ships **no** `min` or `max` at all and
  relies on that error alone, so this is stricter than Shopify's own reference theme.
- **The radios get the last word on `disabled`.** `applyMethod` enables every input
  its method owns, the date input included, so it ends by calling `applyWhen()`.
  `applyWhen` reads `dateBox.hidden` — what `applyMethod` has just decided — so a
  "Send it to me" voucher never posts a `Send on` even with "Pick a date" still
  checked. That exact case is checked; without it, choosing a date and then
  switching method schedules a send for a voucher nobody is sending.
- **"Today" and "Send immediately" were two controls for one outcome.** The chip
  posted `Send on: <today>`, the reset posted nothing. Shopify documents only "without
  a date specified, the gift card is sent immediately" and says nothing about a
  same-day date, so the difference was either nil or a scheduled-job delay against
  copy that promises "within minutes". The question does not arise any more.

### `From` is gone, because it could never reach the recipient

There was a **From** field posting `properties[From]`. It reached the bag, the order
in admin and the buyer's own confirmation — never the person getting the voucher. The
gift card notification renders in `gift_card` scope, with no `order` and no
`line_item`, so a line item property cannot appear in it, and
[the `gift_card` object](https://shopify.dev/docs/api/liquid/objects/gift_card) has no
sender property to hold one. There is no template workaround; the data is not in scope.

The page was already admitting it: the Message hint read *"sign it if you'd like them
to see who it's from"* directly beneath a From field that they never see. `Message`
carries it now, and its hint says so: "Sign it if you'd like them to know who it's
from." (The hint also described a posted voucher until the printed method was
removed later the same day — see the section below.)

### `Delivery` is posted for every method now

It used to be posted only for `Printed and posted`, so an order for an emailed voucher
said nothing about how it was sent and staff inferred it from whether `Recipient email`
was present. Every method posts it. Only one input is ever enabled, which is what keeps
inputs sharing a name legal. (There were three the morning this was written and two by
the evening — see below.)

`Sent to me` therefore no longer posts a completely bare line. That does **not** change
what Shopify does: issuing to the buyer follows from the *absence* of `Recipient email`
and the send flag, not from the absence of every property. The check that used to read
"posts no properties at all" now reads "Delivery is the only property".

### Four of the six amount blocks said nothing

The buttons come from the gift card product's variants; a block only decorates a
variant it matches, with a tag and a preselected flag. `€10`, `€20`, `€100` and `€150`
each had an empty tag and `preselected: false`, and a variant with no block already
renders a blank tag — so deleting them changed no pixel. Two remain: `€25` ("Popular")
and `€50` ("Most gifted", preselected). Both `templates/page.gift-vouchers.json` and
the section's own preset were trimmed, so a freshly added section starts the same way.
Adding a block for a denomination you do not intend to label achieves nothing.

The summary panel also had `€50` typed in twice as a literal while the hero used
`{{ gv_default }}`. Change which amount is preselected and, with JS blocked, the
summary lied. It reads `{{ gv_default }}` now — the one-thing-in-two-places rule at
the top of this file, in the same section it warns about.

### Printed and posted was removed the same day (1 Oct 2026)

Client decision: **vouchers are online only.** The method went, and with it the
button, the `Postal address` field, its `Delivery` value and its branch in
`applyMethod`. Two methods remain, `By email` (default) and `Send it to me`.

The address field is the part that mattered. It was `required`, so left behind on a
branch nothing can select it would have made the form refuse to submit with nothing
on screen explaining why — the worst kind of leftover, because the control that
would have shown the error is the one that is hidden.

The copy was the larger job and the easier one to miss: the hero line, the method
intro, both How it works cards, the About paragraph and two FAQ answers all promised
a posted voucher. `gift-voucher.py` now reads the rendered body text and fails on
"printed", "posted", "post it", "in a card" or "postal" appearing anywhere on the
page — the controls are easy to check and the sentences are what a customer
actually meets.

`templates/collection.gifting.json` said vouchers were available "online and in
store" and now says online. The Gifting session landed the identical change as
`e167fe1` while this branch was in the queue; the rebase dropped the duplicate.

**The page now makes no claim about vouchers sold in the shops, in either direction**
(client, 1 Oct 2026, a few hours after the above). Three places did:

- the **"Prefer to buy in store?" aside** in the summary column — removed whole,
  including its store-locator link;
- the **FAQ on where a voucher can be spent**, which used to end "the shops sell
  their own vouchers for that". It now reads, verbatim as given: *"Online at
  mccormackspharmacy.ie only. It can't be used in our shops."* — where this voucher
  works, without a word about what the counter sells;
- the **"not on sale online" notice**, which promised "Vouchers are available at the
  counter in any of our seven stores" and linked to the store locator. Not named in
  the request, changed anyway: it is the same claim, and it renders only when the
  gift card product is missing or unpublished — the branch nobody looks at is exactly
  where a withdrawn promise survives for a year. It now says to check back soon.

`gift-voucher.py` bans `"in store"` and `"at the counter"` in the rendered body
alongside the posted words, and checks the aside's heading is gone. The new FAQ
sentence is phrased so it trips neither: it says "in our shops", which is the claim
the client allows. The nav's **"In-Store Services"** is hyphenated and so does not
match — if that is ever written without the hyphen, this check fails on the header
rather than on this page, and the word list is where to look.

`setup/VOUCHER-POST-FLOW.md` is marked NOT NEEDED rather than deleted. The Flow was
never built, so there is nothing to switch off; the file is the record of a reversed
decision and the build steps if printed vouchers return.

### Later: the delivery methods should be radios too

The delivery methods are still `<button aria-pressed>` toggles. Pressed buttons do
not announce "pick one of these" the way a radio group does, and the same argument
that retired the calendar applies to them. Left alone deliberately on 1 Oct so that
change stayed one thing; `applyMethod` is the money path and the conversion wants its
own commit and its own run of `gift-voucher.py`. The custom dot styling and
`state.method` would both go. **Now a two-option choice**, which makes it the same
shape as the date radios directly below it — two controls, one page, two idioms.

---

## `product.gift_card?` was false in every preview (1 Oct 2026)

The theme asks `product.gift_card?` in five places — the two buy boxes in
`main-product.liquid`, `product-card-url`, `product-restricted` and `buy-assurance`.
**Every one of them rendered as false in the preview**, and no check could have caught
it, because liquidjs looks `gift_card?` up as a *literal key*: `gift_card: true` alone
does not satisfy it. Shopify's Liquid treats the `?` as an alias; liquidjs does not.

The repo already knew this trap and had already handled it twice, which is what makes
this worth writing down. `posted_successfully?` and `attached_to_variant?` are both in
`render_preview.mjs` as `{ posted_successfully: x, 'posted_successfully?': x }`.
`gift_card?` is the one that was missed. The fixture carries it now, and so does every
catalogue product (as `false`, which is the honest value — nothing in `catalogue.json`
is a gift card — but it has to be *present*, or `if` and `unless` disagree about what
is missing).

Before the fix, adding a render of the gift card's product page produced a page with
an ordinary add-to-bag form and a **pharmacy questionnaire gate**: `product-restricted`
returns true for a gift card, so `pq_set` fell through to `'default'` and set
`is_gated`. On the live store `{% if product.gift_card? %}` is tested first and wins,
so the shop was always right — but the preview was showing the wrong branch of a money
path, silently, and would have kept doing so.

**`/products/gift-voucher` now renders.** The fixture existed only as `all_products`,
never as `product`, so the branch that replaces the buy box with a link to
`/pages/gift-vouchers` was in no preview at all — the same blind spot that let a dead
Add-to-bag link survive on the voucher page. `gift-voucher.py` section 6 asserts the
buy box is that link, that no `form[action*=/cart/add]` and no `[data-pdp-submit]`
exist on the page, that the questionnaire gate is absent, and that the mobile bar
links to the page rather than carrying a `[data-add-id]` quick add.

Grep for `\w+\.\w+\?` in the theme before adding a fixture; the full set in use is
`form.posted_successfully?`, `product.gift_card?` and `image.attached_to_variant?`.

---

## The gift voucher card is white on lime — a client decision (23 Sep 2026)

The voucher card in the gift vouchers hero (`page-gift-vouchers.liquid`) shows the
real logo and all its text in **white** on its lime-to-green gradient. That was chosen
after the options were laid out: dark ink on the lime (7.14:1), white on a dark-green
card (6.13:1), or white on the lime. White on the lime is **1.99:1** at the card's
lime corner and 3.06:1 at the green end, against 4.5:1 for the labels and 3:1 for the
amount and the logo.

`setup/verify/contrast.py` **fails** on it: the amount and three labels, at 1440 and
390, eight failures. That is deliberate. It is not carved out the way
`button_text_white` is, because no one has approved weakening the check for it. If
the decision stands, the carve-out belongs in `contrast.py` next to the button one,
scoped to this card, with its count printed on every run.

**To reverse it:** on the card's wrapper, change `color:#ffffff` back to
`color:var(--c-on-accent)`, and on the logo `<img>` change the filter from
`brightness(0) invert(1)` to `brightness(0)`. Using the full-colour logo instead
doesn't work: its lime and grey vanish on the lime card (1.02:1 and 1.40:1).

How the logo gets there: it is the header's own logo URL (`snippets/logo-src.liquid`),
turned white by the CSS filter, not a second white file. A logo uploaded under
Theme settings → Brand must stay a **transparent PNG**, or the filter turns the
whole rectangle white.

---

## The other four contrast failures are the hero, and the checker is wrong about them (1 Oct 2026)

`contrast.py` reports **12** failures, not eight, and for a while the entry above read
as though it accounted for all of them. It does not. Four are on the **homepage hero**,
at 1440 and 390:

| | Reported | Actual |
|---|---|---|
| "Vitamins & Supplements" | 1.16:1 | **2.04:1** |
| "Premium vitamins, minerals and Irish hea…" | 1.02:1 | **1.77:1** |

The reported figures are wrong because the checker reads the **CSS fallback**.
`hero-slider.liquid` sets `background:#E6F2D5` on the slide wrapper, which is what sits
under the hero image while it loads and what `getComputedStyle` returns; the text is
actually over the photograph. The real ratios are the ones on the right (client
measurement, 1 Oct 2026). They still fail AA — this is a real contrast problem, just
not the one the numbers describe, and it is **not** the voucher card.

Both are left failing on purpose and **not** fixed on the branch that found this
(`gvdate/native-date-input`, a gift voucher change). Written down because an accepted
failure is a good place for an unrelated one to hide: the voucher card's eight were
documented, the suite was known to fail on `contrast`, and four homepage failures sat
inside that for as long as nobody counted them.

**If you are reading this because `contrast.py` failed:** the count is the thing to
check first. Eight means the voucher card alone. Twelve means the card plus this hero.
Anything else is new and nothing here covers it.

---

**This is why `npm run verify` reports a failure on a clean tree.** `contrast.py`
counts these four elements (the card's "Gift Voucher", the amount, "Valid 5 years"
and "Online only") as WCAG AA failures at 1.99:1, because they are. The check is
right and the site is shipping the client's decision anyway.

Until 30 Sep the suite was a single `&&` chain, so contrast failing meant
`questionnaire`, `medicine-declaration`, `bag-remove` and `gift-voucher` never ran
at all — four checks silently skipped on every run, including in CI. The chain is
now `setup/verify/run-all.sh`, which runs all 27 and reports failures at the end.
Contrast still fails and still exits non-zero; it just no longer hides anything.
If the client reverses this decision, the expected result is 27/27.

**The runner takes its list from the directory, not from a list.** Every
`setup/verify/*.py` runs, so a new check is picked up by existing — the first
version of this script named them by hand, which is the defect at the top of this
file and would have orphaned the next check written. The exception is `SKIP` at
the top of the script, currently `continue-selling` and `offer-carts`: those two
drive the **real store** and need a `shopify theme dev` server, so they cannot run
against the local preview and are listed as skipped in the summary rather than
failed. A new real-store check has to be named there; a new preview check needs
nothing.

## Headings are Nunito, not Arial Rounded — a decision (24 Sep 2026)

The design handoff sets headings in **Arial Rounded MT Bold**. The theme now sets them
in **Nunito**, self-hosted beside Mulish. Arial Rounded is a macOS/iOS system font, so
the handoff was only ever seen as designed on Apple hardware: Windows drew Arial and
Android drew Roboto. Even on a Mac it was wrong: the font is a single bold face that
declares itself weight 400, and nearly every heading asks for 800, so Chrome drew a
synthetic bold over it.

Nunito was picked over Baloo 2, Quicksand and Varela Round after screenshots of the
homepage, a collection and a product page at 1440 and 390. It has real 700 and 800
(the only weights headings use), it is by Mulish's designer, and on seven pages at both
widths no heading wraps differently from Arial Rounded. Quicksand stops at 700 and
Varela Round at 400, so both would fake the 800 again.

- **One place:** `--font-heading` in `base.css`. Every heading reads the token; there
  are no typed-out font stacks left, and `setup/verify/fonts.py` fails if one appears.
- **The file:** `assets/nunito-variable.woff2`, 38 KB, Google's latin subset — the same
  230 characters as `mulish-variable.woff2` — declared and preloaded in
  `theme.liquid`, `password.liquid` and `templates/gift_card.liquid`.
- **To reverse it:** set `--font-heading` back to `'Arial Rounded MT Bold', Arial,
  sans-serif` and delete the Nunito preload and `@font-face` from those three files.

---

## Why fixture coverage matters — three worked examples

All three had shipped through code review, and all three were invisible for the same
reason: nothing in any preview ever rendered the state that exposed them. The first
two were found in the same pass.

This is a different blind spot from content in a closed accordion or tab (see "Audits
have to open every accordion, tab and modal"). There the state exists on the page
and nothing opened it. Here the state never renders at all unless a fixture forces it.

### 1. The variant picker never worked


`main-product.liquid` emitted its variants JSON *after* the inline IIFE that reads
it. `getElementById` returned null on every product page, so selecting a pack size
changed no price, no SKU, and **no hidden variant id**. The form submitted the first
variant whatever the shopper chose.

On this catalogue that is not a UX bug. Pack sizes and strengths are variants, so a
customer selecting 240 capsules and receiving 60, or selecting one strength and
receiving another, is a **dispensing-adjacent error** — wrong quantity or wrong
strength of a medicine, caused by the storefront rather than by the pharmacy.

It survived because it was invisible to every safeguard:

- **theme-check passed.** The markup is valid Liquid.
- **Reading the code did not reveal it.** Both halves are correct in isolation; the
  defect is that one runs before the other exists.
- **261 automated assertions passed.** Every one of them ran against rendered
  output, and no multi-variant product rendered in any preview, because every
  fixture had `has_only_default_variant: true`.

The bug was found in the first minute after a multi-variant fixture existed, by
clicking the control in a browser.

**The rule this gives us.** A branch that renders in no preview is covered by no
check, however many checks there are. When adding a branch, the question is not
"did I write a test" but "does this appear in rendered output at all" — if not, the
fixture is part of the work, not a follow-up. `archive/docs/COVERAGE.md` tracks what still
renders nowhere.

One other was found the same way in the same pass: **the PDP's own Add to bag had
never been exercised.** The harness dropped the form's `data-ajax-add` attribute,
which is what binds the AJAX handler, so every add-to-cart check clicked a
collection tile instead — a different code path. The button itself turned out to be
fine; the harness had been lying about it.

The variant defects that came after were the same shape. The one-option fixture's
first variant was in stock, so nothing rendered a product whose first variant is
sold out and also the cheapest. That is the case where `price_min` and
`selected_or_first_available_variant` point at different variants, and most of those
defects lived there. `setup/verify/variant-integrity.py` has the fixture now and
records what it caught.

### 2. Consent could not be answered on a mobile product page

The banner shipped at `z-index: 90`. The sticky mobile buy bar sits at 150. On any
product page below the mobile breakpoint the buy bar was painted over the bottom of
the banner, physically covering **Accept and Reject**. The banner was visible. Its
buttons were not clickable.

Product pages are the highest-traffic page type on the site, and mobile is the
majority of that traffic. So for most visitors, on the page they were most likely to
land on, the consent choice could be neither given nor refused.

That makes it **a compliance failure before it is an analytics one**. Under GDPR and
the ePrivacy regulations a refusal has to be as available as an acceptance; a banner
whose Reject button cannot be pressed does not meet that, regardless of what the
banner says. The analytics consequence — the theme fails closed, so nothing
non-essential fires until consent is answered, so those sessions were invisible to
GA4 — is the smaller of the two problems.

Like the variant picker, it was invisible in code review. Both values are correct on
their own. `z-index: 90` is a sensible number for a banner and `150` is a sensible
number for a buy bar; the defect only exists in the relationship between two
declarations in different files, at one viewport, on one template.

**The fix, and why the check is written the way it is.** The banner is now `400`,
above every other fixed layer in the theme. The regression check does *not* read the
stylesheet — asserting `z-index: 400` would pass while a new element at 500 buried
the banner again, which is exactly how this arrived. Instead it puts the browser at
the mobile viewport, finds the Accept and Reject buttons, and calls
`document.elementFromPoint` at their centres, asserting that what is topmost at that
pixel is the button itself. That fails for *any* cause — a new fixed element, a
transform creating a stacking context, a drawer, a chat widget — not just for a
stylesheet edit. It was confirmed to fail at the old value before being kept.

**If you add a fixed or sticky element to this theme**, that is the check you will
hit, and it is asking a real question: does your new element cover the consent
controls on a mobile product page? Raising its `z-index` past 400 to make your
element sit on top is the wrong answer. The consent banner is meant to be the
topmost layer on the site.

### 3. The pharmacist questionnaire gate failed open (24 Sep 2026)

A gated product carries a `pharmacy.questionnaire` metafield pointing at a
questionnaire. If that questionnaire was deleted, the metafield's `.value` resolved to
nil, which the product page read as "not gated". So a product that should have needed
a pharmacist's questionnaire showed an ordinary buy box. A questionnaire with zero
questions had the same problem.

No check caught it, because every fixture's questionnaire existed and had questions.
It was found by asking what happens when the target is missing, not by a test.

It now fails closed (2ea967e). Whether the metafield is *present* decides if the
product is gated. Whether the questionnaire has questions is checked separately. A
deleted or empty target shows a "not available" notice with no form, no add button
and no opener, and the mobile buy bar is disabled. `setup/verify/questionnaire.py`
has a fixture for each of the two states and asserts that neither offers a way to
add the product. See "Pharmacist questionnaire — the suitability gate" above.

---

## The sticky header's three constants are measured, not taste (10 Sep 2026)

`assets/theme.js` carries three magic numbers in the sticky-header block. All three
look arbitrary, all three were arrived at by measuring the thing misbehaving, and
removing any of them reintroduces a specific defect. They are recorded here because
the obvious maintenance instinct — "why 6? why not 0?" — is exactly wrong.

**`STEP = 10` — a direction change needs 10px of travel before it counts.**
Without it every pixel of movement is a direction, so a shopper resting a finger on
a trackpad flips the bar between hidden and revealed continuously. 10px is small
enough that a deliberate flick still registers instantly and large enough that hand
tremor does not.

**The 6px dead band on `is-pinned`.** The header sits below a 26px announcement bar
on desktop and 24px on mobile, so it pins at roughly `scrollY` 25–27. The obvious
test is `wrap.getBoundingClientRect().top <= 0`, and that is what it was first
written as. Measured: **oscillating 4px across that boundary flipped the class 15
times.** Each flip cross-fades the shadow over 300ms, so the shadow pumps for as
long as the shopper sits there — and the boundary is easy to sit on, because it is
where iOS rubber-banding parks you. Pinning now latches at `top <= 0` and only
releases above `top > 6`. **Same 4px shake, measured again: 1 flip.**

That 15-to-1 is the whole justification for the number. If you remove the band the
suite still passes, the page still looks right in a screenshot, and the defect only
appears when a human wobbles near the top of the page.

**`GRACE = 500` — the gesture window.** Only a `wheel`, a `touchmove` or a scrolling
key may hide the bar, and only within 500ms. This exists because hiding on *any*
downward scroll meant the skip link hid the very header its `scroll-padding-top` had
just reserved 130px for, leaving the shopper looking at empty space above their
target. Two details are load-bearing:

- **`Enter` is not in `SCROLL_KEYS`.** Activating the skip link is a keydown; if it
  counted as a scroll gesture the fix would undo itself.
- **The window is refreshed by scrolling while already open.** iOS fires no
  `touchmove` once the finger lifts, but momentum keeps scrolling. A fixed 500ms
  from the last touch would stop hiding halfway through a flick, which reads worse
  than never hiding.

Revealing is deliberately *not* gated — a programmatic scroll that brings the header
back is never the wrong way to be wrong.

**If you change any of these**, re-measure rather than reason about it: drive a
browser, oscillate across the boundary, and count `class` mutations on `.hdr-sticky`
with a `MutationObserver`. That is how all three numbers were set.

**Related:** the header's height is now constant at every breakpoint (122.4px
desktop, 112.1px mobile) and `--hdr-pinned` in `base.css` must track it — it is what
`scroll-padding-top` uses to keep anchors clear of the bar. If you change the
header's height, change that token in the same edit.

---

## Reading width — one token, 580px, and it stops working below 14.5px (25 Sep 2026)

Body copy is capped at `--measure` in `base.css`: policies, the seven legal-sidebar
pages, articles, product descriptions, collection and gift-voucher copy, about,
careers, withdraw, loyalty, wishlist and common conditions. The aim is under about
90 characters a line. Before this, the legal pages ran 153 and articles 190.

**The limit: 580px only holds for text at 14.5px and above.** A pixel cap gives a
character count that depends on the type size and the letters. Measured with every
accordion open, 580px gives 89 or under on every page. The worst is the wishlist
note at 14.5px, which is the smallest text using the token. At 600px that same note
reached 93. So did a line of short, narrow words on withdraw.

What that means when you add copy:

- **Text smaller than 14.5px needs its own, narrower cap.** Do not put it under
  `--measure`; it will pass review and run over 90.
- **Do not raise the token.** 600 and 620 were both tried and measured over 90.
- **The 17px intros are not on the token.** They stay at `64ch`, which measured 75
  to 85 characters at that size. A `ch` cap scales with the font; a pixel cap does not.
- **Check a change by counting characters on rendered lines, not by pixel width.**
  Count them at every width, with accordions and tabs open (next section).

---

## Audits have to open every accordion, tab and modal (25 Sep 2026)

**Any audit of this site, by a script or by eye, must open every accordion, tab,
`<details>` and modal before it measures anything.** Content that is collapsed or
hidden on load has no size, so an audit that looks at the page as it loads does not
check it. The audit does not report it as a pass or a fail; it leaves it out.

It has happened twice:

1. **The prescriptions form.** Five labels let their selects run off phone screens,
   51px off at 360. The width audit found four. The fifth was in the "Repeat
   prescriptions" tab, hidden until clicked, and turned up only because someone
   went looking.
2. **The common conditions FAQ.** Its answers ran 1000px wide, about 140 characters
   a line, inside collapsed accordions. The reading-width audit measured every page
   and never saw them.

**For clipping, `setup/verify/sweep.py` handles this now.** It opens every
`<details>` and `[data-acc-toggle]` in `main`. It shows each `[data-view]` tab
through its own button, so the theme lays it out. It checks element bounds in each
state. It also fails on any form control that was never on screen and is hidden by
a toggle, so a new kind of toggle it cannot open fails the check instead of being
skipped.

**Nothing else does it.** Contrast, reading width, spacing and copy checks all
look at the page as it loads unless they are written otherwise. When you write a
new check or run an audit by hand:

- Use the sweep's walk. Copy its `CLIPPED` preamble: open everything, then visit
  each tab.
- Say which states were covered. A result that only covers the page as loaded
  should say so.

---

## Correct code, wrong behaviour — the defects only a browser finds (10 Sep 2026)

**Eight** defects in this theme have now shipped through code review and a passing
test suite, and every one was found the same way: by driving a real browser and
measuring what it did, rather than by reading the source. Two of them have their own
section below ("The mega panel scrolled sideways at 1024"); this is the tally and
the pattern they share.

| # | Defect | Why reading it did not help |
|---|---|---|
| 1 | Variant picker: JSON emitted after the IIFE that reads it | Both halves correct in isolation; only the order was wrong |
| 2 | Consent banner at `z-index: 90` under a buy bar at `150` | Both numbers sensible; the defect lives between two files |
| 3 | `.crec-add`/`.wish-add` taking ink from `--c-on-primary` on an `--c-accent` surface | Passed while both tokens happened to resolve alike |
| 4 | Mega panel asking 1030px of columns inside a 904px panel at 1024 | The arithmetic is only wrong at one viewport nobody rendered |
| 5 | Mega panel `max-height` in `vh`, which cannot know the panel's own top | Correct unit, correct number, wrong thing to measure from |
| 6 | `--hdr-delta` declared once at 32px for a band that compresses 26.4px | The comment promised "per breakpoint"; the override was simply never written |
| 7 | Skip link landing with 46px of `main` behind the pinned header | Nothing in the source is wrong — the missing thing is a declaration that was never there |
| 8 | Mobile predictive search scrolling out of view while still focused | Every component correct; the composition was not |

The last three were found in one measuring pass on 10 Sep 2026. None is a typo, a
broken selector, or a thing a linter can see. `theme-check` reports 0 errors, 59/59
liquid checks pass and 49/49 templates render clean with all eight present.

**The shape they share.** Each is a *relationship* between two things that are
individually correct — a declaration and the element it was meant to cover, a token
and the surface it sits on, a value and the breakpoint it was never written for.
Source review reads one thing at a time, so it structurally cannot see this class of
defect. Only the composed, rendered, scrolled result can.

**What it costs when it slips through.** Not evenly. #1 was dispensing-adjacent —
wrong strength or quantity of a medicine. #2 was a compliance failure before it was
an analytics one. #7 is an accessibility defect aimed precisely at the person who
most depends on the control. #8 put a shopper on the highest-intent control on a
pharmacy site, typing into a field that had scrolled off screen. "Looks fine" is not
evidence about any of these.

**They cluster at viewports nobody looks at.** #4, #5 and #6 are all defects of the
in-between widths — 904px of panel at a 1024px viewport, a nav that wraps to two
rows at 1024, a compression band from 901 to 1100. Work gets checked at 1440 and at
390 and the laptop widths between them go unrendered. When measuring, include 1024.

A ninth belongs beside them for a different reason: the PDP's Add to bag had never
actually been exercised, because the harness dropped the `data-ajax-add` attribute
and every check clicked a collection tile instead. The button was fine. **The check
was lying**, which is the failure mode above applied to the safeguards themselves.

**The rule.** For anything positional, layered, scroll-linked, focus-linked or
breakpoint-dependent, a passing suite is not evidence. Put a browser at the real
viewport, do the thing a shopper would do, and measure the result — heights,
`getBoundingClientRect`, `elementFromPoint`, class mutations, CLS. Write the check
against *observed behaviour* rather than against the declaration you just made:
`verify/consent.py` asserts what is topmost at the button's centre pixel, not that
`z-index` is 400, precisely so it catches causes nobody has thought of yet. And see
"Why fixture coverage matters" above for the other half of this — a branch that
renders in no preview is covered by no check, however many checks there are.

---

### The consent banner is ours to maintain, including when the law moves (11 Sep 2026)

Shopify's own privacy banner was disabled in Settings -> Customer privacy, because
running it alongside ours put its z-index 2,000,000 over our 400 and made our Accept
and Reject unclickable. Ours was kept: it drives Shopify's Customer Privacy API
directly (`setTrackingConsent`), honours the shop's region rules
(`shouldShowBanner`), offers granular preferences/analytics/marketing, fails closed if
the API errors, and carries 80 assertions plus a recorded contrast decision. Shopify's
banner duplicated that rather than adding to it.

**Global Privacy Control was checked before disabling theirs, and is not lost.** GPC is
handled by the Customer Privacy API, not by the banner UI. Measured on the live store
with `Sec-GPC: 1` and `navigator.globalPrivacyControl = true`, with Shopify's
`storefront-banner.js` blocked at the network layer so its banner never entered the DOM:

    sale_of_data       ""  ->  "no"
    saleOfDataAllowed  true -> false
    getCCPAConsent()   "no_interaction" -> "no"

Identical with the banner script allowed and blocked, and set before any banner is
touched. So the signal is processed by the API we already load ourselves. For Irish
traffic it is not load-bearing anyway - region resolves IE, regulation GDPR,
`saleOfDataRegion` false, `shouldShowCCPABanner` false - but it works for US visitors
where GPC has legal force under CCPA/CPRA.

**The standing obligation this creates.** Shopify maintains their banner against
regulatory change; nobody maintains ours but us. If consent law changes - new
categories, new wording, new default behaviour, a new signal like GPC - our banner does
not follow automatically and someone has to update `snippets/consent-banner.liquid`,
the handlers in `theme.js`, and `verify/consent.py`. That is a live obligation for a
pharmacy, which sits in a higher-scrutiny sector than most retail. Whoever takes this on
at handover needs to know it is theirs.

If that maintenance is ever unwanted, the reversal is cheap and asymmetric: re-enable
Shopify's banner in Settings -> Customer privacy (one toggle) and remove ours. Keeping
both is the one option that is never correct - it is where this started.

### The sub-class the harness cannot reach: markup Shopify injects (11 Sep 2026)

The eight defects above are all findings a browser could reach locally. Two more found
on 11 Sep 2026 are a different animal: **they are caused by DOM the preview never emits,
so no local check can fail, however the harness is written.** Rendering the theme
locally is not rendering it on Shopify.

**1. The sticky header never pinned on a real store.** `{% sections 'header-group' %}`
wraps each section in `<div class="shopify-section shopify-section-group-header-group">`.
That wrapper is exactly as tall as the header inside it - 122px against 122px - and a
sticky element cannot travel past its parent's box, so it scrolled away like static
content and took the departments and the search with it. Locally the header renders
straight into body flow, whose box is the whole page, so it pins perfectly. Fixed in
aea18dc by making the wrapper the sticky box.

**2. Two consent banners, and Shopify's covers ours.** Shopify's own privacy banner
(`shopify-pc__banner`, z-index **2,000,000**) renders alongside our `.cc-banner`
(z-index 400). `elementFromPoint` at the centre of our Accept button returns
`DIV.shopify-pc__banner__btns`: our Accept and Reject are unclickable. This is the
z-index-90-under-the-buy-bar incident again, from an element that does not exist in the
preview at all - so `verify/consent.py`, which was written precisely to catch that class
of failure by hit-testing the button's centre pixel, passes 80/80 locally and would
never have seen it.

**What this changes.** "Passing locally" now has a documented ceiling. For anything
positional, sticky, layered or z-index dependent, the check has to run against a real
store before it means anything. Two specific traps that will recur:

- **Every section in a group carries the group class.** The announcement bar is also a
  `shopify-section-group-header-group`, so styling the class pins the announcement bar
  on top of everything. Scope to the section you mean - `:has(> .hdr-sticky)`.
- **A sticky wrapper keeps its box when its contents translate away.** After the header
  hid, an invisible 122px band swallowed every click beneath it; `elementFromPoint`
  returned `DIV.shopify-section` instead of the page. `pointer-events: none` on the
  wrapper with `auto` on the header. Test hit-testing, not just position.

Both were found by driving the live store with the preview theme, which is the only
place they exist. There is no harness change that would have caught either.

## The PSI logo in the footer is a regulatory requirement

PSI *Guidance on Internet Supply of Non-Prescription Medicines* (v1, 2015),
section 2.1: the EU common logo must be "clearly displayed on every page of
the website which relates to the sale of medicines online, which links to
the Internet Supply List on the PSI website". Collection pages, search and
the cart all offer medicines, so the footer instance is the one that meets
this; it links to the list filtered to our entry (registration 10001884).
Do not remove it, hide it per template, or point it at our own page. The
same section also requires the PSI's contact details, a link to psi.ie and
a two-year transaction-record statement, which live on the Internet Supply
Pharmacy page.

**Source relied on, checked 10 September 2026:** PSI *Guidance on Internet
Supply of Non-Prescription Medicines*, Version 1, dated June 2015 (July 2015
in its page headers), the version published on psi.ie on that date, plus the
Internet Supply pages on psi.ie. Whether the PSI has issued anything since,
or has corresponded with the client about their listing, is unconfirmed;
re-check both before relying on this section again.

The copy beside the product buy box (PSI-registered line, Ask a pharmacist,
a second logo) is reassurance, not compliance. It shows on medicines only:
products tagged with the restricted tag or typed under "Pharmacy > ...".
The Product section's "Show the pharmacist lines on every product" checkbox
turns it on everywhere; default off.

## The mega panel scrolled sideways at 1024 for as long as it existed

Found by measuring, September 2026. The Medicines & Health panel asked for six
columns with a 155px minimum each: 6 x 155 plus five 20px gaps is 1030px of
content inside a panel that is 904px wide at a 1024px viewport, so the panel
scrolled horizontally by 128px and the sixth column sat off the right edge.
Nothing reported it, because a panel that scrolls sideways looks like a panel
that ends where the scroll starts, and `verify/sweep.py` only checks document
overflow on pages whose panels are closed.

The fix removed the fixed column split entirely: the groups are one flow and
the browser balances them into the panel's own column count, so the columns
narrow instead of overflowing. If a panel is ever given a fixed
`grid-template-columns` again, check the arithmetic against the panel width at
1024, not just at 1440.

The panel's height cap has the same shape of problem. `max-height` in `vh`
cannot know the panel's top, which moves from 147px to 211px when the nav wraps
to two rows at 1024, so a cap generous enough at 1440 put the bottom of the
panel below the viewport at 1024, where the sticky nav means it can never be
scrolled to. `theme.js` now sets the cap from the panel's measured top when it
opens; the `84vh` in the markup is the no-JS fallback.

## The mega menu comes from taxonomy.json, like everything else in the nav

Until September 2026 the four multi-column panels were scraped out of the
design handoff HTML with a headless browser and rewritten on the way through:
hover styles mapped to classes, hrefs re-derived by handleizing the anchor
text, brand hexes swapped for tokens. The mobile drawer, the breadcrumbs and
the category chips all came from `taxonomy.json`, so the desktop nav was the
one surface that could disagree with it and nothing would notice.

`gen_mega.py` reads the taxonomy now. The switch produced identical content —
same departments, groups, leaves and order in all eight panels — because the
design markup had not in fact drifted; the risk was that it could, silently.
All the design ever supplied that the taxonomy cannot is panel chrome (width,
the no-JS fallback offset, padding, column count), which is a table at the top
of the generator. Column splits are computed rather than drawn: the split that
minimises the tallest column while keeping taxonomy order reproduces exactly
the splits the designer had chosen by hand.

`setup/verify/mega-taxonomy.py` asserts the result against the taxonomy and
also asserts the generator has not gone back to reading the design file or
importing a browser. A build no longer needs either.

## The multi-buy offers are automatic discounts, not anything in the theme (30 Sep 2026)

The eight multi-buy and gift offers from the old site ("3 for €10", "Buy one get
one half price", "Free tanning mitt with every Tan Studio item") are Shopify
automatic discounts, applied at the cart. **Nothing in the theme implements
them.** The theme only shows the words, through `custom.promo_label`, and the
words and the discount are two separate things that have to be changed together —
the label says "3 for €10" whether or not a discount exists behind it.

- **Built and checked by** `setup/offers/discounts.py` and
  `setup/verify/offer-carts.py`. The verify script builds one real cart per
  discount against the real catalogue and matches the total **to the cent**.
- **Read the percentage note in `discounts.py` before changing a price** in any
  of these sets. Shopify truncates the per-line discount rather than rounding it,
  so the obvious percentage (the saving divided by the price) leaves every
  fixed-price offer a cent short and "3 for €10" charges €10.01. It did, for
  about ten minutes on 30 Sep, until a cart test with an exact match caught it.
  An earlier run of the same test passed 9/9 with a one-cent tolerance, which is
  why that tolerance is now zero.
- **Two collections exist only to scope a discount**: `3-for-10` and `3-for-5`,
  smart collections on the tags `Clearance > 3 for €10` and
  `Clearance > 3 FOR €5`. They are not published and nothing links to them, so
  they look exactly like the unlinked collections deleted on 25 Sep (below).
  **Deleting them switches two offers off silently.** Their descriptions say so.
- Every one of them has `combinesWith.productDiscounts: true` and no
  `usesPerOrderLimit`: six of a 3-for-€10 product is €20, not one discounted
  trio and three at full price.
- **The free mitt is not added to the bag for the customer.** Shopify discounts a
  gift once it is in the cart; it never puts it there. The old site behaves the
  same way, which is why this was left as is rather than automated.

## Seasonal rotation is manual — nothing in this theme is date-scheduled

**There is no date scheduling anywhere in the theme. Not the hero slides, not
the hot offers, not the category pills.** This gets assumed otherwise, so:
rotating anything seasonal is a person editing the theme, twice a year, in
these places:

- **Category pills** on a department page: the `chip_links` override on that
  collection's template (theme editor → the collection page → Category chips).
  September 2026 example: Gifting's override lists its six taxonomy entries
  with Christmas Shop moved last; delete the override in November and the
  taxonomy order (Christmas Shop first) shows again. Overrides on taxonomy
  departments are validated by `setup/verify/chips-taxonomy.py` — labels and
  links must match taxonomy entries, order is free.
- **Homepage category pills**: the row is the eight departments from
  `snippets/departments.liquid` (generated, nav order) plus the section's
  promo-link blocks (Sale, Brands, kept equal to the header's). To promote
  something for a season add Pill blocks to the section: any Pill block
  replaces the generated eight, the promo links stay; delete the Pill blocks
  to go back. `setup/verify/chips-taxonomy.py` rejects a pill that is not a
  nav department or a header promo link.
- **Hero slides**: add/remove/reorder the slide blocks in the editor. The
  "Summer Travel Shop" slide is one of these; retitle or remove it when the
  season turns. An offer flash is the slide's Badge setting, live text and
  blank by default; never a starburst baked into the artwork.
- **Homepage promo strip**: the strip's text, button and link are section
  settings (theme editor → homepage → Promo strip). September 2026 it still
  reads "Pollen levels are rising"; that is hayfever copy from spring.
- **Sale page**: heading, badge, copy and chips are settings on the Sale
  collection template. Keep the heading "Sale" outside a named event.
- **Search page popular categories**: the pills on the empty-search state
  are the `popular_links` setting on the Search results section, one
  "Label | URL" per line.
- **Hot offers**: edit the offer blocks. Do not bake limited-time claims into
  the artwork itself; the badge text is a setting precisely so it can expire.

**Why not Liquid date gating** (`{% if "now" ... %}`): Shopify caches rendered
pages on its CDN, and Liquid runs when the cache fills, not when the customer
loads the page. A date comparison evaluated at cache time shows stale state
for as long as the cached copy lives — a "Christmas from Nov 1" pill can stay
hidden days into November, or a "until Dec 26" banner can survive into
January, differently per CDN node. The failure is silent and unreproducible
from the office. If gating is ever built, it must be client-side JS reading
`data-start`/`data-end` attributes (visitor clock, link still present in
cached HTML, brief flash before JS hides it — all acceptable; stale cache is
not).

**Agreed line (Sep 2026):** if seasonal slots become a pattern across pills,
hero and hot offers together, build one shared JS mechanism then. Not before.

## Product page: "You May Also Like" is under the description on purpose (10 Sep 2026)

The recommendations list used to sit in the buy column, under the delivery
lines. It was moved to the left column, after the description tabs and before
the FAQ, capped at 600px wide. Two reasons, and one cost.

1. Beside the gallery it competed with Add To Bag for the same column.
2. The gallery image went from 85% to 70% of its box the same day (the
   catalogue is 600px square, so 85% was upscaling at 1440; see
   IMAGE-BRIEF.md). With the list gone the buy column ends at 531px beside a
   673px gallery, a balance that needs no height cap on the gallery.

The cost: the page is 325px taller at 1440 than before, because the list no
longer fills space that the taller gallery gave for free. The columns
balancing was judged worth the scroll. If that ever flips, the reversal is
to move the list back into `.pdp-right` after the buy-assurance block, and
drop the `.pdp-recs` flex order from the mobile rules; do not cap the
gallery height instead, which shrinks the photo to fit whatever the buy
column happens to be for that product.

**Changed 28 Sep 2026, at the client's request, for wide desktop only.** From
1101px the product page is a CSS grid (`main-product.liquid`, the
`min-width: 1101px` block): gallery and buy box in row 1, the tabs and "You
May Also Like" side by side in row 2, the list in the 400px buy column and
starting level with the tabs, then the FAQ. The description keeps `--measure`.
Below 1101px nothing changed: the left column is 540px at 1024, too narrow to
share, so the list stays under the description.

The balance above no longer holds. The buy box has grown (PSI verify block,
Save for later, express placeholder), and on 4 of 5 preview fixtures it now
ends below the gallery: by 16px (Nurofen Plus), 21px (the gated fixture),
73px (sold out) and 120px (CeraVe, with variants) at 1440. Row 2 starts under
whichever is taller, so that is the gap under the gallery. The earlier rule
still applies: do not cap the gallery to close it. If the gap matters, the
fix is to shorten the buy box.

**`psi25/order-review` also edits `sections/main-product.liquid`** (the express
checkout and the gated buy box). It branched before this layout landed
(8e8ec97), so it must be rebased onto `main` before its next push to any
theme. Pushing it unrebased puts the old file back and silently undoes the
side column. Before pushing that file, check that its `min-width: 1101px`
grid block is still there.

## Brand pages — which brands get one (24 Sep 2026)

`setup/brands.json` was rebuilt from the live catalogue on 24 Sep 2026. It is
the source for the Brands page A–Z, the brand collections in
`collections.json`, and the brand tier in the category snippets. It had been a
design-time list: 44 of its 88 brands had no products, and the store's biggest
vendors (BPerfect, Medicare, Jenny Glow) had no page.

The rule: **a vendor with 5 or more published products gets a page.** Two
deliberate exceptions:

- **Thin but kept:** 19 brands with 1–4 products stay, and are flagged to the
  client as a ranging question rather than removed. They include CeraVe,
  Sudocrem, Bio-Oil, Neutrogena, Oral-B and Viagra Connect, which customers
  search for by name.
- **Adopted, not duplicated:** BPerfect, Voduz, Luna By Lisa and Pestle & Mortar
  use the client's own collections (same handle, same vendor rule). They
  remain the client's, and `provision.mjs rules` will not overwrite them.

A brand page's rule is `VENDOR EQUALS <title>`. Shopify matches it ignoring
case and accents: the fabÜ page matches vendor "Fabu". So a title can read
"Calvin Klein" while the vendor stays "CALVIN KLEIN".

**A new collection 404s on the storefront until it is published** to the
Online Store. Publishing needs `read_publications` and `write_publications`,
which the catalogue token has carried since 24 Sep (see "Store API access").
All 134 brand collections were checked as published on that date.

Letter chips on the Brands page link only to letters that have a brand. The
rest render greyed out, so removing a brand can no longer leave a chip that
jumps nowhere. X and Y are greyed out as of this rebuild.

---

## Category pages: 30 removed, 4 switched to type (25 Sep 2026)

141 of the 193 group and sub-category pages were empty. Every one matched on a
tag (`TAG EQUALS <title>`) that no product carried; every page matching on type
had products. The pages were reviewed one by one (word match on product titles,
then a hand check of every candidate). Decisions, approved by Kakion:

- **30 removed from `taxonomy.json`**: 17 dropped (nothing stocked, e.g. Nail
  Polish, Nicotine Gum, the Diabetes Care group; or a duplicate, e.g. Verucca,
  Pain Relief & Headache) and 13 merged into their parent (under 3 products, e.g.
  Nicotine Sprays, Insoles). The menus, chips and breadcrumbs regenerate from
  the taxonomy, so the links went with it. The store collections were left
  in place at first, then deleted with the other unlinked collections (next
  section). To bring one back, put its title back in `taxonomy.json`,
  regenerate, and recreate the collection from its saved rule.
- **4 switched to an existing type**, recorded in `collection-rules.json`:
  Ladies Fragrance, Baby Accessories, Baby Skincare, Slimming.
- **Tag-based sub-pages are filled by tagging products** with the rule's exact
  condition. Take it from the live rule, not the page title: Dry Skin, Eczema &
  Psoriasis matches the tag `Eczema & Psoriasis`.
- Medicines & Health pages wait for a pharmacist's sign-off, and 39 pages the
  word match could not fill go to the client to map by hand.

`setup/verify/mobile-nav.py` used to assert 18 Medicines groups and 18 Vitamins
items. It now reads both counts from `taxonomy.json`, so the next removal does
not turn it red.

---

## Unlinked store collections deleted (25 Sep 2026)

98 collections on the store had no link from anything: not the generated
menus, chips or breadcrumbs, not the brand A-Z, not a theme setting, not an
admin menu, not a redirect. All were deleted, approved by Kakion; no discount
was limited to any of them.

- **68 were empty**: the 30 category pages removed above, and brand
  collections for brands with no products.
- **30 had products**, and every product was also on a linked page. They were
  old type-based pages that duplicated a menu page (`face-makeup`,
  `cold-flu`, `supplements`, `gifts`, `baby` and so on) plus `brands`, which
  matched products typed `Brands > <brand>`. Those 36 products were retyped
  to real categories first.
- **Kept deliberately:** `pharmacist-review-required` (the staff worklist of
  every tagged product) and `frontpage` (Shopify's default).

Every deleted collection's title, handle, rule, description and SEO is in
`archive/store-cleanup-2026-09-25/deleted-collections.json`. A recreated
collection gets a new ID.

How the check was done, so it can be repeated: take every store collection
handle and remove the ones that are in `collections.json` (menu, group, leaf),
in `brands.json`, or in the theme as `/collections/<handle>`,
`collections['<handle>']` or a `"collection": "<handle>"` setting. Pull the
live theme too, not just the repo. Watch for false matches: `brands`,
`supplements`, `gifts` and `baby` all appear in the theme as **block IDs** in
`index.json` and `header-group.json`, which are not links.

---

## Products on no category page retyped (25 Sep 2026)

195 products were on no category page: typed as a brand (`Brands > BPerfect`),
with no type, with a leftover type (`Clearance > 3 for €10`, `Luna Haircare`),
with a brand name as the type, or missing the department (`Lips` for
`Beauty > Lips`). 175 were retyped, approved by Kakion; 20 are held for a
decision. Every row, before and after, is in
`archive/store-cleanup-2026-09-25/retypes.csv`.

- Every new type is one that an existing type rule already matches, so each
  product lands on a leaf page and its department.
- The 6 Mx Health home tests were typed `Pharmacy > Medical Devices` and tagged
  `Self Testing Kits`; the pregnancy and ovulation tests also carry their
  page tag and `Trying To Conceive`. Group pages match their own tag only;
  they do not collect their sub-pages' products.
- A `Pharmacy >` type turns on the pharmacist lines in `buy-assurance`, so
  Dettol, surgical spirits and similar now show them. It does not gate
  anything; the pharmacist hold follows the `pharmacist-review` tag.
- Sidena 50mg (sildenafil, P on the HPRA list) had no `pharmacist-review`
  tag, so it sold without the questionnaire. It has the tag now (next section).

---

## Licensed medicines outside Pharmacy tagged (25 Sep 2026)

18 products on the HPRA register (8 P, 10 GSL) were typed outside the Pharmacy
department. With no `Pharmacy >` type they skipped the pharmacist lines in
`buy-assurance`, and with no `pharmacist-review` tag they could be added to
the bag in one click. Approved by Kakion:

- **All 18 tagged `pharmacist-review`**, P and GSL alike. The tag is what
  blocks quick-add (`product-restricted`), so it went on first; 12 were live.
- **10 retyped into Pharmacy**: Sidena (`Pharmacy > Sexual Health`), Canesten
  Combi (`Pharmacy > Women's Health`), Anhydrol Forte and both Capasal
  shampoos (`Pharmacy > Medicated Skincare`), Corsodyl gel and mouthwash
  (`Pharmacy > Oral Health`), Calpol 6+ Fastmelts and Deep Heat Spray
  (`Pharmacy > Pain Relief`), Desenex (`Pharmacy > Foot & Nail Care`).
- **8 kept their type** so they stay where customers look for them; the tag
  gives them the pharmacist lines and the quick-add block: Ferrograd,
  Clonfolic, Magnesium Verla, both Kalms (Vitamins), and the three Ovelle
  emollients (`Skincare > Body Care`).
- **For the pharmacist**: the register match for Corsodyl 50g Dental Gel
  (matched the mouthwash licence) is for another product; it is on the "Check
  licence" tab of the pharmacist workbook.
- **Calpol 6+ Fastmelts has its own licence.** The title match picked the
  infant suspension, but the register lists Calpol Six Plus Fastmelts 250 mg
  Paracetamol orodispersible tablets, PA23490/003/005, general sale, with no
  supply conditions (checked 26 Sep 2026). It was on the "Check licence" tab as
  a mismatch; that row now records the correct licence.

The list came from `medicine-classification-2026-09-25.csv` (HPRA register
match); a product it did not match is not proven to be a non-medicine.

## pharmacist-review rebuilt from the HPRA register (25 Sep 2026)

The tag had been applied by department, so plasters, bandages and throat sweets
carried it alongside medicines. It was rebuilt from
`medicine-classification-2026-09-25.csv` (a title match against the HPRA human
register), approved by Kakion:

- 532 tagged before. 208 had no licence match; each was checked by hand.
  **200 untagged**, their previous tags logged so any can be restored.
- **8 kept** although the title match missed them: Ov Iodine Tincture 30ml
  (Iodine Tincture BP, PA0206/025/001, pharmacy only), Broncho Stop Junior
  (probably Buttercup Bronchostop, TR2006, general sale), Fleaway Plus x5
  (veterinary medicines, not on the human register) and Hayfever Heroes Bundle
  (may contain antihistamines).
- Licensed P and GSL: all 202 were already tagged. The 162 the match marked
  "unsure" were left as they were: 122 tagged, 40 not, Sudocrem among them.
- **332 tagged after.** The workbook's "Needs a pharmacist check" (renamed "Medicine classification" on 28 Sep) tab lists
  them, licensed medicines first.

"No match" means the title matched no licence name, not that the product is
proven not to be a medicine. Any product with a licence number on its pack
gets the tag, whatever the classification says.

### 17 licensed medicines the match missed, tagged 26 Sep 2026

A re-check against the register found 17 licensed products still untagged,
15 of them live: Nizoral Dandruff Shampoo and Oilatum 500ml (both P), four
Sudocrem, two E45 Cream, two Dettol Liquid, Regaine Men Foam, Caldesene,
Caldease, Oraldene, two Ov Calamine Lotion and Ov Aqueous Cream (GSL). All 17
tagged `pharmacist-review`; before state in
`archive/store-cleanup-2026-09-26/tag-and-draft-before.csv`. The classification
CSV now carries their status, marked "corrected by hand 26 Sep 2026".

The title match failed in three ways. Any rebuild that reuses it will fail the
same way:

- **A pack size read as a strength.** "Caldesene Medicated Powder 100G" was
  rejected against the licence's "10%" because 100g looked like a
  contradicting strength. Same for Oraldene, Nizoral and Caldease.
- **Every word of the licence name required in the title.** "Dettol
  Antiseptic Disinfectant", "Regaine for Men Extra Strength Scalp Foam" and
  "Sudocrem Antiseptic Healing Cream" have words the titles lack. E45's
  licence name runs on into its ingredients ("E45 Cream White Soft
  Paraffin"), so "white" became a required word.
- **Generic licence names count only when they begin the title.** Ovelle's
  licences are "Calamine Lotion" and "Aqueous Cream"; the titles start "Ov".
  The licence holder was never used.

Those products were then left untagged because the rebuild left "unsure"
matches as they were, and the old tag had followed the Pharmacy department,
which none of them are in.

**Pack size changes the class, too.** Panadol Actifast 20Pk, Panadol Extra
24Pk, Lemsip Max Cold & Flu 10Pk and Gaviscon Peppermint 600ml match GSL
licences, but the licence makes those pack sizes pharmacy only. The
classification CSV and the workbook now say P for all four. Paracetamol and
pseudoephedrine licences also cap packs per sale (one or two); nothing on the
website enforces that yet.

## Two things that look like failures when tagging products

- **Shopify splits tags on commas.** `tagsAdd` with `Skin, Hair & Nails`
  stores two tags, `Skin` and `Hair & Nails`. The Skin, Hair & Nails page
  still picked the product up, but check the stored tags after adding any tag
  with a comma, and never give a new rule a comma in its condition.
- **Collection pages lag a few minutes behind a tag change.** Straight after
  a bulk tag run, three Vitamins pages read 0 products although every product
  carried the right tag; a few minutes later all were there. Read the
  product's `collections` to check a tag worked, or wait before counting a
  page.

---

### Calpol Vapour, Carnation pads and Capasal corrected, 28 Sep 2026

Calpol Vapour Plug & Nightlight and Calpol Vapour Refill Pads 5Pk carried
`pharmacist-review` because the title match paired them with the Calpol
infant suspension licence on the word "Calpol". Neither is on the HPRA
authorised human medicines list (`latestHumanlist.xml`, checked 28 Sep), so
the tag came off both. Capasal Therapeutic Shampoo 250ml had vendor
"Canesten", which put it on the Canesten brand page; it is now "Capasal". It
keeps the tag (Capasal Therapeutic Shampoo is P). Its leftover `Canesten`
tag was swapped for `Capasal` later the same day. Before state in
`archive/store-cleanup-2026-09-28/untag-and-vendor-before.csv`.

Carnation Bunion Pads 4Pk lost the tag the same day, for the same reason:
the match offered it Carnation's three licences (Callous Caps, Corn Caps and
Vericap, PA23188/001/001-003), and it is none of them. Eight more Carnation
products carried it on the same non-match and lost it later that day: Heel
Grips, Gel Toe Separators, Animal Wool, Hydrocolloid Blister Care, Corn Pads
9Pk, Fleecy Stretch Padding, Chiropody Felt and Corn Shields. None is on the
register and none is medicated. Callous Caps and Corn Caps (salicylic acid)
are licensed and keep it. The client pack followed on 29 Sep: the nine rows came out of the
"Medicine classification" tab and the Handover now says 337 (219 licensed,
118 other). The eight are still typed `Pharmacy > Foot & Nail
Care` (Corn Shields `Pharmacy > First Aid`), so they stay on those pages and
show the pharmacist lines, and they are still off the Shop channel.

The two Calpol Vapour products were then retyped `Baby > Baby Health`, the
page Snufflebabe Vapour Rub is on, with the type-mirror tag swapped to match,
and put back on the Shop channel. That takes them off Medicines & Health.
Vicks Comfort Plug In is the same kind of product and is still typed
Children's Medicine and tagged `pharmacist-review`; it was not reviewed.
Before state for the 28 Sep afternoon changes is in
`archive/store-cleanup-2026-09-28/carnation-calpol-capasal-before.csv`.

---

## Predictive search — what the store's search actually does (28 Sep 2026)

The header dropdown is `sections/predictive-search.liquid`, fetched by
`theme.js` from `/search/suggest`. Three things about the search behind it
that the Shopify docs get wrong for this store:

- **It is semantic search, not prefix-plus-one-typo.** "neurofen",
  "nurophen" and "nurfen" all find Nurofen; "paracetamol" finds Panadol Extra,
  whose title never says paracetamol; "headache" finds Excedrin and Nurofen.
  45 misspellings of the top 10 medicine brands all found the right brand.
- **`resources[options][fields]` is ignored.** Adding tag, then body, gave
  identical results for "paracetamol" and "ibuprofen", and restricting it to
  `vendor` still matched titles. Don't add it expecting a change.
- **Synonym groups can't be used here.** Shopify's free Search & Discovery
  app has had synonym groups, but by 28 Sep its Synonyms section was gone on
  this store. Merchants on Shopify's forums report the same from 16 Sep 2026,
  with the move to semantic search; no official Shopify notice was found.
  - **Installed?** The client reports the app is installed. The API can't
    confirm it: the catalogue token has no `read_apps` scope, and there is no
    API for synonym groups.
  - **What's set?** Nothing is visible or editable. A "menthol, deep heat"
    test on 28 Sep had no effect in the dropdown or on `/search`.
  - **So:** the synonym work was dropped, and the draft ingredient-to-brand
    list is not kept. The weak ingredient searches below remain. The levers
    left are product titles and descriptions, which the semantic search reads.
    If Shopify brings synonyms back, rerun the menthol test before relying on
    them.

The weak spots are ingredient searches for combination products: "menthol",
"phenylephrine" (whose top hit is Phenergan, a different medicine),
"caffeine", "guaifenesin", "zinc oxide", "folic acid".

The storefront is password protected, so `/search/suggest.json` returns 401
without the storefront session cookie; the Storefront API answers "Online
Store channel is locked". Test against a logged-in cookie jar.

**The dropdown markup is the ARIA 1.2 combobox pattern.** Focus stays in the
input; arrows move `aria-activedescendant` over `[role=option]` links in
labelled `[role=group]`s inside `#predictive-search-results` (the listbox,
which arrives with each response; `[data-ps-panel]` is only the box). Don't
put anything but groups and options inside the listbox, and don't move focus
into the panel: `funnel.py` checks both. On phones the panel is absolute, not
fixed (`.hdr-sticky`'s transform), and `theme.js` sets `--ps-top` so it
reaches the foot of the screen. Shopify wraps the typed part of a suggested
search in `<mark>`; the preview mock uses `<b>`, and `base.css` styles both.

---

## Generated snippets — edit the generator, never the output (three times now)

Nine snippets are written by three scripts in `setup/`: `gen_brands.py` owns
`brand-az.liquid`, `gen_mega.py` owns `mega-menu.liquid`, and
`gen_category_nav.py` owns the breadcrumb, chips, chip, level, rank and
mobile-nav snippets. The list is the `GENERATORS` map in
`setup/verify/generators.py`. A hand edit to any of these holds only until
the next regeneration, when the generator puts the old markup back.

It has happened three times, each a sitewide sweep that fixed the generated
file and forgot the script:

1. **26 Aug 2026, the colour-token sweep (d34e944).** `brand-az` and
   `mega-menu` were tokenised; `gen_brands.py` still emitted `#92C83F` and
   `gen_mega.py` still emitted `#82C914`. Found the next day by regenerating
   against a clean tree (7e546e7), which is when `generators.py` was written.
2. **10 Sep 2026, the muted-grey merge (2e4997d).** The breadcrumb and
   mega-menu snippets moved to `#666b60`; the two generators carried the old
   value. Caught by the check before the commit and fixed inside it.
3. **10 Sep 2026, the button system (0cde784).** `category-chip.liquid` was
   rewritten onto the `.chip` classes by hand; `gen_category_nav.py` kept the
   old inline-styled anchors. The check went red at 10:34 and 25
   commits landed over it before a562623 mirrored the change at 13:36.

The third is the instructive one. The check existed and was first in
`npm run verify`, but the landing recipe below says `npm test`, and nobody
runs the full chain for a CSS change. So `generators.py` now runs in
`npm test` as well: it needs no server, takes seconds, and a drifted
generator invalidates everything rendered after it.

When a sweep touches one of the nine files, change the generator and run it;
the snippet follows. The snippet's `git diff` should then be exactly what you
meant, and `npm test` green before the branch lands.

## The buttons were inverted, and the hover shadow is now load-bearing (11 Sep 2026)

Primary actions used to rest deep green and go lime on hover. They now rest **lime
with dark ink** and go **deep green with white ink** on hover. Both pairings pass AA
— lime/dark is 7.14:1, deep green/white is 6.13:1 — and the contrast suite reports
1890/1890 either way, so nothing here is an accessibility fix. It is a brand choice.

**Do not remove the `box-shadow` on `.btn-fill:hover`.** It looks like decoration
and it is not. This is the whole reason this section exists.

### Why the lift needs help now

The hover carries a 1px `translateY(-1px)`. Under the old scheme that lift agreed
with the colour: the button went from dark to light as it rose, and a surface that
rises catches more light. Inverted, the button goes from light to **dark** as it
rises. Darkening while rising is what a receding surface does, so the colour and the
motion now pull in opposite directions. The shadow is the only cue left that says
which way the button moved.

### Why it had to be retuned rather than kept

A drop shadow reads as depth by its contrast **against the page**, not against the
button. `rgba(42,43,42,.16)` over white is a 1.26:1 halo whoever casts it — that
number does not change. What changed is the edge it sits beside:

| Hover state | Button edge vs page | Halo vs page | Halo as a share of the edge |
|---|---|---|---|
| Old: lime hover | 1.99:1 | 1.26:1 | **26%** |
| Inverted, shadow untouched | 6.13:1 | 1.26:1 | **5%** |
| Inverted, shadow retuned | 6.13:1 | 1.52:1 | **10%** |

At 5% it is not a shadow, it is fringing — indistinguishable from no shadow at all
in a side-by-side render. Tinting it with the button's own hue and carrying it to
`rgba(63,107,79,.38)` buys back half. Ten percent is roughly the ceiling: nothing
soft competes with a 6:1 edge, which is exactly why the original value was fine
under lime and is not fine under deep green.

So the two variants deliberately **do not share a shadow value**:

| Class | Rests | Hovers to | Shadow, tuned for the hover colour |
|---|---|---|---|
| `.btn-fill` | lime | deep green | `0 6px 16px rgba(63,107,79,.38)` |
| `.btn-deep` | deep green | lime | `0 6px 14px rgba(42,43,42,.16)` |

The shadow follows whichever colour is **on top during hover**, not the class. If you
ever unify them to one value, one of the two stops working and it will be the one you
are not looking at.

### `.btn-deep` — the inverse variant, and when to reach for it

The lime is a light colour, so a primary action on a light ground of the same hue
stops separating. On the promo strip's `#E6F2D5` the lime measures **1.71:1** against
its own bar and reads as one more category chip; the deep green is 5.26:1 there.
`.btn-deep` is that case and only that case — a solid button, the old treatment,
kept because an outline would go soft on an already-light strip.

Everything else stays `.btn-fill`. Buttons on plain white sit at 1.99:1, which is low
as a number but carries on hue and on the dark ink; do not go reclassifying them.

**`.btn-lime` was deleted.** Once resting went lime it was a byte-for-byte duplicate
of `.btn-fill` with a different hover, which is how two identical buttons end up
behaving differently. Its two uses became `.btn-fill`, and the mobile drawer pair
that had been deep green + lime is now `.btn-deep` + `.btn-fill` — same design, one
class fewer.

### One thing the inversion fixed by accident

`.btn-fill` on a `--c-dark` panel used to be deep green on deep green: **1.00:1**, the
button shape completely invisible, only its white label showing. "See open roles" on
the About page and the phone number on Prescriptions had both been plain bold text
pretending to be buttons. They are 3.08:1 now. Worth knowing, because a future revert
to a deep green resting state brings both back.

### The PDP stopped using lime for two different things

Once resting went lime, the product page had the primary action and a promotional
badge in the same colour — `--c-accent` on ADD TO BAG and `--c-primary` on the
gallery badge measure **1.02:1 against each other**, which is to say they are the
same colour. "Sixteen RGB points apart" is not a separation; luminance is.

That was not a new decision to make. The site already had a sale colour — the
collection card's red — and the product page was the only surface not using it. So:

| Element | Was | Now |
|---|---|---|
| PDP gallery badge | `--c-primary` lime | `--c-sale` red, matching the card — 5.44:1 on white, 2.73:1 against the button lime |
| PDP buy-column pill | `--c-accent` lime | `--c-tint` with `--c-text` ink, 12.20:1 — supporting information, not a second CTA |

The pill is an inline reassurance row with an icon, not a corner flag, so it did not
want the red; stacked directly above ADD TO BAG it only needed to stop looking like
a button.

**`--c-sale` is now a token.** The red had been hardcoded in four places and the
product page had already drifted off it, which is the entire defect above. It is in
`base.css` rather than `theme.liquid` because it is not editor-driven, and it is
deliberately *not* `--c-error`: a reduced price is not a failure.

> **Do not put `--c-primary-text` on `--c-tint`.** It measures **3.95:1** and fails
> AA. It is a tempting pairing — the brand ink on the brand tint — and it is the
> obvious thing to reach for when styling a quiet green chip. Use `--c-text` on the
> tint, which is 12.20:1. `--c-primary-text` is darkened to clear AA **on white**
> (4.60:1) and that margin does not survive a tinted ground.

### Checking it after a change

`setup/verify/contrast.py` will **not** catch any of this. It measures text on its
background and both pairings pass, so it stays green through every mistake described
above. The shadow, the lift and the button-against-its-ground separation are all
invisible to it. Look at a hover in a browser.

---

## The client handover PDFs are built from Markdown (25 Sep 2026)

The client gets `setup/HANDOVER.md`, `setup/IMAGES-HANDOVER.md` and
`setup/PHARMACIST-QUESTIONS.md` as PDFs, not as Markdown. After any change to
one of them, rebuild all three:

```sh
python3 setup/build_client_pdfs.py ~/Downloads/McCormacks-Client-Pack
```

That writes `1-Handover.pdf`, `3-Images-Handover.pdf` and
`5-Pharmacist-Questions.pdf`, dated with the build date, with the logo and the
same styling. Needs `pip3 install --user markdown`, Python Playwright and
Google Chrome. A PDF left over from before the last edit says something the
repo no longer does, so rebuild before sending, not after. **The PDFs are not in
git, by design, so nothing in a diff, a commit or `npm test` will tell you
they have gone stale** — the only thing that knows is this paragraph. On
30 Sep a session edited HANDOVER.md, checked whether a Handover PDF was
tracked, found none, and concluded there was nothing to rebuild; the pack in
`~/Downloads` then said the Sale collection had one product while 89 were on
sale. Another session caught it eight minutes later. "Untracked" means the
rebuild is manual, not that it is unnecessary.

**To check what a built PDF actually says, use `pdftotext` or pypdf, never
`strings`.** These PDFs deflate their text streams, so `strings` cannot see
the words at all — and it does not fail, it returns nothing and lets you read
that as "the phrase is absent". On 30 Sep it was used to confirm a rebuild and
reported the same phrases present and then absent across two runs before the
extractor, rather than the file, was suspected. A verification that cannot see
its subject is worse than none, because it answers. Until 28 Sep the
images handover was built from a Word file in ~/Downloads; it moved into the
repo so all three have one source each.

The pack's two workbooks (`2-Pharmacist-Review-Website-Pages.xlsx` and
`3-Images-Action-List.xlsx`) have no build script: they are edited in place,
with a before copy kept under `archive/client-pack-<date>/`.

### What the pack says about medicines (28 Sep 2026)

- **Every medicine order is reviewed; there is no shortlist.** The workbook's
  "Needs a pharmacist check" (renamed "Medicine classification" on 28 Sep) tab asks the pharmacist whether our
  classification is right (Pharmacy-only, General sale or Not a medicine), not
  whether a product needs a check. **An answer never removes the
  `pharmacist-review` tag by itself.** A "Not a medicine" goes back to the
  pharmacist before anyone changes the product.
- **The pack said the hold was built but not yet tested** (28 to 30 Sep). It is
  tested now, and the over-18 tick box is live. The wording was corrected in
  HANDOVER.md and PHARMACIST-QUESTIONS.md on 30 Sep; change all three together
  if it moves again.

### Checking a medicine's licence: read hpra.ie, and three traps (28 Sep 2026)

An audit of the pharmacist sign-off sheet against HPRA's own documents found
ten rows wrong. Record of what the checks were and what went wrong:

- **Match the product, not the brand.** "Uniflu With Vitamin C" was treated as
  the codeine product for three days. Its licence (Uniflu with Vitamin C,
  PA1113/005/001) has no codeine; the codeine product is Uniflu Plus with
  Vitamin C (PA1113/006/001), which neither website sells. The limits CSV had
  the right licence all along; the questions draft cited the wrong one.
- **Pack size is not quantity per sale.** Motilium's condition ("MPS: 10: MQP:
  100 mg") and Anusol HC's ("maximum pack size - 12 suppositories") cap the
  pack a pharmacy may sell without a prescription. Neither limits packs per
  sale.
- **hpra.ie cuts licence conditions at 256 characters**, on the product page
  and in its data alike. Several paracetamol conditions stop before the
  pharmacy-pack wording, so the per-sale number cannot be read there. The
  general-sale rule (one pack per retail transaction) is in S.I. 540/2003
  itself; the pharmacy "two packs" comes from each licence.
- **A manufacturer's consultation guide is not a licence condition.** Viagra
  Connect's and Cialis's conditions say "HCP consultation required for OTC
  supply". Sidena's have none; its "Essential information for the supply of
  Sidena" gives the legal category (pharmacy only) and calls its Pharmacy
  Consultation Guide optional.
- **No official 16-tablet sildenafil limit was found.** The HPRA documents for
  Sidena, Viagra Connect and Cialis for men set no per-sale quantity, and
  S.I. 540/2003 has none. The figure appears as a retailer's own policy.

The product records come from `sfapi.hpra.ie/api/HumanApprovedProducts` with
`{"id": "<product id>"}`, called from a page on hpra.ie (it refuses requests
made from outside a browser page). Product ids come from the site's search.
The per-row audit is in `~/Downloads/Fergal-Sign-Off-Audit-2026-09-28.xlsx`.

### Adding products: the 7-column upload sheet (28 Sep 2026)

Keelan's team fills `7-Product-Upload-Sheet.xlsx`: barcode, product name with
size, price, stock, medicine or not, supplier link (optional) and a note
(optional). Kakion turns each row into a product with `setup/product-import/`
(type, vendor, tags, the `pharmacist-review` tag for every medicine, Online
Store only for medicines), and checks it before it goes live.

Retired on 28 Sep, both in `archive/client-pack-2026-09-28/`: the 28-page
staff guide (`4-Staff-Guide-Adding-Products.pdf`), which taught staff to add
products straight into Shopify and to publish to all channels, and the 13-column
V1 sheet. Don't send either again.

## Product titles: till notes and a lost "no" (28 Sep 2026)

24 titles fixed, titles only, approved by Kakion. Handles were left alone, so
some handles still carry the old text (`…-blue-clonmel`, `tena-lady-rmal`);
that is deliberate. Before and after in
`archive/store-cleanup-2026-09-28/titles-before.csv`.

- **Till notes in titles.** Imported titles carried notes from the shops' till
  system: pack colour and maker ("Paralief … 24Pk Blue Clonmel"; Clonmel is
  Clonmel Healthcare, not the shop), stock codes ("6'S-5069", "Can509"),
  prices ("2Pk €7"), "(New)" and cut-off words ("Blister T"). Two were left:
  "Brylcream Gel Cream 2 For €6" (pack size unknown) and "Tubigrip Bandage
  0.5M Natural F 1" (meaning of the "1" unknown).
- **"no" deleted from some titles.** An earlier import removed every "no",
  in any case and mid-word: Normal became "Rmal", Nordic "Rdic", Pharmanord
  "Pharmard", Lansinoh "Lansih", Snoring "Sring", Retinol "Retil". 14 titles
  were hit, all non-medicines, and no descriptions; 74 other titles kept their
  "no", so it was one batch. A title that looks like a mangled brand name is
  worth checking for this before assuming a typo.
- **Titles are keys elsewhere.** `setup/quantity-limit-tags-draft.csv` and the
  classification CSV match products by title. The Paralief row in the
  quantity-limit draft was updated with the store; a later title change needs
  the same.
- **Jointace Original's description was Jointace Omega-3's.** Replaced; the
  old text is in `jointace-description-before.html` beside the CSV.

## 146 descriptions restored from the old site, tabs filled (30 Sep 2026)

The 146 non-medicines whose old-site page still had the fuller text now carry
it, in the old site's own wording. Before state in
`archive/store-cleanup-2026-09-30/description-restore-before.jsonl`, the fetched
pages in `old-site-descriptions.json` beside it, scripts in
`setup/descriptions/`.

- **The old site's accordion is `<dl class="mz_accordion">`**, with a `<dt>`
  naming each section and a `<dd>` holding it: Product Information, How To Use,
  Active Ingredients, Returns Policy. `extract.py` reads it from the served
  HTML. The `mz_tabs` block further down the page looks like the same thing and
  is always empty — it is filled by JavaScript, so anything fetching the page
  gets nothing from it. The `itemprop="description"` meta is the *cut* text, not
  the full one; don't take it.
- **Product Information became the description. How To Use and Active
  Ingredients became `custom.how_to_use` and `custom.ingredients`**, which
  `main-product.liquid` already renders as the How To Use and Ingredients tabs
  (77 and 50 products). Both definitions are `multi_line_text_field`, so their
  value is plain text: bullets keep their marker and go on their own line, since
  there is no `<li>` to carry the list. Returns Policy is boilerplate on every
  page and was skipped.
- **Only non-medicines.** No product tagged `pharmacist-review` was touched, and
  the writer refuses one that is, refuses a product whose description moved
  since the plan, and refuses one whose tabs are already filled.
- **Three products word it differently on the old site and two of those are
  shorter.** Quies Foam Ear Plugs 3Pk and Kelkin Tea Tree Shampoo 250Ml took the
  old site's shorter text because the store's longer text was cut mid-sentence
  and the old site's is a finished sentence. The Quies text on the store also
  described *wax* earplugs on a *foam* product. Longer is not the test; finished
  is.
- **A 301 is not a refusal.** The first fetch run stopped at one because `curl`
  was not following redirects, and the same URL answered 200 a minute later.
  `fetch_old.py` follows redirects now and stops only on 403, 429 or a 5xx. The
  10-second gap between pages still stands — 146 pages fetched at that pace with
  no refusal at all.
- **Two products the old site could not improve** were left alone by the length
  test before the three-exception rule was added: the guard is still there, and
  it is what stops a "restore" from shortening a description by accident.

## Inline bullets in descriptions: 39 turned into real lists (30 Sep 2026)

Descriptions imported with their bullets run into one paragraph — "…verruca
virus. • Quick and easy application; • Results in 1-2 weeks; • No plasters
required;" — and with headings stuck to the end of the previous sentence
("…warts and verrucas. DIRECTIONS: Soak the affected region…"). 39 products
fixed, formatting only: every word unchanged, in the same order. Before state
in `archive/store-cleanup-2026-09-30/description-formatting-before.jsonl`;
the scripts are in `setup/descriptions/`.

- **Only the markers moved.** Bullets became `<li>`, headings started a new
  `<p>`, and the semicolons that ended a bullet came off. `write.py` re-reads
  each product after writing and compares the letter-and-digit stream of the
  rendered text against the before state; the only punctuation allowed to
  disappear is `•`, `-`, `–`, `*` and `;`. Anything else fails the product.
- **`•` is safe to split on; `-` is not.** 33 descriptions have dashes that
  could be bullets and only 9 are. The rest use a dash to join a label to its
  meaning — "Paracetamol - For relief of headache" (Night Nurse), "Treats
  heartburn - Forms a protective barrier" (Gaviscon), "1 Secure - Secure &
  discreet" (TENA Lady). Splitting those would delete a dash that carries the
  sentence. The 9 real ones were done by hand in `manual.py`, each one typed
  out and checked letter by letter. Don't automate this; re-read the list.
- **`·` and `*` are almost never bullets.** Every middot on the store is a
  brand name (Sensi·Kin, b·bold) and every asterisk but one is a footnote
  marker ("35% smoother hair**"). Udo's Super 8 is the single product that
  uses `*` as a bullet.
- **A heading only counts when a full stop precedes it.** "Product Features:"
  after "…most shoes." is a heading; "contains:" in "Vitamin b complex
  contains: thiamine" is mid-sentence and must stay put. `fix.py` requires
  `[.!?;•]` before the heading word, which is what keeps the second kind
  alone.

### The broken-description list for the pharmacist (30 Sep 2026)

651 products have a description that is cut off, empty or garbled —
422 cut mid-sentence, 133 cut mid-word, 78 with no description at all, 20 with
mojibake ("â€™", "Ã¬") or a `.?` where a paragraph break was lost, 8 with two
words run together, 3 with a sentence repeated. `broken.py` rebuilds the list;
`sheet.py` writes `~/Downloads/Descriptions-To-Fix.xlsx` with a tab each for
the 12 medicines, the 146 non-medicines the old site can still supply, and the
493 left for staff.

- **The import cut the source at 485–500 characters**, not 500 exactly, because
  entities (`&amp;` is five characters, one glyph) shift the count. A
  description whose source falls in that band and does not end in punctuation
  was cut; one that ends unpunctuated well under it is usually just a feature
  list ("Mint fresh", "Vegan friendly") and is not flagged.
- **"Another product's text" cannot be found automatically.** Two checks were
  tried and both produced only false positives: a description naming a
  different brand than the title (the Fusion 5 Gift Set legitimately describes
  Gillette) and one contradicting the title's colour or SPF ("red" matches
  inside "reduces", "grey hair" inside every root concealer). The Jointace
  Original case from 28 Sep was same-brand and read perfectly. Only someone who
  knows the products can spot these; the sheet does not claim to list them.
- **A shared description across a product family is usually correct**, not a
  mistake: 92 groups of products share one description, and nearly all are
  colours, sizes or flavours of the same thing (TePe brushes, Halls Soothers,
  Nivea Sun). Don't treat a duplicate as a defect without looking.

## Descriptions cut at 500 characters; medicines restored from the old site (28 Sep 2026)

Product descriptions were imported cut at 500 characters, often mid-word and,
for medicines, mid-warning ("Do not take with any other pseudoe"). 685 look
cut, 71 of them medicines; the list, with whether the old site has the full
text, is `setup/truncated-descriptions-2026-09-28.csv`. The April import file
from Efulfill is not in the project; the July export of the old site's
database has full descriptions for only 1,038 products.

- **Medicines were restored from the old site's "Product Information" text**,
  word for word, whitespace collapsed into one paragraph as before. Before and
  after in `archive/store-cleanup-2026-09-28/medicine-descriptions-before*.csv`.
- **Restored descriptions carry the old site's quantity and "over 18"
  lines** ("MAXIMUM order quantity of THREE packs per order", "You Must Be
  Aged Over 18 Years to Purchase This Product") and its typos. Nothing on this
  site enforces those limits, and some disagree with the licence caps. The
  quantity pass after Fergal's sign-off corrects them; until then, don't treat
  a description as the source for a limit.
- **50 restored.** Five of them took the old site's wording over ours, which
  differed (Bonjela Teething repeated itself, Nicorette Cools 2Mg 20Pk and
  Panadol Ets 24Pk carried another product's text). **Not restored:** Dulcolax
  and Salatac, cut on the old site too.
- Fetch the old site no faster than one page every 10 seconds: at four at a
  time it returned 403 to everything for several minutes.
