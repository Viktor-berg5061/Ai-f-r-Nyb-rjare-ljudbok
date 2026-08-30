#!/usr/bin/env python3
"""Steg 2: bygg sökbart PDF i verifierad ordning."""
import subprocess, os, json
import img2pdf

CROP = "/home/agentops/bok-projekt/crop"
OUT = "/home/agentops/bok-projekt"
# verifierad ordning: foto 2-3 flyttas efter foto 12 (sid 12-13 hör till kap 1)
order = [1] + list(range(4, 13)) + [2, 3] + list(range(13, 180))
files = [os.path.join(CROP, f"{i:03d}.jpg") for i in order]
for f in files:
    assert os.path.exists(f), f"saknas: {f}"
print(f"{len(files)} sidor i ordningen", flush=True)

# 1) bild-PDF (förlustfri JPEG-inbäddning)
pages_pdf = os.path.join(OUT, "pages.pdf")
with open(pages_pdf, "wb") as fh:
    fh.write(img2pdf.convert(files))
print(f"pages.pdf: {os.path.getsize(pages_pdf)/1e6:.1f} MB", flush=True)
