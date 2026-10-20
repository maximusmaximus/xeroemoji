"""Engine R: render-based. Rasterise the colour source into flat ownership (ID) maps at high resolution,
derive the line art from VISIBLE regions in pixel space, then vectorise with potrace.
No geometry from build.py or engine_vector is used."""
import shutil,os,io,re,subprocess,tempfile,numpy as np,scipy.ndimage as nd
from lxml import etree
import common as C, gt
POTRACE=os.environ.get('POTRACE') or shutil.which('potrace') or os.path.join(os.path.dirname(os.path.abspath(__file__)),'tools','potrace')
def _idsvg(code,layers,fit,mode,cfg):
    """mode 'all': every layer at its footprint; 'wide': thin layers removed; 'thinline': only thin layers,
    each drawn at its line weight (its centreline, source caps/joins)"""
    t,_=gt.load(code); root=t.getroot(); root.set('shape-rendering','crispEdges')
    own={}
    for li,L in enumerate(layers):
        for m in L['members']: own[m]=(li,L)
    for el in list(root.iter()):
        sid=el.get('data-sid')
        if sid is None: continue
        if int(sid) not in own: el.getparent().remove(el); continue
        li,L=own[int(sid)]; c=gt.idcol(li); keep=True
        if L['kind']=='fill':
            el.set('fill',c); el.set('stroke','none'); keep=mode!='thinline'
        else:
            el.set('fill','none'); el.set('stroke',c)
            if L['kind']=='wide': keep=mode!='thinline'
            else:
                keep=mode!='wide'
                if mode=='thinline':
                    if int(sid)!=L['members'][-1]: keep=False
                    else:
                        s=C.stroke_width(el)/float(re.sub('[a-z]+','',el.get('stroke-width','1')) or 1)
                        el.set('stroke-width',str(L['weight']/s))
                elif mode=='all': el.set('stroke-width',str(L['foot']/(C.stroke_width(el)/float(re.sub('[a-z]+','',el.get('stroke-width','1')) or 1))))
        for k in('opacity','fill-opacity','stroke-opacity','style','filter','stroke-dasharray'*0+'_'): el.attrib.pop(k,None)
        if not keep: el.getparent().remove(el)
    for el in root.iter():
        if el.tag not in gt.SHAPES and not gt.in_defs(el) and el.tag!=gt.NS+'mask':
            el.attrib.pop('opacity',None); el.attrib.pop('filter',None)
    gt._wrap(root,fit); return etree.tostring(root)
def _ids(svg,S): return gt.decode(gt.render(svg,S))
def _band(mask_edge,r): return nd.distance_transform_edt(~mask_edge)<=r
def masks(code,cfg,S=2048,fit=None,weights=('inner','outer'),keephl=False):
    fit=fit or cfg['fit']; k=S/512*fit
    t,layers=C.scene(code,keephl)
    Ia=_ids(_idsvg(code,layers,fit,'all',cfg),S)
    Iw=_ids(_idsvg(code,layers,fit,'wide',cfg),S)
    thin=[i for i,L in enumerate(layers) if L['kind']=='thin']
    # shading merges (shared rule, by source sid) -> union-find on layer index
    sid2l={m:i for i,L in enumerate(layers) for m in L['members']}
    par=list(range(len(layers)))
    def f(x):
        while par[x]!=x: x=par[x]
        return x
    for a,b in gt.merges(code,keephl):
        if int(a) in sid2l and int(b) in sid2l: par[f(sid2l[int(a)])]=f(sid2l[int(b)])
    lut=np.array([f(i) for i in range(len(layers))]+[-1,-2]) if layers else np.array([-1,-2])
    G=np.where(Iw>=0,lut[np.clip(Iw,0,None)],Iw)
    inner=cfg[weights[0]]; outer=cfg[weights[1]]
    # pinholes inside one layer (degenerate folds / zero-area notches in the source path, e.g. 1f504 arrow tips):
    # an enclosed hole smaller than 60px^2 @512 is not a visible shape, so it takes the enclosing layer (same rule as engine V's Sil)
    amax=60*(S/512)**2
    for v in np.unique(G[G>=0]):
        m=G==v
        # thin notches (< ~3px @512 wide) cut into a layer by a self-crossing outline are closed the same way
        cl=nd.binary_closing(m,iterations=int(round(1.5*S/512)))&~m
        if cl.any():
            lab,n=nd.label(cl); sz=nd.sum(np.ones_like(lab),lab,range(1,n+1))
            sm=np.isin(lab,1+np.nonzero(sz<amax)[0]); G[sm]=v; m=G==v
        h=nd.binary_fill_holes(m)&~m
        if not h.any(): continue
        lab,n=nd.label(h); sz=nd.sum(np.ones_like(lab),lab,range(1,n+1))
        small=np.isin(lab,1+np.nonzero(sz<amax)[0])
        G[small]=v; Iw=np.where(small&(Iw<0),Iw.max()+0,Iw)
    Sil=Iw>=0
    # fill pin-holes (AA cracks) in the silhouette
    Sil=nd.binary_closing(Sil,iterations=2)|Sil
    diff=np.zeros_like(Sil)
    for ax in(0,1):
        a=np.diff(G,axis=ax)!=0; both=(np.take(G,range(G.shape[ax]-1),axis=ax)>=0)&(np.take(G,range(1,G.shape[ax]),axis=ax)>=0)
        e=a&both
        if ax==0: diff[:-1]|=e; diff[1:]|=e
        else: diff[:,:-1]|=e; diff[:,1:]|=e
    diff&=~nd.binary_dilation(Iw==-2,iterations=1)|diff   # keep
    blk_inner=_band(diff,inner*k/2) if diff.any() else np.zeros_like(Sil)
    sedge=Sil^nd.binary_erosion(Sil)
    blk_outer=_band(sedge,outer*k/2) if sedge.any() else np.zeros_like(Sil)
    wide_blk=(blk_inner&Sil)|blk_outer
    white=Sil.copy()
    if thin:
        thin_vis=np.isin(Ia,thin)
        # a thin wire hides wide edges beneath its footprint only where it is painted after the wide layer there
        # (outside the silhouette: the nearest wide layer)
        if Sil.any():
            _,ind=nd.distance_transform_edt(Iw<0,return_indices=True)
            Wn=Iw[ind[0],ind[1]]
            first=np.array([L['first'] for L in layers]); last=np.array([L['last'] for L in layers])
            over=thin_vis&(Wn>=0)&(first[np.clip(Ia,0,None)]>last[np.clip(Wn,0,None)])
            wide_blk&=~over
        Lt=_ids(_idsvg(code,layers,fit,'thinline',cfg),S)
        tb=(Lt>=0)&((Lt==Ia)|np.isin(Ia,thin))   # only wide/fill layers occlude a wire here; wire-over-wire is the gap rule below
        out=np.zeros_like(Sil); gapw=np.zeros_like(Sil); done=[]
        for t_ in reversed(thin):
            m=tb&(Lt==t_)
            if not m.any(): continue
            # over/under: a white break only where a later wire's OUTLINE is painted over this wire's core
            # (front footprint drawn after this wire's last member); wires sharing one paint pass join instead
            front=np.zeros_like(Sil)
            for u,mu in done:
                if layers[u]['first']>layers[t_]['last'] and not C.ends_on(layers[u],layers[t_]): front|=mu
            if front.any():
                cut=m&(nd.distance_transform_edt(~front)<=cfg['gap']*k)
                if cut.any():
                    # only a real CROSSING breaks the back wire (front continues on both sides of it);
                    # a T-junction (front wire ends on this one) joins without a break
                    foot=nd.binary_dilation(m,iterations=int(layers[t_]['foot']*k/2))
                    lab,n=nd.label(cut,structure=np.ones((3,3)))
                    r=int((cfg['gap']+layers[t_]['foot']/2)*k)+4
                    for j,sl in enumerate(nd.find_objects(lab),1):
                        y0,y1=max(sl[0].start-r,0),sl[0].stop+r; x0,x1=max(sl[1].start-r,0),sl[1].stop+r
                        c=lab[y0:y1,x0:x1]==j
                        N=nd.binary_dilation(c,iterations=r)
                        F=front[y0:y1,x0:x1]&N&~foot[y0:y1,x0:x1]
                        if nd.label(F,structure=np.ones((3,3)))[1]>=2: m[y0:y1,x0:x1]&=~c
            out|=m; done.append((t_,m))
        blk=wide_blk|out
    else: blk=wide_blk
    return blk,white|blk,dict(layers=len(layers),thin=len(thin),fit=fit)
def trace(mask,S):
    """potrace a boolean mask -> one path d (in 512 units)"""
    if not mask.any(): return ''
    h,w=mask.shape
    pbm=b'P4\n%d %d\n'%(w,h)+np.packbits(mask,axis=1).tobytes()
    r=subprocess.run([POTRACE,'-b','svg','--flat','-t','4','-a','1.0','-O','0.3','-u','10','-r','72','-W',str(w)+'pt','-H',str(h)+'pt','-o','-','-'],input=pbm,capture_output=True,check=True).stdout.decode()
    g=re.search(r'<g transform="([^"]+)"',r).group(1); ds=re.findall(r' d="([^"]+)"',r)
    return g,' '.join(ds)
def build(code,cfg,S=2048,keephl=False):
    res={}
    for tag,wts,fit in(('512',('inner','outer'),cfg['fit']),('72',('inner72','outer72'),cfg['fit72'])):
        S=2048 if tag=='512' else 1024
        for attempt in range(6):
            b,o,info=masks(code,cfg,S,fit,wts,keephl)
            m=int(4*S/512)
            if not(b[:m].any() or b[-m:].any() or b[:,:m].any() or b[:,-m:].any()): break
            fit=round(fit*0.97,4)
        res[tag]=svg_of(o,b,S,fit); res['info'+tag]=dict(info,fit=fit)
    return res
def svg_of(white,black,S,fit=1.0):
    parts=[]
    for m,col in((white,'#fff'),(black,'#000')):
        tr=trace(m,S)
        parts.append(f'<path fill="{col}" transform="scale({512/S}) {tr[0]}" d="{tr[1]}"/>' if tr else f'<path fill="{col}" d=""/>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512" data-fit="{fit}" data-engine="raster">'+''.join(parts)+'</svg>'
