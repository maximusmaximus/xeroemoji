import math
"""Shared RULES (not geometry) for both engines: config, source loading, layer rules, thin-stroke rule.
Geometry is computed independently by engine_raster (render + trace) and engine_vector (skia-pathops)."""
import os,sys,json,re,math
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import gt
from svgelements import Matrix
NS=gt.NS
DEFAULT=dict(inner=6.0,outer=15.0,inner72=7.5,outer72=18.8,fit=0.99,fit72=0.97,
             thin_factor=2.0,      # stroke-only shapes thinner than thin_factor*outer stay single black lines
             thin_weight=10.0,     # consistent black weight for thin wires (px @512); never wider than the source footprint
             gap=6.0,
             band_min=3, band_len=80.0,   # banded body: >=3 parallel bands, each >=80px long
             small_div=12.0, small_min=4.0,   # small dense wires: weight <= extent/12 (>=4px)
             band_overlap=0.8,     # thin wire whose centreline runs >80% alongside other cores = part of a banded body              # white break (px @512) where a back thin strand passes under a front one
             min_thin=None,max_thin=None)  # thin line weight clamp; default [inner, outer]
def config(path=None,**kw):
    c=dict(DEFAULT)
    if path: c.update(json.load(open(path)))
    c.update({k:v for k,v in kw.items() if v is not None})
    c['min_thin']=c['min_thin'] or c['inner']; c['max_thin']=c['max_thin'] or c['outer']
    return c
def set_source(d): gt.R=d.rstrip('/')+'/'
def _viewport(sv):
    """implicit transform of a NESTED <svg x y width height viewBox> (preserveAspectRatio xMidYMid meet)"""
    vb=sv.get('viewBox')
    f=lambda k,d=0: float(re.sub('[a-z%]+','',sv.get(k,str(d))) or d)
    x,y=f('x'),f('y')
    if not vb: return f'translate({x} {y})'
    vx,vy,vw,vh=[float(v) for v in re.split(r'[ ,]+',vb.strip())]
    w,h=f('width',vw),f('height',vh); s=min(w/vw,h/vh)
    tx=x+(w-vw*s)/2-vx*s; ty=y+(h-vh*s)/2-vy*s
    return f'matrix({s} 0 0 {s} {tx} {ty})'
def ctm(el):
    ts=[]; p=el
    while p is not None:
        if p.tag==NS+'svg' and p.getparent() is not None: ts.append(_viewport(p))
        if p.get('transform'): ts.append(p.get('transform'))
        p=p.getparent()
    m=Matrix()
    for t in ts: m=m*Matrix(t)   # svgelements: A*B applies A then B, so innermost first
    return m
def stroke_width(el):
    """source stroke width in 512 user units (after transforms)"""
    try: w=float(re.sub('[a-z]+','',el.get('stroke-width','1')))
    except: w=1.0
    m=ctm(el); return w*math.sqrt(abs(m.a*m.d-m.b*m.c))
def scene(code,keephl=False):
    """paint-ordered layers with the shared rules applied:
    kind 'fill' (filled shape; its own stroke is the source outline), 'wide' (stroke-only, wide -> white ribbon),
    'thin' (stroke-only, thin -> single black line), translucent layers removed."""
    t,sh=gt.load(code); out=[]
    for s in sh:
        if s['translucent'] and not keephl: continue
        el=s['el']
        if s['filled']: kind='fill'; w=0
        elif s['stroked']:
            w=stroke_width(el); kind='stroke'
            if w<=1e-6: continue   # zero-width stroke paints nothing
        else: continue
        out.append(dict(sid=s['sid'],kind=kind,w=w,el=el,key=geomkey(el),members=[s['sid']]))
    # border pairs: a stroke-only layer redrawn later on the SAME geometry with a narrower stroke is the core of a
    # wire whose dark outline is the earlier, wider one. Merge into one wire: footprint = wider width, core = narrower,
    # painted at the core's (later) position. Thin/wide is decided on the core.
    strokes=[x for x in out if x['kind']!='fill']; drop=set()
    for i,a in enumerate(strokes):
        for b in strokes[i+1:]:
            if b['key']==a['key'] and b['w']<a['w'] and id(b) not in drop and id(a) not in drop:
                b['foot']=max(a.get('foot',a['w']),a['w']); b['members']=a['members']+b['members']
                b['widths']=a.get('widths',[a['w']])+[b['w']]; drop.add(id(a)); break
    out=[x for x in out if id(x) not in drop]
    for x in out:
        x['first']=min(x['members']); x['last']=max(x['members'])
        if x['kind']=='fill': continue
        x.setdefault('foot',x['w'])
        # body width: outline + body (+ highlight) triples are bodies of the middle width; a plain border pair's
        # body is its core. (v6-final: the snake coil / pretzel were misread as thin wires via their highlight.)
        ws=sorted(x.get('widths',[x['w']]),reverse=True)
        x['body']=ws[1] if len(ws)>=3 else x['w']
        x['kind']='thin' if x['body']<CFG['thin_factor']*CFG['outer'] else 'wide'
        x['weight']=min(CFG['thin_weight'],max(x['foot'],CFG['inner'])) if x['kind']=='thin' else 0
    # clip-path ends: a wire clipped by a path ENDS on the wire drawn along that path (racket strings on the rim),
    # so it is a T-junction there, never a crossing
    root=t.getroot(); ids={e.get('id'):e for e in root.iter() if e.get('id')}
    for x in out:
        cl=set(); p=x['el']
        while p is not None:
            m=re.search(r'url\(#([^)]+)\)',p.get('clip-path') or '')
            if m and m.group(1) in ids: cl|={e.get('d') for e in ids[m.group(1)].iter() if e.get('d')}
            p=p.getparent()
        x['clips']=cl
    _banded(code,t,out,keephl)
    return t,out
def ends_on(front,back):
    return bool(front.get('clips')) and back['el'].get('d') in front['clips']
def _banded(code,t,out,keephl):
    """wires laid side by side (rainbow bands) are one BODY, not separate wires: a thin layer whose CORE outline
    runs along other thin cores for more than CFG['band_overlap'] of its boundary is promoted to wide.
    (Crossings, junctions and meshes touch only briefly and stay wires.)"""
    th=[x for x in out if x['kind']=='thin']
    if not th: return
    import numpy as np
    from lxml import etree
    S=512; masks={}
    import scipy.ndimage as nd
    for x in th:
        tt,_=gt.load(code); root=tt.getroot()
        keep=set(x['members'])
        for el in list(root.iter()):
            sid=el.get('data-sid')
            if sid is None: continue
            if int(sid) not in keep: el.getparent().remove(el); continue
            w=float(re.sub('[a-z]+','',el.get('stroke-width','1')) or 1); sc=stroke_width(el)/w if w else 1
            el.set('stroke','#000'); el.set('fill','none'); el.set('stroke-width',str(x['w']/sc if sc else w))
            for k in('opacity','stroke-opacity','style','stroke-dasharray'): el.attrib.pop(k,None)
        masks[id(x)]=gt.render(etree.tostring(root),S)[...,3]>=128
    from skimage.morphology import skeletonize
    # small dense wires (snowflakes, sparks): a 10px line on a ~30px glyph fills it solid, so the weight follows
    # the wire's own size: weight <= skeleton-extent/12, never below 4px
    for x in th:
        sk=skeletonize(masks[id(x)]); ys,xs=np.nonzero(sk)
        if len(ys)<2: continue
        ext=math.hypot(ys.max()-ys.min(),xs.max()-xs.min())*512/S
        x['weight']=min(x['weight'],max(CFG['small_min'],ext/CFG['small_div'])); x['_ext']=ext
    if len(th)<2: return
    sks={k:nd.binary_dilation(skeletonize(v),iterations=1) for k,v in masks.items()}
    for x in th:
        m=masks[id(x)]
        if m.sum()<4: continue
        others=np.zeros_like(m)
        for y in th:   # only wires that never cross/overlap this one can be its parallel band neighbours
            if y is not x and not (sks[id(y)]&sks[id(x)]).any(): others|=masks[id(y)]   # centrelines never meet
        from skimage.morphology import skeletonize
        sk=skeletonize(m)
        if sk.sum()<3 or not others.any(): continue
        side=others&~nd.binary_dilation(m,iterations=2)   # neighbours BESIDE this core (not copies on top of it)
        if not side.any(): continue
        d=nd.distance_transform_edt(~side)
        run=(d[sk]<=x['w']/2*S/512+4).mean()   # share of the centreline running alongside another core
        if run>CFG['band_overlap']: x['banded']=True
    # a banded BODY is >=3 long parallel bands (rainbow arcs); 1-2 short neighbours (zipper teeth, rim glints, ski
    # pairs, tentacles) stay wires
    bd=[x for x in th if x.get('banded') and x.get('_ext',0)>=CFG['band_len']]
    if len(bd)<CFG['band_min']: bd=[]
    for x in th:
        x.pop('banded',None)
    for x in bd: x['banded']=True; x['kind']='wide'; x['weight']=0
def geomkey(el):
    a={k:v for k,v in el.attrib.items() if k in('d','points','cx','cy','r','rx','ry','x','y','width','height','x1','y1','x2','y2')}
    return (el.tag,tuple(sorted(a.items())),str(ctm(el)))
CFG=config()
