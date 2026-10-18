# Pixel audit: do highlight pixels touch any stroke (outline ink or internal line)?
import re,io,sys,numpy as np,cairosvg
from PIL import Image
from scipy.ndimage import binary_dilation
INK=(0x24,0x16,0x0a)
HL=re.compile(r'<(path|ellipse|circle)\b[^>]*?(?:data-hl="1"|(?:fill|stroke)="#fff"[^>]*?opacity="0?\.(?:5|55|6|62|7|8)\d*")[^>]*?/>')
def r(svg): return np.array(Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(),output_width=512,output_height=512))).convert('RGBA')).astype(int)
def kill_hl(svg): return HL.sub(lambda m:m[0].replace('/>',' visibility="hidden"/>'),svg)
SHAPE=re.compile(r'<(path|ellipse|circle|rect|polygon|polyline|line)\b[^>]*?/>')
def outline_only(svg):
    i=svg.find('</defs>'); i=i+7 if i>=0 else svg.find('>',svg.find('<svg'))+1
    def f(m):
        e=m[0]
        if re.search(r'stroke="#24160a"',e) and m[1] in ('path','ellipse','circle'):
            return re.sub(r'fill="[^"]*"','fill="none"',e) if 'fill="' in e else e.replace('/>',' fill="none"/>')
        return e.replace('/>',' visibility="hidden"/>')
    return svg[:i]+SHAPE.sub(f,svg[i:])
def audit(svg,dil=2):
    a=r(svg); b=r(kill_hl(svg))
    hl=(np.abs(a[...,:3]-b[...,:3]).sum(2)>24)&(b[...,3]>200)
    ink=(np.abs(b[...,:3]-np.array(INK)).sum(2)<60)&(b[...,3]>200)
    # EDGE rule: only outline strokes count (elements stroked in INK), drawn stroke-only; internal lines/markings/ink dots excluded
    # outline mask rendered IN PLACE (every element keeps all of its ancestor transforms): outline elements stroke-only,
    # everything else hidden. v1 re-rendered the outline elements under only the leading <g> transforms after </defs>, so
    # outlines inside nested part groups (bust, head, hand groups) landed in the wrong frame (the pilot 1f645 read 0).
    om=r(outline_only(svg))[...,3]>100
    st=binary_dilation(ink&om,iterations=dil)
    return int((hl&st).sum()), int(hl.sum())
    # internal lines: render only stroked non-ink, non-hl open lines (opacity .8 inner lines + tube-less strokes)
    lines=re.findall(r'<path d="[^"]*" fill="none" stroke="(?!#fff)[^"]*" stroke-width="[\d.]+" stroke-linecap="round" opacity="0?\.8"/>',svg)
    s2=svg.split('</defs>')[0]+'</defs>'
    head=re.search(r'</defs>((?:<g [^>]*>)+)',svg)[1]
    li=r(s2+head+''.join(lines)+'</g>'*head.count('<g')+'</svg>')[...,3]>100
    st=binary_dilation(ink|li,iterations=dil)
    return int((hl&st).sum()), int(hl.sum())
if __name__=='__main__':
    for p in sys.argv[1:]: print(p.split('/')[-1],*audit(open(p).read()))
# ---- known exceptions (qc/hlaudit-known-exceptions.json): locked approved art with hits found by the fixed mask (2026-10-18) ----
def known_exception(name,svg):
    """True if this file is a recorded exception AND unchanged (svg md5 matches); gates count its hits as known, not failures"""
    import json,hashlib,os
    d=os.environ.get('XEROQC_SET')
    if not d:   # set root: nearest parent of this file holding svg/ and qc/ (work/ in the workspace, qc/checkers/ in the repo)
        d=os.path.dirname(os.path.abspath(__file__))
        while d!=os.path.dirname(d) and not (os.path.isdir(d+'/svg') and os.path.isdir(d+'/qc')): d=os.path.dirname(d)
    p=d+'/qc/hlaudit-known-exceptions.json'
    if not os.path.exists(p): return False
    e=json.load(open(p))['files'].get(name)
    return bool(e) and e['svg_md5']==hashlib.md5(svg.encode()).hexdigest()
