#!/usr/bin/env python3
"""Hat-fit check (standing rule for People batches): headwear must fit the head.

For an SVG whose head art is wrapped in <g data-headart="1"> and whose headwear is in <g data-hat="1">, with the hat
band line marked by <path data-band="1">:
  head_visible = pixels that change when the head-art group is removed (head, hair, ears seen through/around the hat)
  band_y       = pixel row of the band line (found by stroking the marker and diffing)
  violation    = head_visible pixels above band_y - TOL  (i.e. head/hair poking out above the crown or beside it
                 above the band). Hair below the band (sides/back) is allowed.
Files with data-hat but no band marker fall back to the lowest hat pixel in the head-centre column.
Usage: hatfit.py file.svg [...]   -> prints one line per file, exit 1 if any violation.
"""
import sys,re,io
import numpy as np, cairosvg
from PIL import Image
from scipy import ndimage
SZ=512; TOL=3; MINPX=6

def render(svg):
    return np.asarray(Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(),output_width=SZ,output_height=SZ))).convert('RGBA')).astype(int)

def drop_group(svg,attr):
    i=svg.find(f'<g {attr}'); 
    if i<0: i=svg.find(attr); i=svg.rfind('<g',0,i)
    if i<0: return None
    depth=0; j=i
    for m in re.finditer(r'<g\b[^>]*?(/?)>|</g>',svg[i:]):
        t=m.group(0)
        if t.startswith('</'): depth-=1
        elif not t.endswith('/>'): depth+=1
        if depth==0: j=i+m.end(); break
    return svg[:i]+svg[j:]

def diff(a,b): return (np.abs(a-b).max(axis=2)>24)

def check_svg(svg):
    if 'data-hat' not in svg: return None
    full=render(svg); nohead=drop_group(svg,'data-headart="1"')
    if nohead is None: return {'error':'no data-headart marker'}
    head=diff(full,render(nohead))
    head=ndimage.binary_opening(head,iterations=1)
    if 'data-band' in svg:
        sb=re.sub(r'(<path data-band="1"[^>]*?)stroke="none"',r'\1stroke="#ff00ff" stroke-width="2"',svg)
        rows=np.where(diff(full,render(sb)).any(axis=1))[0]
        band=int(np.median(rows)) if len(rows) else None
    else: band=None
    if band is None:
        hat=diff(full,render(drop_group(svg,'data-hat="1"')))
        ys,xs=np.where(hat); cx=int(np.median(xs)); col=np.where(hat[:,cx-3:cx+4].any(axis=1))[0]
        band=int(col.max())
    v=head.copy(); v[band-TOL:,:]=False
    lab,n=ndimage.label(v); sizes=ndimage.sum(v,lab,range(1,n+1)) if n else []
    bad=int(sum(s for s in sizes if s>=MINPX))
    ys,xs=np.where(v)
    return {'band_px':band,'viol_px':bad,'where':(f'x{xs.min()}-{xs.max()} y{ys.min()}-{ys.max()}' if bad else '')}

def check_file(p): return check_svg(open(p).read())

if __name__=='__main__':
    fails=0
    for p in sys.argv[1:]:
        r=check_file(p)
        if r is None: continue
        ok=('error' not in r) and r['viol_px']==0
        fails+=not ok
        print(('OK  ' if ok else 'FAIL'),p,r)
    print('hatfit fails:',fails); sys.exit(1 if fails else 0)
