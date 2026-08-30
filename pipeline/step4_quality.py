#!/usr/bin/env python3
"""Kvalitetsbedömning av OCR-text: hitta dåliga sidor."""
import os, re, json

OCR = "/home/agentops/bok-projekt/ocr"
results = []
for fn in sorted(os.listdir(OCR)):
    if not fn.endswith(".txt"):
        continue
    idx = int(fn[:3])
    txt = open(os.path.join(OCR, fn), encoding="utf-8").read()
    words = re.findall(r"[A-Za-zÅÄÖåäöéà-]+", txt)
    if not words:
        results.append((idx, 0, 0.0)); continue
    # andel ord >=4 bokstäver (riktiga ord) vs skräp (1-2 tecken)
    good = sum(1 for w in words if len(w) >= 4)
    ratio = good / len(words)
    results.append((idx, len(words), round(ratio, 2)))

results.sort(key=lambda r: r[2])
worst = [r for r in results if r[1] > 30 and r[2] < 0.55]  # tillräckligt med text men mycket skräp
blank = [r for r in results if r[1] <= 30]
print(f"Totalt: {len(results)} sidor | tomma/nästan-tomma: {len(blank)} | dåliga (mycket skräp): {len(worst)}")
print()
print("DÅLIGA SIDOR (foto-nr, ord, andel riktiga ord):")
print(", ".join(f"{i}({w},{r:.2f})" for i, w, r in worst))
print()
print("TOMMA:", ", ".join(str(i) for i, _, _ in blank))
json.dump({"worst": [r[0] for r in worst], "blank": [r[0] for r in blank]},
          open("/home/agentops/bok-projekt/kvalitet.json", "w"))
