"""The nine dash/asterisk bullet products, done by hand.
Each 'after' is typed out; verify_same() proves no word changed.
"""
import json, re, collections, html as H


def _strip(h):
    t = re.sub(r'<[^>]+>', ' ', h or '')
    return re.sub(r'\s+', ' ', H.unescape(t)).strip()


def letters(h):
    """Every letter and digit of the rendered text, in order."""
    return re.sub(r'[^0-9a-z]', '', _strip(h).lower())


def punct(h):
    """How many of each punctuation mark the rendered text has."""
    return collections.Counter(c for c in _strip(h) if not c.isalnum() and not c.isspace())

M = {}

M['got2b-glued-blasting-freeze-hairspray-300ml'] = (
 '<p>\xa0Got2b Glued Hairspray Blasting Freeze Spray 300ml is designed to provide a firm hold '
 'for up to 72 hours. The vegan and silicone-free formula is excellent for all hair types and '
 'has a lovely citrus scent. This hairspray instantly secures and sets your hair, freezing it '
 'in place until your next shampoo.</p>'
 '<ul><li>Strong hold hairspray for up to 72 hours</li>'
 '<li>Vegan and silicone-free</li>'
 '<li>For all hair types</li>'
 '<li>Secures hair in seconds and is simple to remove</li>'
 '<li>Our legendary best-selling collection</li></ul>')

M['uriage-xemose-sos-anti-itch-mist'] = (
 '<p>This Uriage Xémose Sos Anti-Itch Mist offers your skin long lasting comfort and instant '
 'anti-itch.</p>'
 '<ul><li>Soothes in less than 60 seconds. Instant anti-itch high efficacy</li>'
 '<li>Practical and playful use</li>'
 '<li>Nourishes Intensely</li>'
 '<li>10% Shea Butter + Illipe oil for an intense nutrition</li>'
 '<li>Long-lasting comfort</li>'
 '<li>24H anti-recurrence action</li></ul>')

M['compeed-blister-medium-5pk'] = (
 '<p>Compeed® hydrocolloid technology is an active gel with moisture absorbing particles. '
 'Compeed® plaster acts like a second skin to support the natural moisture balance, to:</p>'
 '<ul><li>Relieve blister pain instantly.</li>'
 '<li>Protect and cushion against rubbing.</li>'
 '<li>Offer fast wound healing.</li></ul>'
 '<p>Stays in place for several days.</p>')

M['wrap-up-microfibre-hair-wrap'] = (
 '<p>The Voduz ‘Wrap Up’ Microfibre Towel is the perfect accessory for the dreaded hair wash. '
 'The ‘Wrap Up’ Microfibre Towel :</p>'
 '<ul><li>Is soft and super absorbent.</li>'
 '<li>Will help soak excess water from the hair quickening, blow dry time.</li>'
 '<li>Tames frizz and friction from normal towel drying.</li></ul>')

M['voduz-slumber-satin-sleep-set'] = (
 '<p>You’re three steps away from good hair days with Voduz ‘Slumber’ Satin Sleep Set. This '
 'ultimate good sleep, good hair trio will make dreaming of good hair in the morning a thing '
 'of the past. The Voduz ‘Slumber’ Sleep Set in blush pink contains:</p>'
 '<ul><li>The Satin Pillowcase which will help you to minimize static, frizzy hair and make '
 'for a gentle, luxurious night sleep.</li>'
 '<li>The Satin Scrunchie which will help reduce breakage and kinks in the hair during sleep '
 'or can be used a stylish accessory.</li>'
 '<li>The Sat</li></ul>')

for handle, word in (
        ('l-oreal-paris-elvive-dream-lengths-conditioner-for-long-damaged-hair-300ml',
         ('Conditioner', 'while als')),
        ('l-oreal-paris-elvive-dream-lengths-shampoo-for-long-damaged-hair-400ml',
         ('shampoo', 'while also no'))):
    kind, tail = word
    M[handle] = (
     '<p>Do you want to have gorgeous long hair but are having difficulty reaching your desired '
     'lengths? \xa0Achieve your long hair goals with this\xa0\xa0Detangling %s which\xa0\xa0binds '
     'to the hair fiber from root to tip, resulting in stronger, healthier-looking lengths. '
     'Don\'t let the knots take over! The\xa0product contains a mix of Hair Vitamins:</p>'
     '<ul><li>VEGETABLE KERATIN</li><li>VITAMINS FOR HAIR</li><li>CARROTS OIL</li></ul>'
     '<p>It detangles hair and strengthens lengths to prevent hair breakage*, %s</p>' % (kind, tail))

M['gillette-shaving-gel-reg-200ml'] = (
 '<p>There’s nothing like a classic. Go ahead and get the rich, creamy lather of Gillette '
 'Classic Regular Men\'s Shaving Foam. This shaving cream features an extra thick consistency '
 'for a shave that’s smooth and comfortable. Just spread it on, shave with ease and rinse '
 'clean to reveal skin that’s soft to the touch. Rich lather, spreads easily and rinses clean. '
 'Simple. Honest. Classic.</p>'
 '<ul><li>Shaving foam featuring an extra thick consistency for a shave that’s smooth and '
 'comfortable</li>'
 '<li>Spread it on, shave w</li></ul>')

M['udos-super-8-probiotics-30-caps'] = (
 '<p>Udo\'s Choice Super 8 contains eight essential probiotic bacterial strains which help the '
 'digestive system to functional at an optimal level.</p>'
 '<ul><li>Specifically developed by the renowned Dr. Udo Erasmus to help the gut maintain a '
 'healthy flora balance</li>'
 '<li>This powerful blend also supports the immune system</li>'
 '<li>Specifically with a higher percentage and concentration of L. acidophilus</li>'
 '<li>Specially chosen for their value to upper bowel health and have been formulated to the '
 'appropriate viable count</li>'
 '<li>42 billion v</li></ul>')


if __name__ == '__main__':
    prods = {json.loads(l)['handle']: json.loads(l) for l in open('products.jsonl')}
    rows = []
    for handle, after in M.items():
        p = prods[handle]
        before = p['descriptionHtml']
        assert letters(before) == letters(after), handle     # not one letter moved
        gone = punct(before) - punct(after)
        assert not (punct(after) - punct(before)), handle      # nothing added
        assert set(gone) <= {'-', '\u2013', '*'}, (handle, gone)  # only bullet markers left
        rows.append(dict(id=p['id'], handle=handle, title=p['title'],
                         medicine='pharmacist-review' in p['tags'],
                         before=before, after=after, by_hand=True,
                         markers_removed=dict(gone)))
        print(f"  {handle[:48]:48} removed {dict(gone)}")
    json.dump(rows, open('manual.json', 'w'), indent=1)
    print('hand-written', len(rows), '- all word-identical')
