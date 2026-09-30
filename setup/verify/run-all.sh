#!/bin/sh
# Run every check, then report what failed.
#
# This was a single `&&` chain in package.json, which stops at the first failure.
# contrast.py fails on a recorded client decision (the white-on-lime gift voucher
# card, MAINTENANCE.md), so it failed on every run, and the four checks after it —
# questionnaire, medicine-declaration, bag-remove, gift-voucher — never ran at all.
# A suite that cannot get past its own known failure is not a suite.
#
# Every check still counts: a failure here is a failure, contrast included. The
# change is only that one does not hide the others. PORT is inherited, so
# `PORT=8736 npm run verify` still works.
set -u
cd "$(dirname "$0")/../.." || exit 1

CHECKS="generators chips-taxonomy mega-taxonomy consent funnel mobile-nav
        header-wrapper header-band sweep fonts wishlist back-in-stock variants
        variant-integrity pagination hero-swipe trust-bar breadcrumb form-states
        render-states product-faq quick-view contrast questionnaire
        medicine-declaration bag-remove gift-voucher"

failed=""
passed=0
for c in $CHECKS; do
  printf '\n=== %s ===\n' "$c"
  if python3 "setup/verify/$c.py"; then
    passed=$((passed + 1))
  else
    failed="$failed $c"
  fi
done

printf '\n========================================\n'
if [ -z "$failed" ]; then
  printf 'verify: all %d checks passed\n' "$passed"
  exit 0
fi
printf 'verify: %d passed, FAILED:%s\n' "$passed" "$failed"
printf '\nScroll up for each failure. If one of these is a known and accepted\n'
printf 'failure, it belongs in MAINTENANCE.md with the decision that made it so --\n'
printf 'not in a chain that stops everything after it.\n'
exit 1
