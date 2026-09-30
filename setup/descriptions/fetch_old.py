"""Fetch the old site's product pages, one every 10 seconds, stop at the first refusal.
MAINTENANCE.md: "Fetch the old site no faster than one page every 10 seconds: at four
at a time it returned 403 to everything for several minutes."
"""
import json, subprocess, time, sys, os
from extract import sections

UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0 Safari/537.36')
GAP = 10

todo = json.load(open('restore-list.json'))
done = {}
if os.path.exists('old-site.json'):
    done = json.load(open('old-site.json'))

for i, r in enumerate(todo, 1):
    if r['handle'] in done:
        continue
    if done:
        time.sleep(GAP)
    p = subprocess.run(['curl', '-sL', '-A', UA, '-w', '\n%{http_code}', r['live_url']],
                       capture_output=True, text=True, timeout=90)
    body, _, code = p.stdout.rpartition('\n')
    code = code.strip()
    if code in ('403', '429') or code.startswith('5'):
        print(f'REFUSED {code} at #{i} {r["handle"]} - stopping', flush=True)
        break
    if code != '200':                 # 404 and friends: note it, keep going
        print(f'  #{i:3} {r["handle"][:44]:44} HTTP {code}', flush=True)
        done[r['handle']] = {'sections': {}, 'http': code}
        json.dump(done, open('old-site.json', 'w'), indent=1)
        continue
    s = sections(body)
    if not s:
        print(f'  #{i:3} {r["handle"][:44]:44} no accordion', flush=True)
        done[r['handle']] = {'sections': {}, 'http': 200}
    else:
        done[r['handle']] = {'sections': s, 'http': 200}
        pi = s.get('Product Information', '')
        print(f'  #{i:3} {r["handle"][:44]:44} {len(pi):5} chars '
              f'{"+" + ",".join(k for k in s if k not in ("Product Information", "Returns Policy")) if len(s) > 2 else ""}',
              flush=True)
    json.dump(done, open('old-site.json', 'w'), indent=1)

print(f'\nfetched {len(done)} of {len(todo)}')
