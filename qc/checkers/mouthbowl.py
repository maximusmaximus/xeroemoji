"""Crescent ('smile-bowl') mouth: detection + the shared bowl gradient (Max 2026-10-17 16:43 PT).
The mouth = a BOWL path (open arc between the two pointed corners, closed by the straight chord; gradient fill) drawn
immediately before a CRESCENT path that starts at the same corner point (solid fill, Z-closed, the pointed smile line)."""
import re
PATH=re.compile(r'<path\b[^>]*?/>')
def _d(tag):
    m=re.search(r'\bd="([^"]+)"',tag); return m.group(1) if m else ''
def _start(d):
    m=re.match(r'\s*M\s*([-\d.]+)[ ,]([-\d.]+)',d); return (m.group(1),m.group(2)) if m else None
def find(svg):
    """-> list of (bowl_match, crescent_match) pairs"""
    ps=list(PATH.finditer(svg)); out=[]
    for a,b in zip(ps,ps[1:]):
        if svg[a.end():b.start()].strip(): continue
        ta,tb=a.group(0),b.group(0); da,db=_d(ta),_d(tb)
        if not da or not db or 'url(#' not in ta: continue
        if da.rstrip().endswith(('Z','z')) or not db.rstrip().endswith(('Z','z')): continue
        if _start(da) is None or _start(da)!=_start(db): continue
        fb=re.search(r'\bfill="([^"]+)"',tb)
        if not fb or fb.group(1).startswith('url('): continue
        out.append((a,b))
    return out

# ---- the shared bowl gradient -------------------------------------------------------------------------------------
# Head-art mouth bowls (gradient id families of Max's original head art): person/child 116, man 128, woman/girl 122,
# boy 110, pilot astronaut-woman and health-worker heads. Other crescent pairs (eyes of 😅, cheek details) are not mouths.
MOUTHFAM=('template6Artboard128copy12_','template6Artboard162_','template6Artboard155_','template6Artboard128copy6_',
          'template10Artboard828_','template10Artboard833_')
# Offsets run from the ARC side of the bowl (bottom of the mouth, under the crescent) to the CHORD (top lip line).
# The bottom stops equal the crescent colour at full opacity, so the crescent's inner edge disappears into the bowl
# (no hard line); it then fades up through a warm mouth-interior tone to a light top so the chord edge stays crisp.
STOPS={'ink':[(0,'#000000',1),(.26,'#1a0806',.95),(.6,'#7a2a1c',.6),(.88,'#ffffff',.2),(1,'#ffffff',.34)],
       'red':[(0,'#ff0000',1),(.24,'#ff0000',.9),(.52,'#ff7a7a',.45),(.78,'#ffffff',.85),(1,'#ffffff',.95)]}
MARK='data-mouthbowl="1"'
def gid(kind,arc_low): return f'mbowl-{kind}-{"a" if arc_low else "r"}'
def gdef(kind,arc_low):
    y1,y2=(0,1) if arc_low else (1,0)
    st=''.join(f'<stop offset="{o}" stop-color="{c}" stop-opacity="{a}"/>' for o,c,a in STOPS[kind])
    return f'<linearGradient id="{gid(kind,arc_low)}" x1="0.5" y1="{y1}" x2="0.5" y2="{y2}">{st}</linearGradient>'
def _arc_low(d):
    nums=[float(v) for v in re.findall(r'-?\d+(?:\.\d+)?',d)]
    ys=nums[1::2]; y0=ys[0]
    return (min(ys)<y0) if abs(min(ys)-y0)>abs(max(ys)-y0) else False
def pairs(svg):
    out=[]
    for a,b in find(svg):
        g=re.search(r'url\(#([^)]+)\)',a.group(0)).group(1)
        if g.startswith(MOUTHFAM) or g.startswith('mbowl-'): out.append((a,b))
    return out
HIDDEN='data-mouthbowl="hidden"'
def _R(svg):
    import io,cairosvg,numpy as np
    from PIL import Image
    return np.asarray(Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(),output_width=512,output_height=512))).convert('RGBA')).astype(int)
def crescent_visibility(svg,b):
    """fraction of the crescent that is actually visible in the final art (1.0 = nothing drawn over it).
    Compares the crescent's footprint in the full file against the file cut off right after the crescent."""
    import numpy as np
    t=re.sub(r'fill="[^"]+"','fill="#00ff01"',b.group(0),count=1)
    pre=svg[:b.start()]; dep=len(re.findall(r'<g\b(?![^>]*/>)',pre))-pre.count('</g>'); tail='</g>'*dep+'</svg>'
    m=lambda a,c:int((np.abs(a-c).max(2)>40).sum())
    e=m(_R(pre+t+tail),_R(pre+tail))
    return (m(_R(pre+t+svg[b.end():]),_R(pre+svg[b.end():]))/e) if e else 0.0
def apply(svg,check_hidden=True,min_vis=0.6):
    """give every crescent-mouth bowl the shared gradient (idempotent). Returns (svg, n_mouths_changed).
    A mouth whose crescent is covered by other art (helmet visor, veil, beard, hood, a 🙅 hand-made mouth, a family
    member drawn over another) is left byte-for-byte as it was: recolouring a bowl nobody can see the crescent of
    would only add a stray smudge."""
    ps=pairs(svg); need={}; out=[]; last=0; n=0
    for a,b in ps:
        t=a.group(0)
        if HIDDEN in t: out.append(svg[last:a.start()]+t); last=a.end(); continue
        if MARK not in t and check_hidden and crescent_visibility(svg,b)<min_vis:
            out.append(svg[last:a.start()]+t); last=a.end(); continue
        fb=re.search(r'\bfill="([^"]+)"',b.group(0)).group(1).lower()
        kind='red' if fb in ('#ff0000','red') else 'ink'
        lo=_arc_low(re.search(r'\bd="([^"]+)"',t).group(1)); need[gid(kind,lo)]=gdef(kind,lo)
        t=re.sub(r'\s*fill-opacity="[\d.]+"','',t); t=re.sub(r'fill="url\(#[^)]+\)"',f'fill="url(#{gid(kind,lo)})"',t)
        if MARK not in t: t=t.replace('<path ',f'<path {MARK} ',1)
        out.append(svg[last:a.start()]+t); last=a.end(); n+=1
    svg=''.join(out)+svg[last:]
    add=''.join(v for k,v in need.items() if f'id="{k}"' not in svg)
    if add: svg=svg.replace('</defs>',add+'</defs>',1)
    return svg,n
