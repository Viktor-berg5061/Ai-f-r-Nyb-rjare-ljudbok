#!/usr/bin/env python3
"""Rebuild the final TEXT PDF from the CLEAN vision OCR (ocr_vision via pages_clean.json).
Same verified reading order, flowing paragraphs, correct spelling.
"""
import os, json
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib.colors import HexColor

OUT = "/home/agentops/bok-projekt/AI för nybörjare 2.0 - TEXT.pdf"
pages = json.load(open('pages_clean.json'))

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

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

story = []
story.append(Spacer(1, 5 * cm))
story.append(Paragraph("AI FÖR NYBÖRJARE", title1))
story.append(Paragraph("Allt du behöver för att komma i gång med artificiell intelligens", title2))
story.append(Paragraph("Johan Falk &nbsp;·&nbsp; Upplaga 2.0 &nbsp;·&nbsp; Natur &amp; Kultur", title2))
story.append(Spacer(1, 2 * cm))
story.append(Paragraph("OCR-textversion (vision-modell) · 179 fotograferade sidor · genererad 2026-08-28", title3))
story.append(PageBreak())

for p in pages:
    bn = p['display_page']
    story.append(Paragraph(f"· {bn} ·", pgno))
    for para in p['paras']:
        story.append(Paragraph(esc(para), body))
    story.append(PageBreak())

doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=2.2 * cm, rightMargin=2.2 * cm,
                        topMargin=2.0 * cm, bottomMargin=2.0 * cm,
                        title="AI för nybörjare 2.0 - TEXT", author="Johan Falk (OCR-text)")
doc.build(story)
print(f"OK: {OUT} | {os.path.getsize(OUT)/1e6:.2f} MB")
