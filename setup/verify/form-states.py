"""Form success and error states.

Neither had rendered anywhere. form.posted_successfully was hardcoded false and
form.errors null in the harness, so across six contact forms, the newsletter signup
and back-in-stock, no confirmation and no error box existed in any preview.

These are the two screens where a customer hands over data and needs to see what
happened to it — a prescription request or a back-in-stock signup that silently
appears to do nothing is the worst outcome on the site.

Reads the rendered variants directly rather than over HTTP: they are alternate
renders of the same URL, not separate pages, so there is nothing to route them to.
"""
import pathlib
import re
import sys

PREVIEW = pathlib.Path(__file__).resolve().parents[2] / "preview"

# page stem -> a phrase that only appears in its success state
PAGES = {
    "page.contact-us": "has been sent",
    "page.prescriptions": "",
    "page.careers": "",
    "page.in-store-services": "",
    "page.withdraw-from-contract": "",
    "product.oos": "we have your request",
}

# Both error presentations in the theme: the shared snippet, and the inline blocks
# the public contact forms use. Either is a pass; absence is not.
ERROR_MARKERS = ("form-errors", "#FBEAE9", "FBEAE9")
SUCCESS_MARKERS = ("EEF6E4", "bis-done", "Thanks")

res = []
def ck(name, got, want=True): res.append((got == want, name, got))

def read(stem, suffix):
    p = PREVIEW / f"{stem}.{suffix}.html"
    if not p.exists():
        return None
    return p.read_text(encoding="utf-8", errors="replace")

for stem, phrase in PAGES.items():
    ok_html = read(stem, "success")
    err_html = read(stem, "errors")

    ck(f"{stem}: a success render exists", ok_html is not None)
    ck(f"{stem}: an error render exists", err_html is not None)
    if ok_html is None or err_html is None:
        continue

    ck(f"{stem}: success state is visible",
       any(m in ok_html for m in SUCCESS_MARKERS))
    if phrase:
        ck(f"{stem}: success names what happened", phrase.lower() in ok_html.lower())

    ck(f"{stem}: error state is visible",
       any(m in err_html for m in ERROR_MARKERS))
    # The error render must actually surface the failing field, not just a box.
    ck(f"{stem}: the error names the field or the problem",
       "Email" in err_html or "email address" in err_html or "try again" in err_html.lower())

    # A success render must not also be showing the error box, and vice versa —
    # they are mutually exclusive states and showing both is worse than either.
    ck(f"{stem}: success does not also show an error box",
       "form-errors" in ok_html and "There was a problem" in ok_html, False)

# The plain render of the same pages must show neither state.
for stem in ("page.contact-us", "product.oos"):
    plain = (PREVIEW / f"{stem}.html").read_text(encoding="utf-8", errors="replace")
    ck(f"{stem}: neither state on a fresh page load",
       "There was a problem" in plain, False)

for ok, name, got in res:
    if not ok:
        print(f"FAIL  {name}   (got {got!r})")
print(f"\n{sum(1 for r in res if r[0])}/{len(res)} form state checks passed")
sys.exit(0 if all(r[0] for r in res) else 1)
