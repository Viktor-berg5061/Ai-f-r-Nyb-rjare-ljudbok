#!/usr/bin/env python3
"""Benchmark a vision model on one page: latency + text quality."""
import json, os, base64, io, time, urllib.request, urllib.error

def key():
    NAME = 'OPENROUTER_' + 'API_KEY'
    for line in open(os.path.expanduser('~/.hermes/.env')):
        parts = line.strip().split('=', 1)
        if len(parts) == 2 and parts[0] == NAME:
            return parts[1].strip().strip('"').strip("'")
K = key()

def run(model, img='pdfj/003.jpg', prompt='Du är en exakt OCR-motor för svensk boktext. Transkribera all text i bilden exakt, rad för rad. Återge endast texten.'):
    from PIL import Image
    im = Image.open(img).convert('RGB'); im.thumbnail((1600,1600))
    b=io.BytesIO(); im.save(b,'JPEG',quality=88)
    b64=base64.b64encode(b.getvalue()).decode()
    payload={'model':model,'messages':[{'role':'user','content':[{'type':'image_url','image_url':{'url':'data:image/jpeg;base64,'+b64}},{'type':'text','text':prompt}]}]}
    req=urllib.request.Request('https://openrouter.ai/api/v1/chat/completions',data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+K,'Content-Type':'application/json'})
    t0=time.time()
    try:
        r=json.load(urllib.request.urlopen(req,timeout=90))
        txt=r['choices'][0]['message']['content'].strip()
        return round(time.time()-t0,1), txt
    except urllib.error.HTTPError as e:
        return round(time.time()-t0,1), f'HTTP{e.code} {e.read().decode()[:120]}'

for m in ['z-ai/glm-4.5-flash','z-ai/glm-4.5v','deepseek/deepseek-v4-flash-vision-exp','moonshotai/kimi-k3']:
    t,txt=run(m)
    print(f'=== {m} : {t}s ===')
    print(txt[:180])
    print()
