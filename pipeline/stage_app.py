#!/usr/bin/env python3
"""Stage the webroot for GitHub Pages inside the repo: assemble app/audio + app/data.
Copy generated MP3 + sync into app/audio/, keep everything relative to index.html.
"""
import json, os, shutil, glob

def main():
    os.makedirs('app/audio', exist_ok=True)
    os.makedirs('app/data', exist_ok=True)
    # copy all mp3 + sync
    for pat in ['audio/*.mp3', 'audio/*.sync.json']:
        for f in glob.glob(pat):
            dst = os.path.join('app/audio', os.path.basename(f))
            if not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(f):
                shutil.copy2(f, dst)
    # build index.json (paths relative to app/, pointing to audio/...)
    pages = json.load(open('pages.json'))
    chapters = json.load(open('chapters.json')) if os.path.exists('chapters.json') else []
    ch_by_order = {c['order']: c['title'] for c in chapters}
    idx = {'audio': {}, 'sync': {}, 'divider': {}, 'bookLabel': {}, 'chapterTitle': {}}
    for p in pages:
        o = p['order']
        mp3 = f'audio/{o:03d}_s{p["idx"]:03d}.mp3'
        syn = f'audio/{o:03d}_s{p["idx"]:03d}.sync.json'
        idx['audio'][o] = mp3 if os.path.exists(mp3) and os.path.getsize(mp3) > 1000 else None
        idx['sync'][o] = syn if os.path.exists(syn) else None
        idx['divider'][o] = bool(p['is_divider'])
        idx['bookLabel'][o] = p['book_page'] if p['book_page'] is not None else None
        if p['chapter']:
            idx['chapterTitle'][o] = p['chapter']
        elif o in ch_by_order:
            idx['chapterTitle'][o] = ch_by_order[o]
    json.dump(idx, open('app/data/index.json', 'w'), ensure_ascii=False)
    json.dump(chapters, open('app/data/chapters.json', 'w'), ensure_ascii=False, indent=2)
    # rebuild search.json from app copy
    s = {}
    for p in pages:
        syn = f'app/audio/{p["order"]:03d}_s{p["idx"]:03d}.sync.json'
        if not os.path.exists(syn): continue
        try: wl = json.load(open(syn))
        except Exception: continue
        for wi, w in enumerate(wl):
            wt = (w.get('w') or '').lower().strip()
            if wt: s.setdefault(wt, []).append({'o': p['order'], 'w': wi})
    json.dump(s, open('app/data/search.json', 'w'), ensure_ascii=False)
    # also copy raw text per page for offline fallback? (optional) skip
    nonnull = sum(1 for v in idx['audio'].values() if v)
    print(f'stage done: app/audio mp3={len(glob.glob("app/audio/*.mp3"))} sync={len(glob.glob("app/audio/*.sync.json"))} | index audio nonnull={nonnull}')

if __name__ == '__main__':
    main()
