#!/usr/bin/env python3
"""Build app/data/pages/<order>.json v2 from clean text + clean audio sync.
Robust word alignment via difflib sequence matching (not blind index), so the
highlighted word is the one actually spoken. Falls back to interpolation.
"""
import json, os, re
from difflib import SequenceMatcher

def tok(s):
    return s.split()

def align(text_words, sync):
    """Return list of {t,s,e} for each text word, using sync [{w,s,e}].
    Map by sequence-match; interpolate time for unmatched text words."""
    Nt = len(text_words)
    if Nt == 0:
        return []
    if not sync:
        return [{'t': w, 's': 0, 'e': 0} for w in text_words]
    sync_words = [x.get('w') for x in sync]
    res = [None] * Nt
    # strip punctuation for matching to reduce noise
    def key(w): return re.sub(r'[^\wåäöÅÄÖ]', '', w.lower())
    sm = SequenceMatcher(None, [key(w) for w in text_words], [key(w) for w in sync_words], autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op in ('equal', 'replace'):
            # distribute sync[j1:j2] across text[i1:i2]
            n_t = i2 - i1; n_s = j2 - j1
            for k in range(n_t):
                if n_s == 0:
                    res[i1 + k] = None
                else:
                    j = j1 + min(int(k * n_s / n_t), n_s - 1)
                    res[i1 + k] = {'t': text_words[i1 + k], 's': sync[j]['s'], 'e': sync[j]['e']}
    # fill any None by interpolating between neighbors
    def get_times(i):
        if res[i]:
            return res[i]['s'], res[i]['e']
        return None
    for i in range(Nt):
        if res[i]:
            continue
        lo = next((res[j]['s'] for j in range(i - 1, -1, -1) if res[j]), 0)
        hi = None
        for j in range(i + 1, Nt):
            if res[j]:
                hi = res[j]['e']; break
        if hi is None:
            hi = lo + 0.3
        if hi <= lo:
            hi = lo + 0.3
        res[i] = {'t': text_words[i], 's': lo, 'e': hi}
    return res

def main():
    pages = json.load(open('pages_clean.json'))
    os.makedirs('app/data/pages', exist_ok=True)
    n = 0; drift = 0
    for p in pages:
        o = p['order']; idx = p['idx']
        syncf = f'audio_clean/{o:03d}_s{idx:03d}.sync.json'
        sync = []
        if os.path.exists(syncf):
            try: sync = json.load(open(syncf))
            except Exception: sync = []
        paras = p['paras']
        para_tokens = [tok(pp) for pp in paras]
        flat = [w for seg in para_tokens for w in seg]
        words = align(flat, sync)
        if len(words) != len(flat):
            drift += 1
        json.dump({'order': o, 'paras': paras, 'para_tokens': para_tokens, 'words': words},
                  open(f'app/data/pages/{o:03d}.json', 'w'), ensure_ascii=False, separators=(',', ':'))
        n += 1
    print(f'built app/data/pages v2 for {n} pages (drift-guard triggers: {drift})')

if __name__ == '__main__':
    main()
