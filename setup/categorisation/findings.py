"""Hand-made judgement calls for the sweep: things no regex decides.

Each list is read by build.py. Keep the wording plain; Keelan reads these.
"""

# Collections with nothing to put in them, and what to do instead.
STAY_EMPTY = [
 # handle, title, verdict, why
 ('sport', 'Sport', 'Remove',
  'Nothing stocked is sports nutrition or sports therapy. The nearest items (three Physiologix '
  'supports, one Nuun electrolyte sachet) belong on Supports and Other Supplements.'),
 ('la-roche-posay', 'La Roche-Posay', 'Remove',
  'No product has this vendor and none is stocked under any spelling. The brand page 404s in effect.'),
 ('proven', 'Proven', 'Remove',
  'No product has this vendor. Same as La Roche-Posay.'),
 ('elizabeth-arden', 'Elizabeth Arden', 'Remove',
  'Brand page with no products. The only empty brand page left.'),
 ('hot-offers', 'Hot Offers', 'Keep empty — client curates',
  'A merchandising page, not a category. It fills when someone tags the products they want '
  'promoted. Not a job for this sweep.'),
 ('new-in', 'New In', 'Keep empty — client curates',
  'Same as Hot Offers. Four products are typed "New", which is a type doing a tag’s job; '
  'see the rules tab.'),
 ('exfoliators', 'Exfoliators (Body Skincare)', 'Keep thin or remove',
  'No body exfoliator is stocked. Every scrub and peel is facial and already sits on '
  'Exfoliators & Peels. One borderline item (Dove Gentle Scrub Body Wash) is proposed at medium.'),
 ('odour-control-barrier-creams', 'Odour Control & Barrier Creams', 'Keep thin',
  'No continence barrier cream is stocked. Caldesene Adult Powder and Senset Cleans Foam are the '
  'nearest and are proposed at medium; both are a stretch.'),
 ('foot-soak-odour-control', 'Foot Soak & Odour Control', 'Keep thin',
  'One product (Scholl Fresh Step foot spray). No foot soaks stocked.'),
 ('oximeters-weighing-scales', 'Oximeters & Weighing Scales', 'Rename or keep thin',
  'One oximeter, no weighing scales, no blood-pressure monitors. Either rename the page to '
  'Oximeters or leave it at one product.'),
]

# Collections whose RULE is the problem, not the products.
RULE_FIXES = [
 # handle, title, rule now, proposed rule, gain, why
 ('brain-health', 'Brain Health', "TAG EQUALS 'Brain Health'",
  "TYPE EQUALS 'Supplements > Brain Health & Omega Oils'", '2 → 12',
  'The type already exists and holds exactly the right 12 products. Two of them carry the tag, '
  'which is why the page shows 2. A rule change fills it with no tagging at all.'),
 ('baby-feeding', 'Baby Feeding', "TAG EQUALS 'Baby Feeding'",
  "TYPE EQUALS 'Baby > Feeding'", '2 → 2',
  'The rule condition has no ">" but the two products are typed "Baby > Feeding" and tagged the '
  'same. Shopify matches them anyway because it folds the punctuation, so the page works by luck. '
  'Make the rule say what it means before someone "fixes" the tags.'),
 ('travel-sickness', 'Travel Sickness', "VENDOR EQUALS 'Kwells' OR VENDOR EQUALS 'Stugeron'",
  "TAG EQUALS 'Travel Sickness'", '2 → 2',
  'A rule listing two brand names cannot take a third. It is the only leaf page keyed to vendors '
  'and it breaks the moment a new travel-sickness line comes in. Tag the two products instead.'),
 ('eye-health', 'Eye Health', "TYPE EQUALS 'Supplements > Eyes & Ears'", 'leave as it is', '3 → 3',
  'Correct already. Noted because the three Macushield products are proposed for Macular '
  'Degeneration & Glaucoma as well, so they will sit on both pages. That is intended.'),
 ('cuticle-nail-care', 'Cuticle & Nail Care', "TAG EQUALS 'Cuticle & Nail Care'",
  'merge into Beauty > Nails > Nail Care', '1 → —',
  'A near-duplicate of the filled Nail Care page (10 products) in a different department. '
  'Customers will not know which one to use. One of the two should go.'),
 ('dry-skin', 'Dry Skin', "TAG EQUALS 'Dry Skin'", 'merge with Dry Skin, Eczema & Psoriasis', '3 → —',
  'Two leaves for the same thing: "Dry Skin" under Dermatological Skincare and "Dry Skin, Eczema '
  '& Psoriasis" under Problem Skin. Three products carry both tags already.'),
 ('—types', 'Types doing a tag’s job', 'n/a', 'n/a', 'n/a',
  'Four products are typed "New", one "Sale", one "Christmas Shop", one "Bundles". A type is the '
  'product’s category; a season or a promotion is a tag. These seven land on no category page '
  'because of it.'),
 ('—orphantypes', '61 product types no leaf page matches', 'n/a',
  'either a TYPE rule per leaf, or tag the products', '1,398 products on a department only',
  'The leaf pages are tag-driven and the tagging was never done. Every filled leaf page is '
  'filled by a TYPE rule. This is the single biggest cause of thin sub-navigation and it is why '
  '1,398 products sit on a department page with no sub-category.'),
 ('—companion', 'Pharmacy > Companion Animal has no page', 'n/a',
  'add a leaf to taxonomy.json, or retype the products', '5 products',
  'Five Fleaway Plus veterinary lines are typed into a department that the taxonomy has no page '
  'for. The old site had /c/pet-health/. Decide whether McCormack’s sells pet health online.'),
]

# Products sitting on a page that does not describe them. (handle-free; matched on title)
WRONG_CATEGORY = [
 # title match, what it is, type now, proposed type, proposed tag, confidence
 ('Uddermint Cream 600ml', 'A veterinary udder cream for dairy cows', 'Vitamins & Supplements',
  'DECISION NEEDED — not a vitamin', '', 'high',
  'The known example. It is on the Vitamins page because its type says "Vitamins & Supplements" '
  'and it carries no tags at all. It is not a supplement. People do buy it as a menthol muscle '
  'rub, but it is licensed for cattle, so putting it on Muscle & Joint Pain would present a '
  'veterinary product as a human medicine. Either give it a veterinary page (see Companion '
  'Animal, rules tab) or take it off the website. Pharmacist call.'),
 ('^Tena', 'Continence pads, pants and men’s guards — 12 products',
  "Toiletries > Feminine Care / Toiletries > Men's Grooming", 'Pharmacy > Continence Care',
  'Continence Care + Pads / Pants / Bladder Weakness', 'high',
  'The whole Continence Care group and its four leaves are empty while all 12 Tena products sit '
  'under Feminine Care and Men’s Grooming. This is the biggest single miscategorisation.'),
 ('^Durex', 'Condoms and one lubricant — 11 products', "Toiletries > Men's Grooming",
  'Pharmacy > Sexual Health', 'Condoms (10; not Durex Play)', 'high',
  'Condoms are not grooming. Moving them also gives them the pharmacist lines in buy-assurance.'),
 ('Medicare Digital Pulse Oximeter', 'A pulse oximeter', 'Pharmacy > Covid19',
  'Pharmacy > Medical Devices', 'Oximeters & Weighing Scales + Electrical Healthcare', 'high',
  'Covid19 is a dead category holding this one product.'),
 ('Clearblue', 'Four pregnancy tests and one ovulation test, split over two departments',
  'Pharmacy > Sexual Health (3) / Toiletries > Feminine Care (2)', 'Pharmacy > Sexual Health for all five',
  'Pregnancy Tests (4) / Ovulation Tests (1) + Trying To Conceive', 'high',
  'Three sit on the Sexual Health page beside Viagra and Cialis; the other two are under Feminine '
  'Care. Pregnancy Tests and Ovulation Tests have one product each.'),
 ('Regaine Men Foam', 'Minoxidil 5% foam, a P medicine', "Toiletries > Men's Grooming",
  'Pharmacy > Sensitive Conditions', 'Hair Loss', 'high',
  'A pharmacy-only medicine filed under grooming. It is already tagged pharmacist-review.'),
 ('Phyto.*Anti Hair Loss|Phytocyane', 'Three anti-hair-loss treatments', 'Toiletries > Hair Care',
  'keep the type', 'Hair Loss', 'high', 'Hair Loss is empty; these are what it is for.'),
 ('Quies Foam Ear Plugs', 'Foam earplugs', 'Toiletries > Travel', 'Pharmacy > Eye & Ear Care',
  'Ear Care & Earplugs', 'high', 'Ear Care & Earplugs is empty and named for this product.'),
 ('Quies Pure Wax', 'Wax earplugs', 'Toiletries > Travel', 'Pharmacy > Eye & Ear Care',
  'Ear Care & Earplugs', 'medium',
  '"Wax" here is what the plugs are made of, not an ear-wax treatment. Easy to file wrong.'),
 ('Dioralyte', 'Oral rehydration salts', 'Pharmacy (no sub-category)',
  'Pharmacy > Stomach & Digestion', 'Diarrhoea', 'high',
  'Typed to the bare department, so it reaches no leaf page.'),
 ('Sidena 50Mg', 'Sildenafil 50mg, a P medicine', 'Pharmacy > Sexual Health', 'keep the type',
  'fix the tags', 'high',
  'Its tags are "Pharmacy" and "Sexual Health" as two separate tags, not "Pharmacy > Sexual '
  'Health" as one. This is the comma-split trap in MAINTENANCE. Harmless today because the page '
  'matches on type, but the tags are wrong.'),
 ('Tena Lady Discreet Med Pant 6Pk', 'A Tena product carrying the wrong brand tag',
  'Toiletries > Feminine Care', 'Pharmacy > Continence Care', 'swap tag Quest → Tena Lady', 'high',
  'It is tagged "Quest", so it appears on the Quest brand page and not on Tena Lady.'),
 ('Waxperts Beautiful Body Oil', 'A post-waxing body oil', "Pharmacy > Women's Health",
  'Toiletries > Hair Removal', '', 'high',
  'Sitting among the Canesten and iron supplements. Its two sibling Waxperts products are '
  'already under Hair Removal.'),
 ('Casacol Expectorant Sf 125Ml', 'A cough syrup', 'Pharmacy > Pain Relief',
  'Pharmacy > Cold & Flu', 'Cough', 'high',
  'The 300ml bottle of the same syrup is already under Cold & Flu.'),
 ('Nurofen Cold And Flu Tabs 24Pk', 'Cold and flu tablets', 'Pharmacy > Pain Relief',
  'Pharmacy > Cold & Flu', 'Cold & Flu Combination Products', 'high',
  'Also check whether this is a duplicate of "Nurofen Cold & Flu 24Pk", which is already under '
  'Cold & Flu. Same pack size, two products.'),
 ('Calpol Infant Sf 140Ml', 'Children’s paracetamol', 'Pharmacy > Pain Relief',
  "Pharmacy > Children's Medicine", 'Baby & Children Pain Relief', 'high',
  'The other two Calpol Infant lines are under Children’s Medicine.'),
 ('Buplex Ibuprofen 400Mg Tabs 24Pk', 'Ibuprofen tablets', 'Pharmacy > First Aid',
  'Pharmacy > Pain Relief', '', 'high',
  'The 12Pk of the same tablets is under Pain Relief. First Aid is plasters and bandages.'),
 ('Alka Seltzer 20Pk', 'Effervescent aspirin', 'Pharmacy > Pain Relief', 'pick one and use it',
  '', 'medium',
  'The 10Pk is under Stomach & Digestion. Alka Seltzer is both; the two pack sizes should agree.'),
 ('Difflam Oral Rinse 300Ml', 'Benzydamine mouth rinse', 'Pharmacy > Cold & Flu',
  'Pharmacy > Oral Health', 'Sore Throat + Mouth Ulcers & Cold Sores', 'medium',
  'Difflam Spray is under Oral Health. The rinse is used for both a sore throat and mouth ulcers.'),
 ('Sorefix Rescue Cold Sore Cream', 'A cold sore cream', 'Pharmacy > Cold & Flu',
  'Pharmacy > Oral Health', 'Mouth Ulcers & Cold Sores', 'high',
  'Filed under Cold & Flu on the word "cold".'),
 ('Compeed Blister (Medium 5Pk|Mix 5Pk)', 'Two blister plaster packs', 'Pharmacy > Medicated Skincare',
  'Pharmacy > Foot & Nail Care', 'Blisters & Bunion Care', 'high',
  'The other three Compeed blister packs are already under Foot & Nail Care.'),
 ('Ultrapure Hydrogen Peroxide130ml', 'Hydrogen peroxide', 'Pharmacy > Medicated Skincare',
  'Pharmacy > First Aid', 'Antiseptics & Wound Cleaning', 'high',
  'The 250ml bottle is under First Aid. Note the missing space in the title, too.'),
 ('Medicare Lifesense Thermometer', 'A thermometer', 'Baby > Baby Health',
  'Pharmacy > Medical Devices', 'Electrical Healthcare', 'medium',
  'The infrared one is under Medical Devices. A baby thermometer is arguably both; pick one.'),
 ('Vaseline Pet Jelly', 'Petroleum jelly — three sizes, two types',
  'Baby > Baby Health (250ml) / Baby > Baby Wipes & Changing (50ml, 100ml)', 'one type for all three',
  '', 'medium', 'Three sizes of one product on two different pages.'),
 ("Novomins Women's Bio-Balance Gummies", 'A women’s supplement', "Women's Health (no department)",
  "Supplements > Women's Wellbeing", '', 'high',
  'The type is missing its department, so it matches no menu page at all.'),
 ('Uriage Gentle Jelly Face Scrub', 'A face scrub', 'Skincare > Body Care', 'Skincare > Face',
  'Exfoliators & Peels', 'high', 'Typed to Body Care; it is a facial product.'),
 ('Elave (Facial Intense Moisture Surge|Oil Free Moisturiser)', 'Two facial moisturisers',
  'Skincare > Body Care', 'Skincare > Face', 'Facial Moisturisers', 'high', 'Same as the Uriage scrub.'),
 ("L'il Critters Gummy Vites", 'A children’s multivitamin', 'Pharmacy > Back to School',
  "Supplements > Children's Supplements", '', 'high',
  'A seasonal type holding one product all year. Back to School is a campaign, not a category.'),
 ('Sculpted Bronze Base 30Ml Pump Medium/ Dark', 'A bronzing base', 'Beauty > Face',
  'Beauty > Tanning', 'Bronzer', 'medium',
  'The other three Bronze Base products are under Tanning.'),
 ('^Fleaway Plus', 'Five veterinary flea treatments', 'Pharmacy > Companion Animal',
  'DECISION NEEDED — no page exists', '', 'high',
  'They reach the Medicines & Health department and then nothing. See the rules tab. They are '
  'tagged pharmacist-review because they are veterinary medicines.'),
 ('Castor Oil 100M;', 'Castor oil — and a typo in the title', '(no type)',
  'DECISION NEEDED', '', 'medium',
  'No type, so no category page. Also: the title ends "100M;" instead of "100Ml".'),
 ('Bio-Oil', 'Four Bio-Oil lines', 'Baby > Maternity Care', 'keep the type',
  'already tagged Dry Skin and Problem Skin', 'low',
  'Defensible where it is — Bio-Oil is sold for stretch marks — but two of the three are '
  'also tagged into Skincare, so the range is split across departments.'),
 ('^Dettol', 'Four Dettol lines on four different pages',
  'First Aid / Bath & Shower / Masks, Gloves & PPE / Handsoap & Sanitiser', 'one type for the range',
  'Antiseptics & Wound Cleaning', 'medium',
  'Not wrong one by one, but a customer looking for Dettol finds it in four places.'),
]

# The 21 products on no category page at all.
ORPHANS = [
 ('Treat Yo Self .* Fizz', 'Bath fizz — 4 products', 'New', 'Toiletries > Bath & Shower', 'high'),
 ('(Cleanse|Nourish|Jungle Fresh) (Duo|Washbag)|Africa Washbag', 'Dove and Lynx gift duos and washbags — 5 products',
  'Sale > Christmas Shop', 'Gifts > Gifts for Him / Gifts for Her', 'medium'),
 ('Pestle & Mortar The Heroes Collection', 'A double-cleanse gift set', 'Christmas Shop',
  'Skincare > Cleanse', 'high'),
 ('J&J Cotton Buds', 'Cotton buds — 2 products', '(no type)', 'Toiletries > Cotton & Accessories', 'high'),
 ('Ultra ?Pure (Citric Acid|Glucose Powder)|Ultrapure Liquid Paraffin|Purified Water 5L',
  'Dispensary chemicals — 4 products', '(no type)', 'DECISION NEEDED — no page for these', 'low'),
 ('Sula Sugar Free Sweets', 'Sugar-free sweets — 2 products', '(no type)',
  'DECISION NEEDED — the Diabetes Care page was removed on 25 Sep', 'low'),
 ('Discreet Nasal Snoring Aid', 'A nasal snoring aid', '(no type)',
  'Pharmacy > Sensitive Conditions + Healthy Mind & Sleeping Aids', 'medium'),
 ('Castor Oil 100M;', 'Castor oil', '(no type)', 'DECISION NEEDED — see the wrong-category tab', 'low'),
 ('Electric Picnic Bundle', 'A bundle', 'Bundles', 'Sale > Bundles', 'high'),
]
