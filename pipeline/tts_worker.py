#!/usr/bin/env python3
"""Parallel-capable TTS worker. Partition pages by order range to avoid collisions.
Usage: python3 tts_worker.py <start_order> <end_order>
"""
import json, os, sys, time, urllib.request, urllib.error

VOICE = 'a1843c13ba504f589506a1df30ca39db'
MODEL = 'fish-audio/s2.1-pro-free'
ENDPOINT = 'https://openrouter.ai/api/v1/audio/speech'

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
    start = int(sys.argv[1]); end = int(sys.argv[2])
    key = load_key()
    pages = json.load(open('pages.json'))
    os.makedirs('audio', exist_ok=True)
    done = failed = 0
    for p in pages:
        o = p['order']
        if o < start or o > end:
            continue
        out = os.path.join('audio', f'{o:03d}_s{p["idx"]:03d}.mp3')
        if os.path.exists(out) and os.path.getsize(out) > 3000:
            done += 1; continue
        text = p['text'].strip()
        if not text:
            open(out, 'wb').write(b''); done += 1; continue
        ok = False
        for attempt in range(4):
            try:
                sz = synthesize(text, out, key)
                if sz < 2000: raise ValueError('tiny')
                ok = True; break
            except Exception as e:
                print(f'  order {o} attempt {attempt}: {type(e).__name__}: {e}', flush=True)
                time.sleep(4 * (attempt + 1))
        if ok:
            done += 1; print(f'W OK order {o} (idx {p["idx"]})', flush=True)
        else:
            failed += 1; print(f'W FAIL order {o} (idx {p["idx"]})', flush=True)
        time.sleep(0.4)
    print(f'WORKER [{start}-{end}] DONE generated={done} failed={failed}', flush=True)

if __name__ == '__main__':
    main()
