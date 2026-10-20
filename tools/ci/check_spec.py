#!/usr/bin/env python3
"""Validate svg/ and png/ file names against Unicode emoji-test.txt 18.0 (fully-qualified, FE0F dropped).
Fails on missing, extra, malformed or non-lowercase names, and on emoji-map.json drift."""
import json, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parents[2]
test = ROOT / 'tools/ci/emoji-test-18.0.txt'
assert '# Version: 18.0' in test.read_text(encoding='utf-8')[:400] or 'Emoji Version 18.0' in test.read_text(encoding='utf-8'), 'not emoji-test 18.0'
want = {}
for l in test.read_text(encoding='utf-8').splitlines():
    if '; fully-qualified' in l:
        cps = l.split(';')[0].split(); want['-'.join(c.lower() for c in cps if c.upper() != 'FE0F')] = l.split('#', 1)[1].strip()
errs = []
NAME = re.compile(r'^[0-9a-f]{4,6}(-[0-9a-f]{4,6})*$')
for d in ('svg', 'png'):
    have = {p.stem for p in (ROOT / d).glob(f'*.{d}')}
    errs += [f'{d}: bad file name {h}' for h in have if not NAME.match(h)]
    errs += [f'{d}: missing {k} ({want[k]})' for k in sorted(set(want) - have)]
    errs += [f'{d}: not in emoji-test 18.0: {k}' for k in sorted(have - set(want))]
for mp in ('demos/emoji-map.json', 'packages/python/xeroemoji/emoji-map.json'):
    m = json.loads((ROOT / mp).read_text(encoding='utf-8'))
    if set(m) != set(want): errs.append(f'{mp}: keys differ from emoji-test 18.0 ({len(m)} vs {len(want)})')
print(f'emoji-test 18.0 fully-qualified: {len(want)}; problems: {len(errs)}')
for e in errs[:50]: print('  ' + e)
sys.exit(1 if errs else 0)
