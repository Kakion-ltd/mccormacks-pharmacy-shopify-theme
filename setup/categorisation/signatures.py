"""Per-collection match signatures for the categorisation sweep (1 Oct 2026).

Each target names the candidate pool (product types it may draw from) and three
regexes over the product title. A product matches at the first confidence level
whose pattern hits, after `drop` has removed the known false friends. The pool is
what keeps the regexes short: `blush` is unambiguous inside `Beauty > Face` and
useless across the whole catalogue, where it also matches a Jo Malone fragrance.
"""

# pool kinds: ('=', exact types) or ('^', type prefixes) or None for the whole catalogue
def E(*t): return ('=', t)
def P(*t): return ('^', t)

COLD = E('Pharmacy > Cold & Flu')
CHILD = E("Pharmacy > Children's Medicine")
ALLERGY = E('Pharmacy > Allergy Relief')
STOMACH = E('Pharmacy > Stomach & Digestion', 'Pharmacy')
PAIN = E('Pharmacy > Pain Relief')
FOOT = E('Pharmacy > Foot & Nail Care')
EYEEAR = E('Pharmacy > Eye & Ear Care')
SENS = E('Pharmacy > Sensitive Conditions')
FIRSTAID = E('Pharmacy > First Aid')
ORAL = E('Pharmacy > Oral Health', 'Toiletries > Dental')
MEDSKIN = E('Pharmacy > Medicated Skincare')
WOMEN = E("Pharmacy > Women's Health")

# handle: (pool, high, medium, low, drop, note)
SIGS = {
 # ---------------------------------------------------------------- Pain Relief
 'baby-children-pain-relief': (E("Pharmacy > Children's Medicine", 'Pharmacy > Pain Relief'),
   r'Calpol|Nurofen Child|Easofen Child|Paralink|Panadol Baby|Tefin \d+Mg Ibuprofen',
   r'', r'', r'Calpol 6\+ Fastmelts', ''),
 'muscle-joint-pain': (PAIN,
   r'Deep Heat|Voltarol|Diclac|Thermacare|Tramma Gel|Arnicare|Cydonia (Horse Balm|Uplifting Horse|Lively Tigers|Soothing Arnica|Cooling Polar)',
   r'Celtic Wind Cbd|Nubit', r'', r'', ''),
 # ---------------------------------------------------------------- Cold & Flu
 'cold-flu-combination-products': (E('Pharmacy > Cold & Flu'),
   r'Lemsip|Night Nurse|Benylin 4 Flu|Benylin Day & Night|Advil Cold|Nurofen Cold|Panadol C&F|Actifed|Uniflu With Vitamin|Ilvico',
   r'', r'', r'Lemsip Max Cough', ''),
 'cough': (E('Pharmacy > Cold & Flu', "Pharmacy > Children's Medicine"),
   r'Cough|Expectorant|Benylin|Buttercup Broncho|Broncho Stop|Casacol|Exputex|Robitussin|Viscolex',
   r'', r'', r'Benylin 4 Flu|Benylin Day & Night', ''),
 'sore-throat': (E('Pharmacy > Cold & Flu'),
   r'Strepsils|Difflam|Gelorevoice',
   r'Halls|Jakemans|Fishermans Friend', r'', r'', 'Halls/Jakemans/Fisherman’s sit between confectionery and a throat lozenge'),
 'blocked-nose-sinus': (E('Pharmacy > Cold & Flu', 'Pharmacy > Allergy Relief'),
   r'Otrivine|Sudafed|Sudaplus|Sinex|First Defense|Vicks Inhaler|Olbas|Sinutab|Sinus|Sterimar|Neilmed|Sreeze Nasal|Vaporub|Vapopads',
   r'Beconase|Flixonase|Nasacort', r'', r'Otrivine Antistin', 'The steroid sprays are hayfever first; they also relieve a blocked nose'),
 # ---------------------------------------------------------------- Stomach
 'nausea-acid-indigestion-reflux': (STOMACH,
   r'Gaviscon|Rennie|Nexium|Losec|Emazole|Pepcid|Maalox|Alka Seltzer|Bisodol|Motilium',
   r'', r'', r'Rennie Deflatine|Gaviscon Infant', ''),
 'bloating-gas': (STOMACH, r'Deflatine|Bloateze', r'', r'', r'', ''),
 'constipation': (STOMACH,
   r'Dulcolax|Dulcosoft|Fybogel|Senokot|Microlax|Lactulose|Milk Of Magnesia|Glycerol Supp',
   r'', r'', r'', ''),
 'diarrhoea': (STOMACH, r'Imodium|Arret|Dioralyte', r'', r'', r'', ''),
 'cramping-irritable-bowel': (STOMACH, r'Buscopan|Colpermin', r'', r'', r'', ''),
 'haemorrhoids-piles': (E('Pharmacy > Stomach & Digestion', 'Pharmacy > Pain Relief',
                          'Pharmacy > Medicated Skincare', 'Pharmacy > Sensitive Conditions'),
   r'Anusol|Preparation H', r'', r'', r'', ''),
 # ---------------------------------------------------------------- Sensitive
 'menopause': (E("Supplements > Women's Wellbeing", "Pharmacy > Women's Health", 'Women’s Health'),
   r'Meno Active|Meno & Peri|Menopause Test', r'', r'', r'', 'Supplements and a test, not medicines'),
 'hair-loss': (None, r'Regaine|Anti Hair Loss|Phytocyane', r'', r'', r'', ''),
 'thrush-antifungal': (E("Pharmacy > Women's Health", 'Pharmacy > Foot & Nail Care',
                         'Pharmacy > Medicated Skincare', 'Toiletries > Feminine Care'),
   r'Canesten|Daktarin|Desenex|Lamisil', r'Relactagel|Femfresh', r'', r'Canesten 1% Cream', ''),
 'headlice': (E('Pharmacy > Sensitive Conditions', "Pharmacy > Children's Medicine"),
   r'Full Marks|Lyclear|Lice Dr|Vamousse', r'', r'', r'', ''),
 'cystitis': (E('Pharmacy > Sensitive Conditions'), r'Cystopurin', r'', r'', r'', ''),
 'skintags-warts-veruccas': (E('Pharmacy > Foot & Nail Care'),
   r'Salactol|Salatac|Wartner|Wart|Verruca|Veruca', r'', r'', r'', ''),
 'nicotine-patches': (E('Pharmacy > Nicotine Replacement'), r'Patch', r'', r'', r'', ''),
 # ---------------------------------------------------------------- Eye & Ear
 'dry-eye': (EYEEAR,
   r'Hylo|Tears Naturale|Thealoz|Artelac|Murine Dry|Optrex Actimist|Optrex Refreshing|Optrex Soothing',
   r'Optrex Multi Action Eye Wash', r'', r'', ''),
 'blepharitis-eyelid-hygiene': (EYEEAR, r'Blephaclean|Blepharitis|Lid Wipes|Optase Moist Heat', r'', r'', r'', ''),
 'macular-degeneration-glaucoma': (E('Supplements > Eyes & Ears'), r'Macushield', r'', r'', r'',
   'Macushield is for age-related macular degeneration. Nothing stocked is for glaucoma'),
 'ear-wax-treatments': (E('Pharmacy > Eye & Ear Care', 'Toiletries > Travel'),
   r'Cerumol|Exterol|Tropex|Audiclean|Cl-Ear Express', r'Quies Pure Wax', r'', r'', ''),
 'ear-care-earplugs': (E('Pharmacy > Eye & Ear Care', 'Toiletries > Travel'),
   r'Ear Plugs|Earplug', r'Cl-Ear Ear Relief|Cl-Ear Olive Oil|Duracell Hearing Aid', r'', r'', ''),
 # ---------------------------------------------------------------- Sleep / mind
 'healthy-mind-sleeping-aids': (E('Pharmacy > Sensitive Conditions', 'Supplements > Sleep & Stress',
                                  'Supplements', "Supplements > Children's Supplements"),
   r'Nytol|Panadol Night|Kalms',
   r'Rescue Remedy|Stress B Complex|Revive Active Sleep|Night-Time Gummies|Magnesium Gummies', r'', r'', ''),
 'sleep-rest': (E('Pharmacy > Sensitive Conditions', 'Supplements > Sleep & Stress'),
   r'Nytol|Panadol Night|Kalms', r'Rescue Remedy|Stress B Complex', r'', r'',
   'A group page matches its own tag only, so it needs the tag even where a leaf already has the product'),
 # ---------------------------------------------------------------- Oral
 'dry-mouth': (ORAL, r'Bioxtra|Biotene|Dry Mouth', r'', r'', r'', ''),
 'gum-health-gingivitis': (ORAL, r'Corsodyl|Gingival|Gum Health|Tepe|Interdental|Flosser', r'', r'', r'', ''),
 'mouth-ulcers-cold-sores': (E('Pharmacy > Oral Health', 'Pharmacy > Cold & Flu',
                               'Pharmacy > Medicated Skincare', 'Toiletries > Dental'),
   r'Zovirax|Acic 5%|Viralief|Compeed Cs|Compeed Discreet Cold Sore|Sorefix|Bonjela Gel 15G|Carbosan|Kin Care Gel',
   r'Difflam|Anbesol', r'', r'Bonjela Teething', ''),
 'teething': (E('Pharmacy > Oral Health', 'Baby > Baby Health', 'Baby'),
   r'Teething|Teetha', r'', r'', r'Soother & Comforter', ''),
 # ---------------------------------------------------------------- Continence
 'continence-care': (E('Toiletries > Feminine Care', "Toiletries > Men's Grooming"),
   r'^Tena', r'', r'', r'', 'All 12 Tena lines; the group page needs its own tag'),
 'bladder-weakness': (E("Toiletries > Men's Grooming", 'Toiletries > Feminine Care'),
   r'Tena Men', r'', r'', r'', ''),
 'pads': (E('Toiletries > Feminine Care'),
   r'Tena Lady (Discreet Mini|Normal|Extra|Maxi Night|Duo Pack)|Tena Lady Normal Discreet', r'', r'', r'Pant', ''),
 'pants': (E('Toiletries > Feminine Care', "Toiletries > Men's Grooming"), r'Tena.*Pant', r'', r'', r'', ''),
 'odour-control-barrier-creams': (E('Pharmacy > Medicated Skincare', 'Pharmacy > Sensitive Conditions'),
   r'', r'Caldesene Adult Powder|Senset Cleans Foam', r'', r'',
   'Nothing here is sold as a continence barrier cream; these two are the nearest thing'),
 # ---------------------------------------------------------------- Conceive / sexual
 'pregnancy-tests': (E("Pharmacy > Sexual Health", 'Pharmacy > Medical Devices', 'Toiletries > Feminine Care'),
   r'Pregnancy', r'', r'', r'', ''),
 'ovulation-tests': (E("Pharmacy > Sexual Health", 'Pharmacy > Medical Devices', 'Toiletries > Feminine Care'), r'Ovulation', r'', r'', r'', ''),
 'trying-to-conceive': (E("Pharmacy > Women's Health", 'Pharmacy > Sexual Health',
                          'Pharmacy > Medical Devices', "Supplements > Women's Wellbeing",
                          'Toiletries > Feminine Care'),
   r'Pregnancy|Ovulation', r'Clonfolic|Proceive|Folic Acid', r'', r'', ''),
 'erectile-dysfunction': (E('Pharmacy > Sexual Health'),
   r'Viagra Connect|Cialis|Sidena', r'', r'', r'', 'All five carry questionnaire-ed already'),
 'condoms': (E("Toiletries > Men's Grooming"), r'^Durex', r'', r'', r'Durex Play', ''),
 # ---------------------------------------------------------------- First aid
 'antiseptics-wound-cleaning': (E('Pharmacy > First Aid', 'Pharmacy > Medicated Skincare',
                                  'Toiletries > Bath & Shower', 'Toiletries > Masks, Gloves & PPE',
                                  'Toiletries > Handsoap & Sanitizer'),
   r'Antiseptic|Savlon|Iodine Tincture|Surgical Spirits|Hydrogen Peroxide|Rowarolan|Wound|Bepantiseptic',
   r'Dettol', r'', r'', 'Dettol is spread over four product types; see the wrong-category tab'),
 'bandages-plasters': (E('Pharmacy > First Aid'),
   r'Plaster|Medicrepe|Mediform|Melolin|Mepore|Micropore|Meditape|Medisilk|Medilite|Mediswab|Medigauze|Medporex|Inadine|Jelonet|Triangular Bandage|Zinc Oxidetape|Tubular Gauze|Finger Cots',
   r'', r'', r'Blister Plasters|Corn Removal Plasters|Durance', ''),
 'supports': (E('Pharmacy > First Aid'),
   r'Support|Tubigrip|Tubular Supp|Thumb Stall', r'Heel Cushion|Foam Toe Protector', r'', r'', ''),
 'cold-therapy-heat-therapy': (E('Pharmacy > First Aid', 'Pharmacy > Pain Relief', 'Gifts > Christmas Shop'),
   r'Ice Pack|Hot Pack|Hot Cold Pack|Thermacare|Kool N Soothe|Instant Ice Spray',
   r'Warmies|Hot Water Bottle|Cydonia Cooling Polar Ice', r'', r'', ''),
 'insect-bites-prevention': (E('Pharmacy > First Aid', 'Pharmacy > Allergy Relief',
                               'Pharmacy > Travel Essentials', 'Toiletries > Travel'),
   r'Anthisan|Jungle Formula|Xpel|Bug Band', r'', r'', r'', ''),
 # ---------------------------------------------------------------- Foot
 'athletes-foot': (FOOT, r'Daktarin|Desenex', r'', r'', r'', ''),
 'fungal-nail-infection': (FOOT, r'Curanail|Mycosan', r'', r'', r'', ''),
 'cracked-heels-dry-skin': (E('Pharmacy > Foot & Nail Care', 'Skincare > Hands & Feet', 'Skincare > Body Care'),
   r'Cracked Heel', r'Keratosane|Working Hands', r'', r'', ''),
 'blisters-bunion-care': (E('Pharmacy > Foot & Nail Care', 'Pharmacy > Medicated Skincare', 'Pharmacy > First Aid'),
   r'Blister|Bunion', r'', r'', r'Sterile Burn', ''),
 'corn-callous-care': (E('Pharmacy > Foot & Nail Care', 'Pharmacy > First Aid'),
   r'Callous Caps|Corn Caps|Corn Pads|Corn Shields|Corn Removal', r'', r'', r'', ''),
 'chiropody-felt-padding': (FOOT,
   r'Chiropody Felt|Fleecy Stretch Padding|Animal Wool', r'Heel Grips|Gel Toe Separators', r'', r'', ''),
 'toe-nail-care': (E('Pharmacy > Foot & Nail Care', 'Beauty > Nails', 'Baby > Soothers & Accessories'),
   r'Toe Nail Clipper', r'Gel Toe Separators', r'Foam Toe Protector', r'Baby Nail Clippers', ''),
 'foot-soak-odour-control': (FOOT, r'Fresh Step', r'', r'', r'',
   'One product. No foot soaks stocked'),
 # ---------------------------------------------------------------- Devices
 'oximeters-weighing-scales': (E('Pharmacy > Covid19', 'Pharmacy > Medical Devices'),
   r'Oximeter', r'', r'', r'', 'No weighing scales stocked — see the rules tab'),
 'electrical-healthcare': (E('Pharmacy > Covid19', 'Pharmacy > Medical Devices', 'Baby > Baby Health'),
   r'Oximeter', r'Thermometer Infrared|Lifesense Thermometer', r'', r'', ''),
 # ---------------------------------------------------------------- Fragrance
 'ladies-fragrance-sets': (E("Gifts > Women's Fragrance", 'Gifts > All Fragrances'),
   r'Gift Set|Giftset|\d\s?Pc|\d Piece|Piece (Ladies|Set)', r'', r'', r'', ''),
 'ladies-fragrance-singles': (E("Gifts > Women's Fragrance"),
   r'.', r'', r'', r'Gift Set|Giftset|\d\s?Pc|\d Piece|Deodorant|Body Mist|Shower Gel|Body Spray',
   'Every women\u2019s fragrance in the type that is not a set'),
 'mens-fragrance-sets': (E("Gifts > Men's Fragrance"),
   r'Gift Set|Giftset|\d\s?Pc|\d Piece', r'', r'', r'', ''),
 'mens-fragrance-singles': (E("Gifts > Men's Fragrance"),
   r'.', r'', r'', r'Gift Set|Giftset|\d\s?Pc|\d Piece|Deodorant|Body Mist|Shower Gel|Body Spray',
   'Every men\u2019s fragrance in the type that is not a set'),
 # ---------------------------------------------------------------- Beauty leaves
 'lipstick': (E('Beauty > Lips'), r'Lipstick', r'', r'', r'', ''),
 'lip-gloss': (E('Beauty > Lips', 'Beauty > Face', 'Beauty'), r'Lip Gloss|High Shine Gloss|Hydralip', r'', r'', r'', ''),
 'lip-liner': (E('Beauty > Lips'), r'Lip Liner', r'', r'', r'', ''),
 'mascara': (E('Beauty > Eyes', 'Beauty'), r'Mascara', r'Lash Booster', r'', r'', ''),
 'eyeliner': (E('Beauty > Eyes', 'Beauty'), r'Eyeliner', r'', r'', r'', ''),
 'eyeshadow': (E('Beauty > Eyes', 'Beauty'), r'Eyeshadow|Eye Palette', r'', r'', r'', ''),
 'blusher': (E('Beauty > Face', 'Beauty'), r'Blush', r'', r'', r'Bronze & Blush|Line & Shine|Hydralip|Lip Oil|Lip Library', ''),
 'bronzer': (E('Beauty > Face', 'Beauty'), r'Bronzer|Cronzer|Bronze & Blush|Shape Stick Bronze|Cream Luxe Bronze|Instant Bronze Boost',
   r'Bronze Glow Primer|Perfection Primer Bronze', r'', r'', ''),
 'false-eyelashes': (E('Beauty > Brows & Lashes', 'Beauty > Eyes'),
   r'The One Lashes|Striplash Adhesive', r'Lash Growth Serum|Lash Booster', r'', r'', ''),
 'tweezers': (E('Beauty > Brushes & Accessories'), r'Tweezer', r'', r'', r'', ''),
 'makeup-brushes-tools': (E('Beauty > Brushes & Accessories', 'Beauty > Face', 'Beauty'),
   r'Brush Cleaner|Makeup Brush|Base Brush|Empress Base', r'Tweezer|Sponge|Applicator', r'', r'', ''),
 'makeup-brush-cleaners': (E('Beauty > Face', 'Beauty'), r'Brush Cleaner', r'', r'', r'', ''),
 'tanning-mitts': (E('Beauty > Tanning', 'Skincare > Cleanse'),
   r'Tan(ning)? Mitt|Velvet Tan Mitt|Applicator Glove Mitt', r'Cleanse Off Mitt', r'', r'', ''),
 'gradual-tan': (E('Beauty > Tanning'), r'Gradual', r'', r'', r'', ''),
 'false-nails-nail-wraps': (E('Beauty > Nails'), r'False Nail|Nail Wrap|Press On', r'', r'', r'', ''),
 'cuticle-nail-care': (E('Beauty > Nails'), r'Cuticle', r'Nail Strengthener|Nail Treatment|Nail File|Nail Clipper', r'', r'', ''),
 # ---------------------------------------------------------------- Skincare leaves
 'anti-ageing': (E('Skincare > Face', 'Skincare', 'Skincare > Eye Care'),
   r'Anti-Ageing|Anti Ageing|Retinoid|Retinol', r'Wrinkle|Firming|Collagen Boost', r'', r'', ''),
 'moisturisers': (E('Skincare > Body Care'), r'Body (Lotion|Cream|Butter|Moisturis)', r'Moisturis', r'', r'', ''),
 'exfoliators': (E('Skincare > Body Care', 'Toiletries > Bath & Shower'),
   r'', r'Gentle Scrub Body Wash', r'', r'',
   'No body exfoliator is stocked; the scrubs and peels are all facial and already on Exfoliators & Peels'),
 'dry-skin': (E('Skincare > Face', 'Skincare > Body Care', 'Skincare', 'Baby > Maternity Care'),
   r'Dry Skin', r'Dry To Very Dry', r'', r'',
   'Near-duplicate of Dry Skin, Eczema & Psoriasis \u2014 see the rules tab'),
 'dry-skin-eczema-psoriasis': (E('Skincare > Body Care', 'Pharmacy > Medicated Skincare', 'Skincare'),
   r'Eczema|Psoriasis|Xemose|Epaderm|Doublebase|Silcocks|Aqueous Cream|Oilatum|E45|Astral', r'', r'', r'', ''),
 'problem-skin': (E('Pharmacy > Medicated Skincare', 'Skincare > Face', 'Skincare'),
   r'Acne|Blemish|Clearer Skin', r'', r'', r'', ''),
 # ---------------------------------------------------------------- Vitamins leaves
 'skin-hair-nails': (E("Supplements > Women's Wellbeing", 'Supplements', 'Vitamins'),
   r'Skin.*Hair.*Nail|Hair.*Skin.*Nail|Collagen', r'Biotin', r'', r'', ''),
 'brain-health': (E('Supplements > Brain Health & Omega Oils'), r'.', r'', r'', r'',
   'The whole type. Better fixed as a rule change than by tagging \u2014 see the rules tab'),
 'baby-feeding': (E('Baby > Feeding'),
   r'.', r'', r'', r'', 'The live rule is TAG "Baby Feeding" but the type is "Baby > Feeding" — see the rules tab'),
}
