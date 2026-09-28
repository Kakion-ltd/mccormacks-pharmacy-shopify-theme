"""Builds the client PDFs in the staff guide's style: A4, logo on page 1, grey
running title, build date and page number in the footer, green accents.

    python3 setup/build_client_pdfs.py <outdir>

Writes <outdir>/1-Handover.pdf from setup/HANDOVER.md, <outdir>/3-Images-Handover.pdf
from setup/IMAGES-HANDOVER.md and <outdir>/5-Pharmacist-Questions.pdf from
setup/PHARMACIST-QUESTIONS.md. Rebuild after every change to any of them. Needs `pip3 install --user markdown`, Python Playwright
(already used by setup/verify) and Google Chrome.
"""
import base64, datetime, html, os, re, sys
import markdown
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
LOGO = os.path.join(HERE, "..", "shopify-theme", "assets", "mccormacks-logo.png")
logo = "data:image/png;base64," + base64.b64encode(open(LOGO, "rb").read()).decode()
today = datetime.date.today()
DATE = f"{today.day} {today:%B %Y}"

CSS = """
@page { size: A4; margin: 26mm 20mm 22mm; }
body { font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif; color: #2a2b2a;
       font-size: 10.5pt; line-height: 1.5; margin: 0; }
.logo { height: 15mm; margin: 0 0 9mm; }
.bar { height: 5px; background: #82C914; border-radius: 3px; margin: 0 0 7mm; }
h1 { font-size: 22pt; line-height: 1.2; margin: 0 0 4mm; color: #1a1a1a; letter-spacing: -.01em; }
h2 { font-size: 15pt; color: #3F6B4F; margin: 9mm 0 3mm; padding-top: 3mm;
     border-top: 1px solid #e6e7e4; break-after: avoid; }
h3 { font-size: 12pt; color: #1a1a1a; margin: 6mm 0 2mm; break-after: avoid; }
p { margin: 0 0 3mm; } ul, ol { margin: 0 0 3mm; padding-left: 6mm; } li { margin: 0 0 1.2mm; }
strong { color: #1a1a1a; }
code { font-family: Menlo, monospace; font-size: 9pt; background: #f1f2ef; padding: 0 3px; border-radius: 3px; }
blockquote { margin: 0 0 3mm; padding: 3mm 4mm; background: #f6f9f1; border-left: 3px solid #82C914; border-radius: 0 6px 6px 0; }
blockquote p:last-child { margin: 0; }
.caption { color: #6b6b6b; font-size: 9pt; }
table { width: 100%; border-collapse: collapse; margin: 0 0 3mm; font-size: 9.5pt; break-inside: avoid; }
th { text-align: left; font-size: 8pt; letter-spacing: .06em; text-transform: uppercase; color: #6b6b6b;
     padding: 0 2mm 1.5mm; border-bottom: 2px solid #3F6B4F; }
td { padding: 1.6mm 2mm; border-bottom: 1px solid #e6e7e4; vertical-align: top; }
tr:nth-child(even) td { background: #f6f9f1; }
p, li { orphans: 3; widows: 3; }
p:has(+ ol), p:has(+ ul) { break-after: avoid; }
"""

def page(title, running, body):
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>{CSS}</style></head><body><img class="logo" src="{logo}" alt="McCormack's Pharmacy"><div class="bar"></div>{body}</body></html>"""

def pdf(p, doc, running, path):
    pg = p.new_page(); pg.set_content(doc, wait_until="load")
    hdr = f"""<div style="width:100%;font-family:-apple-system,Helvetica,Arial;font-size:7.5px;color:#8a8a8a;letter-spacing:.12em;
      text-transform:uppercase;margin:0 20mm;padding-bottom:3px;border-bottom:.5px solid #d9dad6;">{html.escape(running)}</div>"""
    ftr = f"""<div style="width:100%;font-family:-apple-system,Helvetica,Arial;font-size:7.5px;color:#8a8a8a;margin:0 20mm;
      padding-top:3px;border-top:.5px solid #d9dad6;display:flex;justify-content:space-between;">
      <span>{DATE}</span><span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span></div>"""
    pg.pdf(path=path, format="A4", print_background=True, display_header_footer=True,
           header_template=hdr, footer_template=ftr, margin={"top": "26mm", "bottom": "22mm", "left": "20mm", "right": "20mm"})
    pg.close()

def md_doc(name):
    """Markdown as written, from setup/. Section rules replace the --- dividers."""
    src = open(os.path.join(HERE, name)).read().replace("\n---\n", "\n")
    # A list straight after a paragraph line needs a blank line for python-markdown.
    src = re.sub(r"(?m)^(?!- |\d+\. |\s|>)(\S.*)\n(- |\d+\. )", r"\1\n\n\2", src)
    return re.match(r"# (.+)", src).group(1), markdown.markdown(src, extensions=["tables", "sane_lists"])

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome")
    for name, running, out in (("HANDOVER.md", "Website handover", "1-Handover.pdf"),
                               ("IMAGES-HANDOVER.md", "Product images", "3-Images-Handover.pdf"),
                               ("PHARMACIST-QUESTIONS.md", "Questions before purchase", "5-Pharmacist-Questions.pdf")):
        title, body = md_doc(name)
        pdf(b, page(title, running, body), running, f"{OUT}/{out}")
    b.close()
print("built")
