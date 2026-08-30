#!/usr/bin/env python3
"""Find the right auth for opencode-go. Tries several header combos (text-only call)."""
import json, os, time, urllib.request, urllib.error

def env(name):
    for line in open(os.path.expanduser('~/.hermes/.env')):
        parts = line.strip().split('=', 1)
        if len(parts) == 2 and parts[0] == name:
            return parts[1].strip().strip('"').strip("'")
    return None

APIK = env('OPENCODE_GO_' + 'API_KEY')
COOKIE = env('OPENCODE_GO_AUTH_' + 'COOKIE')
WS = env('OPENCODE_GO_' + 'WORKSPACE_ID')
print('api_key len:', len(APIK) if APIK else 0, '| cookie len:', len(COOKIE) if COOKIE else 0, '| ws:', WS)

BASE = 'https://opencode.ai/zen/go/v1/chat/completions'
payload = {'model': 'deepseek-v4-flash-vision-exp', 'messages': [{'role': 'user', 'content': 'Säg OK'}], 'max_tokens': 8}

combos = {
    'bearer_api': {'Authorization': 'Bearer ' + (APIK or '')},
    'bearer_cookie': {'Authorization': 'Bearer ' + (COOKIE or '')},
    'cookie_hdr': {'Cookie': COOKIE or '', 'Authorization': 'Bearer ' + (APIK or '')},
    'api+ws': {'Authorization': 'Bearer ' + (APIK or ''), 'x-workspace-id': WS or ''},
    'cookie+ws': {'Authorization': 'Bearer ' + (COOKIE or ''), 'x-workspace-id': WS or ''},
}

UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

for name, hdr in combos.items():
    h = dict(hdr); h['Content-Type'] = 'application/json'
    h['User-Agent'] = UA
    h['Accept'] = 'application/json'
    h['Accept-Language'] = 'sv-SE,sv;q=0.9,en;q=0.8'
    req = urllib.request.Request(BASE, data=json.dumps(payload).encode(), headers=h)
    try:
        t0 = time.time()
        r = urllib.request.urlopen(req, timeout=30)
        d = r.read().decode()
        print(f'{name}: HTTP{r.status} in {round(time.time()-t0,1)}s -> {d[:80]}')
    except urllib.error.HTTPError as e:
        print(f'{name}: HTTP{e.code} {e.read().decode()[:80]}')
    except Exception as e:
        print(f'{name}: {type(e).__name__}: {e}')
