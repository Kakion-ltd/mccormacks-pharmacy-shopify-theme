# McCormack's Pharmacy website — handover

Updated 30 September 2026. The store has been in the pharmacy's ownership since
25 September. This lists what is still needed from the pharmacy, what Kakion is
still building, and what is already done.

Every item says who owns it:

- **Pharmacy**: something only the pharmacy can do or decide.
- **Kakion**: something we will do.
- **Decision needed**: we need an answer before anyone can act.

The website is on the store now, behind the password page. Customers cannot
see it until the password is taken off, and the six launch blockers below need
to be settled before that happens.

---

## 1. What the pharmacy needs to do

### The six launch blockers

These have to be settled before the website opens to customers.

**1. Real stock figures. Owner: Pharmacy.**
Every product on the store says it has either 1 in stock (1,762 products) or 0
in stock (663 products). Those are placeholder numbers from the import, not
real counts. Until they are real, the website will sell things you don't have
and mark things "sold out" when they are on the shelf. We need either real
counts or a decision on how stock will be kept up to date, for example from
your shop system.

**2. Card payments. Owner: Pharmacy.**
Customers can't pay until the store's payment account is set up in Shopify.
That needs the business's own details: company and bank details and proof of
identity. Only the owner can enter them. The store is in your name now, so
Fergal can start this now. Shopify checks the details itself, which can take a
few days, so it is worth starting first. Once it is on, we will put one real
test order through together and refund it.

**3. Same-day dispatch cut-off. Owner: Pharmacy.**
The questions on every category page except Bundles and Sale (eleven sets of
questions in all) say "order before 3pm". Tell us the real time. The website won't promise same-day dispatch until you do.

**4. How a pharmacist reviews medicine orders. Owner: Pharmacy (pharmacist).**
The PSI's guidance (section 2.5 of its guidance on internet supply) says a
pharmacist must personally review and authorise **every** order that contains
a medicine before it is sent. That covers pharmacy-only and general sale
medicines alike. There is no shortlist: every product marked as a medicine is
covered.

The website marks 337 products as medicines. The hold that stops those orders
being sent until a pharmacist approves them **is built and tested**. Every order
containing a medicine is put on hold, marked "awaiting pharmacist", and the shop
gets an email. The pharmacist prints a record sheet for the order, ticks and
signs it, and approves the order by adding a tag with their initials and
releasing the hold. An order released without that tag is put back on hold.

The tick box where the customer confirms, before paying, that they are over 18
and will use the medicine as the leaflet says **is on the live website**, so a
medicine order placed the normal way arrives with that confirmation on it.

**If an order is tagged "no declaration", the customer skipped the bag-page tick
box. Contact them to confirm they are over 18 and have read the leaflet before
approving.** This is the website working as intended, not a fault. Nearly
everybody buys through the basket, which always shows the tick box. A handful of
ways round it can't be closed: someone who has saved a direct link to the
checkout, the "buy again" button in a customer account, an order you create
yourself in Shopify, or an order from another sales channel. Rather than let one
of those through unnoticed, the website marks the order so you know to ask.

Please tell us:

- Who will review medicine orders, and how quickly, and the initials each
  pharmacist will use to approve.
- Whether the wording of the tick box, and the line under it saying a
  pharmacist reviews every medicine order, is right.
- How each order is approved or refused. Shopify can't pause a customer at
  checkout while a pharmacist looks, so the order of events would be: the
  customer pays, a pharmacist reviews the order, and it is either sent or
  cancelled and refunded. The customer is told this before they pay.
- Whether the signed record sheet suits you. It covers the rest of section 2.5
  except one part: it records that the buyer is over 18, knows to follow the
  pack's instructions and is buying a reasonable quantity, and, kept for two
  years, it is the record of each sale. Spotting repeat requests for medicines
  open to misuse, such as painkillers, antihistamines and laxatives, is still
  open: tell us how you want to handle it.

Some medicines also ask the customer questions before they can be added to the
bag. **On 30 September 2026 Fergal decided to use your current website's
questions rather than the set we drafted**, so that is what is being built:

- **Viagra Connect (4 and 8 pack), Cialis (4Pk and 8Pk) and Sidena** ask the
  same fourteen Yes/No questions your current website asks, word for word.
- **Every other medicine** asks two: a tick to confirm the buyer is over 18, and
  "Are you taking any other medication?", where Yes opens a box to say which.
- **No answer stops the sale.** Every answer is saved on the order, beside the
  medicine it was asked about, for you to read before you approve it. That is
  how your current website works too.
- **Curanail asks nothing**, as on your current website. **Anusol HC stays off
  the website**, as on your current website, where it is enquiry-only.
- Uniflu with Vitamin C is on hold until you tell us whether it needs questions.

What your current website asks, and how it compares with the draft we sent, is
in `setup/old-site-questionnaires.md`. Our draft (`5-Pharmacist-Questions.pdf`)
is kept as the proposal it was; nothing in it is built. Two things in it are
still worth your eye, and neither is blocked by this decision: the questions
about medicines that slow sildenafil down, which neither website asks, and
whether Anusol HC should go on sale at all.

**5. Who reads the website's email inbox. Owner: Pharmacy.**
Seven forms on the website send an email and nothing else:

- back-in-stock requests
- contact
- cancelling an order (the withdrawal form)
- booking an in-store service
- careers
- two prescription forms

Shopify keeps no copy of any of them. If an email is deleted, the request is
gone. Please name the person who reads info@mccormackspharmacy.ie. They should
file these emails rather than delete them.

Naming one person unblocks three things:

- **Back-in-stock requests can be switched on.** They are off until someone
  owns the inbox.
- **Prescription requests have an owner.** Both prescription forms are live,
  and at the moment nobody is named to act on what they send.
- **Withdrawal acknowledgements get sent.** When a customer withdraws from an
  order, the law says we must acknowledge it in a durable form, such as an
  email, without delay. A message on the screen doesn't count, and the
  website can't send that email itself. Until someone replies to each
  withdrawal request by hand, quoting the reference number it carries (it
  starts "WD-"), we are not meeting that requirement.

**The in-store services booking form stays off, even once the inbox has an
owner.** A booking can include a note about a customer's health, and that
should not sit in a shared inbox. It stays off until those requests have
somewhere safer to go. Until then, the services pages point customers to their
nearest shop and the phone.

**6. Test the store's emails. Owner: Kakion, with the pharmacy.**
The store's email addresses are now the two you gave us:

- **info@mccormackspharmacy.ie** is the store's contact email, and the address
  the store's emails come from. Every form on the website sends here: both
  prescription forms, contact, cancelling an order and careers, and
  back-in-stock requests once they are switched on.
- **sales@mccormackspharmacy.ie** gets the staff order notifications: the
  email Shopify sends your team when an order comes in.

Neither has been tested yet. Before the password comes off, we'll check both
with you: one test through a form, to confirm it arrives at info@, and one test
order, to confirm the notification arrives at sales@.

### Questions for the pharmacist

**The "Do I need a prescription?" answer. Owner: Pharmacy (pharmacist).**
Every one of the 293 category pages carries this answer:

> All items in this collection can be bought without a GP prescription.
> Prescription-only medicines are not sold online in Ireland — you can submit a
> prescription for dispensing instead, and collect it in store or have it
> delivered.

We are not confident it is right. It says nothing about pharmacy-only
medicines, which need a pharmacist's involvement even though no prescription
is needed. Please approve it or rewrite it.

**Answers shown on product pages. Owner: Pharmacy (pharmacist).**
Each product can carry its own short questions and answers. Google may show
those answers on its own results page, away from the product. So on a pharmacy
site, each one needs your sign-off before it goes up. None have been written
yet.

### PSI rules for selling medicines online

**Internet Supply List registration for each shop. Owner: Pharmacy.**
The PSI's guidance is explicit that every pharmacy supplying medicines online
must be registered on the Internet Supply List in its own right, even when
several pharmacies share one website. We hold one registration, number
10001884, and the website's PSI logo links to it. Please send us the
registration numbers for the other six shops, or confirm which shops that one
registration covers.

This may limit which shop can fulfil online medicine orders. A shop that isn't
registered shouldn't dispatch them, so the answer decides where medicine
orders are sent from.

**The website's address. Owner: Kakion, with the pharmacy.**
Your Internet Supply List entry names the website as
**www.mccormackspharmacy.ie**, and the PSI logo on every page links to that
entry. So the new website must go live at exactly that address. If you ever
want a different address, the PSI has to update the entry first. Moving the
address across needs whoever manages your domain and its settings; we'll
arrange that with you before launch.

### The legal pages

**Which version of each legal page is the right one. Decision needed:
pharmacy and your solicitor.**
The terms and conditions, returns policy and shipping policy each exist twice
on the store, with different wording. The privacy policy also exists twice,
but both copies say the same thing.

- One set is Shopify's own. Checkout and the order emails always link to that
  set, and we can't change that.
- The other set is pages we built.

Please have your solicitor confirm the correct text. We will then point every
link at the confirmed version and remove the duplicates. Registration, the
footer and the sidebar on the legal pages already point at Shopify's set; the
services, prescription and back-in-stock forms still point at ours.

The withdraw-from-contract page was rewritten on 25 September with the
business's details. Please ask your solicitor to review that too.

**Cookie policy updated 30 September 2026; David Reilly to review.**
The draft marker is gone, and the page is on the live store. `/pages/cookie-policy`
now carries the pharmacy's own text, and the cookie table is the seven
cookies the live store actually sets, scanned that day in a fresh browser: accept all, then home page,
product, add to bag, checkout. All seven are Shopify's own. No Google, Meta
or other third-party analytics or advertising cookie was set at any point,
because none is installed.

What the scan confirmed, and what David should know when reviewing:

- Before any consent choice, only four cookies were set, all of them
  necessary or functional: `_shopify_essential`, `cart_currency`,
  `localization` and `_shop_app_essential` (on Shopify's `shop.app`). No
  analytics and no marketing cookie. Shopify's consent state read empty for
  analytics, marketing and preferences.
- `_shopify_analytics` and `_shopify_marketing` appeared only after Accept
  all, which is what the law requires.
- There is no Google tag on the site, so there is no Google consent default
  to check. The gate is Shopify's consent API instead, and it is closed
  until the visitor answers. Re-check this the day any Google or Meta pixel
  is added.

**Two things that went with it, both since done and both live:**

- **The banner now offers the same three groups as the policy.** It had a
  fourth, Preferences, which described itself as remembering "choices like
  your nearest store". Nothing did that: the store locator asks the browser
  for a position every time and stores nothing, no cookie in the scan
  belonged to that group, and no pixel on the store asks for that
  permission. It was a switch that changed nothing, naming a group the
  policy does not have. Removed. The theme now never grants preferences, so
  if a service in that group is ever added it stays switched off until both
  the banner and this policy get the group back.
- **Privacy Policy is now one document from the legal pages.** The sidebar
  beside the policy used to link `/pages/privacy-policy` while the text
  linked Shopify's `/policies/privacy-policy`; both now go to Shopify's,
  which is the copy checkout and the order emails use and the only one a
  customer can be shown at checkout. That sidebar is shared by all seven
  legal pages, so all seven moved together.

  `/pages/privacy-policy` is still live and still linked from three forms:
  the in-store services booking, the prescription upload and the
  back-in-stock request. Those three ask the customer to consent to their
  details — health details, in the prescription case — being handled as that
  document sets out, so which document they name is part of the solicitor's
  decision above, not a link tidy-up. They are deliberately left alone until
  that is settled.

**The privacy policy contradicts this, and the cookie policy is the one with
the evidence.** Both copies of the privacy policy name Google Analytics, the
Facebook Pixel, Google Tag, Doubleclick, AdRoll, Nosto, Pubble, Trustpilot,
BrotherMailer and Realex. The 30 September scan found none of them: no
request to any of those domains, and no cookie from any of them, because
none is installed. The privacy policy is describing a different website,
most likely the old one. David should read the two together and treat the
cookie table as the record of what the site actually does. A separate piece
of work is already drafting the privacy policy replacement.

Re-run the cookie scan before launch, and again whenever a pixel is added
under Settings > Customer events. A cookie table that lists something the
site no longer sets, or omits something it now does, is the same defect in a
new place. The same goes for the banner: a group in one and not the other is
how this started.

### What the website says on your behalf

**The five Google reviews on the homepage. Owner: Pharmacy.**
The homepage quotes five real Google reviews by name: Bryan Mc Bride, Amy
O'Brien, Stephen Donohoe, Ray Keogh and Eimear Murphy. Each card shows **five
stars**, which tells customers that each of those people gave you five stars
on Google. Please check each review on your Google Business Profiles and
confirm the stars match. If any gave fewer than five, tell us and we'll
correct that card or take it down.

**"Trusted by customers since 2010". Owner: Pharmacy, if you want a number.**
The strip under the header on the homepage, product, collection and search
pages used to read "Trusted by over 20,000 customers since 2010". That number
came from the design mock-up and nobody could say where it came from, so we
have removed it.

If you have a real figure you can stand over, it can go back in: Theme
settings › Trust bar › Message 3 › Text. It changes every page that shows the
strip at once.

### Store details

**Click and collect. Decision needed: pharmacy.**
Which shops will offer collection? Pickup is switched on shop by shop in
Shopify, and the website then shows it by itself. If you won't offer
collection at launch, tell us, and we'll remove the "Click & Collect" button
from the bag so it doesn't promise something you can't do.

**Bank holidays. Decision needed: pharmacy.**
Your shops follow Sunday hours on bank holidays, and the website says so. But
Google will show normal weekday hours on a bank holiday unless we give it a
dated list each year. Decide whether that is worth doing.

**Gift vouchers need switching on. Owner: Pharmacy.**
The gift voucher page now sells a real Shopify gift card, and the seven old
"E-Gift Card" products have been taken off the website — they took money and
issued no voucher code, so they could not stay. One step is left, in Shopify admin:
**Products → Gift cards → activate gift cards**. There are Shopify gift card
terms to accept, so it may need whoever owns the Shopify account rather than a
staff user. Shopify refuses to let anyone create a gift
card product until that is done, so until it is, the voucher page tells customers
vouchers aren't available online and points them at the shops. Nothing else is
outstanding; the page, the emails and the staff alert are built and tested.

**The gift voucher card. Decision needed: pharmacy.**
You chose white writing on the lime-green voucher card. It is hard to read,
and it fails the readability standard the rest of the site meets. Please
confirm you want to keep it. Dark writing is a one-line change if you
reconsider.

### The Sale offers are live, and nobody has said when they end

**Decision needed: pharmacy.** The offers from your old website are now on the
new one, so the two sites show the same prices at launch.

What went on:

- **88 products** show a reduced price with the old price struck through beside
  it, taken from what your old site was showing on 30 September. The Sale
  collection holds all 88, up from 1. An 89th, BPerfect Chroma Cover Luminous
  Foundation W5, has its offer set up but isn't on the website: it isn't
  published to the online shop and has no stock. It will show the same offer
  if you publish it.
- **Eight multi-buy and gift offers** work automatically in the bag: 3 for €10,
  3 for €5, Buy 2 for €7 on Batiste, 2 for €52.45 on Revive Zest Active, Buy 4
  for €3 on the BioMiracle wipes, buy one get one half price on Revive Active
  and on Mitchum, and a free tanning mitt with every BPerfect Tan Studio item.
  Each one has been tested in a real bag and comes to the exact advertised
  total.
- **Six prices were corrected.** The five BPerfect Chroma Cover foundations and
  the Foot Soak Bundle were at your old site's *pre-sale* price on the new site,
  so they were higher than what you were actually charging.
- **71 products show an offer line** beside the price, such as "3 for €10" or
  "While stocks last", in your old site's words tidied up.

**The one thing we need from you: when does each offer end?**

**Nothing on the website has an end date.** There is no scheduling anywhere in
it: an offer line reads exactly the same on the 1st of January as it did the day
it went up, and it keeps reading that way until a person removes it. Right now
that includes 18 products saying "While stocks last" and 10 saying "€5 off while
stocks last".

So please tell us, for each offer, either an end date or "until we say
otherwise". Offers that are already over can come off in the same pass. We will
also need telling when a multi-buy ends, because the offer line and the
discount in the bag are two separate things and both have to be switched off —
one without the other either advertises a discount that no longer applies, or
applies one the page does not mention.

**Two things we have left alone for you to confirm**, listed in the offers
review sent separately: 29 offers that look out of date (Black Friday badges, an
Electric Picnic bundle, suncream deals, and 18 products your old site shows as
out of stock), and 2 Sculpted By Aimee bundles that are on the old site but not
on the new one. The Electric Picnic bundle has been taken out of the Sale
collection, as it is out of stock and the festival was in August.

**A pricing check: were these products ever sold at the struck-through price?**
These prices came from your old site exactly as it showed them, so this is a
question, not a problem we have found. A few of them look like a recommended
retail price with a fixed percentage taken off, rather than a price the product
was actually sold at:

- **SVR, 8 products, all exactly 30% off.** Struck-through prices of €17, €19,
  €31, €37, €51 and €54.
- **Azio Beauty, 7 products, all exactly 20% off.** Struck-through prices of
  €22, €28 and €34.
- **Sculpted By Aimee Oily Skin Morning Routine Bundle**, €159.99 against
  €200.00.

Every one of those struck-through prices is a whole euro amount, and each range
has the same discount to the cent.

Why it matters: a struck-through price tells a customer they are saving money,
and a saving has to be measured against a price you actually charged. Under the
EU price-reduction rules, the struck-through price should be the lowest price
you charged in the 30 days before the sale started. If these products were sold
at those prices in that time, nothing changes. If they weren't, the
struck-through price should come off. The price customers pay stays the same;
the page just stops claiming a saving. For Azio that would also mean removing
the "20% off Azio Beauty" offer line.

Please don't unpublish the last product in the Sale collection without telling
us: with nothing published, the "On Sale This Month" section on the homepage
does not appear at all.

### Products

**Adding new products. Owner: Pharmacy (Keelan's team).**
To add products, fill in `7-Product-Upload-Sheet.xlsx`, one row per product:

- barcode
- product name, with the size
- price
- how many you have in stock
- whether it is a medicine
- a link to the product on the supplier's website (optional)
- a note for us (optional)

Send it to us and we'll add the products, put each one in the right category
and brand, and check them before they go live.

**Is it a medicine?** Look on the pack for a licence number: PA or PPA
followed by numbers, TR (herbal medicines), EU/1/, or VPA (medicines for pets).
If there is one, answer Yes, even if it looks like a toiletry: Sudocrem and
E45 Cream are medicines. Every order for a medicine waits for a pharmacist
(launch blocker 4). If you're not sure, answer Yes and add a note.

**Real stock numbers only.** If you put 1 when you have none, the website
sells something you can't send. If you put 0 when it is on the shelf, it shows
"sold out" and the sale is lost.

**70 products added to the store but not on the website yet. Owner:
Pharmacy (stock numbers), then Kakion.**
On 23 September 70 products were added from the pharmacy's product list. All
70 are sold on your current website, so they are approved for online sale, but
they are not on the new website yet. Among them are the ranges that were
missing from the new shop: Lerelle Beauty (8), Harry's (7) and Dr Squatch (6),
along with Mx Health home tests (6), Lippy (5) and others. None of them has
stock tracking yet, so each goes on once we have a real stock number for it.

- **62 are not medicines.**
- **8 are medicines:** Sidena 50mg, Canesten Combi, E45 Cream 125g, Calpol 6+
  Fastmelts, Calpol Infant Sugar Free 140 ml, Deep Heat Spray, and two Ovelle
  ointments. Sidena and Canesten Combi also need their questions set up first
  (see the pharmacist questions document).

**Check how each medicine is classified. Owner: Pharmacy (pharmacist).**
Spreadsheet: `2-Pharmacist-Review-Website-Pages.xlsx`, tab "Medicine classification". It lists the 337 products the website treats as medicines. For each,
tell us whether our classification is right: pharmacy-only, general sale, or
not a medicine. The first 219 are licensed medicines on the HPRA register; the
other 118 need the pharmacist's judgement, including five veterinary flea
treatments. Every one of the 337 stays marked as a medicine until you have
answered, and any answer of "not a medicine" is one we'll check with you before
changing anything.

The same workbook asks three more things. "Pages to fill" lists 281 products
we think may belong on 29 empty category pages: Yes or No for each. "Confirm
Medicines & Health" has 120 products we have matched to 33 pages, held back
until a pharmacist agrees. "Decisions" has five questions: four about
particular medicines (Calpol Infant 140 ml, E45 Cream, the Tefin 75 mg
description, the Zirtek 30-pack's licence) and whether to pay
for an app that enforces per-order quantity limits at checkout. They are also
in the pharmacist questions document. `6-Quantity-Limit-Tags-Draft.csv` lists
the 46 medicines those limits would cover, with the most per order we
suggest for each, for the pharmacist to confirm.

**Brands on the current website versus the new shop. Owner: Pharmacy.**
We compared the two on 9 September. Some brands have fewer products in the new
shop than on your current website: for example, Jenny Glow has 67 there and 44
here. Three brands that were missing, Lerelle Beauty, Harry's and Dr Squatch,
have since been added and are among the 70 products above.

The catalogue has changed since, so we'll send you a refreshed comparison.
Please then check whether the missing products should come across.

**Sizes sold as separate products. Decision needed: pharmacy.**
The import turned each size into its own product. For example, Revive Active
comes as six separate products (7-pack up to 360 sachets). About 115 product
ranges are affected. Grouping each range into one product with a "choose your
size" option is easier for customers. It is a catalogue job, and it needs the
old web addresses redirected (see section 2).

**Brands with only a few products. Decision needed: pharmacy.**
Nineteen brands have between one and four products but still have their own
brand page, because customers search for them by name. Examples are CeraVe,
Sudocrem, Bio-Oil, Neutrogena and Oral-B. Keep, expand or drop each one.

---

## 2. What is still to be built or finished

**The pharmacist hold on medicine orders. Owner: Kakion. Done.**
Built on 28 September and **tested on the live website on 30 September**. Every
order containing a medicine waits for a pharmacist's approval before it can be
sent. Seven test orders proved it, and all were cancelled afterwards: a medicine
order is held and tagged for you; a non-medicine is not; releasing an order
without adding your approval tag puts it straight back on hold and flags it; and
an order released *with* the tag goes through. The over-18 tick box is on the
live website too, so orders now arrive with the customer's declaration.

**Questions before purchase. Owner: Kakion. Done, with one thing for you.**
Live since 30 September and tested with real test orders. Every medicine asks
the over-18 tick and "Are you taking any other medication?"; the five erectile
dysfunction products ask eighteen questions; Curanail asks nothing. The answers
appear on the order beside the medicine they were asked about.

**The one thing to know: no answer stops a sale.** That is the decision, and it
is your current website's behaviour. In testing we answered "No" to "is this for
a man aged 18 or over with erectile dysfunction" and the order still went
through, arriving for the pharmacist with that "No" on it. If you would rather
some answers stopped the sale outright, tell us which and we will set them.

**Redirects from the old website. Owner: Kakion (needs a list from the
pharmacy).**
When the new site goes live, every address from the old site that Google knows
about must lead to the matching page on the new one. Otherwise those links
break, and search rankings drop. Nothing is set up yet. We need the old site's
full list of page addresses, or access to it, and we'll build the matching list.

**Click and collect. Owner: Kakion, once the pharmacy decides.**
The website side is ready. It is waiting on the shop-by-shop decision above.

**Homepage slide readability. Owner: Kakion.**
On the Vitamins & Supplements slide, the white heading sits on pale green and
can't be read. We will fix the colours.

**Hero and banner artwork. Owner: Pharmacy supplies, Kakion places.**
Some images are still missing. Where an image is missing, the website shows a
neat placeholder. We need photographs of the seven shops: a phone camera is
fine, held landscape.

**Test the website's forms with a real submission. Owner: Kakion, with the
pharmacy.**
None of the website's forms has been sent on the real store yet. We'll send
one test form and one test order together, and confirm each reaches the right
inbox and reads properly: the form at info@, the order notification at sales@
(see launch blocker 6).

**Point the remaining links at the right legal pages. Owner: Kakion.**
Waiting on the solicitor's decision.

**Seasonal content. Owner: Pharmacy (we can show you how).**
Nothing on the website changes with the seasons by itself. The homepage slides
(currently including Back To School), the offers and the promotional strip are
changed by hand in the theme editor.

**Remove the old spare design. Owner: Kakion.**
The store still holds one spare copy of the website design, "Policies
Preview", from the previous developer. Customers don't see it. It stays until
you've signed everything off, then we'll remove it so nobody edits the wrong
one.

---

## 3. What is done

All of this is built, checked and on the store, as of 28 September.

- The new design, on every page, on phones and computers.
- 2,425 products, arranged in 8 departments and 175 categories,
  plus 134 brand pages and an A–Z brands page.
- Menus built from the same category list, so the header, the phone menu and
  the category pages always agree.
- Search with suggestions as you type.
- Filters that open as a panel on phones, with Apply and Clear all always on
  screen, and a sort box that matches the rest of the site.
- On phones, a single "back" link at the top of each page instead of the long
  trail of links.
- A bag that slides in from the side, a wishlist, and a "quick view" on
  product cards.
- The seven shops, with addresses, phone numbers, opening hours, a map, and a
  "use my location" button that puts the nearest shop first. Google reads the
  opening hours too. The map's Google key only works on your own web
  addresses, so nobody else can run up charges on it.
- The gift voucher page.
- Delivery: Ireland only. Standard €6, express €9, free over €65. The
  free-delivery amount is set in one place, so the website can't contradict
  itself.
- The store in your name since 25 September, with its emails coming from
  and going to your own addresses.
- Online sales through the website only. Medicines are not offered in
  Shopify's Shop app, which does not show the PSI logo.
- Questions before purchase for medicines that need them, ready for the
  questions the pharmacist approves.
- "Tell me when it's back" requests on sold-out products: built, but
  **switched off**, so customers can't use it yet. It goes on once the inbox has
  an owner (launch blocker 5). A person from the pharmacy replies; it is not an
  automatic alert.
- The cookie banner, with the choices Irish and EU law require.
- The PSI registration mark in the footer, linked to your Internet Supply List
  entry, and the PSI's contact details on the Registered Internet Supply
  Pharmacy page.
- A set of automatic checks we run on each update: readability, layout on
  phones, forms, menus and the questions before purchase.
