#!/bin/bash
# Build pipeline v2: waits for refine (pid), then rebuilds clean text, audio,
# word-sync, text pages, TEXT.pdf and stages docs/. Does NOT push.
cd /home/agentops/bok-projekt

echo "[$(date +%H:%M:%S)] waiting for refine to settle (refine OR draft covers 179) ..."
N=$(python3 -c "
import os
c=0
for i in range(1,180):
    ok = os.path.exists(f'ocr_clean/{i:03d}.txt') and os.path.getsize(f'ocr_clean/{i:03d}.txt')>=20
    d  = os.path.exists(f'ocr_vision/{i:03d}.txt') and os.path.getsize(f'ocr_vision/{i:03d}.txt')>=20
    if ok or d: c+=1
print(c)
")
echo "[$(date +%H:%M:%S)] refine+draft coverage: $N/179 -> build_clean_pages"
python3 build_clean_pages.py ocr_clean pages_clean.json

echo "[$(date +%H:%M:%S)] TTS workers start ..."
python3 tts_worker2.py 1 60 audio_clean &
python3 tts_worker2.py 61 120 audio_clean &
python3 tts_worker2.py 121 179 audio_clean &
wait
echo "[$(date +%H:%M:%S)] TTS DONE -> word sync"
python3 word_sync_v2.py

echo "[$(date +%H:%M:%S)] SYNC DONE -> build_text_v2 + pdf"
python3 build_text_v2.py
python3 build_textpdf_clean.py

echo "[$(date +%H:%M:%S)] PDF DONE -> stage docs/"
python3 stage_v2.py
echo "[$(date +%H:%M:%S)] PIPELINE BUILD COMPLETE"
