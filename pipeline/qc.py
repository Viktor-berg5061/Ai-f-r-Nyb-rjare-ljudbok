#!/usr/bin/env python3
"""QC: verify every page's text + sync alignment for sanity, before deploy."""
import json, os, glob, statistics

def flat(paras):
    return [w for p in paras for w in p.split()]

pages = json.load(open('pages_clean.json'))
issues = []
durs = []
for p in pages:
    o = p['order']
    data = json.load(open(f'app/data/pages/{o:03d}.json'))
    paras = data['paras']
    words = data['words']
    flat_tokens = flat(paras)
    # text length
    tl = sum(len(x) for x in paras)
    # word count match
    if len(words) != len(flat_tokens):
        issues.append((o, 'WORD_COUNT_MISMATCH', len(words), len(flat_tokens)))
    # duration sanity
    if words:
        dur = words[-1]['e']
        durs.append(dur)
        if dur <= 0:
            issues.append((o, 'ZERO_DURATION', dur, None))
        if len(words) < 8 and tl > 120:
            issues.append((o, 'TL?' , len(words), tl))
    else:
        if tl > 0:
            issues.append((o, 'NO_WORDS_BUT_TEXT', tl, None))

print('pages checked:', len(pages))
print('avg page duration (s):', round(statistics.mean(durs),1) if durs else 0)
print('with content:', sum(1 for p in pages if p['text_len']>60), '/ 179')
print('ISSUES:', len(issues))
for it in issues:
    print(' ', it)

# sample a spread of pages text (formerly-garbled + random) to eyeball
print('\n=== SAMPLE TEXT (first 150 chars) ===')
for o in [40, 77, 104, 107, 145, 172]:
    for p in pages:
        if p['order'] == o:
            print(f'--- order {o} ---')
            print('\n'.join(p['paras'])[:150])
            break
