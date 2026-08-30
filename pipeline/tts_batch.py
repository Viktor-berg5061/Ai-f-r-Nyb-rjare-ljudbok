#!/usr/bin/env python3
"""Bulk TTS for the whole book using OpenRouter fish-audio (Svensk Narrativ Röst).

Reads pages.json, generates one MP3 per page in reading order, with retry.
Voice: a1843c13ba504f589506a1df30ca39db (Svensk Narrativ Röst — verified Swedish,
natural deep male narrator, says 'AI' correctly when written uppercase).
"""
import json, os, sys, time, urllib.request, urllib.error, hashlib

VOICE = 'a1843c13ba504f589506a1df30ca39db'
MODEL = 'fish-audio/s2.1-pro-free'   # correct slug on /audio/speech (no :free suffix)
ENDPOINT = 'https://openrouter.ai/api/v1/audio/speech'
OUTDIR = 'audio'
SLEEP_BASE = 4.0

def load_key():
    prefix = 'OPENROUTER_API_' + 'KEY'
    for line in open(os.path.expanduser('~/.hermes/.env')):
        if line.startswith(prefix + '='):
            return line.split('=', 1)[1].strip().strip('"').strip("'")

def synthesize(text, out, key, timeout=180):
    payload = {'model': MODEL, 'input': text, 'response_format': 'mp3', 'voice': VOICE}
    req = urllib.request.Request(ENDPOINT, data=json.dumps(payload).encode(),
        headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    r = urllib.request.urlopen(req, timeout=timeout)
    data = r.read()
    open(out, 'wb').write(data)
    return len(data)

def main():
    key = load_key()
    pages = json.load(open('pages.json'))
    os.makedirs(OUTDIR, exist_ok=True)
    only = sys.argv[1:] if len(sys.argv) > 1 else None
    done = 0; failed = 0
    for p in pages:
        order = p['order']; idx = p['idx']
        if only and str(order) not in only and str(idx) not in only:
            continue
        out = os.path.join(OUTDIR, f'{order:03d}_s{idx:03d}.mp3')
        if os.path.exists(out) and os.path.getsize(out) > 3000:
            done += 1; continue
        text = p['text'].strip()
        if not text:
            open(out, 'wb').write(b''); done += 1; continue
        ok = False
        for attempt in range(3):
            try:
                sz = synthesize(text, out, key)
                if sz < 2000:
                    raise ValueError(f'tiny audio {sz}b')
                ok = True
                break
            except urllib.error.HTTPError as e:
                body = e.read().decode()[:200]
                print(f'  order {order} HTTP {e.code}: {body}', flush=True)
                time.sleep(SLEEP_BASE * (attempt + 1))
            except Exception as e:
                print(f'  order {order} err: {e}', flush=True)
                time.sleep(SLEEP_BASE * (attempt + 1))
        if ok:
            done += 1
            print(f'OK order {order} (idx {idx}) -> {os.path.basename(out)}', flush=True)
        else:
            failed += 1
            print(f'FAIL order {order} (idx {idx})', flush=True)
        # polite rate limiting
        time.sleep(0.6)
    print(f'DONE. generated={done} failed={failed}', flush=True)

if __name__ == '__main__':
    main()
