# McCormack's Pharmacy website — handover

Written 24 September 2026, before the Shopify store moves into the pharmacy's
ownership. It lists what is still needed from the pharmacy, what Kakion is
still building, and what is already done.

Every item says who owns it:

- **Pharmacy**: something only the pharmacy can do or decide.
- **Kakion**: something we will do.
- **Decision needed**: we need an answer before anyone can act.

The website is on the store now, behind the password page. Customers cannot
see it until the password is taken off, and the four launch blockers below need
to be settled before that happens.

---

## 1. What the pharmacy needs to do

### The four launch blockers

These have to be settled before the website opens to customers.

**1. Real stock figures. Owner: Pharmacy.**
Every product on the store says it has either 1 in stock (1,815 products) or 0
in stock (659 products). Those are placeholder numbers from the import, not
real counts. Until they are real, the website will sell things you don't have
and mark things "sold out" when they are on the shelf. We need either real
counts or a decision on how stock will be kept up to date, for example from
your shop system.

**2. Card payments. Owner: Pharmacy.**
Customers can't pay until the store's payment account is set up in Shopify.
That needs the business's own details: company and bank details and proof of
identity. Only the owner can enter them, which is why it waits for the
transfer. Once it is on, we will put one real test order through together and
refund it.

**3. Delivery rates. Owner: Pharmacy, then Kakion.**
We need your delivery prices, and two numbers confirmed:

- **Free delivery over €65 or €60?** The website says €65 everywhere. Your
  About Us text says €60. One of them is wrong.
- **Same-day dispatch cut-off.** Twelve of the category-page questions say
  "order before 3pm". Tell us the real time. The website won't promise
  same-day dispatch until you do.

Once we have your answers, we'll enter them.

**4. Which medicines need a pharmacist check. Owner: Pharmacy (pharmacist).**
The website can make a customer answer your questions before buying a medicine.
Their answers come to you with the order, and nothing is sent until you
approve it. This is built and tested, but it has nothing to work on yet,
because nobody has said which products need it.

At the moment all 521 products in your "Pharmacy" department are treated the
same way. That includes things that are not medicines at all: for example, a
suncare travel set is filed under Pharmacy > Travel Sickness and shows "Ask a
pharmacist before you buy". We need a list of the products that genuinely need
a pharmacist check, and the questions to ask for each. The spreadsheet of all
521 is described under "Product questions" below.

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

**How the pharmacist check works with payment. Owner: Pharmacy (pharmacist).**
Shopify can't hold a customer at the till while a pharmacist looks at their
answers. So the order of events is:

1. The customer pays.
2. A pharmacist reviews the answers.
3. The order is either sent, or cancelled and refunded.

The customer is told this before they pay. Please confirm:

- You are happy with this way of working.
- You are happy with the wording the customer sees.
- Who will review these orders, and how quickly.

**Answers shown on product pages. Owner: Pharmacy (pharmacist).**
Each product can carry its own short questions and answers. Google may show
those answers on its own results page, away from the product. So on a pharmacy
site, each one needs your sign-off before it goes up. None have been written
yet.

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

### Store details

**Map positions for the seven shops. Owner: Pharmacy.**
The "use my location" button on the store finder stays switched off until
every shop has its exact map position (latitude and longitude). You can copy
these from each shop's Google Business Profile.

**Who reads the website's email inbox. Owner: Pharmacy.**
Seven forms on the website send an email and nothing else:

- back-in-stock requests
- contact
- cancelling an order
- booking an in-store service
- careers
- two prescription forms

Shopify keeps no copy of any of them. If an email is deleted, the request is
gone. Please name the person who owns that inbox. They should file these
emails rather than delete them.

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

### Product questions (from the two spreadsheets)

**The 521 "pharmacist review" products. Owner: Pharmacy (pharmacist).**
Spreadsheet: `pharmacist-review-gated-products.csv`. It lists every product in
the Pharmacy department, with type, brand, price and stock. Please mark the
ones that genuinely need a pharmacist check. This is the list that settles
launch blocker 4.

**Brands on the current website versus the new shop. Owner: Pharmacy.**
Spreadsheet: `brand-counts-live-vs-catalogue.csv`, dated 9 September.

- Some brands have fewer products in the new shop than on your current
  website. For example, Jenny Glow has 67 there and 44 here.
- A few brands have none in the new shop: Lerelle Beauty, Harry's and
  Dr Squatch.

Please check whether the missing products should come across. We'll refresh
the numbers first, because the catalogue has changed since.

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
Some images are still missing, including photos of the seven shops. Where an
image is missing, the website shows a neat placeholder. The image brief
(`IMAGE-BRIEF.md`) lists every slot with the size it needs.

**Mobile filter and sort. Owner: Kakion.**
Built and checked, not yet live:

- On phones, the filter now opens as a panel from the side, with **Apply** and
  **Clear all** always on screen.
- The sort box matches the rest of the site.

Due to go live in the next update.

**Mobile "back" link and breadcrumbs. Owner: Kakion.**
Built and checked, not yet live. On phones, a single "back" link replaces the
long trail of page links at the top of the page. Due in the same update.

**Test the website's forms with a real submission. Owner: Kakion, with the
pharmacy.**
None of the seven email forms has been sent on the real store yet. We'll send
one test together and confirm it reaches the right inbox and reads properly.

**Point the remaining links at the right legal pages. Owner: Kakion.**
Waiting on the solicitor's decision.

**Seasonal content. Owner: Pharmacy (we can show you how).**
Nothing on the website changes with the seasons by itself. The homepage slides
(currently including Back To School), the offers and the promotional strip are
changed by hand in the theme editor.

**Small tidy-ups. Owner: Kakion.**
- The store still holds two spare copies of the website design: "Policies
  Preview", from the previous developer, and a development copy. Neither is
  shown to customers. We'll remove them after the handover so nobody edits
  the wrong one.
- The store-finder map uses a Google Maps key. It should be locked to your
  web address in Google's settings, so nobody else can use it and run up
  charges.
- The "cancel an order" form doesn't label its emails the way the other six
  do. It is a small fix, so the inbox can sort them.
- An unfinished change to the widths of the drop-down menus. We'll finish it
  or drop it.

---

## 3. What is done

All of this is built and checked. The most recent work, including the
pharmacist check, goes onto the store in the final update before the handover.

- The new design, on every page, on phones and computers.
- About 2,474 products, arranged in 8 departments and roughly 290 categories,
  plus 134 brand pages and an A–Z brands page.
- Menus built from the same category list, so the header, the phone menu and
  the category pages always agree.
- Search with suggestions as you type.
- A bag that slides in from the side, a wishlist, and a "quick view" on
  product cards.
- The seven shops, with addresses, phone numbers, opening hours and a map.
  Google reads the opening hours too.
- The gift voucher page.
- The pharmacist check for medicines, ready for your list and your questions.
- "Tell me when it's back" requests on sold-out products. A person from the
  pharmacy replies; it is not an automatic alert.
- The cookie banner, with the choices Irish and EU law require.
- The PSI registration mark in the footer.
- The free-delivery amount set in one place, so the website can't contradict
  itself.
- A set of automatic checks we run on each update: readability, layout on
  phones, forms, menus and the pharmacist check.
