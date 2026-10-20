#!/usr/bin/env python3
"""Coverage check: every svg/ file name (and its fully-qualified emoji-test.txt form with FE0F) must shape
to exactly one COLR glyph. Usage: verify_font.py fonts/XeroEmoji-COLRv1.ttf svg/ [emoji-test.txt]"""
import sys, pathlib, uharfbuzz as hb
from fontTools.ttLib import TTFont
font_path, svgdir = sys.argv[1], pathlib.Path(sys.argv[2])
tt = TTFont(font_path); colr = {r.BaseGlyph for r in tt['COLR'].table.BaseGlyphList.BaseGlyphPaintRecord}
order = tt.getGlyphOrder()
face = hb.Face(open(font_path, 'rb').read()); font = hb.Font(face)
def one(cps):
    b = hb.Buffer(); b.add_codepoints(cps); b.guess_segment_properties(); hb.shape(font, b, {})
    g = [order[i.codepoint] for i in b.glyph_infos]
    g = [x for x in g if x not in ('g_fe0f', 'uniFE0F', 'space')]   # FE0F: blank glyph, or HarfBuzz's invisible default-ignorable
    return len(g) == 1 and g[0] in colr
seqs = [[int(c, 16) for c in p.stem.split('-')] for p in svgdir.glob('*.svg')]
ok = sum(one(s) for s in seqs); bad = [s for s in seqs if not one(s)]
print(f'COLR glyphs: {len(colr)}; svg sequences shaping to one color glyph: {ok}/{len(seqs)}')
if len(sys.argv) > 3:
    fq = [l.split(';')[0].split() for l in open(sys.argv[3], encoding='utf-8') if '; fully-qualified' in l]
    fq = [[int(c, 16) for c in s] for s in fq]; okq = sum(one(s) for s in fq)
    print(f'emoji-test.txt fully-qualified sequences rendered: {okq}/{len(fq)}')
for s in bad[:20]: print('MISSING', '-'.join('%x' % c for c in s))
sys.exit(1 if bad else 0)
