"""Fergal's questionnaire PDF: one page per set, from the theme snippet and the plan CSV.

  python3 setup/build_question_sets_pdf.py ~/Downloads/questionnaires-for-fergal.pdf

Needs reportlab. LIVE is the date on every page; change it before re-sending.
"""
import re, json, csv, sys
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, KeepTogether
from xml.sax.saxutils import escape as e

LIVE = "Thursday 8 October 2026"
snip = open("shopify-theme/snippets/pharmacy-question-set.liquid").read()
sets = dict(re.findall(r"when '([^']+)' -%\}\n(.*?)\n", snip))
plan = {}
for r in csv.DictReader(open("setup/questionnaire-sets-plan-2026-10-01.csv")):
    plan.setdefault(r["set"], []).append(r["title"] + (" (draft, not on sale)" if r["status"] == "DRAFT" else ""))
ed_products = ["Viagra Connect 50mg Tablets 4 Pack", "Viagra Connect 50mg Tablets 8 Pack", "Cialis For Men Tadalafil Tablets 4Pk", "Cialis For Men Tadalafil Tablets 8Pk", "Sidena 50mg Tablets 4 Pack"]

KIND = {"yes_no": "Yes / No", "confirm": "Tick to confirm (required)", "yes_no_details": "Yes / No, Yes asks for detail",
        "choice": "Pick one", "multi": "Tick all that apply"}
ss = getSampleStyleSheet()
GREEN = colors.HexColor("#4a7a0c")
st = {
 "banner": ParagraphStyle("b", parent=ss["Normal"], fontName="Helvetica-Bold", fontSize=10.5, textColor=colors.white, leading=14),
 "h1": ParagraphStyle("h1", parent=ss["Heading1"], fontSize=18, spaceAfter=2, textColor=GREEN),
 "sub": ParagraphStyle("s", parent=ss["Normal"], fontSize=9.5, textColor=colors.HexColor("#555555"), spaceAfter=8, leading=13),
 "h2": ParagraphStyle("h2", parent=ss["Heading3"], fontSize=11.5, spaceBefore=8, spaceAfter=4),
 "p": ParagraphStyle("p", parent=ss["Normal"], fontSize=9.5, leading=13),
 "q": ParagraphStyle("q", parent=ss["Normal"], fontSize=9.5, leading=12.5),
 "small": ParagraphStyle("sm", parent=ss["Normal"], fontSize=8.5, leading=11),
}

def banner(text, bg=GREEN):
    t = Table([[Paragraph(e(text), st["banner"])]], colWidths=[180*mm])
    t.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), bg), ("LEFTPADDING", (0,0), (-1,-1), 8),
                           ("TOPPADDING", (0,0), (-1,-1), 6), ("BOTTOMPADDING", (0,0), (-1,-1), 6)]))
    return t

def questions(name, qs=None):
    qs = qs or st["q"]
    rows = [["", Paragraph("<b>Question</b>", qs), Paragraph("<b>Answer</b>", qs)]]
    for i, item in enumerate(sets[name].split("||"), 1):
        parts = item.split("::")
        kind, label = parts[0], parts[1]
        ans = KIND[kind] + (": " + ", ".join(parts[2].split("|")) if len(parts) > 2 else "")
        rows.append([str(i), Paragraph(e(label), qs), Paragraph(e(ans), qs)])
    t = Table(rows, colWidths=[7*mm, 120*mm, 53*mm], repeatRows=1)
    t.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("FONTSIZE", (0,0), (-1,-1), 9),
        ("LINEBELOW", (0,0), (-1,-1), 0.4, colors.HexColor("#dddddd")), ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#eef4e4")),
        ("TOPPADDING", (0,0), (-1,-1), 3), ("BOTTOMPADDING", (0,0), (-1,-1), 3)]))
    return t

def products(names):
    if not names:
        return Paragraph("<i>None. No product on the website is in this set at the moment.</i>", st["p"])
    style = st["small"] if len(names) > 20 else st["q"]
    names = sorted(names)
    half = (len(names) + 1) // 2 if len(names) > 8 else len(names)
    cols = [names[:half], names[half:]] if len(names) > 8 else [names, []]
    rows = [[Paragraph(e(a), style), Paragraph(e(b), style) if b else ""] for a, b in
            zip(cols[0], cols[1] + [""] * (len(cols[0]) - len(cols[1])))]
    t = Table(rows, colWidths=[90*mm, 90*mm])
    t.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("TOPPADDING", (0,0), (-1,-1), 1), ("BOTTOMPADDING", (0,0), (-1,-1), 1)]))
    return t

PAGES = [
 ("painkillers", "Painkillers: paracetamol, ibuprofen, aspirin and combinations", "New. Not in the 25 September draft.",
  "A short declaration rather than screening questions. The age bands tell you when an adult is buying a children's product, "
  "or an adult product for a child. Cold & flu combinations and gels are <b>not</b> included: see the last page."),
 ("ppi", "Heartburn: proton pump inhibitors", "Draft set 3, 25 September.", ""),
 ("sumatriptan", "Migraine: sumatriptan", "Draft set 4, 25 September.",
  "The licence asks for a heart-risk assessment by a doctor or pharmacist. These questions do not replace it; your review of the order is where it happens. "
  "Draft question 8 asked two things, so it is two questions here (8 and 9)."),
 ("domperidone", "Domperidone", "Draft set 5, 25 September.", ""),
 ("thrush", "Vaginal thrush", "Draft set 6, 25 September.", "Canesten 1% Cream (a general antifungal) is not included, as in the draft."),
 ("nasal-steroid", "Steroid nasal sprays", "Draft set 7, 25 September.",
  "The draft asked about glaucoma or cataracts for Nasacort only. The website asks it of both products, so one set covers them."),
 ("curanail", "Curanail", "Draft set 7, 25 September.",
  "<b>This reverses your 30 September choice.</b> Curanail asks nothing today, because the old website asked nothing. "
  "If you want to keep it that way, say so and it stays as it is."),
 ("anusol-hc", "Anusol HC suppositories", "Draft set 7, 25 September.",
  "Only the hydrocortisone pack. Anusol Supp 12Pk, Anusol Suppositories 24Pk, Anusol Cream and Anusol Wipes are not included: please tell us if any of them is a hydrocortisone product."),
 ("gaviscon-infant", "Gaviscon Infant", "Draft set 7, 25 September.", ""),
 ("vermox", "Vermox (mebendazole)", "Draft set 7, 25 September.", ""),
 ("sedating-antihistamine", "Sedating antihistamines", "Draft set 8, 25 September.",
  "Panadol Night contains paracetamol but gets this set, not the painkillers one: each product has one set. "
  "Draft question 1 named only Phenergan's age; it now points to the leaflet for the others. "
  "Night Nurse Liquid 160ml is not included (the draft asked whether it should be)."),
 ("codeine", "Codeine", "Draft set 2, 25 September.",
  "Built and ready, but on no product: nothing on the website contains codeine as far as we can tell. "
  "If you list any codeine medicine, it gets these questions the moment it is tagged. Draft questions 1 and 7 are adapted: "
  "age is a pick-one, and question 7 is split in two (7 and 8)."),
]

story = []
story += [Paragraph("Questions before purchase: beyond erectile dysfunction", st["h1"]),
          Paragraph("For Fergal, McCormacks Pharmacy. Prepared 1 October 2026 by Kakion.", st["sub"]),
          banner(f"Going live on {LIVE} unless you object"), Spacer(1, 10)]
story.append(Paragraph(
 "On 1 October you decided that only the five erectile dysfunction products ask questions. This pack proposes questions for "
 f"<b>{sum(len(v) for v in plan.values())} more products in {len([p for p in PAGES if plan.get(p[0])])} sets</b>, "
 "mostly from the draft we sent on 25 September, plus a new painkiller declaration. One page per set follows: the questions, "
 "word for word as the customer sees them, and the products that get them.", st["p"]))
story.append(Spacer(1, 6))
story.append(Paragraph("<b>How it works, as for the ED products today</b>", st["h2"]))
for b in [
 "The customer answers on the product page before the medicine goes in the bag. Every question must be answered.",
 "<b>No answer stops a sale.</b> The draft's \"stop\" answers are not built, as you decided on 30 September. "
 "You see every answer on the order, under the product, and decide.",
 "Every medicine order is still held for your review after payment, and the bag still asks for the over-18 tick. Nothing about the hold changes.",
 "Every other medicine keeps an ordinary Add to bag with no questions.",
]:
    story.append(Paragraph("• " + b, st["p"]))
story.append(Spacer(1, 6))
story.append(Paragraph("<b>What we need from you</b>", st["h2"]))
story.append(Paragraph(f"Nothing, if you are happy. Otherwise, before {LIVE}: cross out a question, reword it, or move a product in or out of a set. "
                       "A reply by email is enough.", st["p"]))
story.append(Spacer(1, 6))
rows = [["Set", "Products", "Questions"]] + [[t, str(len(plan.get(n, []))), str(len(sets[n].split("||")))] for n, t, *_ in PAGES]
t = Table(rows, colWidths=[120*mm, 25*mm, 25*mm])
t.setStyle(TableStyle([("FONTSIZE", (0,0), (-1,-1), 9), ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ("LINEBELOW", (0,0), (-1,-1), 0.4, colors.HexColor("#dddddd")), ("ALIGN", (1,0), (-1,-1), "RIGHT")]))
story += [t, PageBreak()]

for name, title, src, note in PAGES:
    story += [banner(f"Going live on {LIVE} unless you object"), Spacer(1, 8),
              Paragraph(e(title), st["h1"]), Paragraph(e(src) + " No answer stops the sale; every question is required.", st["sub"]),
              Paragraph(f"Questions ({len(sets[name].split('||'))})", st["h2"]), questions(name),
              Paragraph(f"Products ({len(plan.get(name, []))})", st["h2"]), products(plan.get(name, []))]
    if note:
        story += [Spacer(1, 6), Paragraph("<b>Note.</b> " + note, st["p"])]
    story.append(PageBreak())

story += [banner("Already live since 30 September 2026: for reference, no change", colors.HexColor("#666666")), Spacer(1, 8),
          Paragraph("Erectile dysfunction", st["h1"]),
          Paragraph("Draft set 1, merged with the old website's questions on your instruction of 30 September.", st["sub"]),
          Paragraph(f"Questions ({len(sets['ed'].split('||'))})", st["h2"]), questions("ed", st["small"]),
          Paragraph("Products (5)", st["h2"]), products(ed_products), PageBreak()]

story += [Paragraph("Not included: tell us if any should be", st["h1"]),
          Paragraph("These are medicines near a set that we left out. They keep an ordinary Add to bag.", st["sub"])]
for head, items in [
 ("Cold & flu combinations containing paracetamol or ibuprofen (19)", "Advil Cold & Flu; Benylin 4 Flu; Benylin Day & Night; Ilvico; Lemsip Headcold, Max Cold & Flu, Max Cough Cold, Max Sinus & Flu, Max Strength, Original; Night Nurse Caps (in the sedating set) and Liquid; Nurofen Cold & Flu (two listings); Nurofen Sinus & Pain; Panadol C&F Relief; Sinutab N/D; Sudaplus N/D; Uniflu With Vitamin C. Most also contain pseudoephedrine, which the 25 September draft suggested handling without questions."),
 ("Topical anti-inflammatories (9)", "Voltarol gels (6), Diclac 1% gels (2), Nurofen Durance plasters."),
 ("Other pain products (3)", "Strepsils Intensive (flurbiprofen lozenge), Bonjela Gel (choline salicylate), Sumatran Relief (has its own migraine set)."),
 ("Related products not in the draft's lists", "Night Nurse Liquid 160ml; Anusol Supp 12Pk, Anusol Suppositories 24Pk, Anusol Cream 23g, Anusol Soothing Wipes; Canesten 1% Cream 20g and 50g; Uniflu Immune Defence and Uniflu Cough Stop (not tagged as medicines)."),
]:
    story += [Paragraph(e(head), st["h2"]), Paragraph(e(items), st["p"])]

def foot(c, d):
    c.saveState(); c.setFont("Helvetica", 7.5); c.setFillColor(colors.HexColor("#888888"))
    c.drawString(15*mm, 10*mm, "McCormacks Pharmacy: questions before purchase. Prepared by Kakion, 1 Oct 2026.")
    c.drawRightString(195*mm, 10*mm, f"Page {d.page}"); c.restoreState()
SimpleDocTemplate(sys.argv[1], pagesize=A4, leftMargin=15*mm, rightMargin=15*mm, topMargin=14*mm, bottomMargin=16*mm,
                  title="Questions before purchase: for Fergal", author="Kakion").build(story, onFirstPage=foot, onLaterPages=foot)
