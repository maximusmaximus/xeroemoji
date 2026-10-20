"""Shared ground truth for the black line build and the x-ray test.
Works on the ORIGINAL colour SVG: assigns each paintable shape a stable id (document order),
decides which shapes are see-through (removed) or low-contrast shading (removed), and renders
an ownership (ID) map with a unique flat colour per shape, no anti-aliasing."""
import re,io,numpy as np,cairosvg
from lxml import etree
from PIL import Image
import os
R=os.environ.get('BL_SRC',os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','svg')).rstrip('/')+'/'
NS='{http://www.w3.org/2000/svg}'
SHAPES={NS+t for t in('path','circle','ellipse','rect','polygon','polyline','line')}
DEFS={NS+'clipPath',NS+'mask',NS+'defs',NS+'linearGradient',NS+'radialGradient',NS+'pattern'}
SHADE_CONTRAST=40   # max-channel mean RGB difference across a shape's boundary below which its edge is shading
def in_defs(el):
    p=el.getparent()
    while p is not None:
        if p.tag in DEFS: return True
        p=p.getparent()
    return False
def _lum(c):
    c=(c or '').strip().lower()
    if c in('white',): return 1.0
    if c in('black',): return 0.0
    m=re.fullmatch(r'#([0-9a-f]{3}|[0-9a-f]{6})',c)
    if not m: return 1.0
    h=m.group(1); h=''.join(x*2 for x in h) if len(h)==3 else h
    r,g,b=(int(h[i:i+2],16)/255 for i in(0,2,4)); return 0.2126*r+0.7152*g+0.0722*b
def eff_opacity(el):
    o=1.0; p=el
    while p is not None:   # all ancestors, through nested <svg> viewports (v6-final: hand drop shadows were missed)
        for k in('opacity','fill-opacity'):
            if p is el or k=='opacity':
                try: o*=float(p.get(k,'1'))
                except: pass
        st=p.get('style','')
        m=re.search(r'(?:^|;)\s*opacity\s*:\s*([\d.]+)',st)
        if m: o*=float(m.group(1))
        p=p.getparent()
    return o
def load(code):
    t=etree.parse(R+code+'.svg'); root=t.getroot()
    grads={}
    for g in root.iter(NS+'linearGradient',NS+'radialGradient'):
        ops=[float(x.get('stop-opacity','1')) for x in g.iter(NS+'stop')]
        grads[g.get('id')]=max(ops) if ops else 1
    shapes=[]; n=0
    for el in root.iter():
        if el.tag in SHAPES and not in_defs(el):
            el.set('data-sid',str(n)); n+=1
            # implicit black fill on a path made only of 2-point open segments has no area: it is a stroked line set
            if el.get('fill') is None and el.get('stroke') not in(None,'none') and el.tag==NS+'path' and \
               re.fullmatch(r'\s*(?:M\s*[-\d.]+[ ,]*[-\d.]+\s*L\s*[-\d.]+[ ,]*[-\d.]+\s*)+',el.get('d','')): el.set('fill','none')
            fill=el.get('fill','#000'); stroke=el.get('stroke','none')
            m=re.search(r'url\(#([^)]+)\)',fill)
            translucent=eff_opacity(el)<0.9 or (m is not None and grads.get(m.group(1),1)<0.9)
            if fill=='none' and stroke not in('none',None):   # line art: its own stroke opacity / gradient decides
                try: so=float(el.get('stroke-opacity','1'))
                except: so=1
                ms=re.search(r'url\(#([^)]+)\)',stroke or '')
                op=eff_opacity(el)*so
                if op<0.9 or (ms is not None and grads.get(ms.group(1),1)<0.9): translucent=True
                # a dark/mid-tone line at >=0.6 opacity is drawing (strings, mesh, cords), not a highlight
                if translucent and ms is None and op>=0.6 and _lum(stroke)<0.7: el.set('data-cand','1')
            if el.get('display')=='none' or el.get('visibility')=='hidden': translucent=True
            shapes.append(dict(sid=n-1,el=el,filled=fill!='none',stroked=stroke not in('none',None),translucent=translucent))
    st=_structural(code,t,shapes)
    for s in shapes:
        if s['sid'] in st: s['translucent']=False
        s['el'].attrib.pop('data-cand',None)
    return t,shapes
_STRUCT={}
def _structural(code,t,shapes):
    """semi-opaque (0.6-0.9) mid/dark lines that are DARKER than the paint beneath them are drawing (racket/cart
    mesh, parachute cords); lines lighter than what is under them are highlights (v6-final)"""
    key=(R,code)
    if key in _STRUCT: return _STRUCT[key]
    cand=[s for s in shapes if s['el'].get('data-cand')]
    res=set()
    if cand:
        import copy
        def sub(keep,opaque=False):
            r2=copy.deepcopy(t.getroot())
            for e in list(r2.iter()):
                sid=e.get('data-sid')
                if sid is not None and not keep(int(sid)): e.getparent().remove(e)
                elif sid is not None and opaque:
                    for k in('opacity','stroke-opacity','style'): e.attrib.pop(k,None)
            return render(etree.tostring(r2),256)
        tr={x['sid'] for x in shapes if x['translucent']}
        for s in cand:
            # paint beneath = everything drawn before it (transparent counts as white paper)
            u=sub(lambda i:i<s['sid'] and i not in tr).astype(float)/255
            lu=(0.2126*u[...,0]+0.7152*u[...,1]+0.0722*u[...,2])*u[...,3]+(1-u[...,3])
            m=sub(lambda i:i==s['sid'],True)[...,3]>=128
            if m.any() and _lum(s['el'].get('stroke'))<lu[m].mean()-0.05: res.add(s['sid'])
    _STRUCT[key]=res; return res
def _wrap(root,fit):
    g=etree.SubElement(root,NS+'g'); g.set('transform',f'translate(256 256) scale({fit}) translate(-256 -256)')
    for c in list(root):
        if c is not g and c.tag not in DEFS: g.append(c)
def idcol(i): i+=1; return '#%02x%02x%02x'%(i&255,(i>>8)&255,(i>>16)&255|0x80)
def id_svg(code,fit=1.0,drop=(),keephl=False,fill_strokes=False):
    t,sh=load(code); root=t.getroot(); root.set('shape-rendering','crispEdges')
    for s in sh:
        el=s['el']
        if (s['translucent'] and not keephl) or s['sid'] in drop: el.getparent().remove(el); continue
        c=idcol(s['sid'])
        if s['filled']: el.set('fill',c)
        if s['stroked']:
            if s['filled'] and not fill_strokes: el.set('stroke','none')
            elif s['filled']:   # validation mode: the stroke gets its own id so its inner edge is an id edge
                el.set('stroke','none'); cl=etree.fromstring(etree.tostring(el)); cl.set('fill','none'); cl.set('stroke',idcol(s['sid']+40000)); el.addnext(cl)
            else: el.set('stroke',c)
        for k in('opacity','fill-opacity','stroke-opacity','style','filter'): el.attrib.pop(k,None)
    for el in root.iter():
        if el.tag not in SHAPES and not in_defs(el) and el.tag!=NS+'mask':
            el.attrib.pop('opacity',None); el.attrib.pop('filter',None)
    _wrap(root,fit); return etree.tostring(root),sh
def color_svg(code,fit=1.0,drop=(),keephl=False):
    """actual colour artwork, minus removed layers, strokes of filled shapes removed (they are the source's own outline)"""
    t,sh=load(code); root=t.getroot()
    for s in sh:
        el=s['el']
        if (s['translucent'] and not keephl) or s['sid'] in drop: el.getparent().remove(el); continue
        if s['filled'] and s['stroked']: el.set('stroke','none')
    _wrap(root,fit); return etree.tostring(root)
def render(svg,size):
    return np.asarray(Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg,output_width=size,output_height=size))).convert('RGBA'))
def decode(a):
    """-1 transparent, -2 not an id colour (AA / unknown), else shape id"""
    r,g,b,al=[a[...,i].astype(np.int64) for i in range(4)]
    ok=(b&0x80)==0x80
    ids=r+(g<<8)+((b&0x7f)<<16)-1
    out=np.where(al==0,-1,np.where((al==255)&ok,ids,-2))
    return out
def shading(code,keephl=False,size=256):
    """ids of filled, interior shapes whose whole visible boundary is low-contrast in the colour render"""
    s,sh=id_svg(code,1.0,(),keephl); I=decode(render(s,size)); C=render(color_svg(code,1.0,(),keephl),size)[...,:3].astype(int)
    out=set(); fills={x['sid'] for x in sh if x['filled'] and not x['stroked'] or x['filled']}
    H,W=I.shape
    for sid in np.unique(I):
        if sid<0 or sid not in fills: continue
        m=I==sid
        if m.sum()<20: continue
        diffs=[];touch_bg=0;n=0
        for dy,dx in((0,2),(2,0),(0,-2),(-2,0)):
            sh2=np.roll(np.roll(m,dy,0),dx,1); nb=np.roll(np.roll(I,dy,0),dx,1)
            edge=m&(nb!=sid)
            # pixels just inside vs just outside along this direction
            ins=C[edge]; outc=np.roll(np.roll(C,dy,0),dx,1)[edge]; nbv=nb[edge]
            touch_bg+=(nbv==-1).sum(); n+=edge.sum()
            valid=nbv>=0
            if valid.any(): diffs.append(np.abs(ins[valid]-outc[valid]).max(1))
        if not n or not diffs: continue
        d=np.concatenate(diffs)
        if touch_bg/n<0.05 and len(d)>10 and np.percentile(d,90)<SHADE_CONTRAST: out.add(int(sid))
    return out
def full_color_svg(code,fit=1.0,drop=(),keephl=False):
    t,sh=load(code); root=t.getroot()
    for s in sh:
        if (s['translucent'] and not keephl) or s['sid'] in drop: s['el'].getparent().remove(s['el'])
    _wrap(root,fit); return etree.tostring(root)
MERGE_CONTRAST=60
def pair_contrast(code,keephl=False,size=256,I=None):
    """median local contrast (max-min over a 7px normal, max channel) of the actual colour render along each shape-pair boundary"""
    import collections
    if I is None:
        s,_=id_svg(code,1.0,(),keephl); I=decode(render(s,size))
    C=render(full_color_svg(code,1.0,(),keephl),I.shape[0])[...,:3].astype(int); H,W=I.shape
    P=collections.defaultdict(list)
    for dy,dx in((0,1),(1,0)):
        a=I[:H-dy,:W-dx]; b=I[dy:,dx:]
        ys,xs=np.nonzero((a!=b)&(a>=0)&(b>=0))
        offs=np.arange(-8,9)
        yy=np.clip(ys[:,None]+offs[None]*dy,0,H-1); xx=np.clip(xs[:,None]+offs[None]*dx,0,W-1)
        S=C[yy,xx]  # n,7,3
        con=(S.max(1)-S.min(1)).max(1)
        for k1,k2,c in zip(a[ys,xs],b[ys,xs],con): P[(min(k1,k2),max(k1,k2))].append(c)
    return {k:(len(v),float(np.median(v))) for k,v in P.items()}
MERGE_COLOR=70
def merges(code,keephl=False,size=256):
    """pairs whose shared boundary is low-contrast in the colour art AND whose region colours are alike
    (the second rule stops transitive chains like skin-band-visor-hair collapsing into one region)"""
    s,_=id_svg(code,1.0,(),keephl); I=decode(render(s,size))
    C=render(full_color_svg(code,1.0,(),keephl),size)[...,:3].astype(int)
    med={}
    def col(i):
        if i not in med:
            m=I==i; med[i]=np.median(C[m],axis=0) if m.any() else np.zeros(3)
        return med[i]
    out=[]
    for k,(n,m) in pair_contrast(code,keephl,size,I).items():
        if n>=8 and m<MERGE_CONTRAST and np.abs(col(k[0])-col(k[1])).max()<MERGE_COLOR: out.append(k)
    return out
