#!/usr/bin/env python3
"""Generate 4 Swedish male voice probes from edge-tts sv-SE-MattiasNeural
with neural-network pitch/rate variation (NOT ffmpeg resample — that destroys
phonemes). Verifies each output is Swedish via faster-whisper, then converts to
Opus for Telegram voice bubbles.
"""
import subprocess, os, sys, glob, json

EDGE = "/home/agentops/.hermes/hermes-agent/venv/bin/edge-tts"
WHISPER = "/home/agentops/venv-stt/whisper_cli.py"  # adjust if different
OUT = "/home/agentops/bok-projekt/probes"
os.makedirs(OUT, exist_ok=True)

# A book-appropriate Swedish text (from the actual book theme, not the deepfake text)
TEXT = (
    "Kapitel ett. Artificiell intelligens. "
    "Du har säkert hört talas om AI, men vad betyder det egentligen? "
    "Vi människor lär oss genom att se, höra och läsa. "
    "På samma sätt kan datorer nu lära sig mönster. "
    "Från 1950-talets första försök till dagens neutrala nätverk. "
    "I den här boken går vi igenom grunderna."
    "Häng med, och vi börjar i början."
)

# (label, pitch_hz, rate, description)
probes = [
    ("1-naturlig",  "+0Hz",  "+0%", "MattiasNeural baslinje (korrekt svenska, neutral uppläsare)"),
    ("2-mork",      "-20Hz", "-8%", "Mörkare, lugnare — klassisk ljudboks-berättar"),
    ("3-djup",      "-35Hz", "-12%","Djup och dramatisk, dokumentär-berättar"),
    ("4-bas",       "-50Hz", "-10%","Riktigt djup bas, auktoritär"),
]

# Whisper binary check
W_bin = None
cands = [
    "/home/agentops/venv-stt/bin/whisper_cli.py",
    "/home/agentops/venv-stt/whisper_cli.py",
    "/home/agentops/.hermes/hermes-agent/venv/bin/faster-whisper",
]
for c in cands:
    if os.path.exists(c):
        W_bin = c
        break
# find any whisper cli in venv-stt
if not W_bin:
    for p in glob.glob("/home/agentops/venv-stt/**/*whisper*", recursive=True):
        if os.path.isfile(p):
            W_bin = p
            break

results = []
for label, pitch, rate, desc in probes:
    mp3 = os.path.join(OUT, f"prov-{label}.mp3")
    ogg = os.path.join(OUT, f"prov-{label}.ogg")
    cmd = [EDGE, "--voice", "sv-SE-MattiasNeural", "--pitch", pitch,
           "--rate", rate, "--text", TEXT, "--write-media", mp3]
    print("="*60)
    print(f"### Probe {label}  [{desc}]")
    print("CMD:", " ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        print("  EDGE FAIL:", r.stderr[-300:])
        continue
    size = os.path.getsize(mp3)
    print(f"  mp3: {size} bytes")
    # convert to ogg
    subprocess.run(["ffmpeg", "-y", "-i", mp3, "-c:a", "libopus", "-ac", "1",
                    "-b:a", "128k", ogg], capture_output=True)
    # whisper verify (if we have it)
    lang = "?"
    if W_bin:
        try:
            rr = subprocess.run(["python3", W_bin, ogg, "--language", "sv"],
                                capture_output=True, text=True, timeout=180)
            txt = rr.stdout.strip()
            # quickly detect language by checking for swedish characters/words
            sw_markers = sum(txt.lower().count(k) for k in
                             ["är", "och", "det", "som", "människor", "den här", "kapitel", "genom", "boken"])
            non_markers = sum(txt.lower().count(k) for k in
                              ["und", "der", "die", "auf", "ist", "och ", "det är", "the"])
            print("  whisper text (first 120):", txt[:120].replace("\n"," "))
            lang = f"sv-marque={sw_markers} non={non_markers}"
        except Exception as e:
            print("  whisper err:", e)
    else:
        print("  (no whisper binary found)")
    results.append({"label": label, "ogg": ogg, "desc": desc, "size": size,
                    "whisper": lang})
    print("  OK:", ogg)

print("\n\n==== SUMMARY ====")
for r in results:
    print(f"{r['label']}: {os.path.getsize(r['ogg'])} bytes ogg | whisper={r['whisper']}")
