"""diff / check / select / sheet / golden sub-commands for pipeline.py"""
import os,sys,json,re,shutil,io
import numpy as np,scipy.ndimage as nd
from PIL import Image,ImageDraw,ImageFont
from multiprocessing import Pool
HERE=os.path.dirname(os.path.abspath(__file__))
def add_parsers(sp):
    d=sp.add_parser('diff'); d.add_argument('--a',required=True); d.add_argument('--b',required=True); d.add_argument('--out',required=True); d.add_argument('--codes'); d.add_argument('--tol',type=float,default=2.0); d.add_argument('--flag',type=float,default=0.93)
    c=sp.add_parser('check'); c.add_argument('--build',required=True); c.add_argument('--src',required=True); c.add_argument('--out',required=True); c.add_argument('--codes'); c.add_argument('--config')
    s=sp.add_parser('select'); [s.add_argument(x,required=True) for x in('--a','--b','--diff','--checks-a','--checks-b','--xray-a','--xray-b','--out')]
    h=sp.add_parser('sheet'); h.add_argument('--builds',required=True); h.add_argument('--codes',required=True); h.add_argument('--out',required=True); h.add_argument('--size',type=int,default=256); h.add_argument('--names'); h.add_argument('--cols',type=int,default=4)
    g=sp.add_parser('golden'); g.add_argument('action',choices=['test','approve']); g.add_argument('--build',required=True); g.add_argument('--golden',default=os.path.join(HERE,'golden')); g.add_argument('--min',type=float,default=0.97); g.add_argument('--engine',choices=['vector','raster'],help='test only codes whose approved reference came from this engine')
def run(a): {'diff':cmd_diff,'check':cmd_check,'select':cmd_select,'sheet':cmd_sheet,'golden':cmd_golden}[a.cmd](a)
def _codes(spec,build):
    if spec and spec.startswith('@'): return [l.strip() for l in open(spec[1:]) if l.strip()]
    if spec: return spec.split(',')
    L=json.load(open(f'{build}/build-log.json')); return sorted(c for c in L if 'copy_of' not in L[c])
def masks(png):
    v=np.asarray(Image.open(png).convert('RGBA')); a=v[...,3]>=128
    return a&(v[...,:3].mean(2)<128),a
def agree(A,B,tol):
    if not A.any() and not B.any(): return 1.0
    dA=nd.distance_transform_edt(~A)<=tol; dB=nd.distance_transform_edt(~B)<=tol
    return float(((A&dB).sum()+(B&dA).sum())/max(A.sum()+B.sum(),1))
# ---------------- diff
_D={}
def _diff1(c):
    a=_D['a']
    try:
        Ba,Oa=masks(f'{a.a}/png/512/{c}.png'); Bb,Ob=masks(f'{a.b}/png/512/{c}.png')
    except Exception as e: return dict(code=c,error=str(e),flag=True)
    ag=agree(Ba,Bb,a.tol); iou=float((Ba&Bb).sum()/max((Ba|Bb).sum(),1)); oi=agree(Oa,Ob,a.tol)
    r=dict(code=c,black_agree=round(ag,4),black_iou=round(iou,4),opaque_agree=round(oi,4),flag=bool(ag<a.flag or oi<a.flag))
    if r['flag']:
        h=np.full(Ba.shape+(3,),255,np.uint8); h[Ba&Bb]=0; h[Ba&~Bb]=[220,0,0]; h[Bb&~Ba]=[0,90,255]
        os.makedirs(f'{a.out}/heat',exist_ok=True); Image.fromarray(h).save(f'{a.out}/heat/{c}.png')
    return r
def cmd_diff(a):
    os.makedirs(a.out,exist_ok=True); _D['a']=a; cs=_codes(a.codes,a.a)
    with Pool(initializer=_D.update,initargs=({'a':a},)) as P: R=P.map(_diff1,cs,8)
    fl=[r for r in R if r['flag']]
    S=dict(checked=len(R),flagged=len(fl),tol_px=a.tol,flag_below=a.flag,mean_agree=round(float(np.mean([r.get('black_agree',0) for r in R])),4),
           worst=[(r['code'],r.get('black_agree')) for r in sorted(fl,key=lambda r:r.get('black_agree',0))[:40]])
    json.dump(dict(summary=S,results=R),open(f'{a.out}/diff.json','w'),indent=0); print(json.dumps(S))
# ---------------- checks
def _src_info(code,cfg,keephl):
    import common as C,gt
    t,lay=C.scene(code,keephl)
    ids,sh=gt.id_svg(code,1.0,(),keephl); I=gt.decode(gt.render(ids,512))
    col=gt.render(gt.full_color_svg(code,1.0,(),keephl),512)
    return lay,I,col
def _centre_ref(code,lay,fit,cfg):
    """reference: the source's thin wires (core centrelines) drawn at the configured wire weight"""
    import gt,common as C
    from lxml import etree
    t,_=gt.load(code); root=t.getroot(); keep={L['members'][-1]:L for L in lay if L['kind']=='thin'}
    for el in list(root.iter()):
        sid=el.get('data-sid')
        if sid is None: continue
        if int(sid) not in keep: el.getparent().remove(el); continue
        L=keep[int(sid)]; w=float(re.sub('[a-z]+','',el.get('stroke-width','1')) or 1); s=C.stroke_width(el)/w
        el.set('stroke','#000'); el.set('fill','none'); el.set('stroke-width',str(L['weight']/s))
        for k in('opacity','stroke-opacity','style'): el.attrib.pop(k,None)
    gt._wrap(root,fit); return gt.render(etree.tostring(root),512)[...,3]>=128
def _holes(M,minr):
    bg=~M; lab,n=nd.label(bg); 
    if n==0: return 0
    border=set(np.unique(np.r_[lab[0],lab[-1],lab[:,0],lab[:,-1]]))
    cnt=0
    for i,sl in enumerate(nd.find_objects(lab),1):
        if i in border: continue
        reg=lab[sl]==i
        if nd.distance_transform_edt(np.pad(reg,1)).max()>=minr: cnt+=1
    return cnt
def _ends(M,excl=None):
    from skimage.morphology import skeletonize
    sk=skeletonize(M); nb=nd.convolve(sk.astype(int),np.ones((3,3),int),mode='constant')-1
    e=sk&(nb==1)
    if excl is not None: e&=~excl
    return int(e.sum())
_C={}
_RV=None
def _REVIEWED():
    global _RV
    if _RV is None:
        p=os.path.join(os.path.dirname(os.path.abspath(__file__)),'golden','reviewed.json')
        _RV=json.load(open(p)) if os.path.exists(p) else {}
    return _RV
def _check1(c):
    a=_C['a']; cfg=_C['cfg']
    import common as C
    L=json.load(open(f'{a.build}/build-log.json')).get(c,{}) if c not in _C['log'] else _C['log'][c]
    kh=bool(L.get('kept_highlights')); fit=float(L.get('fit',cfg['fit']))
    F={}; info={}
    try:
        s=open(f'{a.build}/svg/{c}.svg').read(); s72=open(f'{a.build}/svg-72/{c}.svg').read()
        # structure
        paths=re.findall(r'<path [^>]*>',s)
        if len(paths)!=2 or 'fill="#fff"' not in paths[0] or 'fill="#000"' not in paths[1]: F['structure']=1
        if re.search(r'stroke=|opacity|Gradient|<image|filter',s): F['not_pure']=1
        if len(re.findall(r'<path [^>]*>',s72))!=2: F['svg72_structure']=1
        B,O=masks(f'{a.build}/png/512/{c}.png')
        v=np.asarray(Image.open(f'{a.build}/png/512/{c}.png').convert('RGBA'))
        op=v[...,3]==255; tint=op&(np.abs(v[...,:3].astype(int)-v[...,:1]).max(2)>8)
        if tint.sum()>0: F['tinted']=int(tint.sum())
        if not B.any(): F['empty']=1
        if B[0].any() or B[-1].any() or B[:,0].any() or B[:,-1].any(): F['touches_frame']=1
        a72=np.asarray(Image.open(f'{a.build}/png/72/{c}.png').convert('RGBA'))[...,3]>0
        if a72[0].any() or a72[-1].any() or a72[:,0].any() or a72[:,-1].any(): F['touches_frame_72']=1
        lay,I,col=_src_info(c,cfg,kh)
        # bring source maps into the output's fit
        def fitmap(X,order=0):
            z=nd.zoom(X,fit,order=order); P=np.zeros_like(X) if X.dtype==bool else np.full_like(X,-1); o=(X.shape[0]-z.shape[0])//2
            P[o:o+z.shape[0],o:o+z.shape[1]]=z; return P
        I=fitmap(I); A=fitmap(col[...,3]>=(1 if kh else 128))
        # 1 line weight: thickness histogram on the skeleton of the black
        from skimage.morphology import skeletonize
        dt=nd.distance_transform_edt(B); sk=skeletonize(B); th=2*dt[sk]
        hist=np.histogram(th,bins=[0,4,8,12,16,20,24,32,48,1e9])[0].tolist(); info['thick_hist']=hist
        info['thick_p95']=round(float(np.percentile(th,95)),1) if th.size else 0
        thin=[Lr for Lr in lay if Lr['kind']=='thin']
        if thin:
            T=np.isin(I,[m for Lr in thin for m in Lr['members']])
            W=np.isin(I,[m for Lr in lay if Lr['kind']!='thin' for m in Lr['members']])
            Wn=nd.binary_dilation(W,iterations=int(cfg['outer']+2))   # junctions with fills are judged by the fill rules
            # centreline of the wire CORES (last member of each wire): adjacent wires' dark border members merge into one
            # band whose skeleton runs between the cores (lab-coat pens) - tuned v6-final, see PIPELINE.md
            Tc=np.isin(I,[Lr['members'][-1] for Lr in thin])
            Tsk=skeletonize(Tc)&~Wn
            if Tsk.sum()>20:
                white_on=(O&~B)[Tsk].mean(); info['thin_white_on_centre']=round(float(white_on),3)
                if white_on>0.25: F['thin_inflated']=round(float(white_on),3)   # wire turned into a white ribbon
                # thickness is judged away from where two wires converge (A-frame legs meeting at a shared vertex
                # legitimately merge) and only on a real sample (>=60px of centreline; sharp outline tips alone are
                # not a blob) - tuned v6-final, see PIPELINE.md
                conv=np.zeros_like(Tsk); lim=cfg['thin_weight']*fit+4
                cores=[np.isin(I,[Lr['members'][-1]]) for Lr in thin]
                if len(cores)>1:
                    near=np.zeros(Tsk.shape,int)
                    for cm in cores: near+=nd.distance_transform_edt(~cm)<=lim
                    conv=near>=2
                samp=Tsk&B&~conv; tk=2*dt[samp]
                if tk.size>=60 and np.percentile(tk,90)>lim: F['thin_blob']=round(float(np.percentile(tk,90)),1)
            # 4 topology of thin art: loops and ends (crossing breaks are healed by a closing of gap size)
            Z=nd.binary_dilation(T,iterations=3)
            r=int(cfg['gap']+cfg['thin_weight']/2+2)
            st=np.hypot(*np.mgrid[-r:r+1,-r:r+1])<=r
            # the fills' outer line legitimately reaches outer/2 beyond the source edge: give the reference the same
            # band, otherwise a wire meeting a fill outline looks like a new loop (tuned v6-final, see PIPELINE.md)
            Wb=nd.distance_transform_edt(~W)<=cfg['outer']*fit/2+1 if W.any() else W
            Ot=nd.binary_closing(np.pad((B&Z)|Wb,r+1),structure=st)[r+1:-r-1,r+1:-r-1]
            minr=r+3
            Rf=_centre_ref(c,lay,fit,cfg)&~np.isin(I,[m for Lr in lay if Lr['kind']!='thin' for m in Lr['members']]); Rc=nd.binary_closing(np.pad(Rf|Wb,r+1),structure=st)[r+1:-r-1,r+1:-r-1]   # wire ends meeting a fill outline join in both (v6-final)
            hs,ho=_holes(Rc,minr),_holes(Ot,minr)
            es,eo=_ends(Rc,Wn),_ends(Ot,Wn)
            info.update(loops_src=hs,loops_out=ho,ends_src=es,ends_out=eo)
            if ho!=hs: F['topology_loops']=f'{hs}->{ho}'
            if abs(eo-es)>max(2,0.25*es): F['topology_ends']=f'{es}->{eo}'
        # 2 white between lines: no near-solid black tiles where the source had gaps
        # black lying in the source's open gaps (farther from any source paint than the outer line can spill)
        Gp=nd.distance_transform_edt(~A)>cfg['outer']*fit/2+2
        lab,n=nd.label(B&Gp); big=int((nd.sum(B&Gp,lab,range(1,n+1))>=30).sum()) if n else 0
        info['black_in_gaps_blobs']=big
        if big: F['solid_black_over_gaps']=big
        # 3 shape fidelity: output inside the source (+outer half line), source covered by output
        dA=nd.distance_transform_edt(~A)<=cfg['outer']*fit/2+2.5; prec=float((O&dA).sum()/max(O.sum(),1))
        slack=max([cfg['outer']]+[(Lr['foot']-Lr['weight'])/2 for Lr in thin])*fit+2
        dO=nd.distance_transform_edt(~O)<=slack; rec=float((A&dO).sum()/max(A.sum(),1))
        info.update(sil_precision=round(prec,4),sil_recall=round(rec,4),sil_iou=round(float((O&A).sum()/max((O|A).sum(),1)),4))
        if prec<0.985: F['fidelity_outside_source']=round(prec,4)
        if rec<0.97: F['fidelity_source_missing']=round(rec,4)
    except Exception as e:
        import traceback; F['check_error']=traceback.format_exc()[-300:]
    # per-emoji visual review waivers (golden/reviewed.json): each needs a written reason; reported, never silent
    rv=_REVIEWED().get(c,{})
    waived={k:rv[k] for k in list(F) if k in rv}
    for k in waived: info.setdefault('reviewed',{})[k]=F.pop(k)
    return dict(code=c,fail=sorted(F),detail=F,**info)
def cmd_check(a):
    import common as C
    C.set_source(a.src); cfg=C.config(a.config); os.makedirs(a.out,exist_ok=True)
    log=json.load(open(f'{a.build}/build-log.json')); cs=_codes(a.codes,a.build)
    def init(d): _C.update(d); C.set_source(a.src)
    with Pool(initializer=init,initargs=({'a':a,'cfg':cfg,'log':log},)) as P: R=P.map(_check1,cs,4)
    # tone identity
    tone=0
    M=json.load(open(f'{a.build}/emoji-map.json')) if os.path.exists(f'{a.build}/emoji-map.json') else {}
    for k,v in M.items():
        if v[6] and open(f'{a.build}/svg/{k}.svg','rb').read()!=open(f'{a.build}/svg/{v[6]}.svg','rb').read(): tone+=1
    from collections import Counter
    cnt=Counter(f for r in R for f in r['fail'])
    S=dict(checked=len(R),failed=sum(bool(r['fail']) for r in R),fail_counts=dict(cnt),tone_not_identical=tone,
           examples={k:[r['code'] for r in R if k in r['fail']][:12] for k in cnt})
    json.dump(dict(summary=S,results=R),open(f'{a.out}/checks.json','w'),indent=0); print(json.dumps(S,indent=1))
# ---------------- select
def cmd_select(a):
    D={r['code']:r for r in json.load(open(f'{a.diff}/diff.json'))['results']}
    CA={r['code']:r for r in json.load(open(f'{a.checks_a}/checks.json'))['results']}
    CB={r['code']:r for r in json.load(open(f'{a.checks_b}/checks.json'))['results']}
    XA=_xr(a.xray_a); XB=_xr(a.xray_b)
    LA=json.load(open(f'{a.a}/build-log.json')); LB=json.load(open(f'{a.b}/build-log.json'))
    for d in('svg','svg-72','png/512','png/72'): os.makedirs(f'{a.out}/{d}',exist_ok=True)
    pick={}; review=[]
    for c in sorted(set(CA)|set(CB)):
        okA=not CA.get(c,{'fail':[1]})['fail'] and not XA.get(c,True); okB=not CB.get(c,{'fail':[1]})['fail'] and not XB.get(c,True)
        ch='a' if okA else ('b' if okB else 'a')
        pick[c]=dict(engine=ch,a_ok=okA,b_ok=okB,flag=D.get(c,{}).get('flag'),agree=D.get(c,{}).get('black_agree'))
        if not(okA and okB) or D.get(c,{}).get('flag'): review.append(c)
    L={}
    for c,p in pick.items():
        src=a.a if p['engine']=='a' else a.b
        for d,ext in(('svg','svg'),('svg-72','svg'),('png/512','png'),('png/72','png')): shutil.copy(f'{src}/{d}/{c}.{ext}',f'{a.out}/{d}/{c}.{ext}')
        L[c]=dict((LA if p['engine']=='a' else LB)[c],selected=p)
    M=f'{a.a}/emoji-map.json'
    if os.path.exists(M):
        shutil.copy(M,f'{a.out}/emoji-map.json'); MM=json.load(open(M))
        for c,v in MM.items():
            if v[6] and v[6] in pick:
                for d,ext in(('svg','svg'),('svg-72','svg'),('png/512','png'),('png/72','png')): shutil.copy(f'{a.out}/{d}/{v[6]}.{ext}',f'{a.out}/{d}/{c}.{ext}')
                L[c]=dict(L[v[6]],copy_of=v[6])
    json.dump(L,open(f'{a.out}/build-log.json','w'),indent=0)
    from collections import Counter
    S=dict(selected=dict(Counter(p['engine'] for p in pick.values())),both_ok=sum(p['a_ok'] and p['b_ok'] for p in pick.values()),
           neither_ok=[c for c,p in pick.items() if not p['a_ok'] and not p['b_ok']],review=len(review))
    json.dump(dict(summary=S,pick=pick,review=review),open(f'{a.out}/selection.json','w'),indent=0); print(json.dumps(S))
def _xr(d):
    import csv
    return {r['code']:r['fail']=='True' for r in csv.DictReader(open(f'{d}/results.csv'))}
# ---------------- sheet (label and image come from ONE record)
def sheet(records,out,size=256,cols=4):
    """records: list of dict(code,label,images=[(caption,path)]). Each cell = label band ABOVE its own images.
    Returns the layout so tests can assert label<->code."""
    k=max(len(r['images']) for r in records); band=22; cw=k*size+16; ch=size+band+10
    rows=(len(records)+cols-1)//cols; im=Image.new('RGB',(cols*cw,rows*ch),(128,128,128)); d=ImageDraw.Draw(im)
    try: font=ImageFont.truetype('DejaVuSans.ttf',14)
    except Exception: font=ImageFont.load_default()
    layout=[]
    for i,r in enumerate(records):
        x,y=(i%cols)*cw,(i//cols)*ch
        assert all(os.path.basename(p).startswith(r['code']+'.') for _,p in r['images']), r
        d.rectangle([x+2,y+2,x+cw-3,y+band],fill=(70,70,70))
        d.text((x+6,y+4),f"{r['code']}  {r['label']}  [{' | '.join(cap for cap,_ in r['images'])}]",fill='white',font=font)
        for j,(cap,p) in enumerate(r['images']):
            t=Image.open(p).convert('RGBA').resize((size,size),Image.LANCZOS); im.paste(t,(x+8+j*size,y+band+4),t)
        layout.append(dict(code=r['code'],label_xy=(x+6,y+4),cell=(x,y,x+cw,y+ch),images=[p for _,p in r['images']]))
    im.save(out); json.dump(layout,open(os.path.splitext(out)[0]+'.layout.json','w'),indent=0)
    return layout
def cmd_sheet(a):
    builds=[b.split('=',1) for b in a.builds.split(',')]
    codes=[l.strip() for l in open(a.codes[1:])] if a.codes.startswith('@') else a.codes.split(',')
    codes=[c for c in codes if c]
    names={}
    if a.names and os.path.exists(a.names): names={k:v[2] for k,v in json.load(open(a.names)).items()}
    recs=[dict(code=c,label=names.get(c,''),images=[(lab,f'{p}/png/512/{c}.png') for lab,p in builds]) for c in codes]
    sheet(recs,a.out,a.size,a.cols); print(a.out)
# ---------------- golden
def cmd_golden(a):
    codes=[l.strip() for l in open(f'{a.golden}/codes.txt') if l.strip() and not l.startswith('#')]
    ref=f'{a.golden}/ref'
    if a.action=='approve':
        os.makedirs(ref,exist_ok=True)
        for c in codes:
            shutil.copy(f'{a.build}/svg/{c}.svg',f'{ref}/{c}.svg'); shutil.copy(f'{a.build}/png/512/{c}.png',f'{ref}/{c}.png')
        log=json.load(open(f'{a.build}/build-log.json'))
        json.dump({c:log.get(c,{}).get('engine') for c in codes},open(f'{ref}/engines.json','w'),indent=0)
        print(f'approved {len(codes)} references'); return
    if getattr(a,'engine',None) and os.path.exists(f'{ref}/engines.json'):
        # the reference is the SELECTED output; an engine is held to it only where it was the one selected
        eng=json.load(open(f'{ref}/engines.json')); codes=[c for c in codes if eng.get(c)==a.engine]
    bad=[]
    for c in codes:
        Br,_=masks(f'{ref}/{c}.png'); Bn,_=masks(f'{a.build}/png/512/{c}.png'); g=agree(Br,Bn,1.5)
        if g<a.min: bad.append((c,round(g,4)))
    print(json.dumps(dict(golden=len(codes),regressions=len(bad),below=bad)))
    sys.exit(1 if bad else 0)
