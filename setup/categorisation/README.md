# Categorisation sweep — 1 October 2026

`Categorisation-Sweep.xlsx` is the report. It proposes changes and approves none:
nothing here writes to the store.

## Re-running it

The sweep reads a local copy of the store, not the store itself. Pull one with
the Shopify CLI's read-only `store execute` (it refuses mutations unless
`--allow-mutations` is passed, which nothing here does):

```sh
# collections: id, handle, title, productsCount, ruleSet   -> collections.jsonl
# products:    id, handle, title, productType, vendor, tags, status, description
#                                                          -> products.jsonl
# plus nocat.json, the handles of products on no category page
SWEEP_DATA=<that folder> python3 setup/categorisation/build.py
```

Paginate with `first: 100` and the `endCursor`; the CLI returns the query result
without the GraphQL `data` wrapper, so parse the root.

## The three files

- `signatures.py` — one entry per target page: the product types it may draw
  from, and three title regexes (high / medium / low). The pool is what keeps
  the regexes honest; `blush` is unambiguous inside `Beauty > Face` and useless
  across the catalogue, where it also matches a Jo Malone fragrance.
- `findings.py` — the judgement calls no regex makes: pages that should stay
  empty, rules that are themselves wrong, products in the wrong category, and
  the products on no category page.
- `build.py` — runs the signatures over the pull and writes the workbook.

## Two things that are easy to get wrong

**Shopify's rule matching is looser than an exact string compare.** It folds
case and accents (`VENDOR EQUALS "fabÜ"` matches vendor `Fabu`) and it folds
punctuation, so `TAG EQUALS "Baby Feeding"` matches the tag `Baby > Feeding`.
A rule evaluator that compares strings exactly disagrees with the store on 12
of 316 collections; one that folds disagrees on 3. Of those 3, two are index
lag and one is `baby-feeding` — see the Rules to change tab.

**`productsCount` can lag a tag change by minutes**, as MAINTENANCE records.
Re-pull before trusting a count taken straight after a bulk tag run.
