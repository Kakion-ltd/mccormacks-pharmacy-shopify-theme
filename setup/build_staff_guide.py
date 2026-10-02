"""Builds the staff guide "Managing products" in the retired Adding Products guide's
style: A4 landscape, one step per page, picture on the left, steps on the right.

    python3 setup/build_staff_guide.py <outdir>

Writes <outdir>/5-Staff-Guide-Managing-Products.pdf. Storefront screenshots are in
setup/staff-guide/ (re-take with setup/staff-guide/shoot.py). Admin screenshots are
not in it yet: nobody could log in to admin.shopify.com when it was written, so each
is a dashed box saying what to capture and where the arrow goes. To fill one, save
the capture as setup/staff-guide/<name>.png with the arrow drawn on and rebuild; a
box whose file exists is replaced by the picture.
"""
import base64, datetime, html, os, sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(HERE, "staff-guide")
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
LOGO = os.path.join(HERE, "..", "shopify-theme", "assets", "mccormacks-logo.png")
b64 = lambda f: base64.b64encode(open(f, "rb").read()).decode()
logo = "data:image/png;base64," + b64(LOGO)
today = datetime.date.today()
DATE = f"{today.day} {today:%B %Y}"
RUNNING = "Managing products on the website"

def shot(name, caption):
    """A real screenshot from setup/staff-guide/."""
    return (f'<figure><img src="data:image/png;base64,{b64(os.path.join(SHOTS, name + ".png"))}">'
            f'<figcaption>{caption}</figcaption></figure>')

def admin(name, where, arrow):
    """An admin screenshot: the picture if it has been taken, else a marked box."""
    if os.path.exists(os.path.join(SHOTS, name + ".png")):
        return shot(name, where)
    return (f'<div class="todo"><div class="todo-label">Screenshot to add</div>'
            f'<p><b>Where:</b> {where}</p><p><b>Arrow on:</b> {arrow}</p>'
            f'<p class="todo-file">setup/staff-guide/{name}.png</p></div>')

def card(title, inner):
    return f'<div class="card"><div class="kicker">Reference</div><h3>{title}</h3>{inner}</div>'

def tag(t):
    return f'<code>{t}</code>'

PR = tag("pharmacist-review")

STEPS = [
# ---------------------------------------------------------------- intro
("Before you start", card("What this guide covers", """
<table><tr><th>Section</th><th>What you will change</th></tr>
<tr><td>1. Stock levels</td><td>The quantity on one product, or many at once</td></tr>
<tr><td>2. VAT</td><td>Which rate a product is charged at</td></tr>
<tr><td>3. The pharmacist-review tag</td><td>Whether a pharmacist checks the order</td></tr>
<tr><td>4. Questionnaires</td><td>Which products ask the customer questions</td></tr></table>"""), """
<p>This guide is for staff looking after products that are already on the McCormack's website.
It does not cover adding new products: send those on the product upload sheet as usual.</p>
<ol><li>Sign in at <b>admin.shopify.com</b>.</li>
<li>Click <b>Products</b> in the menu on the left.</li>
<li>Search for the product and click its name to open it.</li></ol>
<p>Every change in this guide is made on that product page, and nothing changes on the website
until you click <b>Save</b>.</p>
<div class="note">Not sure? Leave it as it is and ask. A change that waits a day costs nothing.
A wrong VAT rate or a missing pharmacist check costs a lot more.</div>"""),

# ---------------------------------------------------------------- stock
("Stock: changing the quantity on one product",
 admin("stock-one", "A product page, scrolled to the <b>Inventory</b> box.",
       "the quantity box beside the shop location."), """
<ol><li>Open the product.</li>
<li>Scroll down to the <b>Inventory</b> box.</li>
<li>Click the number in the box beside the shop location and type how many you have.
Type the real count, not a guess.</li>
<li>Click <b>Save</b> at the top of the page.</li></ol>
<p>The website picks up the new number straight away.</p>
<div class="note"><b>The website does not talk to the till.</b> Selling something in the shop does not
lower the number on the website, and a delivery does not raise it. Each number is only as good as
the last time someone typed it in here.</div>"""),

("Stock: changing several products at once",
 admin("stock-bulk", "<b>Products</b> list with three products ticked, then the bulk editor that opens.",
       "the <b>Bulk edit</b> button, and the quantity column in the editor."), """
<ol><li>Click <b>Products</b>.</li>
<li>Tick the box beside each product you want to change. Searching first (for example the brand
name) makes this quicker.</li>
<li>Click <b>Bulk edit</b> at the top of the list. A spreadsheet-style page opens with one row
per product.</li>
<li>Find the quantity column. If it is not there, click <b>Columns</b> and add it.</li>
<li>Click each quantity and type the new number.</li>
<li>Click <b>Save</b>.</li></ol>
<div class="note">Check the product name on each row before you type. The rows look alike, and a
number typed on the wrong row is easy to miss.</div>"""),

("Stock: Track quantity must stay on",
 admin("stock-track", "A product page, <b>Inventory</b> box.",
       "the <b>Inventory tracked</b> (Track quantity) switch, which must show as on."), """
<p><b>Track quantity</b> (shown as <b>Inventory tracked</b> on some screens) tells the website to
keep count of the product. It is on for every product and must stay on.</p>
<ul><li><b>On:</b> the website uses the number you type, and shows <b>Out of stock</b> when a
product has run out.</li>
<li><b>Off:</b> the website ignores the number and treats the product as always available, even
when the shelf is empty.</li></ul>
<p>If you find it switched off on a product, do not switch it on yourself: switching it on with a
wrong count can take the product off sale. Tell Keelan which product it is.</p>
<div class="note">Leave the box <b>Sell when out of stock</b> (or "Continue selling") as you find it.
Keelan decides that setting; see the next page.</div>"""),

("Stock: what happens at zero",
 shot("oos", "From the website: a product at zero shows Out of stock and cannot be added to the bag."), """
<p>When a product's count is 0, it <b>stays on the website</b> and shows <b>Out of stock</b>. It does not
disappear. Customers can still find it, and the Add to bag button is greyed out.</p>
<p>To put it back on sale, type the real count (page 2). It goes back on sale as soon as you
click Save.</p>
<p><b>One exception.</b> Most products that were in stock when the website launched have
<b>Sell when out of stock</b> ticked, because the counts brought over from the old system were
not real counts. Those products <b>keep selling at zero</b> and the count goes below 0. This
is deliberate for now.</p>
<div class="note">So a product can be on sale with nothing on the shelf. If one is ordered that you
do not have, tell the customer straight away. Keelan will turn this off once the counts are
real.</div>"""),

# ---------------------------------------------------------------- VAT
("VAT: how the rate is decided", card("Irish VAT on pharmacy lines", """
<table><tr><th>Rate</th><th>Applies to</th></tr>
<tr><td>0%</td><td>Some oral medicines (zero rated)</td></tr>
<tr><td>13.5%</td><td>Some other lines</td></tr>
<tr><td>23%</td><td>Everything else</td></tr></table>
<p class="caption">Which rate applies to a product is a question for your accountant, not for this
guide.</p>"""), """
<p>Shopify has no box on a product where you type a VAT rate. The rate comes from three places:</p>
<ol><li><b>Charge tax</b>, a tick box on the product. Ticked means VAT is charged.</li>
<li><b>Category</b>, on the product. Shopify uses it to pick the standard rate for that kind of
product.</li>
<li><b>Rate exceptions</b> ("overrides"), set once in Settings for a group of products. These
win over the category.</li></ol>
<p>Prices on the website include VAT. Changing the rate does not change what the customer pays;
it changes how much of that price is VAT.</p>
<div class="note"><b>If you are not sure which rate applies, ask your accountant. Do not guess.</b>
The website charges whatever is set, and every order is recorded at that rate.</div>"""),

("VAT: where the setting is on a product",
 admin("vat-product", "A product page: the <b>Price</b> box and the <b>Product organization</b> box.",
       "the <b>Charge tax on this product</b> tick box, and the <b>Category</b> field."), """
<ol><li>Open the product.</li>
<li>In the <b>Price</b> box, check that <b>Charge tax on this product</b> is ticked. It should be
ticked on every product.</li>
<li>In the <b>Product organization</b> box, the <b>Category</b> shows what kind of product
Shopify thinks it is.</li></ol>
<p>Do not untick <b>Charge tax</b> to make a product zero rated, and do not change the
<b>Category</b> to change the rate. Both change how the sale is recorded for VAT, and your
accountant may want zero-rated items recorded a particular way. Use a rate exception
(next page), and only once your accountant has said which rate.</p>"""),

("VAT: setting a rate for several products at once",
 admin("vat-override", "<b>Settings</b> &rarr; <b>Taxes and duties</b> &rarr; <b>Ireland</b>, the overrides section.",
       "the button to add a product override, and the collection and rate it asks for."), """
<p>A rate exception applies one rate to every product in a <b>collection</b> (a group of products).
That is how you set the rate for several products at once.</p>
<ol><li>Click <b>Settings</b>, bottom left.</li>
<li>Click <b>Taxes and duties</b>, then <b>Ireland</b> (under European Union).</li>
<li>In the overrides section, add a <b>product override</b>.</li>
<li>Choose the collection, type the rate your accountant gave you, and click <b>Save</b>.</li></ol>
<p>Every product in that collection is now charged at that rate.</p>
<div class="note">The rates for medicines are being set up with your accountant now. Before you add
an exception of your own, check with Kakion, so two different rates are not set for the same
products.</div>"""),

("VAT: putting one product into a rate group",
 admin("vat-collection", "A product page, <b>Product organization</b> box.",
       "the <b>Collections</b> field."), """
<p>Once a rate exception exists for a collection, a product takes that rate by being in the
collection.</p>
<ol><li>Open the product.</li>
<li>In the <b>Product organization</b> box, click <b>Collections</b>.</li>
<li>Choose the collection that carries the rate. To take a product out, click the &times; beside
the collection.</li>
<li>Click <b>Save</b>.</li></ol>
<p>Only manual collections can be chosen here. If the collection you want is not in the list,
ask Kakion rather than making a new one.</p>
<div class="note">Same rule as before: if you are not sure which rate a product should have, ask
your accountant first.</div>"""),

# ---------------------------------------------------------------- pharmacist-review
("The pharmacist-review tag: what it does",
 shot("grid", "From the website: the medicine (centre) shows View Product; the hot pack beside it can be added in one click.")
 + shot("med", "On the medicine's own page: the Ask a pharmacist line, and a questionnaire button where the product has one."), f"""
<p>The tag {PR} tells the website a product is a medicine. A product with the tag:</p>
<ul><li><b>Cannot be added to the bag from a list or search.</b> The button says
<b>View Product</b>, so the customer has to open the product page first.</li>
<li><b>Shows the pharmacy lines</b> on its page: "Dispatched from our PSI-registered Irish pharmacy"
and "Ask a pharmacist before you buy".</li>
<li><b>Asks for the over-18 tick</b> on the bag page.</li>
<li><b>Holds the order for a pharmacist.</b> The order cannot be sent until a pharmacist has
checked it and approved it.</li></ul>
<p class="caption">Every product in Medicines &amp; Health shows the pharmacy lines, tag or not, so
seeing them is not proof the tag is there. Check the Tags box.</p>"""),

("The pharmacist-review tag: is it a medicine?", card("Look on the pack for a licence number", """
<table><tr><th>On the pack</th><th>Medicine?</th></tr>
<tr><td>PA or PPA, then numbers</td><td>Yes</td></tr>
<tr><td>TR, then numbers (herbal medicines)</td><td>Yes</td></tr>
<tr><td>EU/1/, then numbers</td><td>Yes</td></tr>
<tr><td>VPA, then numbers (pet medicines)</td><td>Yes</td></tr>
<tr><td>CE mark only</td><td>No</td></tr>
<tr><td>Not sure</td><td>Ask the pharmacist</td></tr></table>"""), """
<p>A product is a medicine if its pack carries a licence number starting <b>PA</b>, <b>PPA</b>,
<b>TR</b>, <b>EU/1/</b> or <b>VPA</b>. It is a medicine even if it looks like a toiletry.</p>
<ul><li><b>Medicines:</b> Sudocrem, medicated corn plasters, painkillers, cold and flu
remedies.</li>
<li><b>Not medicines:</b> ordinary plasters, bandages, test kits, throat sweets.</li></ul>
<p>Every medicine needs the {PR} tag. Anything else should not have it.</p>""".replace("{PR}", PR)),

("The pharmacist-review tag: adding it",
 admin("tag-add", "A product page, <b>Product organization</b> box, with the Tags field open.",
       f"the <b>Tags</b> field, with {PR} typed in."), f"""
<ol><li>Open the product.</li>
<li>In the <b>Product organization</b> box, click <b>Tags</b>.</li>
<li>Type {PR} exactly: <b>all lower case</b>, with the hyphen, no spaces. Press <b>Enter</b>.</li>
<li>Click <b>Save</b>.</li></ol>
<p>Type it, do not copy it from somewhere else: a copied tag can carry a hidden space. Any other
spelling, such as <code>Pharmacist-Review</code> or <code>pharmacist review</code>, is not
recognised by the order hold, and the order goes out with no pharmacist check.</p>
<div class="note">To check, open the product on the website and look at a list it appears in: the
button should say <b>View Product</b>, not Add to bag.</div>"""),

("The pharmacist-review tag: removing it",
 admin("tag-remove", "A product page, <b>Tags</b> field.",
       f"the small &times; on the {PR} tag."), f"""
<ol><li>Open the product.</li>
<li>In the <b>Tags</b> field, click the &times; on {PR}. Leave every other tag alone.</li>
<li>Click <b>Save</b>.</li></ol>
<table><tr><th>If you</th><th>What happens</th></tr>
<tr><td><b>Remove it from a medicine</b></td><td>The medicine can be bought in one click and the
order is <b>sent with no pharmacist check</b>. That breaks the pharmacy's rules for selling
medicines online.</td></tr>
<tr><td><b>Add it to a non-medicine</b></td><td><b>Every order containing it waits for a
pharmacist</b> before it can be sent, even a bottle of shampoo.</td></tr></table>
<div class="note">You can edit this tag yourself. If you are not sure whether a product is a
medicine, leave the tag on and ask the pharmacist.</div>"""),

# ---------------------------------------------------------------- questionnaires
("Questionnaires: what the customer sees",
 shot("modal", "From the website: the questions open in a box over the product page."), """
<p>Some medicines ask the customer a few health questions before they can be added to the
bag.</p>
<ol><li>On the product page, the button says <b>Answer 3 health questions</b> (the number
varies) instead of Add to bag.</li>
<li>Clicking it opens the questions. Every question must be answered.</li>
<li><b>Submit &amp; add to bag</b> puts the product in the bag with the answers attached.</li></ol>
<p>No answer stops the sale. The answers go on the order, and the pharmacist reads them when
checking the order.</p>
<div class="note">The questions do not hold the order. The pharmacist-review tag does that, on
every medicine, with or without questions.</div>"""),

("Questionnaires: which products have one", card("The question sets, by tag", """
<table><tr><th>Tag</th><th>Used on</th></tr>
<tr><td><code>questionnaire-painkillers</code></td><td>Paracetamol, ibuprofen and aspirin products (58)</td></tr>
<tr><td><code>questionnaire-ed</code></td><td>Viagra Connect, Cialis, Sidena (5, not on sale yet)</td></tr>
<tr><td><code>questionnaire-ppi</code></td><td>Losec Control, Nexium Control (4)</td></tr>
<tr><td><code>questionnaire-thrush</code></td><td>Canesten thrush products (3)</td></tr>
<tr><td><code>questionnaire-sedating-antihistamine</code></td><td>Phenergan, Night Nurse, Panadol Night (3)</td></tr>
<tr><td><code>questionnaire-domperidone</code></td><td>Motilium (2)</td></tr>
<tr><td><code>questionnaire-nasal-steroid</code></td><td>Beconase, Nasacort (2)</td></tr>
<tr><td><code>questionnaire-vermox</code></td><td>Vermox (2)</td></tr>
<tr><td><code>questionnaire-sumatriptan</code></td><td>Sumatran Relief (1)</td></tr>
<tr><td><code>questionnaire-anusol-hc</code></td><td>Anusol HC Suppositories (1)</td></tr>
<tr><td><code>questionnaire-gaviscon-infant</code></td><td>Gaviscon Infant (1)</td></tr></table>
<p class="caption">Counts as of 2 October 2026.</p>"""), """
<p>A product's questions are chosen by one tag starting <code>questionnaire-</code>. The table
lists every set in use and what it is on.</p>
<p>Other medicines carry the tag <code>questionnaire-none</code>, which means no questions: the
customer sees an ordinary Add to bag button.</p>
<p>To see which set a product uses, open it and look in its <b>Tags</b>.</p>
<div class="note">This section is only about <b>which products use which set</b>. Writing a new set,
or changing the questions in one, is a separate job for the pharmacist with Kakion: the questions
are part of the website itself and cannot be edited in Shopify.</div>"""),

("Questionnaires: attaching a set to a product",
 admin("q-add", "A product page, <b>Tags</b> field, with a questionnaire tag typed in.",
       "the <b>Tags</b> field, with for example <code>questionnaire-painkillers</code> typed in."), """
<p>Which medicines ask questions is the pharmacist's decision. Check with them first.</p>
<ol><li>Open the product.</li>
<li>In the <b>Tags</b> field, type the set's tag exactly as it is in the table on the previous
page, all lower case. Press <b>Enter</b>.</li>
<li>Leave <code>questionnaire-none</code> and <code>pharmacist-review</code> where they are. The set
wins over <code>questionnaire-none</code> by itself.</li>
<li>Click <b>Save</b>, then open the product on the website and check the button now says
<b>Answer &hellip; health questions</b>.</li></ol>
<div class="note"><b>A misspelt tag takes the product off sale.</b> The website does not recognise
it, so it shows "not available" and nobody can buy the product. One set per product: if a
product has two, only the first counts.</div>"""),

("Questionnaires: taking a set off a product",
 admin("q-remove", "A product page, <b>Tags</b> field.",
       "the small &times; on the <code>questionnaire-</code> tag."), """
<ol><li>Open the product.</li>
<li>In the <b>Tags</b> field, click the &times; on the tag starting <code>questionnaire-</code>
(for example <code>questionnaire-painkillers</code>).</li>
<li><b>Do not remove</b> <code>questionnaire-none</code> or <code>pharmacist-review</code>.</li>
<li>Click <b>Save</b>.</li></ol>
<p>The product now has an ordinary Add to bag button. It is still a medicine: the order is still held
for the pharmacist, and the over-18 tick is still asked on the bag page.</p>
<div class="note">Same as adding: check with the pharmacist before taking questions off a
medicine.</div>"""),

("Quick reference: the tags", card("Type these exactly, all lower case", f"""
<table><tr><th>Tag</th><th>Meaning</th></tr>
<tr><td>{PR}</td><td>It is a medicine: no one-click add, order held for the pharmacist</td></tr>
<tr><td><code>questionnaire-none</code></td><td>No questions</td></tr>
<tr><td><code>questionnaire-&hellip;</code></td><td>Ask that set's questions (page 15)</td></tr></table>"""), """
<ul><li><b>Stock:</b> type the real count, Save. The till does not update the website.</li>
<li><b>Track quantity:</b> always on. Leave <b>Sell when out of stock</b> as you find it.</li>
<li><b>VAT:</b> not sure of the rate? Ask your accountant. The website charges what is set.</li>
<li><b>Medicine:</b> licence number PA, PPA, TR, EU/1/ or VPA on the pack means it needs
<code>pharmacist-review</code>.</li>
<li><b>Questions:</b> which products have them is the pharmacist's call; the questions
themselves are a job for the pharmacist and Kakion.</li>
<li><b>Quantity limits:</b> the website has none today. A customer can order any number of
any product, medicines included, even where the description says "maximum". The pharmacist
sees the quantity when checking a medicine order.</li></ul>
<div class="note">Not sure? Leave it as it is and ask.</div>"""),
]

CSS = """
@page { size: A4 landscape; margin: 0; }
* { box-sizing: border-box; }
body { margin: 0; font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif; color: #2a2b2a;
       font-size: 10pt; line-height: 1.45; }
.page { width: 297mm; height: 210mm; padding: 9mm 14mm 0; position: relative; break-after: page; overflow: hidden; }
.page:last-child { break-after: auto; }
.hdr, .ftr { display: flex; justify-content: space-between; font-size: 7pt; color: #8a8a8a; }
.hdr { letter-spacing: .12em; text-transform: uppercase; padding-bottom: 2mm; border-bottom: .5px solid #d9dad6; }
.ftr { position: absolute; left: 14mm; right: 14mm; bottom: 7mm; padding-top: 2mm; border-top: .5px solid #d9dad6; }
.grid { display: grid; grid-template-columns: 150mm 1fr; gap: 10mm; margin-top: 8mm; height: 168mm; }
.left { display: flex; flex-direction: column; justify-content: center; gap: 4mm; }
.right h2 { font-size: 17pt; line-height: 1.2; color: #1a1a1a; margin: 0 0 4mm; letter-spacing: -.01em; }
.right .sec { color: #3F6B4F; font-size: 8pt; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; margin-bottom: 1.5mm; }
p { margin: 0 0 2.6mm; } ol, ul { margin: 0 0 2.6mm; padding-left: 5mm; } li { margin: 0 0 1.4mm; }
strong, b { color: #1a1a1a; }
code { font-family: Menlo, monospace; font-size: 8.6pt; background: #f1f2ef; padding: 0 3px; border-radius: 3px; color: #1a1a1a; }
.note { margin: 3mm 0 0; padding: 3mm 4mm; background: #eef5fb; border-left: 3px solid #5b8fc7; border-radius: 0 6px 6px 0; }
figure { margin: 0; } figure img { width: 100%; max-height: 120mm; object-fit: contain; object-position: left top;
  border: 1px solid #e0e1dd; border-radius: 6px; display: block; }
.left figure + figure img { max-height: 78mm; }
.left:has(figure + figure) figure:first-child img { max-height: 68mm; }
figcaption, .caption { color: #6b6b6b; font-size: 8pt; margin-top: 1.5mm; }
.card { background: #fff; border: 1px solid #e6e7e4; border-top: 5px solid #82C914; border-radius: 6px; padding: 6mm 7mm; }
.kicker { color: #3F6B4F; font-size: 7.5pt; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; }
.card h3 { font-size: 15pt; margin: 1mm 0 4mm; color: #3F6B4F; }
table { width: 100%; border-collapse: collapse; font-size: 9pt; margin: 0 0 2mm; }
th { text-align: left; font-size: 7.5pt; letter-spacing: .06em; text-transform: uppercase; color: #6b6b6b;
     padding: 0 2mm 1.5mm; border-bottom: 2px solid #3F6B4F; }
td { padding: 1.5mm 2mm; border-bottom: 1px solid #e6e7e4; vertical-align: top; }
tr:nth-child(even) td { background: #f6f9f1; }
.todo { border: 2px dashed #d14343; border-radius: 8px; background: #fdf6f6; height: 110mm; padding: 8mm;
        display: flex; flex-direction: column; justify-content: center; }
.todo-label { color: #b42323; font-weight: 800; font-size: 13pt; letter-spacing: .04em; text-transform: uppercase; margin-bottom: 4mm; }
.todo-file { font-family: Menlo, monospace; font-size: 8pt; color: #8a8a8a; margin-top: 3mm; }
.logo { height: 9mm; display: block; margin-bottom: 5mm; }
"""

SECTION = {1: "", 2: "1 · Stock levels", 6: "2 · VAT", 10: "3 · Pharmacist-review tag",
           14: "4 · Questionnaires", 18: ""}
pages, sec, n = [], "", len(STEPS)
for i, (title, left, right) in enumerate(STEPS, 1):
    sec = SECTION.get(i, sec)
    lg = f'<img class="logo" src="{logo}" alt="McCormack\'s Pharmacy">' if i == 1 else ""
    pages.append(f"""<section class="page"><div class="hdr"><span>{RUNNING}</span><span>Step {i} / {n}</span></div>
<div class="grid"><div class="left">{left}</div><div class="right">{lg}<div class="sec">{sec}</div><h2>{html.escape(title)}</h2>{right}</div></div>
<div class="ftr"><span>{DATE}</span><span>Page {i}</span></div></section>""")
doc = f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{RUNNING}</title><style>{CSS}</style></head><body>{"".join(pages)}</body></html>'

path = os.path.join(OUT, "5-Staff-Guide-Managing-Products.pdf")
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome"); pg = b.new_page(); pg.set_content(doc, wait_until="load")
    over = pg.evaluate("""[...document.querySelectorAll('.right, .left')].map((e,i)=>[Math.floor(i/2)+1, e.scrollHeight-e.clientHeight]).filter(x=>x[1]>2)""")
    pg.pdf(path=path, landscape=True, format="A4", print_background=True, prefer_css_page_size=True)
    b.close()
if over:  # a step that does not fit its page would be cut off silently, so refuse
    sys.exit(f"text overflows on steps {over}; shorten them")
print(f"built {path}, {n} pages")
