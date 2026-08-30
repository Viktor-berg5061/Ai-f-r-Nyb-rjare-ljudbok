#!/usr/bin/env python3
"""Stage v2: build app/audio + app/data (index, chapters, search) from CLEAN
pages_clean.json + audio_clean, then stage docs/ for GitHub Pages.
"""
import json, os, shutil, glob

def main():
    os.makedirs('app/audio', exist_ok=True)
    os.makedirs('app/data', exist_ok=True)
    # copy clean audio + sync into app/audio
    for pat in ['audio_clean/*.mp3', 'audio_clean/*.sync.json']:
        for f in glob.glob(pat):
            dst = os.path.join('app/audio', os.path.basename(f))
            if not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(f):
                shutil.copy2(f, dst)
    pages = json.load(open('pages_clean.json'))
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
        idx['bookLabel'][o] = p['display_page']
        if p['chapter']:
            idx['chapterTitle'][o] = p['chapter']
        elif o in ch_by_order:
            idx['chapterTitle'][o] = ch_by_order[o]
    json.dump(idx, open('app/data/index.json', 'w'), ensure_ascii=False)
    json.dump(chapters, open('app/data/chapters.json', 'w'), ensure_ascii=False, indent=2)
    # search.json from clean sync (key 'w')
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
    # stage docs/
    os.makedirs('docs', exist_ok=True)
    shutil.copytree('app', 'docs', dirs_exist_ok=True)
    n_mp3 = len(glob.glob('app/audio/*.mp3'))
    n_sync = len(glob.glob('app/audio/*.sync.json'))
    print(f'STAGE-V2 done: app/audio mp3={n_mp3} sync={n_sync} | index audio nonnull={sum(1 for v in idx["audio"].values() if v)}')

if __name__ == '__main__':
    main()
