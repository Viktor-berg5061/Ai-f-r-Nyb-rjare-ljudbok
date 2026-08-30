#!/usr/bin/env python3
"""Steg 6: lexikonbaserad stavningsfix av OCR-text, sida för sida."""
import os, re, json
from collections import Counter

DICT_P = "/home/agentops/bok-projekt/sv_aspell.txt"
DICT_P2 = "/home/agentops/bok-projekt/sv_words.txt"
OCR = "/home/agentops/bok-projekt/ocr"
OUT = "/home/agentops/bok-projekt/ocr_fixed"
os.makedirs(OUT, exist_ok=True)

# --- ordlista (hunspell-format: "ord/flaggor") ---
words = Counter()
with open(DICT_P2, encoding="utf-8", errors="ignore") as fh:
    for line in fh:
        w = line.split("/")[0].strip().lower()
        if w and w.isalpha():
            words[w] += 1
DICT = set(words)
print(f"ordlista: {len(DICT)} ord", flush=True)

# aspell-lista (ren ordlista, en per rad)
with open(DICT_P, encoding="utf-8", errors="ignore") as fh:
    for line in fh:
        w = line.strip().lower()
        if w and w.isalpha():
            DICT.add(w)
print(f"ordlista union: {len(DICT)} ord", flush=True)

# extra ord som finns i boken (namn, termer)
DICT |= {"ai", "chatgpt", "gpt", "chatbot", "chatbotar", "deepfakes", "deepfake",
         "mnist", "robotar", "internet", "sverige", "openai", "google", "youtube",
         "bojs", "falk", "imran", "khan", "app", "apps", "chat", "chatt", "quiz",
         "vpn", "usb", "wifi", "sms", "eu", "usa", "kina", "indonesien", "sydkorea",
         "bulgarien", "portugal", "turkiet", "singapore", "pakistani", "pakistan",
         "arcprize", "sumsub", "bbc", "guardian", "wikimedia", "natur", "kultur",
         "alphago", "gpt-4", "o1", "o3", "gpt4", "claude", "gemini", "mistral"}

# --- läs alla sidor, bygg frekvens ---
pages = {}
for fn in sorted(os.listdir(OCR)):
    if fn.endswith(".txt"):
        pages[int(fn[:3])] = open(os.path.join(OCR, fn), encoding="utf-8").read()
book_freq = Counter()
for t in pages.values():
    for w in re.findall(r"[A-Za-zÅÄÖåäö]+", t):
        book_freq[w.lower()] += 1

# --- förväxlingstabell (OCR-klassiker) ---
CH = {"0": "o", "1": "l", "5": "s", "8": "b", "6": "b", "4": "a", "3": "e", "9": "g"}
PAIR = [("rn", "m"), ("vv", "w"), ("ii", "u"), ("cl", "d"), ("lri", "m"), ("|", "l")]

def candidates(w):
    lw = w.lower()
    cands = set()
    for i, c in enumerate(lw):
        if c in CH:
            cands.add(lw[:i] + CH[c] + lw[i+1:])
    for a, b in PAIR:
        if a in lw:
            cands.add(lw.replace(a, b))
    for i in range(len(lw)):           # ta bort första/sista tecken (sväll-OCR)
        if i == 0 or i == len(lw) - 1:
            cands.add(lw[:i] + lw[i+1:])
    for i in range(len(lw) - 1):       # byt plats på grannar
        if lw[i] != lw[i+1]:
            cands.add(lw[:i] + lw[i+1] + lw[i] + lw[i+2:])
    c = {c for c in cands if c in DICT and abs(len(c) - len(lw)) <= 1}
    # frekvens-guard: fixen måste vara väsentligt vanligare än skrivfelet
    return {c for c in c if book_freq[c] > 2 * book_freq[lw]}

def best_fix(w):
    lw = w.lower()
    if lw in DICT:
        return None
    if len(lw) < 3 or not lw.isalpha():
        return None
    cands = candidates(w)
    if not cands:
        return None
    return max(cands, key=lambda c: (book_freq[c], len(c) == len(lw)))

def fix_page(txt, pageno):
    lines = txt.splitlines()
    out_lines = []
    fixes = Counter()
    for line in lines:
        s = line.strip()
        letters = sum(1 for c in s if c.isalpha())
        # skräprad: kort + mest symboler
        if s and len(s) <= 14 and letters / max(1, len(s)) < 0.55:
            continue
        def repl(m):
            w = m.group(0)
            f = best_fix(w)
            if f is None:
                return w
            fixes[(w.lower(), f)] += 1
            # bevara stor bokstav om original börjar med versal och fix också är 'riktigt ord'
            if w[0].isupper() and f.capitalize() in DICT or (w[0].isupper() and w.lower() != f):
                return f.capitalize()
            return f
        # versal-token (AI/AT/Al) korrigeras globalt
        if re.fullmatch(r"A[TlI]", s.strip()):
            fixes[(s.strip(), "AI")] += 1
            out_lines.append("AI")
            continue
        out_lines.append(re.sub(r"[A-Za-zÅÄÖåäö]{3,}", repl, line))
    return "\n".join(out_lines).rstrip() + "\n", fixes

allfix = Counter()
for idx in sorted(pages):
    fixed, fx = fix_page(pages[idx], idx)
    open(os.path.join(OUT, f"{idx:03d}.txt"), "w", encoding="utf-8").write(fixed)
    allfix.update(fx)

top = allfix.most_common(20)
print(f"KLART: {sum(allfix.values())} korrigeringar på {len(pages)} sidor")
print("Topp:", ", ".join(f"{a}->{b}({n})" for (a, b), n in top))
