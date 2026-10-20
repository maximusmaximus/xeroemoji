#!/usr/bin/env python3
"""Build demos/emoji-map.json from qc/coverage.csv (Unicode emoji-test 18.0) and the files in svg/.

Key   = the emoji's codepoints in lowercase hex, joined by '-', with every FE0F removed
        (so text with or without variation selectors finds the same entry).
Value = [file, emoji, name, group, subgroup, order]; file is the base filename in svg/ and png/ (no extension);
        order is the emoji-test 18.0 position (JS sorts number-like keys such as '2764' first, so sort by it).
File names drop FE0F (KEEP_FE0F is empty; the 4 former exceptions were renamed 2026-10-19).
Usage: python3 tools/build_emoji_map.py   (run from the repo root)"""
import csv,json,os,sys
KEEP_FE0F=set()   # none since 2026-10-19 (Max: all filenames drop FE0F)
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
svgs={f[:-4] for f in os.listdir(f'{root}/svg') if f.endswith('.svg')}
out={}
for r in csv.DictReader(open(f'{root}/qc/coverage.csv',encoding='utf-8')):
    full='-'.join(x.lower() for x in r['sequence'].split())
    key=full.replace('-fe0f','').replace('fe0f-','')
    f=full if full in KEEP_FE0F else key
    if f not in svgs: sys.exit(f'missing file for {r["sequence"]} ({f}.svg)')
    out[key]=[f,r['emoji'],r['name'],r['group'],r['subgroup'],len(out)]
assert len(out)==len(svgs)==len({v[0] for v in out.values()}),(len(out),len(svgs))
json.dump(out,open(f'{root}/demos/emoji-map.json','w',encoding='utf-8'),ensure_ascii=False,separators=(',',':'))
print(len(out),'emoji -> demos/emoji-map.json')
