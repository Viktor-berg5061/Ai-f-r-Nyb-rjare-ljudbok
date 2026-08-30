#!/usr/bin/env python3
"""Build data/index.json for the reader app after TTS + sync are done.
Maps order -> audio src, sync src, divider flag, chapter title, book page label.
Also copies pages.json/chapters.json into app/data for static serving.
"""
import json, os, glob

def build():
    pages = json.load(open('pages.json'))
    chapters = json.load(open('chapters.json')) if os.path.exists('chapters.json') else []
    # index chapter titles by order
    ch_by_order = {}
    for c in chapters:
        ch_by_order[c['order']] = c['title']
    audio = {}; sync = {}; divider = {}; bookLabel = {}; chapterTitle = {}
    for p in pages:
        o = p['order']
        mp3 = f'audio/{o:03d}_s{p["idx"]:03d}.mp3'
        syn = f'audio/{o:03d}_s{p["idx"]:03d}.sync.json'
        audio[o] = mp3 if os.path.exists(mp3) and os.path.getsize(mp3) > 1000 else None
        sync[o] = syn if os.path.exists(syn) else None
        divider[o] = bool(p['is_divider'])
        bookLabel[o] = p['book_page'] if p['book_page'] is not None else None
        if p['chapter']:
            chapterTitle[o] = p['chapter']
        elif o in ch_by_order:
            chapterTitle[o] = ch_by_order[o]
    idx = {'audio': audio, 'sync': sync, 'divider': divider,
           'bookLabel': bookLabel, 'chapterTitle': chapterTitle}
    os.makedirs('app/data', exist_ok=True)
    json.dump(idx, open('app/data/index.json', 'w'), ensure_ascii=False)
    json.dump(chapters, open('app/data/chapters.json', 'w'), ensure_ascii=False, indent=2)
    # copy divider mini info into index already has it
    print(f'index.json built: {len(audio)} entries, non-null audio={sum(1 for v in audio.values() if v)}')

if __name__ == '__main__':
    build()
