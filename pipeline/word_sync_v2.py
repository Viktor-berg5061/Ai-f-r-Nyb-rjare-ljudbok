#!/usr/bin/env python3
"""Word-level sync v2 for clean audio (audio_clean). faster-whisper word timestamps.
Output per page: audio_clean/NNN_sIDX.sync.json  [{w,s,e}]
"""
import json, os, glob, sys

def main():
    from faster_whisper import WhisperModel
    m = WhisperModel('base', device='cpu', compute_type='int8')
    files = sorted(glob.glob('audio_clean/*.mp3'))
    only = sys.argv[1:] if len(sys.argv) > 1 else None
    todo = 0; skip = 0
    for f in files:
        base = os.path.splitext(f)[0]
        syncf = base + '.sync.json'
        if only and not any(s in os.path.basename(f) for s in only):
            continue
        if os.path.exists(syncf):
            skip += 1; continue
        if os.path.getsize(f) < 1000:
            open(syncf, 'w').write('[]'); todo += 1; continue
        try:
            segs, info = m.transcribe(f, language='sv', word_timestamps=True)
            words = []
            for seg in segs:
                for w in (seg.words or []):
                    words.append({'w': w.word.strip(), 's': round(w.start, 3), 'e': round(w.end, 3)})
            json.dump(words, open(syncf, 'w'), ensure_ascii=False)
            print(f'{os.path.basename(f)} -> {len(words)} words', flush=True)
            todo += 1
        except Exception as e:
            print(f'ERR {f}: {e}', flush=True)
    print(f'WORD-SYNC-V2 DONE processed={todo} skipped={skip}', flush=True)

if __name__ == '__main__':
    main()
