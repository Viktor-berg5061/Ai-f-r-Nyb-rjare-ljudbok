#!/usr/bin/env python3
"""Build clean reading-order pages from the vision OCR (ocr_vision/).
Joins OCR lines into real flowing paragraphs so TTS reads natural sentences
and the app shows proper paragraphs. Output: pages_clean.json
"""
import json, re, os, sys

MANIF = 'manifest.json'
OCR = sys.argv[1] if len(sys.argv) > 1 else 'ocr_vision'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'pages_clean.json'

manifest = json.load(open(MANIF))
idx_to_page = {e['idx']: e.get('page_num') for e in manifest}
order = [1] + list(range(4, 13)) + [2, 3] + list(range(13, 180))
DIVIDER_IDX = {12: 'DEL I', 59: 'DEL II', 95: 'DEL III', 169: 'Slutord'}

def join_paragraph(raw):
    """Turn OCR text into flowing paragraphs. Blank line = paragraph break.
    Join hyphenated line ends; join lines within a paragraph with a space."""
    raw = raw.replace('\ufeff', '').replace('\x0c', '\n')
    lines = [l.rstrip() for l in raw.splitlines()]
    # drop standalone page-number-only lines
    lines = [l for l in lines if not re.fullmatch(r'\s*[-–—•]?\s*\d{1,4}\s*[-–—•]?\s*', l)]
    paras, cur = [], []
    for l in lines:
        s = l.strip()
        if not s:
            if cur: paras.append(' '.join(cur)); cur = []
            continue
        # hyphenated word split across lines -> merge without space
        if cur and cur[-1].endswith('-'):
            cur[-1] = cur[-1][:-1] + s
        else:
            cur.append(s)
    if cur: paras.append(' '.join(cur))
    paras = [re.sub(r'\s+', ' ', p).replace('  ', ' ').strip() for p in paras]
    paras = [p for p in paras if len(p) > 1]
    return paras

def norm(sp):
    """Normalize AI casing (keep 'AI' uppercase as spoken; URLs lowercase)."""
    return re.sub(r'(?<![./@\w])(?:Ai|A i|a-i)(?![.\w])', 'AI', sp)

pages = []
for order_pos, idx in enumerate(order, start=1):
    f = os.path.join(OCR, f'{idx:03d}.txt')
    # Prefer refined (DeepSeek) text; fall back to the high-quality draft (Gemini) if empty.
    if os.path.exists(f) and os.path.getsize(f) >= 20:
        raw = open(f, encoding='utf-8').read()
    else:
        draft_f = os.path.join('ocr_vision', f'{idx:03d}.txt')
        raw = open(draft_f, encoding='utf-8').read() if os.path.exists(draft_f) else ''
    paras = [norm(p) for p in join_paragraph(raw)]
    book_page = idx_to_page.get(idx)
    pages.append({
        'order': order_pos,
        'idx': idx,
        'book_page': book_page,
        'display_page': book_page if book_page is not None else order_pos,
        'is_divider': idx in DIVIDER_IDX,
        'chapter': DIVIDER_IDX.get(idx, ''),
        'paras': paras,
        'text_len': sum(len(p) for p in paras),
    })

json.dump(pages, open(OUT, 'w'), ensure_ascii=False, indent=2)
print(f'{len(pages)} pages | total chars {sum(p["text_len"] for p in pages)}')
short = [p['order'] for p in pages if p['text_len'] < 40]
print('low-content orders:', short)
divs = [p['order'] for p in pages if p['is_divider']]
print('dividers:', divs)
