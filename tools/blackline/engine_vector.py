"""Engine V: pure vector. Source shapes -> polygons (svgelements parse + own transform/clip/mask/dash handling),
boolean occlusion in paint order and line offsetting with Clipper (pyclipper: exact integer polygon booleans and
offsets; skia-pathops was tried first and produced wrong unions on curved input, see PIPELINE.md).
No rasterising, nothing from build.py or engine_raster."""
import io,re,math,numpy as np,pyclipper as pc
from lxml import etree
from svgelements import SVG,Path as SPath,Move,Line,Close,CubicBezier,QuadraticBezier,Arc,Matrix,Shape
import common as C, gt
NS=gt.NS
SC=1000.0            # integer grid: 1/1000 px at 512
TOL=0.05             # curve flattening tolerance (px)
STATS={}
# ---------- polygon algebra (region = list of integer rings, nonzero, orientation-correct)
def _exe(a,b,op):
    if not a and op in(pc.CT_UNION,):
        a,b=b,[]
    if not a: return []
    p=pc.Pyclipper()
    try:
        p.AddPaths(a,pc.PT_SUBJECT,True)
        if b: p.AddPaths(b,pc.PT_CLIP,True)
        return p.Execute(op,pc.PFT_NONZERO,pc.PFT_NONZERO)
    except pc.ClipperException: return a if op!=pc.CT_INTERSECTION else []
def U(rs):
    allp=[r for x in rs if x for r in x]
    if not allp: return []
    p=pc.Pyclipper(); p.AddPaths(allp,pc.PT_SUBJECT,True); return p.Execute(pc.CT_UNION,pc.PFT_NONZERO,pc.PFT_NONZERO)
def D(a,b): return _exe(a,b,pc.CT_DIFFERENCE) if b else a
def X(a,b): return _exe(a,b,pc.CT_INTERSECTION) if (a and b) else []
_J={'round':pc.JT_ROUND,'miter':pc.JT_MITER,'bevel':pc.JT_SQUARE}
_E={'round':pc.ET_OPENROUND,'butt':pc.ET_OPENBUTT,'square':pc.ET_OPENSQUARE}
def _off(paths,delta,join,end):
    if not paths or delta<=0: return []
    o=pc.PyclipperOffset(miter_limit=4.0,arc_tolerance=TOL*SC); o.AddPaths(paths,_J.get(join,pc.JT_MITER),end)
    return U([o.Execute(delta*SC)])
def stroke(lines,w,cap='round',join='round'):
    """lines: list of (ring, closed) integer polylines -> filled stroke region"""
    op=[l for l,cl in lines if not cl and len(l)>1]; cls=[l for l,cl in lines if cl and len(l)>2]
    return U([_off(op,w/2,join,_E.get(cap,pc.ET_OPENBUTT)),_off(cls,w/2,join,pc.ET_CLOSEDLINE)])
def outline(region,w): return _off(region,w/2,'round',pc.ET_CLOSEDLINE)   # band of width w centred on the boundary
def dilate(region,d): return _off(region,d,'round',pc.ET_CLOSEDPOLYGON) if d>0 else region
def erode(region,d): return _off(region,-d,'miter',pc.ET_CLOSEDPOLYGON) if False else _neg(region,d)
def _neg(region,d):
    if not region: return []
    o=pc.PyclipperOffset(miter_limit=2.0,arc_tolerance=TOL*SC); o.AddPaths(region,pc.JT_MITER,pc.ET_CLOSEDPOLYGON)
    return o.Execute(-d*SC)
def clean(region,sliver=0.8,frag=16.0):
    """drop visible slivers thinner than 2*sliver px and crumbs under frag px^2 (seams between abutting shapes)"""
    if not region: return region
    op=X(dilate(_neg(region,sliver),sliver+0.05),region)
    out=[r for r in op if abs(pc.Area(r))/SC/SC>=frag or pc.Area(r)<0]
    return U([out]) if out else []
def area(region): return sum(pc.Area(r) for r in region)/SC/SC
# ---------- svg -> polylines
def mstr(m): return f'matrix({m.a} {m.b} {m.c} {m.d} {m.e} {m.f})'
def _geom(el,m):
    c=etree.fromstring(etree.tostring(el))
    for k in('transform','clip-path','mask','style','stroke-dasharray'): c.attrib.pop(k,None)
    doc=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><g transform="{mstr(m)}">{etree.tostring(c).decode()}</g></svg>'
    for e in SVG.parse(io.StringIO(doc)).elements():
        if isinstance(e,Shape) and not isinstance(e,SVG):
            p=SPath(e); p.approximate_arcs_with_cubics(); p.reify(); return p   # arcs first: reify of a skewed arc is wrong
    return None
def polylines(sp):
    """svgelements path -> list of (float Nx2 array, closed)"""
    out=[]; cur=[]; closed=False
    for s in sp:
        if isinstance(s,Move):
            if len(cur)>1: out.append((np.array(cur),False))
            cur=[(s.end.x,s.end.y)]
        elif isinstance(s,Close):
            if len(cur)>1: out.append((np.array(cur),True))
            cur=[]
        elif isinstance(s,Line): cur.append((s.end.x,s.end.y))
        elif isinstance(s,(CubicBezier,QuadraticBezier,Arc)):
            L=s.length(error=1e-3) if hasattr(s,'length') else 10
            n=int(min(max(math.sqrt(max(L,0.01)/TOL)/1.5,2),200))
            for t in np.linspace(0,1,n+1)[1:]:
                q=s.point(t); cur.append((q.x,q.y))
    if len(cur)>1: out.append((np.array(cur),False))
    return out
def _int(a): return [(int(round(x*SC)),int(round(y*SC))) for x,y in a]
def fill_region(pl,rule):
    rings=[_int(a) for a,_ in pl if len(a)>2]
    if not rings: return []
    try: return pc.SimplifyPolygons(rings,pc.PFT_EVENODD if rule=='evenodd' else pc.PFT_NONZERO)
    except pc.ClipperException: return []
def _attr(el,k,default=None):
    p=el
    while p is not None:
        v=p.get(k)
        if v is None:
            m=re.search(rf'(?:^|;)\s*{k}\s*:\s*([^;]+)',p.get('style','') or '')
            v=m.group(1).strip() if m else None
        if v is not None: return v
        p=p.getparent()
    return default
def _clips(el,root,fitm):
    res=None; p=el; ids={x.get('id'):x for x in root.iter() if x.get('id')}
    while p is not None and p.tag!=NS+'svg':
        for att in('clip-path','mask'):
            m=re.search(r'url\(#([^)]+)\)',p.get(att) or '')
            if not m or m.group(1) not in ids: continue
            parts=[]
            for ch in ids[m.group(1)].iter():
                if ch.tag in gt.SHAPES:
                    if att=='mask' and (ch.get('fill') or '#000').lower() in('#000','#000000','black','none'): continue
                    t=Matrix(ch.get('transform')) if ch.get('transform') else Matrix()
                    sp=_geom(ch,t*C.ctm(p)*fitm)
                    if sp is not None: parts.append(fill_region(polylines(sp),ch.get('clip-rule') or ch.get('fill-rule') or 'nonzero'))
            g=U(parts); res=g if res is None else X(res,g)
        p=p.getparent()
    return res
def _dash(pl,arr,scale):
    arr=[float(x)*scale for x in re.split(r'[ ,]+',arr.strip()) if x]
    if not arr or sum(arr)<=0: return pl
    if len(arr)%2: arr=arr*2
    out=[]
    for a,cl in pl:
        if cl: a=np.vstack([a,a[:1]])
        seg=np.r_[0,np.cumsum(np.hypot(*np.diff(a,axis=0).T))]; pos=0; i=0; on=True
        while pos<seg[-1]:
            e=min(pos+arr[i%len(arr)],seg[-1])
            if on and e>pos:
                ts=np.r_[pos,seg[(seg>pos)&(seg<e)],e]
                out.append((np.c_[np.interp(ts,seg,a[:,0]),np.interp(ts,seg,a[:,1])],False))
            pos=e; i+=1; on=not on
    return out
def layer_geom(L,root,fitm):
    """(footprint region, centreline (polylines,cap,join) or None, clip region or None)"""
    regs=[]; centre=None; clip=None
    for sid in L['members']:
        el=root.find(f".//*[@data-sid='{sid}']"); m=C.ctm(el)*fitm; sp=_geom(el,m)
        if sp is None: continue
        pl=polylines(sp)
        if L['kind']=='fill': g=fill_region(pl,_attr(el,'fill-rule','nonzero'))
        else:
            dash=_attr(el,'stroke-dasharray'); sc=math.sqrt(abs(m.a*m.d-m.b*m.c))
            if dash and dash!='none': pl=_dash(pl,dash,sc)
            cap=_attr(el,'stroke-linecap','butt') if not dash or dash=='none' else 'butt'
            join=_attr(el,'stroke-linejoin','miter')
            ipl=[(_int(a),cl) for a,cl in pl]
            g=stroke(ipl,L['foot']*fitm.a,cap,join)
            if sid==L['members'][-1]: centre=(pl,ipl,cap,join)
        c=_clips(el,root,fitm)
        if c is not None: g=X(g,c); clip=c
        regs.append(g)
    return U(regs),centre,clip
def crossings(back,front,r):
    """points where the FRONT centreline passes across the BACK one (front continues past r on both sides)"""
    B=np.vstack([a for a,_ in back]) if back else None; res=[]
    if B is None: return res
    for F,cl in front:
        F=np.asarray(F)
        if len(F)<2: continue
        d=np.sqrt(((F[:,None,:]-B[None,:,:])**2).sum(-1)).min(1)
        if cl:   # closed: start where farthest from the back wire
            j=int(np.argmax(d)); F=np.roll(F,-j,axis=0); d=np.roll(d,-j)
        idx=np.flatnonzero(d<=r)
        if not idx.size: continue
        for run in np.split(idx,np.flatnonzero(np.diff(idx)>1)+1):
            if run[0]>0 and run[-1]<len(F)-1 and d[run].min()<r*0.5: res.append(tuple(F[run[np.argmin(d[run])]]))
    return res
def build_one(code,cfg,fit,wi,wo,keephl=False):
    t,layers=C.scene(code,keephl); root=t.getroot()
    fitm=Matrix(f'translate(256 256) scale({fit}) translate(-256 -256)'); k=fit
    G=[layer_geom(L,root,fitm) for L in layers]
    sid2l={m:i for i,L in enumerate(layers) for m in L['members']}; par=list(range(len(layers)))
    def f(x):
        while par[x]!=x: x=par[x]
        return x
    for a,b in gt.merges(code,keephl):
        if int(a) in sid2l and int(b) in sid2l: par[f(sid2l[int(a)])]=f(sid2l[int(b)])
    wide=[i for i,L in enumerate(layers) if L['kind']!='thin']; thin=[i for i,L in enumerate(layers) if L['kind']=='thin']
    cover=[]; vis={}; cover_after={}
    for i in reversed(range(len(layers))):
        cover_after[i]=cover
        if layers[i]['kind']!='thin': vis[i]=D(G[i][0],cover); cover=U([cover,G[i][0]])
    # silhouette: close pin-holes / hairline cracks between abutting shapes (no artwork is that small)
    Sil=U([[r for r in _neg(dilate(cover,0.8),0.8) if not(pc.Area(r)<0 and abs(pc.Area(r))/SC/SC<60)]]) if cover else []
    Sil=U([Sil,cover]) if Sil else cover
    Sil=[r for r in Sil if not(pc.Area(r)<0 and abs(pc.Area(r))/SC/SC<60)]
    groups={}
    for i in wide: groups.setdefault(f(i),[]).append(vis[i])
    tfoot={t_:D(G[t_][0],cover_after[t_]) for t_ in thin}
    outer=outline(Sil,wo*k); blk=[]
    for gi,vs in groups.items():
        gv=U(vs)
        gv=X(_neg(dilate(gv,0.6),0.6),Sil) if len(vs)>1 else gv   # close hairline seams between merged members
        gv=clean(gv)
        if not gv: continue
        last=max(layers[i]['last'] for i in wide if f(i)==gi)
        b=U([X(outline(gv,wi*k),Sil),X(outer,dilate(gv,wo*k/2+0.5))])
        later=[tfoot[t_] for t_ in thin if layers[t_]['first']>last]
        if later: b=D(b,U(later))
        blk.append(b)
    lines={}
    for t_ in thin:
        if G[t_][1] is None: continue
        pl,ipl,cap,join=G[t_][1]
        ln=stroke(ipl,layers[t_]['weight']*k,cap,join)
        if G[t_][2] is not None: ln=X(ln,G[t_][2])
        lines[t_]=(D(ln,cover_after[t_]),pl)
    for t_ in thin:
        if t_ not in lines: continue
        ln,pl=lines[t_]
        for u in thin:
            if u in lines and layers[u]['first']>layers[t_]['last'] and not C.ends_on(layers[u],layers[t_]):
                for x,y in crossings(pl,lines[u][1],layers[t_]['foot']*k/2+cfg['gap']*k):
                    r=(layers[t_]['foot']/2+cfg['gap']+layers[u]['weight'])*k
                    box=[_int([(x-r,y-r),(x+r,y-r),(x+r,y+r),(x-r,y+r)])]
                    ln=D(ln,dilate(X(lines[u][0],box),cfg['gap']*k))
        blk.append(ln)
    return Sil,U(blk)
def d_of(region):
    return ''.join('M'+'L'.join('%.2f %.2f'%(x/SC,y/SC) for x,y in r)+'Z' for r in region if len(r)>2)
def bounds_ok(region,m):
    if not region: return True
    a=np.array([p for r in region for p in r])/SC
    return a[:,0].min()>=m and a[:,1].min()>=m and a[:,0].max()<=512-m and a[:,1].max()<=512-m
def build(code,cfg,keephl=False):
    res={}
    for tag,wi,wo,fit,m in(('512',cfg['inner'],cfg['outer'],cfg['fit'],1.0),('72',cfg['inner72'],cfg['outer72'],cfg['fit72'],512/72*0.6)):
        for _ in range(6):
            W,B=build_one(code,cfg,fit,wi,wo,keephl)
            if bounds_ok(B,m) and bounds_ok(W,m): break
            fit=round(fit*0.97,4)
        res[tag]=(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512" data-fit="{fit}" data-engine="vector">'
                  f'<path fill="#fff" d="{d_of(W)}"/><path fill="#000" d="{d_of(B)}"/></svg>')
        res['info'+tag]=dict(fit=fit)
    return res
