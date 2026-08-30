#!/usr/bin/env python3
"""Re-OCR all pages with a strong vision model (OpenRouter) -> ocr_vision/NNN.txt.
Clean, coherent Swedish for the audiobook. 3 parallel workers.
"""
import json, os, base64, time, io, glob
from concurrent.futures import ThreadPoolExecutor, as_completed

OUTDIR = 'ocr_vision'
os.makedirs(OUTDIR, exist_ok=True)
MODELS = ['google/gemini-3.7-flash', 'qwen/qwen3.8-flash', 'moonshotai/kimi-k3']

def load_key():
    for line in open(os.path.expanduser('~/.hermes/.env')):
        if line.startswith('OPENROUTER_API_KEY='):
            return line.split('=', 1)[1].strip().strip('"').strip("'")

KEY = load_key()
import urllib.request, urllib.error

PROMPT = ("Du är en exakt OCR-motor för svensk tryckt boktext. Transkribera ALL text i bilden "
          "exakt så som den står, rad för rad och stycke för stycke som i boken. "
          "Behåll ordet \"AI\" som versalt. Gå INTE mellan sidor. Återge ENDAST den extraherade "
          "texten, ingen inledning, inga kommentarer, ingen tolkning.")

def ocr_one(idx):
    out = os.path.join(OUTDIR, f'{idx:03d}.txt')
    if os.path.exists(out) and os.path.getsize(out) > 20:
        return (idx, 'skip', '')
    img_path = f'pdfj/{idx:03d}.jpg'
    if not os.path.exists(img_path):
        # try crop_small fallback
        alt = f'crop_small/{idx:03d}.jpg'
        if os.path.exists(alt):
            img_path = alt
        else:
            return (idx, 'noimage', '')
    from PIL import Image
    im = Image.open(img_path).convert('RGB')
    im.thumbnail((1600, 1600))
    buf = io.BytesIO(); im.save(buf, 'JPEG', quality=88)
    b64 = base64.b64encode(buf.getvalue()).decode()
    last = ''
    for attempt in range(5):
        model = MODELS[attempt % len(MODELS)]
        payload = {'model': model, 'messages': [{'role': 'user', 'content': [
            {'type': 'image_url', 'image_url': {'url': 'data:image/jpeg;base64,' + b64}},
            {'type': 'text', 'text': PROMPT}]}]}
        req = urllib.request.Request('https://openrouter.ai/api/v1/chat/completions',
            data=json.dumps(payload).encode(),
            headers={'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json'})
        try:
            r = json.load(urllib.request.urlopen(req, timeout=90))
            txt = r['choices'][0]['message']['content'].strip()
            if len(txt) > 20:
                open(out, 'w', encoding='utf-8').write(txt)
                return (idx, 'ok', len(txt))
            last = 'empty'
        except urllib.error.HTTPError as e:
            last = f'HTTP{e.code}'
            if e.code in (429, 503):
                time.sleep(6 * (attempt + 1)); continue
            time.sleep(3 * (attempt + 1))
        except Exception as e:
            last = f'{type(e).__name__}:{e}'
            time.sleep(4 * (attempt + 1))
    return (idx, 'fail', last)

def main():
    idxs = list(range(1, 180))
    todo = [i for i in idxs if not (os.path.exists(os.path.join(OUTDIR, f'{i:03d}.txt')) and os.path.getsize(os.path.join(OUTDIR, f'{i:03d}.txt')) > 20)]
    print(f'ocr_vision: {len(todo)} pages to OCR of {len(idxs)}', flush=True)
    ok = fail = 0; t0 = time.time()
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = {ex.submit(ocr_one, i): i for i in todo}
        for f in as_completed(futs):
            idx, status, info = f.result()
            if status == 'ok':
                ok += 1
            else:
                fail += 1; print(f'  idx {idx}: {status} {info}', flush=True)
            if (ok + fail) % 10 == 0:
                print(f'  progress ok={ok} fail={fail} elapsed={round(time.time()-t0)}s', flush=True)
    print(f'OCR-VISION DONE ok={ok} fail={fail} elapsed={round(time.time()-t0)}s', flush=True)

if __name__ == '__main__':
    main()
