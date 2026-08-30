#!/usr/bin/env python3
"""One-off careful re-OCR of specific problem pages via opencode-go (DeepSeek),
transcribing ALL visible text verbatim. Usage: python3 fix_pages.py 76 130 43
Writes ocr_clean/NNN.txt.
"""
import json, os, sys, base64, io, time, urllib.request, urllib.error

BASE = 'https://opencode.ai/zen/go/v1/chat/completions'
MODEL = 'deepseek-v4-flash-vision-exp'

def load_key():
    NAME = 'OPENCODE_GO_' + 'API_KEY'
    for line in open(os.path.expanduser('~/.hermes/.env')):
        parts = line.strip().split('=', 1)
        if len(parts) == 2 and parts[0] == NAME:
            return parts[1].strip().strip('"').strip("'")
KEY = load_key()

PROMPT = ("Du är en exakt OCR-motor för svensk tryckt boktext. Transkribera ABSOLUT ALL text "
          "i bilden, exakt och fullständigt, rad för rad och stycke för stycke — inklusive "
          "bildtext, marginalnoteringar, rubriker och listpunkter. Skriv INTE sammanfattningar, "
          "utelämna ingenting. Återge ENDAST den transkriberade texten.")

def reocr(idx):
    img_path = f'pdfj/{idx:03d}.jpg'
    from PIL import Image
    im = Image.open(img_path).convert('RGB')
    im.thumbnail((1800, 1800))
    buf = io.BytesIO(); im.save(buf, 'JPEG', quality=90)
    b64 = base64.b64encode(buf.getvalue()).decode()
    payload = {'model': MODEL, 'messages': [{'role': 'user', 'content': [
        {'type': 'image_url', 'image_url': {'url': 'data:image/jpeg;base64,' + b64}},
        {'type': 'text', 'text': PROMPT}]}], 'max_tokens': 4096}
    req = urllib.request.Request(BASE, data=json.dumps(payload).encode(),
        headers={'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json',
                 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                 'Accept': 'application/json'})
    for attempt in range(5):
        try:
            r = json.load(urllib.request.urlopen(req, timeout=140))
            txt = r['choices'][0]['message']['content'].strip()
            if len(txt) > 20:
                open(f'ocr_clean/{idx:03d}.txt', 'w', encoding='utf-8').write(txt)
                print(f'idx {idx}: OK {len(txt)} chars')
                return True
        except urllib.error.HTTPError as e:
            print(f'idx {idx} HTTP{e.code}', flush=True); time.sleep(6 * (attempt + 1))
        except Exception as e:
            print(f'idx {idx} {type(e).__name__}:{e}', flush=True); time.sleep(5 * (attempt + 1))
    print(f'idx {idx}: FAILED'); return False

if __name__ == '__main__':
    for a in sys.argv[1:]:
        reocr(int(a))
