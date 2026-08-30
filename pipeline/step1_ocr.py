#!/usr/bin/env python3
"""Bokskannings-pipeline steg 1: beskär + OCR + sidnumrering.
159 foton ur repo -> beskurna huvudsidor -> OCR (swe) -> manifest med sidnummer.
"""
import os, re, json, subprocess, sys
from PIL import Image, ImageOps
import cv2
import numpy as np

SRC = "/home/agentops/bok-projekt/repo/Ai för nybörjare 2.0"
OUT_CROP = "/home/agentops/bok-projekt/crop"
OUT_OCR = "/home/agentops/bok-projekt/ocr"
os.makedirs(OUT_CROP, exist_ok=True)
os.makedirs(OUT_OCR, exist_ok=True)

files = sorted(f for f in os.listdir(SRC) if f.lower().endswith(".jpg"))
print(f"Antal foton: {len(files)}", flush=True)

def find_page_crop(im):
    """Hitta den största ljusa ytan (huvudsidan) och returnera bbox (l,t,r,b) i full upplösning."""
    small = im.resize((im.width // 6, im.height // 6))
    g = cv2.cvtColor(np.array(small), cv2.COLOR_RGB2GRAY)
    g = cv2.GaussianBlur(g, (5, 5), 0)
    _, th = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    th = cv2.morphologyEx(th, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, labels, stats, _ = cv2.connectedComponentsWithStats(th)
    if n < 2:
        return None
    # största komponent (index 0 = bakgrund)
    areas = stats[1:, cv2.CC_STAT_AREA]
    idx = 1 + int(np.argmax(areas))
    x, y, w, h = (stats[idx, cv2.CC_STAT_LEFT], stats[idx, cv2.CC_STAT_TOP],
                  stats[idx, cv2.CC_STAT_WIDTH], stats[idx, cv2.CC_STAT_HEIGHT])
    sc = im.width / small.width
    pad = int(0.01 * im.width)
    l = max(0, int(x * sc) - pad); t = max(0, int(y * sc) - pad)
    r = min(im.width, int((x + w) * sc) + pad); b = min(im.height, int((y + h) * sc) + pad)
    area_frac = (w * h) / (small.width * small.height)
    return (l, t, r, b), area_frac

def page_number_from_text(txt):
    """Sök sidnummer: fristående 1-3-siffrigt tal i sista 4 raderna."""
    lines = [l.strip() for l in txt.splitlines() if l.strip()]
    for line in reversed(lines[-4:]):
        m = re.fullmatch(r"[–—-]?\s*(\d{1,3})\s*[–—-]?", line)
        if m:
            n = int(m.group(1))
            if 1 <= n <= 500:
                return n
    return None

manifest = []
for i, fn in enumerate(files, 1):
    try:
        im = Image.open(os.path.join(SRC, fn))
        im = ImageOps.exif_transpose(im).convert("RGB")
        res = find_page_crop(im)
        if res:
            (l, t, r, b), frac = res
            crop = im.crop((l, t, r, b))
        else:
            crop, frac = im, 1.0
        # skala ner till max 1800 px bredd för PDF/OCR-hastighet
        if crop.width > 1800:
            nh = int(crop.height * 1800 / crop.width)
            crop = crop.resize((1800, nh), Image.LANCZOS)
        stem = f"{i:03d}"
        crop_path = os.path.join(OUT_CROP, f"{stem}.jpg")
        crop.save(crop_path, quality=85)
        # OCR
        txt_base = os.path.join(OUT_OCR, stem)
        subprocess.run(["tesseract", crop_path, txt_base, "-l", "swe", "--psm", "3"],
                       capture_output=True, check=True)
        with open(txt_base + ".txt", encoding="utf-8") as fh:
            txt = fh.read()
        pnum = page_number_from_text(txt)
        manifest.append({"idx": i, "photo": fn, "crop": crop_path,
                         "area_frac": round(float(frac), 3), "page_num": pnum,
                         "chars": len(txt)})
        print(f"[{i:3d}/{len(files)}] {fn} pagenum={pnum} frac={frac:.2f} chars={len(txt)}", flush=True)
    except Exception as e:
        print(f"[{i:3d}/{len(files)}] FEL {fn}: {e}", flush=True)
        manifest.append({"idx": i, "photo": fn, "error": str(e)})

with open("/home/agentops/bok-projekt/manifest.json", "w", encoding="utf-8") as fh:
    json.dump(manifest, fh, ensure_ascii=False, indent=1)
print("KLART: manifest.json skriven", flush=True)
