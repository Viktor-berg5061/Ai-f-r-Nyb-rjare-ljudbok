#!/usr/bin/env python3
"""Compress every generated MP3 to 48k mono for data-friendliness.
Fish outputs ~1.1MB/page; this halves size to ~0.5MB while keeping 48k mono
speech quality and Swedish as verified by Whisper.
"""
import glob, subprocess, os, sys

def main():
    only = sys.argv[1:] or None
    files = sorted(glob.glob('audio/*.mp3'))
    saved=0
    for f in files:
        name = os.path.basename(f)
        if only and not any(s in name for s in only):
            continue
        tmp = f + '.comp.mp3'
        subprocess.run(['ffmpeg','-y','-i',f,'-ac','1','-b:a','48k',tmp],capture_output=True)
        if os.path.exists(tmp) and os.path.getsize(tmp) > 0:
            orig=os.path.getsize(f); new=os.path.getsize(tmp)
            os.replace(tmp,f)   # replace in place; sync.json unaffected
            saved += orig-new
    print(f'compressed {len(files)} files, saved {saved/1024/1024:.1f} MB')

if __name__ == '__main__':
    main()
