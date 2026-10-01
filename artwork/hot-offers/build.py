#!/usr/bin/env python3
"""Render the three homepage Special Offers tile images from store product shots.

    python3 artwork/hot-offers/build.py

Generated rather than drawn, for the same reason as the gift voucher card: the
subject of each tile is a *set of products an automatic discount applies to*, and
that set changes. When a discount's product list changes, update PRODUCTS below
and re-run; if you retouch the JPEGs by hand instead, the tile will keep
advertising products the discount no longer covers.

Source shots are the live store's own product photography, downloaded by handle
into src/ and cached there. They are studio shots on white, so each one sits on a
white rounded card over the tile's own colour rather than being cut out — a
threshold cutout eats the white packaging on the Azio jars and the Tan Studio
bottle caps.

No text is baked in: every headline, deal line and button on these tiles is live
HTML drawn over the top by sections/hot-offers.liquid (see IMAGE-BRIEF.md, "Do
not bake text into any image"). The ground colour of each file must stay equal to
that block's `background` setting in templates/index.json, because the spotlight
image bleeds to three card edges and any mismatch shows as a seam.

Sizes come from the section schema, not from artwork/README.md: 1600x800 (2:1)
for the spotlight, 800x600 (4:3) for the two rows. The rows render at 128x96 on a
1440 screen and 96px wide on a phone, which is why each row shot is one product
filling the frame and not a group.
"""
import base64
import io
import pathlib
import sys
import urllib.request

from PIL import Image, ImageDraw

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "src"
ASSETS = HERE.parent.parent / "shopify-theme" / "assets"

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit("needs Playwright: pip3 install --user playwright && playwright install chromium")

# Product shots by handle. Read off the store with:
#   npx shopify store execute -s mccormackpharmacy.myshopify.com \
#     -q '{ products(first: 5, query: "...") { nodes { handle featuredMedia
#          { preview { image { url } } } } } }'
SHOTS = {
    "revive-active-original-30pk":
        "https://cdn.shopify.com/s/files/1/1041/6652/3211/files/revive-active-original-30pk-1_bef2cd85-fde3-4355-bbac-e4d4ab395957.jpg",
    "revive-active-joint-complex-30pk":
        "https://cdn.shopify.com/s/files/1/1041/6652/3211/files/revive-active-joint-complex-30pk-1_513e59bd-f20d-40a4-b092-7287521b0a8e.jpg",
    "revive-active-meno-active":
        "https://cdn.shopify.com/s/files/1/1041/6652/3211/files/revive-active-meno-active-1.jpg",
    "azio-beauty-intense-lifting-day-cream":
        "https://cdn.shopify.com/s/files/1/1041/6652/3211/files/5070000552644.jpg",
    "bperfect-tan-studio-tanning-mousse-ultra-dark-200ml":
        "https://cdn.shopify.com/s/files/1/1041/6652/3211/files/bperfect-tan-studio-tanning-mousse-ultra-dark-200ml-1.jpg",
    "bperfect-double-sided-luxury-velvet-tanning-mitt":
        "https://cdn.shopify.com/s/files/1/1041/6652/3211/files/bperfect-double-sided-luxury-velvet-tanning-mitt-1_92563f04-8b06-4abf-83f8-96fd8ec0d75f.jpg",
}

# One entry per tile.
#
# SPOTLIGHT (`card` style). `ground` must equal the block's `background` in
# templates/index.json, because the panel bleeds to three card edges and any
# mismatch shows as a seam. The packs sit on white cards over that ground, and
# the middle one is drawn larger so the trio reads as a hero.
#
#   The cards must stay inside the middle 70% of the width, and the number is
#   measured, not reasoned about. The panel is 2:1 only below 900px, where the
#   stacked layout sets `aspect-ratio: 2/1` exactly. Above that it is whatever
#   the right-hand column's height makes it, and it is narrowest -- so cropped
#   hardest -- in the middle of the desktop range, NOT at 1440:
#
#       vw     panel      aspect   cover crops each side
#       1440   527x302    1.746    6.3%
#       1280   473x299    1.585   10.4%
#       1100   404x285    1.417   14.6%   <- worst
#       1000   557x278    2.005    0.0%
#        375   343x172    2.000    0.0%
#
#   Two earlier cuts got this wrong by checking only the two widths that happen
#   to crop least. The first ran the cards to 93.5% and clipped Meno Active at
#   1440; the second used 87%, read clean at 1440 and 375, shipped, and clipped
#   both outer packs at 1100. Re-measure with the loop in that table before
#   changing this; do not infer it from one screenshot.
#
# ROWS (`bleed` style). No card and no ground: `.hot-row-img` in
# sections/hot-offers.liquid is already a rounded, clipped 4:3 box, so a card
# inside it is a second frame that shrinks the product. These render 128x96 on a
# 1440 screen and 96px wide on a phone — at that size the product has to fill
# the frame or it reads as a smudge.
SAFE = 0.70

TILES = [
    {
        "out": "offer-revive-bogo.jpg",
        "style": "card",
        "w": 1600, "h": 800, "ground": "#3F6B4F",
        "cards": [
            ("revive-active-joint-complex-30pk", 325),
            ("revive-active-original-30pk", 425),
            ("revive-active-meno-active", 325),
        ],
        "gap": 18,
    },
    {
        "out": "offer-azio-beauty.jpg",
        "style": "bleed",
        "w": 800, "h": 600, "ground": "#ffffff",
        "cards": [("azio-beauty-intense-lifting-day-cream", 560)],
        "gap": 0,
    },
    {
        "out": "offer-bperfect-tan-studio.jpg",
        "style": "bleed",
        "w": 800, "h": 600, "ground": "#ffffff",
        "cards": [
            ("bperfect-tan-studio-tanning-mousse-ultra-dark-200ml", 420),
            ("bperfect-double-sided-luxury-velvet-tanning-mitt", 380),
        ],
        "gap": 8,
    },
]


def fetch(handle: str) -> pathlib.Path:
    """Download a product shot once; later runs reuse src/."""
    dest = SRC / f"{handle}.jpg"
    if not dest.exists():
        SRC.mkdir(parents=True, exist_ok=True)
        print(f"  downloading {handle}")
        with urllib.request.urlopen(SHOTS[handle]) as r:
            dest.write_bytes(r.read())
    return dest


def data_uri(path: pathlib.Path) -> str:
    """Inline the shot, with its studio ground normalised to white.

    The shots do not share a ground: most are on white, but Meno Active is on a
    light grey that reads as a grey block inside its white card, next to two
    white ones. Flood-filling inward from the corners takes the ground and stops
    at the pack edge, so the greys *inside* the packaging survive — which a
    whole-image threshold would not.

    A file:// src is blocked on a set_content page and fails silently as a
    broken-image icon on an otherwise finished-looking tile, hence the data URI.
    """
    im = Image.open(path).convert("RGB")
    w, h = im.size
    for xy in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        if min(im.getpixel(xy)) > 200:          # a light ground, not the product
            ImageDraw.floodfill(im, xy, (255, 255, 255), thresh=32)
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=92)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def html_for(tile: dict) -> str:
    cards = "".join(
        f'<div class="card" style="width:{size}px;height:{size}px">'
        f'<img src="{data_uri(fetch(handle))}" alt=""></div>'
        for handle, size in tile["cards"]
    )
    # A card is white-on-ground with a shadow; a bleed shot is the product alone.
    # Not a cutout either way: these are studio shots on white, and the Azio jar
    # and the Tan Studio cap are white too, so thresholding eats the product.
    card_css = ("background:#fff; border-radius:20px; box-shadow:0 18px 44px rgba(0,0,0,.28);"
                if tile["style"] == "card" else "")
    width = int(tile["w"] * SAFE) if tile["style"] == "card" else tile["w"]
    return f"""<!doctype html><meta charset="utf-8"><style>
  html,body {{ margin:0; padding:0; }}
  body {{ width:{tile['w']}px; height:{tile['h']}px; background:{tile['ground']};
          display:flex; align-items:center; justify-content:center; }}
  /* Cards are held inside the safe width so object-fit:cover cannot clip one. */
  .group {{ width:{width}px; display:flex; align-items:center; justify-content:center;
            gap:{tile['gap']}px; }}
  .card {{ {card_css} overflow:hidden; flex:0 0 auto; display:flex; }}
  .card img {{ width:100%; height:100%; object-fit:contain; padding:16px;
               box-sizing:border-box; display:block; }}
</style><body><div class="group">{cards}</div></body>"""


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for tile in TILES:
            print(tile["out"])
            page = browser.new_page(viewport={"width": tile["w"], "height": tile["h"]})
            page.set_content(html_for(tile))
            page.wait_for_load_state("load")
            # Every shot must have decoded. Without this a blocked or 404 src
            # renders as a broken-image icon and still screenshots cleanly.
            loaded = page.eval_on_selector_all(
                ".card img", "els => els.filter(e => e.complete && e.naturalWidth > 0).length")
            if loaded != len(tile["cards"]):
                sys.exit(f"  {tile['out']}: {loaded}/{len(tile['cards'])} shots decoded")
            out = ASSETS / tile["out"]
            page.screenshot(path=out, type="jpeg", quality=84)
            page.close()
            kb = out.stat().st_size / 1024
            # artwork/README.md: JPEG about quality 80, under 300 KB.
            flag = "" if kb < 300 else "  OVER 300 KB"
            print(f"  -> {out.relative_to(ASSETS.parent.parent)}  {tile['w']}x{tile['h']}  {kb:.0f} KB{flag}")
        browser.close()


if __name__ == "__main__":
    main()
