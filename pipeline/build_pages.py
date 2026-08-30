#!/usr/bin/env python3
"""Build the reading-order page list for the audiobook.

Each photo (idx, file ocr_fixed/NNN.txt) maps to a book page. Correct order from
the OCR session journal: framsida(001) -> [4..12] -> [2,3] -> [13..179].
Book page numbers come from the manifest.json page_num field (photo == page offset).

Output: pages.json = array of {order, idx, book_page (str or int), text, is_divider, chapter}
We normalize: 'AI' stays uppercase (röst uttalar rätt); URLs keep 'ai' lowercase.
"""
import json, re, os

MANIF = 'manifest.json'
OCR = 'ocr_fixed'

manifest = json.load(open(MANIF))

# --- reading order: idx list ---
order = [1] + list(range(4, 13)) + [2, 3] + list(range(13, 180))

# page_num from manifest (photo idx -> book page number)
idx_to_page = {}
for e in manifest:
    idx_to_page[e['idx']] = e.get('page_num')

# chapter boundaries (book page -> chapter title) — from TOC (page 11)
# We don't need titles this pass; just mark dividers.
DIVIDER_IDX = {12: 'DEL I', 59: 'DEL II', 95: 'DEL III', 169: 'Slutord'}

def clean(text):
    """Normalize OCR text for TTS reading."""
    if not text:
        return text
    lines = [l.strip() for l in text.replace('\ufffd', '').splitlines()]
    # remove standalone page-number-only lines
    lines = [l for l in lines if not re.fullmatch(r'\s*[-–—]?\s*\d{1,3}\s*[-–—]?\s*', l)]
    # collapse multiple blank lines
    text = '\n'.join(lines)
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Fix stray Ai / a-i as the word AI (not inside URLs/emails)
    def fix(m):
        return 'AI'
    # only replace standalone 'Ai' or 'a-i' not preceded by dot/slash (URLs)
    text = re.sub(r'(?<![./@\w])(?:Ai|A i|a-i)(?![\w])', 'AI', text)
    return text.strip()

pages = []
for order_pos, idx in enumerate(order, start=1):
    f = os.path.join(OCR, f'{idx:03d}.txt')
    with open(f, encoding='utf-8') as fh:
        raw = fh.read()
    text = clean(raw)
    book_page = idx_to_page.get(idx)
    is_divider = idx in DIVIDER_IDX
    pages.append({
        'order': order_pos,
        'idx': idx,
        'book_page': book_page,
        'display_page': book_page if book_page is not None else order_pos,
        'is_divider': is_divider,
        'chapter': DIVIDER_IDX.get(idx, ''),
        'text': text,
        'text_len': len(text),
    })

json.dump(pages, open('pages.json', 'w'), ensure_ascii=False, indent=2)

# summary
print(f'{len(pages)} pages in reading order')
empty = [p['order'] for p in pages if p['text_len'] < 60]
print('short/low-content orders:', empty)
divs = [p['order'] for p in pages if p['is_divider']]
print('dividers at orders:', divs, [p['chapter'] for p in pages if p['is_divider']])
# collate all text
alltext = '\n\n'.join(p['text'] for p in pages)
print('total chars:', len(alltext))
