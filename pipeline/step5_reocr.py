#!/usr/bin/env python3
"""Steg 5: re-OCR med förbättrad preprocessing. Behåller bäst text per sida."""
import os, re, json, subprocess
from PIL import Image, ImageOps
import cv2
import numpy as np

CROP = "/home/agentops/bok-projekt/crop"
OCR = "/home/agentops/bok-projekt/ocr"
OCR2 = "/home/agentops/bok-projekt/ocr2"
TMP = "/tmp/bok/enh"
os.makedirs(OCR2, exist_ok=True)
os.makedirs(TMP, exist_ok=True)

def score(txt):
    """Andel bokstäver bland alla tecken utom mellanslag. Hög = ren text."""
    t = re.sub(r"\s", "", txt)
    if len(t) < 20:
        return 0.0
    letters = sum(1 for c in t if c.isalpha())
    return letters / len(t)

def enhance_and_ocr(crop_path, out_txt_base):
    im = Image.open(crop_path).convert("RGB")
    if im.width < 2600:
        s = 2600 / im.width
        im = im.resize((2600, int(im.height * s)), Image.LANCZOS)
    g = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(16, 16))
    g = clahe.apply(g)
    g = cv2.bilateralFilter(g, 9, 60, 60)
    # adaptiv tröskel jämnar ut skuggor, behåller text
    th = cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                               cv2.THRESH_BINARY, 41, 12)
    p = os.path.join(TMP, os.path.basename(out_txt_base) + ".png")
    cv2.imwrite(p, th)
    subprocess.run(["tesseract", p, out_txt_base, "-l", "swe", "--psm", "3"],
                   capture_output=True, check=True)
    return open(out_txt_base + ".txt", encoding="utf-8").read()

log = []
files = sorted(f for f in os.listdir(CROP) if f.endswith(".jpg"))
for i, fn in enumerate(files, 1):
    idx = int(fn[:3])
    old_p = os.path.join(OCR, f"{idx:03d}.txt")
    old = open(old_p, encoding="utf-8").read()
    try:
        new = enhance_and_ocr(os.path.join(CROP, fn), os.path.join(OCR2, f"{idx:03d}"))
    except Exception as e:
        new = ""
    so, sn = score(old), score(new)
    if sn > so + 0.005:  # ny bättre
        open(old_p, "w", encoding="utf-8").write(new)
        verdict = "NY"
    elif sn > so - 0.005 and len(new) > len(old) * 1.15:  # likvärdig men mer text
        open(old_p, "w", encoding="utf-8").write(new)
        verdict = "MER"
    else:
        verdict = "gammal"
    log.append(f"[{idx:3d}] gammal={so:.3f} ny={sn:.3f} -> {verdict}")
    if i % 10 == 0:
        print(f"--- {i}/179 klar ---", flush=True)

with open("/home/agentops/bok-projekt/step5.log", "w") as fh:
    fh.write("\n".join(log))
ny = sum(1 for l in log if "-> NY" in l)
mer = sum(1 for l in log if "-> MER" in l)
print(f"KLART. {ny} sidor bättre, {mer} sidor mer text, resten behöll gamla.", flush=True)
