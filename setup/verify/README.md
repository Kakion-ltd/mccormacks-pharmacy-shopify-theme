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
| `sweep.py` | 26 page-loads at two viewports: overflow, broken images, JS errors |
| `fonts.py` | Self-hosted Mulish loads, no third-party font request, out-of-subset glyphs still render |

All run at 1440 and 390.

**What these cannot check.** The preview has no Shopify backend. The full list
of what only a store can verify, from express checkout to customer accounts to
markets, is in [`NEEDS-A-STORE.md`](NEEDS-A-STORE.md). Pixel and consent
procedures are in [`../analytics/README.md`](../analytics/README.md).
