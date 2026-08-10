#!/usr/bin/env bash
# Build dist/mccormacks-theme.zip for Online Store -> Themes -> Add theme -> Upload zip.
# Shopify requires the theme folders at the TOP LEVEL of the archive (no wrapper
# directory), so this zips from inside shopify-theme/.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
THEME="$ROOT/shopify-theme"
DIST="$ROOT/dist"
ZIP="$DIST/mccormacks-theme.zip"

for d in assets config layout locales sections snippets templates; do
  [ -d "$THEME/$d" ] || { echo "missing required folder: $d" >&2; exit 1; }
done

mkdir -p "$DIST"
rm -f "$ZIP"
cd "$THEME"
# -x excludes editor/OS cruft that Shopify rejects or that just bloats the upload
zip -rq "$ZIP" assets config layout locales sections snippets templates \
  -x '*.DS_Store' '*/__MACOSX/*' '*.map' '*.orig' '*.rej'

cd "$ROOT"
COUNT=$(unzip -Z1 "$ZIP" | grep -vc '/$' || true)
SIZE=$(du -h "$ZIP" | cut -f1)
echo "built dist/mccormacks-theme.zip — $COUNT files, $SIZE"
echo "top level: $(unzip -Z1 "$ZIP" | cut -d/ -f1 | sort -u | tr '\n' ' ')"
