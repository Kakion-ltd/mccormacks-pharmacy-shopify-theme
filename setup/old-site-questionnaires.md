# What the old website asks before it sells a medicine

Read on 30 September 2026 from `www.mccormackspharmacy.ie`, by fetching the
product pages and reading the form each one renders. Nothing was bought,
nothing was added to a basket, nothing on that site was changed.

## The short version

The old website has **one questionnaire, on five products**: Viagra Connect
(4 and 8 pack), Cialis (4 and 8 pack) and Sidena. Fourteen Yes/No questions,
the same fourteen on all five.

Every other medicine we checked has **no questions at all**. What it has
instead is two tick boxes, the same two everywhere:

- I am over 18 years of age
- I am not taking any other medication

And **nothing on the page stops any answer.** The questions are not required,
the tick boxes are not required, and a "Yes" to "have you had a heart attack in
the last 6 months" does not stop the sale in the page. The answers are sent to
the pharmacy with the order. Whether the pharmacy's server refuses the order
after that, we could not test without putting a product in a live basket, so we
did not (see "The one thing we could not check").

## How the old site's mechanism works

Each product page can carry two separate things, both set per product in the
shop's admin:

| Thing | Markup | What it renders |
|---|---|---|
| Questions | `mz_questionn_count`, then `mzQstF_1` … `mzQstF_n` | A radio pair, **Yes** and **No**, under each question |
| Tick boxes | `mz_confirmtext_chkbox_count`, then `mz_confirmtext_chkbox_1` … | A checkbox with a sentence beside it |

There is a third, older tick box, `mz_confirmtext_chkbox` (no number), used on
Viagra Connect and Sidena only: "I confirm that this product is for me, the
purchaser."

The Add to Basket button on these products is a `mz_genAjaxLinkPOST` to
`/basket-detail/addall/`. The site's own script (`/Content/javascript/general`)
serialises the whole form and posts it:

```js
genericAjaxProcessActionPOST = function(t,i,r,u){ … $.post(t, $("#mz_form").serialize(), …) }
```

Three things follow from reading that script, and they matter:

1. **No question is required.** There is no `required` attribute anywhere on
   the page and no check in the script. A customer who answers nothing can
   still press Add to Basket.
2. **No tick box is required either.** The script's loop over the tick boxes
   only appends the ones that happen to be ticked; it never counts them.
3. **The page does not know which answer is the wrong one.** The HTML carries
   no "correct answer" for any question, so the page cannot block on an answer
   even in principle. Any blocking would have to happen on the pharmacy's
   server after the post.

So on the evidence of the page itself, every answer **just gets recorded**.
None blocks, none flags.

## The one questionnaire: erectile dysfunction

**On:** Viagra Connect 50mg Tablets 4 Pack; Viagra Connect 50mg Tablets 8 Pack;
Cialis For Men Tadalafil Tablets 4Pk; Cialis For Men Tadalafil Tablets 8Pk;
Sidena 50mg Tablets 4 Pack.

All five carry the identical fourteen questions, character for character. Every
one offers exactly two answers, **Yes** and **No**, and neither answer does
anything in the page.

The wording below is exactly as the site renders it, including its typing
mistakes ("riocigaut", "protsate", "non-artertic") and question 4, which breaks
off mid-sentence.

1. Has your doctor advised that you are not fit enough for any physical and/or sexual activity ?
2. Do you feel very breathless or experience chest pain with light or moderate physical activity, such as walking briskly for 20 minutes or climbing two flights of stairs ?
3. Have you had a heart attack or stroke within the last 6 months ?
4. Do you have any other heart problems or are you under a doctor's care for any of the following
5. Are you taking nitrates (nicorandil or other nitric oxide donors e.g. glyceryl trinitrate,isosorbide mononitrate or isosorbide dinitrate) for chest pain ?
6. Are you using drugs called 'poppers' for recreational purposes (e.g. amyl nitrite)?
7. Are you taking riocigaut or other guanylate cyclase stimulators for lung problems?
8. Are you taking ritonavir (for HIV infection)?
9. Are you taking any CYP3A4 inhibitors, e.g saquinavir (to treat HIV infection), cimetidine (a heartburn treatment), itraconazole or ketoconazole (to treat fungal infections),erythromycin or rifampicin (antibiotics) or diltiazem (for high blood pressure)?
10. Are you taking any alpha-blockers, such as alfuzosin, doxazosin or tamsulosin, which are medicines to treat urinary problems due to enlarged protsate (benign prostatic hyperplasia) or occasionally to treat high blood pressure?
11. Do you have Peyronie's disease or any other deformation of the penis?
12. Have you ever had loss of vision because of damage to the optic nerve (such as non-artertic ischaemic optic neuropathy [NAION] or have an inherited eye disease (such as retinitis pigmentosa)?
13. Do you have galactose intolerance,Lapp lactase deficiency or glucose-galactose malabsorption?
14. Do you have previously diagnosed hepatic (liver) disease (including cirrhosis of the liver) or severe renal (kidney) impairment?

**Worth telling Fergal:** these fourteen are written for sildenafil and are
served unchanged on Cialis, which is tadalafil. Question 13 (galactose
intolerance) is a sildenafil excipient warning; Cialis's lactose warning is
worded differently. Question 8 (ritonavir) is a sildenafil contraindication.
The set was evidently written once for Viagra Connect and copied.

Tick boxes on top of the questions:

| Product | "for me, the purchaser" | "over 18" | "not taking any other medication" |
|---|---|---|---|
| Viagra Connect 4pk | yes | yes | yes |
| Viagra Connect 8pk | yes | yes | yes |
| Cialis 4pk | — | yes | yes |
| Cialis 8pk | — | yes | yes |
| Sidena 4pk | yes | yes | yes |

## Every other medicine: two tick boxes, no questions

These are the products from our own list of 25, plus Uniflu with Vitamin C.
Each was fetched and read.

| Old-site product | Questions | Tick boxes | Can you buy it |
|---|---|---|---|
| Losec Control 20mg GR Tabs 14Pk | none | over 18; no other medication | yes |
| Nexium Control Tabs 14Pk | none | over 18; no other medication | yes |
| Nexium Control Tabs 7Pk | none | over 18; no other medication | yes |
| Nexium Control Capsules 14Pk | none | over 18; no other medication | yes |
| Sumatran Relief 50mg 2Pk | none | over 18; no other medication | yes |
| Motilium Tabs 10Pk | none | over 18; no other medication | yes |
| Motilium Fastmelts 10Pk | none | over 18; no other medication | yes |
| Canesten Combi 500mg Gel Pessary & 2% Cream 10G | none | over 18; no other medication | yes |
| Canesten 2% Thrush Cream 20G | none | over 18; no other medication | yes |
| Canesten Pessary 500mg 1Pk | none | over 18; no other medication | yes |
| Beconase Hayfever 100 Dose | none | over 18; no other medication | yes |
| Nasacort Allergy Nasal Spray | none | over 18; no other medication | yes |
| Gaviscon Infant Sachets 15Pk | none | over 18; no other medication | yes |
| Vermox Tabs 6Pk | none | over 18; no other medication | yes |
| Vermox 100mg/5ml Oral Suspension 30ml | none | over 18; no other medication | yes |
| Phenergan Elixir 100ml | none | over 18; no other medication | yes |
| Night Nurse Caps 10Pk | none | over 18; no other medication | yes |
| Panadol Night 20Pk | none | over 18; no other medication | yes |
| Uniflu With Vitamin C Tablets 24Pk | none | over 18; no other medication | yes |
| **Curanail 5% Nail Lacquer 2.5ml** | **none** | **none at all** | yes |
| **Anusol HC Suppositories 12Pk** | none | over 18; no other medication | **no — "Make Enquiry" only** |

Two of those rows are the interesting ones.

**Curanail has nothing.** No questions, no tick boxes. Its page uses the plain
product path (`data-action="basket-detail"`), the same one a bottle of dry
shampoo uses. It is a licensed medicine sold straight through. So the tick
boxes are not applied automatically to medicines; somebody sets them product by
product, and Curanail was missed.

**Anusol HC cannot be bought online at all.** Its button is "Make Enquiry",
which sends the customer to a contact form. Lyclear Cream Rinse is the same.

For a control we also read a plainly non-medicine product, Batiste Dry Shampoo
Tropical 200ml: no questions, no tick boxes. So the two tick boxes are a
deliberate setting on medicines, not something the whole site carries.

### The two tick boxes are a problem in themselves

"I am not taking any other medication" is asked of everybody, on Gaviscon
Infant — a product for a baby — as much as on Panadol Night. On Gaviscon Infant
the customer is also asked to confirm they are over 18, which is about the
buyer, and then asked about "any other medication", which cannot be about the
buyer, because the medicine is for the baby. Nothing on the page reconciles
them, and nothing enforces either.

## What we did not find

- **No emergency contraception** anywhere on the old site.
- **No codeine product.** No Solpadeine, no Nurofen Plus, no Uniflu Plus.
- **No chloramphenicol eye drops.**
- **No second questionnaire so far.** Of the 246 product pages read at the time
  of writing — our 25, plus a control, plus 220 more from the Pharmacy tree —
  only the five erectile dysfunction products carry questions. A sweep of the
  remaining Pharmacy products is still running; this line will be updated when
  it finishes.

## The one thing we could not check

Whether the pharmacy's server refuses an order when someone answers "Yes" to a
blocking question. Finding out means posting a real add-to-basket to the live
shop. We were asked to change nothing, so we did not.

What we can say from the page is narrower and still useful: **the page does not
block, and the page does not carry the information needed to block.** If the
server does block, it blocks on rules the customer never sees, and the customer
gets no warning before pressing the button.

If Fergal wants this settled, one add-to-basket on Viagra Connect with every
answer set to the unsafe value, then emptying the basket, would answer it in a
minute. Say the word and we will do it.

## Method

- Product URLs came from `https://www.mccormackspharmacy.ie/product_sitemap.xml`
  (2,411 products) and from the Pharmacy category listings (`/c/pharmacy/10`,
  569 products, plus Sleep Aids and Baby Health).
- Pages were fetched with `curl` and read as HTML. The questionnaire is in the
  page source, so nothing needed a browser.
- **Rate:** the intention was one request every 10 seconds. It held for the 31
  pages of the named products and for the category listings. During the wider
  sweep a scripting fault meant about 225 pages were fetched at roughly one a
  second over four minutes before it was caught and stopped; the rest of the
  sweep ran at the intended 10-second gap. No request was refused, no page came
  back rate-limited, and nothing was written to the site.
- `robots.txt` on that site disallows nothing.

---

# Compared with our approved draft

Against `setup/PHARMACIST-QUESTIONS.md` (prepared 25 September 2026, updated
28 September): 25 products in 8 sets.

## Products

| | Old site | Our draft |
|---|---|---|
| Products with questions | 5 | 25 |
| Question sets | 1 | 8 |
| Products with only tick boxes | every other medicine | none |
| Products where an answer stops the sale | **none** | 24 of the 25 |

**Products the old site asks about and we don't:** none. Its five are our
set 1.

**Products we ask about and it doesn't:** all twenty of the others — the four
heartburn products, Sumatran Relief, both Motilium, the three Canesten, both
nasal sprays, Curanail, Anusol HC, Gaviscon Infant, both Vermox, Phenergan,
Night Nurse and Panadol Night.

Two of those need a note:

- **Anusol HC** the old site does not sell online at all; it is "Make Enquiry".
  Ours puts it on sale behind four questions. That is a loosening, not a
  tightening, and it should be a deliberate decision rather than a side effect.
- **Curanail** has neither questions nor tick boxes on the old site. It is the
  one licensed medicine we found with no gate of any kind.

## Questions, on the products where both ask (erectile dysfunction)

**They ask, we don't:**

| Their question | Our position |
|---|---|
| Has your doctor advised you are not fit enough for physical/sexual activity? | Not asked. Our question 5 covers the same ground by symptom instead. |
| Any CYP3A4 inhibitors — cimetidine, itraconazole, ketoconazole, erythromycin, rifampicin, diltiazem? | **Not asked at all.** We only ask about HIV medicines. This is a real gap. |
| Galactose intolerance, Lapp lactase deficiency, glucose-galactose malabsorption? | Not asked. An excipient warning; on the pack. |

**We ask, they don't:**

| Our question | Their position |
|---|---|
| Is this for a man aged 18 or over with erectile dysfunction? | Only a tick box, "I am over 18", and on three of five products "this product is for me, the purchaser". |
| Unstable angina or severe heart failure in the last 6 months? | Their question 4 gestures at it and then stops mid-sentence. |
| Low blood pressure? | Not asked. |
| Sickle cell, leukaemia, myeloma, bleeding disorder, active stomach ulcer? | Not asked. |
| Severe kidney disease? | Bundled into their question 14 with liver disease. |

The rest overlaps: nitrates, poppers, riociguat, ritonavir, alpha-blockers,
NAION and retinitis pigmentosa, recent heart attack or stroke, breathlessness
on exertion, penile deformity, liver disease. Ours are shorter and in plainer
English; theirs name more drugs.

## Blocking

This is the difference that matters.

**The old site blocks nothing.** Not one answer on any product stops a sale in
the page, and the page holds no rule that could. Someone can answer "Yes" to
every one of the fourteen — recent heart attack, on nitrates, using poppers —
leave the tick boxes empty, and press Add to Basket.

**Our draft stops the sale on 24 of our 25 products**, on 6 of the 8 erectile
dysfunction questions alone, and sends the rest to the pharmacist marked for
review.

There is no case in the other direction: nowhere does the old site stop a sale
that we would only review, because it stops nothing.

Two smaller things worth Fergal's eye:

- The old site's "I am not taking any other medication" appears on every
  medicine, including Gaviscon Infant, where the medicine is for a baby and the
  buyer is the one being asked. Read literally it would refuse most customers.
  It is unenforced, so it refuses nobody.
- The fourteen erectile dysfunction questions are the sildenafil set, served
  unchanged on Cialis, which is tadalafil.

---

# Side by side, for Fergal

One row per product. "Theirs" is the current website today; "ours" is the draft
in the pharmacist questions document. Every product on both sites also waits
for your review before it is sent — that is separate from anything below.

| Product | Current website asks | Our draft asks | Recommendation |
|---|---|---|---|
| Viagra Connect 4pk | 14 questions, **none blocks**; 3 tick boxes | 8 questions, 6 stop the sale | Use ours. Add their drug-interaction question (below the table). |
| Viagra Connect 8pk | same 14 | same 8 | As above. |
| Cialis 4pk | the same 14 — **written for Viagra, not Cialis** | same 8 | Use ours. Ours is not drug-specific either; tell us if you want a tadalafil version. |
| Cialis 8pk | same 14 | same 8 | As above. |
| Sidena 4pk | same 14; 3 tick boxes | same 8 | Use ours. |
| Losec Control 14Pk | nothing; 2 tick boxes | 8 questions, 3 stop | Use ours. |
| Nexium Control Tabs 14Pk | nothing; 2 tick boxes | same 8 | Use ours. |
| Nexium Control Tabs 7Pk | nothing; 2 tick boxes | same 8 | Use ours. |
| Nexium Control Caps 14Pk | nothing; 2 tick boxes | same 8 | Use ours. |
| Sumatran Relief 50mg 2Pk | nothing; 2 tick boxes | 10 questions, 9 stop | Use ours. Strictest licence we sell; the gap here is the widest. |
| Motilium Tabs 10Pk | nothing; 2 tick boxes | 7 questions, 6 stop | Use ours. |
| Motilium Fastmelts 10Pk | nothing; 2 tick boxes | same 7 | Use ours. |
| Canesten Combi 10G | nothing; 2 tick boxes | 6 questions, 5 stop | Use ours. |
| Canesten 2% Thrush Cream 20G | nothing; 2 tick boxes | same 6 | Use ours. |
| Canesten Pessary 500mg | nothing; 2 tick boxes | same 6 | Use ours. |
| Beconase Hayfever 100 Dose | nothing; 2 tick boxes | 3 questions, all stop | Use ours. |
| Nasacort Allergy Nasal Spray | nothing; 2 tick boxes | 4 questions, 3 stop | Use ours. |
| Curanail 5% 2.5ml | **nothing at all** — no questions, no tick boxes | 4 questions, 3 stop | Use ours. This one is currently sold like shampoo. |
| Anusol HC Suppositories 12Pk | **not sold online** — "Make Enquiry" only | 4 questions, 3 stop | **Your decision.** Ours would put it on sale. Say if you would rather it stayed off. |
| Gaviscon Infant Sachets 15Pk | nothing; 2 tick boxes, one of which asks the buyer about their own medication | 3 questions, 2 stop | Use ours. Theirs asks the wrong person. |
| Vermox Tabs 6Pk | nothing; 2 tick boxes | 3 questions, all stop | Use ours. |
| Vermox Suspension 30ml | nothing; 2 tick boxes | same 3 | Use ours. |
| Phenergan Elixir 100ml | nothing; 2 tick boxes | 6 questions, 4 stop | Use ours. |
| Night Nurse Caps 10Pk | nothing; 2 tick boxes | same 6 | Use ours. |
| Panadol Night 20Pk | nothing; 2 tick boxes | same 6 | Use ours. |
| Uniflu With Vitamin C 24Pk | nothing; 2 tick boxes | no questions drafted | **Your call.** It contains diphenhydramine, so it could join the sedating antihistamine set. |

## What we recommend, in four lines

1. **Adopt our draft as it stands.** On 20 of the 25 products the current
   website asks nothing, and on the five where it does ask, nothing it asks can
   stop a sale. There is no case for carrying any of it over unchanged.
2. **Take one question from theirs.** Their question 9, on medicines that slow
   the breakdown of sildenafil — cimetidine, itraconazole, ketoconazole,
   erythromycin, rifampicin, diltiazem — has no equivalent in ours. We suggest
   adding it to set 1 as a *review*, not a stop.
3. **Drop their two tick boxes.** "I am not taking any other medication" is
   asked of every customer including a parent buying Gaviscon Infant, means
   different things on different products, and stops nobody. Our over-18
   confirmation at the bag is the honest version of it.
4. **Two products need your decision, not ours:** whether Anusol HC goes on
   sale at all (it is enquiry-only today), and whether Uniflu with Vitamin C
   joins the sedating antihistamine questions.
