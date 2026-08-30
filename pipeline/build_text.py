#!/usr/bin/env python3
"""Build app/data/pages/<order>.json per page for the reader.

Contains real paragraph text (correct OCR spelling) and a flat word list
{ t: displayWord, s: startSec, e: endSec } where each text word is paired to
the Whisper word-time positionally. The reader renders paragraph spans but
highlights using these exact times, so nothing reads before/after.

If text token count ~= sync word count, we map 1:1. If they diverge, we
distribute available times over text words (best-effort, still monotonic).
"""
import json, os, re, glob

def tok(s):
    return s.split()

def build():
    pages = json.load(open('pages.json'))
    os.makedirs('app/data/pages', exist_ok=True)
    total_pages = 0
    for p in pages:
        o = p['order']; idx = p['idx']
        syncf = f'audio/{o:03d}_s{idx:03d}.sync.json'
        sync = []
        if os.path.exists(syncf):
            try: sync = json.load(open(syncf))
            except Exception: sync = []
        raw = p['text']
        paras = [pp.strip() for pp in re.split(r'\n\s*\n', raw) if pp.strip()]
        if not paras and raw.strip():
            paras = [raw.strip()]
        para_tokens = [tok(pp) for pp in paras]
        flat = [w for seg in para_tokens for w in seg]
        times = [round(w['s'],3) for w in sync] if sync else []
        ends  = [round(w['e'],3) for w in sync] if sync else []
        Nf = len(flat); Ns = len(times)
        if Nf == 0:
            word_list = []
        elif Ns == 0:
            word_list = [{'t': w, 's': 0, 'e': 0} for w in flat]
        else:
            word_list = []
            for i in range(Nf):
                if Nf == Ns:
                    s = times[i]; e = ends[i]
                else:
                    # scale: pick time proportional to index
                    j = min(int(i * Ns / Nf), Ns-1)
                    s = times[j]; e = ends[j]
                word_list.append({'t': flat[i], 's': s, 'e': e})
        data = {'order': o, 'paras': paras, 'para_tokens': para_tokens, 'words': word_list}
        json.dump(data, open(f'app/data/pages/{o:03d}.json','w'), ensure_ascii=False, separators=(',',':'))
        total_pages += 1
    print(f'built app/data/pages/*.json for {total_pages} pages')

if __name__ == '__main__':
    build()
