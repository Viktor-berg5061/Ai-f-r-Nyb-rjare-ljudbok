#!/usr/bin/env python3
"""Word-level sync for each page. Transcribes the page's MP3 with faster-whisper
(word_timestamps=True), maps each word to its start time, and writes a JSON file
next to the audio. The reader highlights the current word.

Alignment detail: Whisper words are appended into segments. We collect (word, start,
end) and save under audio/<order>_s<idx>.sync.json.
"""
import json, os, glob, sys

def main():
    from faster_whisper import WhisperModel
    m = WhisperModel('base', device='cpu', compute_type='int8')
    files = sorted(glob.glob('audio/*.mp3'))
    only = sys.argv[1:] if len(sys.argv) > 1 else None
    todo = 0
    for f in files:
        base = os.path.splitext(f)[0]
        syncf = base + '.sync.json'
        if only:
            match = any(s in os.path.basename(f) for s in only)
            if not match:
                continue
        if os.path.exists(syncf):
            continue
        if os.path.getsize(f) < 1000:
            open(syncf, 'w').write('[]')
            continue
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
    print(f'WORD-SYNC DONE, {todo} processed', flush=True)

if __name__ == '__main__':
    main()
