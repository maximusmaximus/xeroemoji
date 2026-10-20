#!/usr/bin/env python3
"""Copy the locked svg/ files to a staging dir for nanoemoji (never touches svg/).
- renames to nanoemoji's emoji_uXXXX_YYYY.svg convention
- duplicate id="..." definitions: later ones are renamed (browsers resolve url(#id) to the FIRST match,
  so rendering is unchanged), because picosvg rejects duplicate ids."""
import re, sys, pathlib, collections
src, dst = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]); dst.mkdir(parents=True, exist_ok=True)
fixed = 0
for f in sorted(src.glob('*.svg')):
    s = f.read_text(encoding='utf-8'); seen = collections.Counter()
    def ren(m):
        global fixed
        i = m.group(2); seen[i] += 1
        if seen[i] == 1: return m.group(0)
        fixed += 1; return f'{m.group(1)}{i}__dup{seen[i]}{m.group(3)}'
    s = re.sub(r'(\bid=")([^"]+)(")', ren, s)
    (dst / ('emoji_u' + f.stem.replace('-', '_') + '.svg')).write_text(s, encoding='utf-8')
print('staged', len(list(dst.glob('*.svg'))), 'svgs; duplicate ids renamed:', fixed)
