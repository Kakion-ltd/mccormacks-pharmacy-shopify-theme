# McCormack's Pharmacy website — handover

Updated 28 September 2026. The store has been in the pharmacy's ownership since
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

The website marks 346 products as medicines. The hold that stops those orders
being sent until a pharmacist approves them **is not built yet**. We will build
it once Fergal confirms how he will review orders. Please tell us:

- Who will review medicine orders, and how quickly.
- How each order is approved or refused. Shopify can't pause a customer at
  checkout while a pharmacist looks, so the order of events would be: the
  customer pays, a pharmacist reviews the order, and it is either sent or
  cancelled and refunded. The customer is told this before they pay.
- How you will cover the rest of section 2.5, which the website does not do by
  itself: recording that the buyer is over 18, knows to follow the pack's
  instructions and is buying a reasonable quantity; keeping a record of each
  sale for two years in a form that can't be altered; and spotting repeat
  requests for medicines open to misuse, such as painkillers, antihistamines
  and laxatives.

Some medicines may also need the customer to answer questions before they can
add them to the bag. That part is built and waiting for your questions: our
draft is in `5-Pharmacist-Questions.pdf`.

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
link at the confirmed version and remove the duplicates. Registration and the
footer already point at Shopify's set.

The withdraw-from-contract page was rewritten on 25 September with the
business's details. Please ask your solicitor to review that too.

**Unfinished wording that customers can see. Owner: Pharmacy and your
solicitor supply the text, then Kakion.**
The cookie policy still carries a draft marker. It isn't hidden in the
editor: it shows on the page itself, so every customer will see it once the
password comes off.

- **Cookie policy:** a box headed "Draft copy" tells the reader the page uses
  placeholder wording. We need the final cookie policy text and the list of
  cookies the site uses.

Send us the confirmed text and we'll put it in and remove the marker. It
should be settled before launch.

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

**The gift voucher card. Decision needed: pharmacy.**
You chose white writing on the lime-green voucher card. It is hard to read,
and it fails the readability standard the rest of the site meets. Please
confirm you want to keep it. Dark writing is a one-line change if you
reconsider.

### The Sale collection has one product on sale

**What goes in the Sale collection. Decision needed: pharmacy.**
The Sale collection holds 2 products, and only 1 of them is on the website:
the Voduz R'oil and Hairdryer Bundle. The Electric Picnic Bundle is in the
collection but isn't on the website.

Sale is one of the most visible things on the site. Customers reach it from:

- the homepage section headed **"On Sale This Month"**
- the **Special Offers** slide on the homepage
- the **Sale** link in the header and in the homepage category row
- the "You may also like" row on the gift vouchers page

Right now, all of them lead to a single product. Please decide what should be
on sale at launch. Enter each product's old price as well as its new one, so
the website can show the reduction. If you'd rather not run a sale at launch,
tell us and we'll take the Sale links and sections down until you do.

Please don't unpublish the last product in the collection without telling us.
If the collection has nothing published, the homepage section falls back to
sample products from the design, with made-up prices.

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
Spreadsheet: `2-Pharmacist-Review-Website-Pages.xlsx`, tab "Medicine classification". It lists the 346 products the website treats as medicines. For each,
tell us whether our classification is right: pharmacy-only, general sale, or
not a medicine. The first 219 are licensed medicines on the HPRA register; the
other 127 need the pharmacist's judgement, including five veterinary flea
treatments. Every one of the 346 stays marked as a medicine until you have
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

**The pharmacist hold on medicine orders. Owner: Kakion, once the pharmacist
decides.**
Every order containing a medicine will wait for a pharmacist's approval before
it can be sent. We build it once Fergal has confirmed how he will review
orders (launch blocker 4).

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
