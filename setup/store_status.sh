#!/usr/bin/env bash
# One command for three answers:
#   1. git: working tree state, and whether main is ahead of or behind origin
#   2. store: the repo theme's id, name, role, and last saved time
#   3. drift: whether the theme on the store matches HEAD, file by file
#
#   npm run store-status
#
# Needs the Shopify CLI logged in to the store (`npx shopify auth login --store …`).
# The saved time needs an Admin API token with read_themes in ADMIN_TOKEN; without
# it the script says so and still answers the other two. Read-only throughout:
# it pulls a copy of the store theme into a temp folder and never pushes.
set -euo pipefail
STORE="${STORE:-mccormackpharmacy.myshopify.com}"
THEME_ID="${THEME_ID:-207567454539}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "== 1. git"
git fetch -q origin
dirty="$(git status --short | wc -l | tr -d ' ')"
read -r ahead behind <<<"$(git rev-list --left-right --count main...origin/main)"
echo "HEAD $(git rev-parse --short HEAD)  $(git log -1 --format=%s | cut -c1-70)"
echo "uncommitted files: $dirty   ahead of origin: $ahead   behind origin: $behind"
[ "$dirty" != 0 ] && git status --short | head -20

echo
echo "== 2. store theme"
export CI=1 SHOPIFY_CLI_NO_ANALYTICS=1
npx shopify theme info --theme "$THEME_ID" --store "$STORE" --json 2>/dev/null \
  | python3 -c 'import sys,json; t=json.load(sys.stdin)["theme"]; print("#%s  %r  role=%s" % (t["id"], t["name"], t["role"]))'
if [ -n "${ADMIN_TOKEN:-}" ]; then
  curl -s -H "X-Shopify-Access-Token: $ADMIN_TOKEN" -H 'Content-Type: application/json' \
    -d "{\"query\":\"{ theme(id: \\\"gid://shopify/OnlineStoreTheme/$THEME_ID\\\") { updatedAt createdAt } }\"}" \
    "https://$STORE/admin/api/2025-01/graphql.json" \
    | python3 -c 'import sys,json; d=json.load(sys.stdin); t=(d.get("data") or {}).get("theme"); print("last saved %s  created %s" % (t["updatedAt"], t["createdAt"]) if t else "saved time: token lacks read_themes (add it to the custom app)")'
else
  echo "saved time: set ADMIN_TOKEN (custom app with read_themes) to see it"
fi
echo "the name records the commit the theme was CREATED from; section 3 says what is on it now"

echo
echo "== 3. store theme vs HEAD"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
npx shopify theme pull --theme "$THEME_ID" --store "$STORE" --path "$TMP" --no-color >/dev/null 2>&1
python3 - "$TMP" "$ROOT/shopify-theme" <<'EOF'
import os, re, sys, subprocess
store, repo = sys.argv[1], sys.argv[2]
SKIP = {'config/settings_data.json'}  # the store owns this file; the editor rewrites it
import json
def norm(b):
    try: s = b.decode()
    except UnicodeDecodeError: return b
    s = re.sub(r'^\s*/\*.*?\*/\s*', '', s, flags=re.S)  # Shopify's auto-generated JSON header
    try: return json.dumps(json.loads(s), sort_keys=True)   # the store reformats JSON; compare meaning
    except ValueError: return s.replace('\r\n', '\n').rstrip('\n')
def files(root):
    out = {}
    for d, _, fs in os.walk(root):
        for f in fs:
            rel = os.path.relpath(os.path.join(d, f), root)
            if rel.startswith('.') or f == '.DS_Store' or rel in SKIP: continue
            out[rel] = os.path.join(d, f)
    return out
# compare against HEAD, not the working tree, so uncommitted edits show up in section 1 rather than here
head = {}
for line in subprocess.run(['git', 'ls-tree', '-r', '--name-only', 'HEAD', 'shopify-theme/'], capture_output=True, text=True, cwd=repo + '/..').stdout.split():
    rel = line[len('shopify-theme/'):]
    if rel in SKIP or rel.startswith('.'): continue  # the CLI never uploads dotfiles
    head[rel] = subprocess.run(['git', 'show', f'HEAD:{line}'], capture_output=True, cwd=repo + '/..').stdout
s = files(store)
only_store = sorted(set(s) - set(head)); only_head = sorted(set(head) - set(s))
differ = sorted(r for r in set(s) & set(head) if norm(open(s[r], 'rb').read()) != norm(head[r]))
if not (only_store or only_head or differ):
    print(f"MATCH: the store theme equals HEAD on all {len(head)} theme files (settings_data.json excluded)")
else:
    print(f"DRIFT: {len(differ)} differ, {len(only_store)} only on the store, {len(only_head)} only in HEAD")
    for r in differ: print("  differs:      ", r)
    for r in only_store: print("  only on store:", r)
    for r in only_head: print("  only in HEAD: ", r)
    print("  push HEAD with: npx shopify theme push --theme", os.environ.get('THEME_ID', '207567454539'), "--path shopify-theme --store", os.environ.get('STORE', 'mccormackpharmacy.myshopify.com'))
EOF
