#!/bin/sh
# Run every preview check, then report what failed.
#
# Two things this fixes, both of which hid real information:
#
# 1. This was a single `&&` chain in package.json, which stops at the first
#    failure. contrast.py fails on a recorded client decision (the white-on-lime
#    gift voucher card, MAINTENANCE.md), so it failed on every run and the four
#    checks after it never ran at all. A suite that cannot get past its own known
#    failure is not a suite.
#
# 2. The replacement listed the checks by hand, which is the defect at the top of
#    MAINTENANCE.md — one thing in two places. A new check would have been written,
#    committed, and silently never run. So the list is now the directory: every
#    setup/verify/*.py runs, and a new one is picked up by existing.
#
# SKIP is the exception, and it is small on purpose. These checks drive the REAL
# store rather than the local preview, so they need a theme dev server and a live
# catalogue and cannot run in this suite. A new one has to be named here; that is
# a smaller and louder obligation than remembering to add every check twice.
set -u
cd "$(dirname "$0")/../.." || exit 1

SKIP="continue-selling offer-carts"

failed=""
passed=0
skipped=""
for f in setup/verify/*.py; do
  c=$(basename "$f" .py)
  case " $SKIP " in *" $c "*) skipped="$skipped $c"; continue ;; esac
  printf '\n=== %s ===\n' "$c"
  if python3 "$f"; then
    passed=$((passed + 1))
  else
    failed="$failed $c"
  fi
done

printf '\n========================================\n'
[ -n "$skipped" ] && printf 'skipped (real-store checks, run them by hand):%s\n' "$skipped"
if [ -z "$failed" ]; then
  printf 'verify: all %d checks passed\n' "$passed"
  exit 0
fi
printf 'verify: %d passed, FAILED:%s\n' "$passed" "$failed"
printf '\nScroll up for each failure. If one of these is a known and accepted\n'
printf 'failure, it belongs in MAINTENANCE.md with the decision that made it so --\n'
printf 'not in a chain that stops everything after it.\n'
exit 1
