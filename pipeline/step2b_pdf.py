#!/usr/bin/env python3
"""Steg 2b: PDF-färdiga JPEGs (mindre) + img2pdf."""
import os
from PIL import Image
import img2pdf

CROP = "/home/agentops/bok-projekt/crop"
PDFJ = "/home/agentops/bok-projekt/pdfj"
OUT = "/home/agentops/bok-projekt"
os.makedirs(PDFJ, exist_ok=True)

order = [1] + list(range(4, 13)) + [2, 3] + list(range(13, 180))
files = []
for i in order:
    src = os.path.join(CROP, f"{i:03d}.jpg")
    dst = os.path.join(PDFJ, f"{i:03d}.jpg")
    if not os.path.exists(dst):
        im = Image.open(src)
        if im.width > 1400:
            nh = int(im.height * 1400 / im.width)
            im = im.resize((1400, nh), Image.LANCZOS)
        im.save(dst, quality=72, optimize=True)
    files.append(dst)

pages_pdf = os.path.join(OUT, "pages.pdf")
with open(pages_pdf, "wb") as fh:
    fh.write(img2pdf.convert(files))
print(f"{len(files)} sidor | pages.pdf: {os.path.getsize(pages_pdf)/1e6:.1f} MB", flush=True)
