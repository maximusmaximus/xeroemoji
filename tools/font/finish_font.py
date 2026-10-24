#!/usr/bin/env python3
"""(The font stays CC BY-NC 4.0 + commercial license on purpose; only the SVG/PNG artwork is CC BY 4.0. See LICENSING.md.)
Finish the nanoemoji output: FE0F-aware ligatures, XeroEmoji name table (CC-BY-NC-4.0), TTF + WOFF2 in fonts/.
Usage: finish_font.py build/XeroEmoji.ttf fonts/ tools/ci/emoji-test-18.0.txt
nanoemoji keys glyphs by the FE0F-less file names; real text usually carries FE0F (e.g. 2764 FE0F 200D 1F525),
so we add a blank zero-width FE0F glyph and a ligature for every fully-qualified emoji-test sequence."""
import sys, pathlib
from fontTools.ttLib import TTFont
src, out = sys.argv[1], pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
test = sys.argv[3]
from fontTools.ttLib.tables._g_l_y_f import Glyph
f = TTFont(src); n = f['name']
order = f.getGlyphOrder(); cmap = f.getBestCmap()
def gname(cp):
    if cp == 0xFE0F: return 'g_fe0f'
    return cmap.get(cp)
if 'g_fe0f' not in order:   # always map FE0F to our own blank zero-width glyph
    f.setGlyphOrder(order + ['g_fe0f']); f['glyf'].glyphs['g_fe0f'] = Glyph(); f['glyf'].glyphOrder = f.getGlyphOrder()
    f['hmtx'].metrics['g_fe0f'] = (0, 0)
    for t in f['cmap'].tables:
        if t.isUnicode(): t.cmap[0xFE0F] = 'g_fe0f'
    f['maxp'].numGlyphs = len(f.getGlyphOrder())
from fontTools.ttLib.tables import otTables as ot
cmap = f.getBestCmap(); subs = []
for lk in f['GSUB'].table.LookupList.Lookup:
    if lk.LookupType == 4: subs += lk.SubTable
known = {}
for st in subs:
    for first, ligs in st.ligatures.items():
        for lg in ligs: known[(first, *lg.Component)] = (st, lg.LigGlyph)
for cp in list(cmap):
    pass
extra = []
for l in open(test, encoding='utf-8'):
    if '; fully-qualified' not in l: continue
    cps = [int(c, 16) for c in l.split(';')[0].split()]
    if 0xFE0F not in cps or len(cps) < 2: continue
    base = tuple(cmap.get(c) for c in cps if c != 0xFE0F); full = [gname(c) for c in cps]
    if None in base or None in full: continue
    lig = known.get(base) if len(base) > 1 else None
    if len(base) == 1: continue          # e.g. 2764 FE0F: base glyph + blank FE0F already renders
    if not lig: continue
    st, target = lig; L = ot.Ligature(); L.Component = full[1:]; L.LigGlyph = target; L.CompCount = len(full)
    st.ligatures.setdefault(full[0], []).append(L); extra.append(target)
for st in subs:
    for k in st.ligatures: st.ligatures[k].sort(key=lambda lg: -len(lg.Component))
print('FE0F ligatures added:', len(extra))
VER = '1.1.0'
names = {0: 'Artwork © 2016-2026 Max Infeld. Xero Emoji.',
         1: 'XeroEmoji', 2: 'Regular', 3: f'XeroEmoji-{VER}', 4: 'XeroEmoji', 5: f'Version {VER}', 6: 'XeroEmoji-Regular',
         9: 'Max Infeld', 11: 'https://github.com/maximusmaximus/xeroemoji', 12: 'https://github.com/maximusmaximus',
         13: 'CC-BY-NC-4.0. Licensed under Creative Commons Attribution-NonCommercial 4.0 International. '
             'Commercial use needs a commercial license: https://github.com/maximusmaximus/xeroemoji/blob/main/COMMERCIAL-LICENSE.md',
         14: 'https://creativecommons.org/licenses/by-nc/4.0/'}
n.names = [r for r in n.names if r.nameID not in names]
for i, v in names.items(): n.setName(v, i, 3, 1, 0x409)
f['head'].fontRevision = 1.1
f.save(out / 'XeroEmoji-COLRv1.ttf')
f = TTFont(out / 'XeroEmoji-COLRv1.ttf'); f.flavor = 'woff2'; f.save(out / 'XeroEmoji-COLRv1.woff2')
for p in sorted(out.glob('XeroEmoji-COLRv1.*')): print(p.name, p.stat().st_size)
