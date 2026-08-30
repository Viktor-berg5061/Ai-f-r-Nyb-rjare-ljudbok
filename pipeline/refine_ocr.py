#!/usr/bin/env python3
"""Refinement pass: proofread each page against its image, via OPENCODE-GO endpoint
(https://opencode.ai/zen/go/v1) with deepseek-v4-flash-vision-exp — a DIFFERENT
model than the Gemini draft, for an independent cross-check.
Reads pdfj/NNN.jpg + draft ocr_vision/NNN.txt -> corrected ocr_clean/NNN.txt.
8 parallel workers.
"""
import json, os, base64, io, time
from concurrent.futures import ThreadPoolExecutor, as_completed

IN_DIR = 'ocr_vision'
IMG_DIR = 'pdfj'
OUT_DIR = 'ocr_clean'
os.makedirs(OUT_DIR, exist_ok=True)

BASE = 'https://opencode.ai/zen/go/v1/chat/completions'
MODEL = 'deepseek-v4-flash-vision-exp'
MODELS = [MODEL, 'glm-5', 'kimi-k2']  # bare opencode-go ids, fallbacks

def load_key():
    NAME = 'OPENCODE_GO_' + 'API_KEY'
    for line in open(os.path.expanduser('~/.hermes/.env')):
        parts = line.strip().split('=', 1)
        if len(parts) == 2 and parts[0] == NAME:
            return parts[1].strip().strip('"').strip("'")
KEY = load_key()
import urllib.request, urllib.error

PROMPT = ("Du är en noggransk korrekturläsare och OCR-granskare för svensk boktext. "
          "Här är en bild av en sida ur en svensk bok och en auto-OCR-draft av samma text. "
          "Läs bilden mycket noggrant och korrigera ALLA fel i draften: felstavningar, felaktiga "
          "eller utelämnade ord och tecken. Rekonstruera ord som är otydliga i bilden utifrån "
          "sammanhanget och betydelsen. Behåll bokens struktur (rubriker, stycken, listor). "
          "Skriv aldrig något som inte står i bilden. Återge ENDAST den korrigerade texten, "
          "ingen inledning, inga kommentarer.")

def refine(idx):
    out = os.path.join(OUT_DIR, f'{idx:03d}.txt')
    if os.path.exists(out) and os.path.getsize(out) > 20:
        return (idx, 'skip', '')
    draft_p = os.path.join(IN_DIR, f'{idx:03d}.txt')
    draft = open(draft_p, encoding='utf-8').read().strip() if os.path.exists(draft_p) else ''
    img_path = os.path.join(IMG_DIR, f'{idx:03d}.jpg')
    if not os.path.exists(img_path):
        return (idx, 'noimage', '')
    from PIL import Image
    im = Image.open(img_path).convert('RGB')
    im.thumbnail((1600, 1600))
    buf = io.BytesIO(); im.save(buf, 'JPEG', quality=88)
    b64 = base64.b64encode(buf.getvalue()).decode()
    user = ('BILDTEXT / OCR-DRAFT:\n' + draft +
            '\n\n---\nKorrigera ovanstående text utifrån bilden. Återge endast korrekt text.')
    last = ''
    for attempt in range(6):
        model = MODELS[attempt % len(MODELS)]
        payload = {'model': model, 'messages': [{'role': 'user', 'content': [
            {'type': 'image_url', 'image_url': {'url': 'data:image/jpeg;base64,' + b64}},
            {'type': 'text', 'text': user}]}], 'max_tokens': 4096}
        req = urllib.request.Request(BASE, data=json.dumps(payload).encode(),
            headers={'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json',
                     'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                     'Accept': 'application/json'})
        try:
            r = json.load(urllib.request.urlopen(req, timeout=120))
            txt = r['choices'][0]['message']['content'].strip()
            if len(txt) > 20:
                open(out, 'w', encoding='utf-8').write(txt)
                return (idx, 'ok', len(txt))
            last = 'empty'
        except urllib.error.HTTPError as e:
            last = f'HTTP{e.code}'
            time.sleep(5 * (attempt + 1))
        except Exception as e:
            last = f'{type(e).__name__}:{e}'
            time.sleep(4 * (attempt + 1))
    return (idx, 'fail', last)

def main():
    idxs = list(range(1, 180))
    todo = [i for i in idxs if not (os.path.exists(os.path.join(OUT_DIR, f'{i:03d}.txt')) and os.path.getsize(os.path.join(OUT_DIR, f'{i:03d}.txt')) > 20)]
    print(f'refine(opencode-go): {len(todo)} pages to proofread of {len(idxs)}', flush=True)
    ok = fail = 0; t0 = time.time()
    with ThreadPoolExecutor(max_workers=2) as ex:
        futs = {ex.submit(refine, i): i for i in todo}
        for f in as_completed(futs):
            idx, status, info = f.result()
            if status == 'ok': ok += 1
            else: fail += 1; print(f'  idx {idx}: {status} {info}', flush=True)
            if (ok + fail) % 10 == 0:
                print(f'  progress ok={ok} fail={fail} elapsed={round(time.time()-t0)}s', flush=True)
    print(f'REFINE(go) DONE ok={ok} fail={fail} elapsed={round(time.time()-t0)}s', flush=True)

if __name__ == '__main__':
    main()
