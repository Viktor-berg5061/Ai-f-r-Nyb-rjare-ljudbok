#!/usr/bin/env python3
"""Build data/search.json — a global word -> {order, wi} index for the reader's
'Hitta ord' feature. Walk each page's sync file, lowercase each word, append
to a per-word list. Keeps the app able to jump to the exact spoken word.
"""
import json, os, glob

def build():
    pages = json.load(open('pages.json'))
    idx = {}
    for p in pages:
        o = p['order']
        syn = f'audio/{o:03d}_s{p["idx"]:03d}.sync.json'
        if not os.path.exists(syn):
            continue
        try:
            words = json.load(open(syn))
        except Exception:
            continue
        for wi, w in enumerate(words):
            wt = (w.get('w') or '').lower().strip()
            if not wt:
                continue
            idx.setdefault(wt, []).append({'o': o, 'w': wi})
    os.makedirs('app/data', exist_ok=True)
    json.dump(idx, open('app/data/search.json', 'w'), ensure_ascii=False)
    print(f'search.json built: {len(idx)} unique words, {sum(len(v) for v in idx.values())} occurrences')

if __name__ == '__main__':
    build()
