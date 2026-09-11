# Browser verification

Playwright scripts that drive the local preview. They exist because the things
they check — a consent gate, a pharmacy gate, a font fallback — all fail
silently, and none of them are visible in a diff.

```sh
npm run dev          # in one terminal
npm run verify       # in another
```

| Script | Checks |
|---|---|
| `consent.py` | Prior consent, equal-prominence reject, no pre-ticked boxes, persistence, reopen, granular grants |
| `funnel.py` | Predictive search, the pharmacy gate on every add surface, cart drawer, cross-sell filtering |
| `sweep.py` | 52 page-loads at four viewports: overflow, broken images, JS errors |
| `header-band.py` | 77 widths from 901 to 1440: nav stays on one line, pills drop once, `--hdr-pinned` matches the measured bar, search placeholder fits |
| `fonts.py` | Self-hosted Mulish loads, no third-party font request, out-of-subset glyphs still render |

Most run at 1440 and 390. `sweep.py` adds 1280 and 1024; `header-band.py` sweeps
every 8px across the desktop band.

**Why a dense sweep for one component.** Three header defects lived between the
sweep's sample widths and none could fail a check there, because a wrapped header
is valid layout — no overflow, no broken image, no JS error, and the suite stayed
green. A step function is the failure mode: any sweep coarse enough to step over
the original bugs will step over their replacement just as cleanly.

**What these cannot check.** The preview has no Shopify backend. The full list
of what only a store can verify, from express checkout to customer accounts to
markets, is in [`NEEDS-A-STORE.md`](NEEDS-A-STORE.md). Pixel and consent
procedures are in [`../analytics/README.md`](../analytics/README.md).
