#!/usr/bin/env python3
"""Steg 3: ren text-PDF av OCR-resultatet (samma verifierade sidordning)."""
import os, re, json
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib.colors import HexColor

OCR = "/home/agentops/bok-projekt/ocr_fixed"
OUT = "/home/agentops/bok-projekt/AI för nybörjare 2.0 - TEXT.pdf"

manifest = {e["idx"]: e for e in json.load(open("/home/agentops/bok-projekt/manifest.json"))}
order = [1] + list(range(4, 13)) + [2, 3] + list(range(13, 180))

def clean(txt):
    txt = txt.replace("\x0c", "\n")
    lines = [l.rstrip() for l in txt.splitlines()]
    paras, cur = [], ""
    for l in lines:
        s = l.strip()
        if not s:
            if cur:
                paras.append(cur); cur = ""
            continue
        if cur.endswith("-"):
            cur = cur[:-1] + s
        else:
            cur = (cur + " " + s) if cur else s
    if cur:
        paras.append(cur)
    paras = [re.sub(r"\s+", " ", p).strip() for p in paras]
    return [p for p in paras if len(p) > 1]

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

body = ParagraphStyle("body", fontName="Times-Roman", fontSize=11.5, leading=16.5,
                      alignment=TA_JUSTIFY, spaceAfter=6)
pgno = ParagraphStyle("pgno", fontName="Helvetica", fontSize=9, leading=12,
                      alignment=TA_CENTER, textColor=HexColor("#888888"),
                      spaceBefore=18, spaceAfter=14)
title1 = ParagraphStyle("t1", fontName="Helvetica-Bold", fontSize=30, leading=38,
                        alignment=TA_CENTER, spaceAfter=14)
title2 = ParagraphStyle("t2", fontName="Helvetica", fontSize=13, leading=19,
                        alignment=TA_CENTER, spaceAfter=30)
title3 = ParagraphStyle("t3", fontName="Helvetica", fontSize=11, leading=17,
                        alignment=TA_CENTER, textColor=HexColor("#555555"))

story = []
story.append(Spacer(1, 5 * cm))
story.append(Paragraph("AI FÖR NYBÖRJARE", title1))
story.append(Paragraph("Allt du behöver för att komma i gång med artificiell intelligens", title2))
story.append(Paragraph("Johan Falk &nbsp;·&nbsp; Upplaga 2.0 &nbsp;·&nbsp; Natur &amp; Kultur", title2))
story.append(Spacer(1, 2 * cm))
story.append(Paragraph("OCR-textversion · 179 fotograferade sidor · genererad 2026-08-28", title3))
story.append(PageBreak())

for idx in order:
    txt_path = os.path.join(OCR, f"{idx:03d}.txt")
    with open(txt_path, encoding="utf-8") as fh:
        raw = fh.read()
    paras = clean(raw)
    bn = manifest.get(idx, {}).get("page_num")
    if bn:
        story.append(Paragraph(f"· {bn} ·", pgno))
    else:
        story.append(Spacer(1, 20))
    for p in paras:
        story.append(Paragraph(esc(p), body))
    story.append(PageBreak())

doc = SimpleDocTemplate(OUT, pagesize=A4,
                        leftMargin=2.2 * cm, rightMargin=2.2 * cm,
                        topMargin=2.0 * cm, bottomMargin=2.0 * cm,
                        title="AI för nybörjare 2.0 - TEXT", author="Johan Falk (OCR-text)")
doc.build(story)
print(f"OK: {OUT} | {os.path.getsize(OUT)/1e6:.2f} MB")
