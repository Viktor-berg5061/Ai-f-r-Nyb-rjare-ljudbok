#!/usr/bin/env python3
"""Deploy stage: assemble the static site under repo/docs/ for GitHub Pages.
Copies app/ shell + data/pages/*.json + audio (mp3 + sync) into docs/,
then rebuilds index.json/search.json with correct relative paths.
"""
import json, os, shutil, glob, sys

ROOT = 'repo/docs'

def clear(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)

def main():
    clear(ROOT)
    os.makedirs(f'{ROOT}/audio', exist_ok=True)
    os.makedirs(f'{ROOT}/data/pages', exist_ok=True)
    # app shell
    for f in glob.glob('app/*'):
        base = os.path.basename(f)
        dst = os.path.join(ROOT, base)
        if os.path.isdir(f):
            shutil.copytree(f, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(f, dst)
    # data/core json
    for f in ['app/data/index.json','app/data/chapters.json','app/data/search.json']:
        if os.path.exists(f):
            shutil.copy2(f, os.path.join(ROOT,'data/', os.path.basename(f)))
    # also ensure chapters.json from root if not staged from app/data
    if not os.path.exists(f'{ROOT}/data/chapters.json') and os.path.exists('chapters.json'):
        shutil.copy2('chapters.json', f'{ROOT}/data/chapters.json')
    # data/pages
    for f in glob.glob('app/data/pages/*.json'):
        shutil.copy2(f, f'{ROOT}/data/pages/' + os.path.basename(f))
    # audio (mp3 + sync) from audio/
    for f in glob.glob('audio/*.mp3'):
        shutil.copy2(f, f'{ROOT}/audio/' + os.path.basename(f))
    for f in glob.glob('audio/*.sync.json'):
        shutil.copy2(f, f'{ROOT}/audio/' + os.path.basename(f))
    # rebuild index.json against the staged files (relative to index.html in docs/)
    pages = json.load(open('pages.json'))
    chapters = json.load(open('chapters.json')) if os.path.exists('chapters.json') else []
    ch_by_order = {c['order']: c['title'] for c in chapters}
    idx = {'audio':{}, 'sync':{}, 'divider':{}, 'bookLabel':{}, 'chapterTitle':{}}
    for p in pages:
        o=p['order']
        mp3=f'audio/{o:03d}_s{p["idx"]:03d}.mp3'
        syn=f'audio/{o:03d}_s{p["idx"]:03d}.sync.json'
        am=os.path.join(ROOT,mp3); sm=os.path.join(ROOT,syn)
        idx['audio'][o]=mp3 if os.path.exists(am) and os.path.getsize(am)>1000 else None
        idx['sync'][o]=syn if os.path.exists(sm) else None
        idx['divider'][o]=bool(p['is_divider'])
        idx['bookLabel'][o]=p['book_page'] if p['book_page'] is not None else None
        if p['chapter']: idx['chapterTitle'][o]=p['chapter']
        elif o in ch_by_order: idx['chapterTitle'][o]=ch_by_order[o]
    json.dump(idx, open(f'{ROOT}/data/index.json','w'), ensure_ascii=False)
    # search.json from staged pages
    s={}
    for p in pages:
        syn=f'{ROOT}/audio/{p["order"]:03d}_s{p["idx"]:03d}.sync.json'
        if not os.path.exists(syn): continue
        try: wl=json.load(open(syn))
        except Exception: continue
        for wi,w in enumerate(wl):
            wt=(w.get('w') or '').lower().strip()
            if wt: s.setdefault(wt,[]).append({'o':p['order'],'w':wi})
    json.dump(s, open(f'{ROOT}/data/search.json','w'), ensure_ascii=False)
    # sync.json files for app already copied
    # total size
    mps=glob.glob(f'{ROOT}/audio/*.mp3')
    tot=sum(os.path.getsize(f) for f in mps)
    print(f'deploy staged: {len(mps)} mp3 ({tot/1024/1024:.1f} MB), {len(glob.glob(f"{ROOT}/audio/*.sync.json"))} sync, {len(glob.glob(f"{ROOT}/data/pages/*.json"))} pagejsons')

if __name__=='__main__':
    main()
