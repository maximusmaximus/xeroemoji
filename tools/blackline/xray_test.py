#!/usr/bin/env python3
"""Independent x-ray test for the Xero black line set.
Ground truth comes from the ORIGINAL colour SVGs (gt.py): every paintable shape is rendered in paint
order with a unique flat id colour (crispEdges, no AA, opacity forced to 1) -> ownership map.
Checks per emoji (tone copies share the result of the emoji they copy):
 A x-ray: black pixels not within tolerance of a visible ground-truth edge (owner change between
   non-merged groups) or the silhouette, and not on visible line-art (stroke-only shapes).
   Fail = any 8-connected violation blob >= --min-blob px at 512.
 B geometry: visible-region boundaries / line centerlines inside later opaque shapes (from build log).
 C reverse: visible ground-truth edges >= --min-edge px with no black line nearby (warning).
 D validation: ID map vs actual colour render (silhouette IoU + colour-edge agreement); the test
   errors for an emoji if they disagree.
usage: xray_test.py --build build/blackline --out build/qc/xray [--codes a,b] [--workers N]"""
import os,re,sys,json,argparse,collections
import numpy as np
from scipy import ndimage as nd
from PIL import Image,ImageDraw
from multiprocessing import Pool
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import gt
pass
import common as RULES
ap=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument('--build',default='build/blackline'); ap.add_argument('--log',default=None)
ap.add_argument('--out',default='build/qc/xray'); ap.add_argument('--codes',default=None)
ap.add_argument('--size',type=int,default=512); ap.add_argument('--inner',type=float,default=6); ap.add_argument('--outer',type=float,default=15)
ap.add_argument('--tol',type=float,default=2.0,help='extra px beyond line half-width')
ap.add_argument('--min-blob',type=int,default=3); ap.add_argument('--min-edge',type=int,default=12)
ap.add_argument('--warn-heat',action='store_true',help='also write heatmaps for missing-edge warnings (blue)')
ap.add_argument('--workers',type=int,default=os.cpu_count()); ap.add_argument('--sheet',type=int,default=48)
A=ap.parse_args() if __name__=="__main__" else ap.parse_args([])
def groups(I,merges):
    par={}
    def f(x):
        while par.get(x,x)!=x: x=par[x]
        return x
    for a,b in merges: par[f(a)]=f(b)
    G=I.copy()
    for v in np.unique(I):
        if v>=0 and f(v)!=v: G[I==v]=f(v)
    return G
def edges(G):
    E=np.zeros(G.shape,bool)
    E[:,1:]|=G[:,1:]!=G[:,:-1]; E[:,:-1]|=G[:,1:]!=G[:,:-1]
    E[1:]|=G[1:]!=G[:-1]; E[:-1]|=G[1:]!=G[:-1]
    return E
def one(code):
    if not os.path.exists(f'{A.build}/svg/{code}.svg'):
        return dict(code=code,xray_blobs=0,xray_px=0,max_blob=0,geo_xray_len=0,missing_edges=0,gt_iou=0,gt_edge_agree=0,gt_valid=True,merges=0,fail=True,missing_output=True)
    S=A.size; svgp=f'{A.build}/svg/{code}.svg'; s=open(svgp).read()
    m=re.search(r'data-fit="([\d.]+)"',s) or re.search(r'scale\(([\d.]+)\)',s); fit=float(m.group(1)) if m else 1.0
    keephl=bool(LOG.get(code,{}).get('kept_highlights'))
    ids,sh=gt.id_svg(code,fit,(),keephl); I=gt.decode(gt.render(ids,2*S))   # ground truth at 2x (1024)
    merges=gt.merges(code,keephl)
    G=groups(I,merges)
    # shared layer rules: thin wires are single lines (their footprint is line art), wide strokes are opaque ribbons
    _,lay=RULES.scene(code,keephl)
    stroke_only={m for L in lay if L['kind']=='thin' for m in L['members']}
    wide_ids={m for L in lay if L['kind']=='wide' for m in L['members']}
    so_mask=np.isin(I,list(stroke_only)) if stroke_only else np.zeros(I.shape,bool)
    so_mask=so_mask.reshape(S,2,S,2).any(axis=(1,3))
    def pool(B): return B.reshape(S,2,S,2).any(axis=(1,3))
    E=pool(edges(G)); Sil=pool(edges(I>=0))
    filled_ids=[x['sid'] for x in sh if x['filled'] or x['sid'] in wide_ids]
    SilF=pool(edges(np.isin(I,filled_ids)))   # silhouette of the filled artwork (where the outer line is centred)
    inner_E=E&~Sil&~nd.binary_dilation(so_mask,iterations=2)
    v=np.asarray(Image.open(f'{A.build}/png/512/{code}.png').convert('RGBA').resize((S,S)))
    blk=(v[...,3]>128)&(v[...,:3].mean(2)<128)
    dE=nd.distance_transform_edt(~E); dS=np.minimum(nd.distance_transform_edt(~Sil),nd.distance_transform_edt(~SilF))
    sc=S/512
    fs,_=gt.id_svg(code,fit,(),keephl,fill_strokes=True); I2=gt.decode(gt.render(fs,S))
    src_outline=nd.binary_dilation(I2>=40000-1,iterations=1)   # visible outline strokes of the colour art (occlusion-correct)
    allowed0=(dE<=(A.inner/2+A.tol)*sc*fit+0.5)|(dS<=(A.outer/2+A.tol)*sc*fit+0.5)|nd.binary_dilation(so_mask,iterations=int(A.inner/2+A.tol))
    allowed=allowed0|src_outline
    V=blk&~allowed
    lab,n=nd.label(V,structure=np.ones((3,3)))
    sizes=nd.sum(V,lab,range(1,n+1)) if n else np.array([])
    blobs=int((sizes>=A.min_blob).sum()); vpx=int(sizes[sizes>=A.min_blob].sum()) if n else 0
    # C reverse
    dB=nd.distance_transform_edt(~blk)
    miss=inner_E&(dB>A.inner/2+A.tol+1)
    ml,mn=nd.label(miss,structure=np.ones((3,3))); ms=nd.sum(miss,ml,range(1,mn+1)) if mn else np.array([])
    missing=int((ms>=A.min_edge).sum())
    # D validation against actual colour render
    C=gt.render(gt.full_color_svg(code,fit,(),keephl),S)
    ca=(C[...,3]>0) if keephl else (C[...,3]>=128); ia=I2>=0; iou=float((ca&ia).sum()/max((ca|ia).sum(),1))
    Ci=C[...,:3].astype(int); ce=np.zeros((S,S),bool)
    ce[:,1:]|=np.abs(Ci[:,1:]-Ci[:,:-1]).max(2)>=90; ce[1:]|=np.abs(Ci[1:]-Ci[:-1]).max(2)>=90
    ce&=ca&nd.binary_erosion(ca,iterations=2)
    I2m=np.where(I2>=40000,I2,I2); e2=edges(groups(I2m,merges)); agree=float((ce&(nd.distance_transform_edt(~e2)<=2.5)).sum()/max(ce.sum(),1)) if ce.sum()>20 else 1.0
    valid=iou>=0.97 and agree>=0.90
    geo=float(LOG.get(code,{}).get('geo_xray_len',0) or 0)
    res=dict(code=code,xray_blobs=blobs,xray_px=vpx,max_blob=int(sizes.max()) if n else 0,geo_xray_len=round(geo,2),
             missing_edges=missing,gt_iou=round(iou,4),gt_edge_agree=round(agree,4),gt_valid=valid,merges=len(merges),
             fail=bool(blobs>0 or geo>1.0 or not valid))
    if res['fail'] or (A.warn_heat and missing):
        hd=f'{A.out}/heat' if res['fail'] else f'{A.out}/heat-warn'
        os.makedirs(hd,exist_ok=True)
        base=Image.new('RGBA',(S,S),(255,255,255,255)); base.alpha_composite(Image.fromarray(v))
        h=np.array(base.convert('RGB')); Vd=nd.binary_dilation(V&np.isin(lab,np.nonzero(sizes>=A.min_blob)[0]+1),iterations=2)
        h[Vd]=[255,0,0]; h[miss&~Vd]=[0,140,255]
        Image.fromarray(h).save(f'{hd}/{code}.png')
    return res
LOG={}
if __name__=='__main__':
    logp=A.log or os.path.join(os.path.dirname(A.build.rstrip('/')),'build-log.json')
    if os.path.exists(logp): LOG.update(json.load(open(logp)))
    M=json.load(open(f'{A.build}/emoji-map.json'))
    codes=A.codes.split(',') if A.codes else [c for c in sorted(M) if not M[c][6]]
    os.makedirs(A.out,exist_ok=True)
    with Pool(A.workers) as P: R=P.map(one,codes,4)
    by={r['code']:r for r in R}
    if not A.codes:
        for c in M:
            if M[c][6]: by[c]=dict(by[M[c][6]],code=c,copy_of=M[c][6])
    fails=[r for r in by.values() if r['fail']]
    summ=dict(checked=len(R),total=len(by),xray_fail=sum(r['xray_blobs']>0 for r in by.values()),
        geo_fail=sum(r['geo_xray_len']>1 for r in by.values()),gt_invalid=sum(not r['gt_valid'] for r in by.values()),
        fail=len(fails),missing_output=sum(bool(r.get('missing_output')) for r in by.values()),missing_edge_warn=sum(r['missing_edges']>0 for r in by.values()),
        params=dict(size=A.size,inner_tol=A.inner/2+A.tol,outer_tol=A.outer/2+A.tol,min_blob=A.min_blob,min_edge=A.min_edge,merge_contrast=gt.MERGE_CONTRAST),
        worst=[(r['code'],r['xray_px']) for r in sorted(R,key=lambda r:-r['xray_px'])[:15] if r['xray_px']])
    json.dump(summ,open(f'{A.out}/summary.json','w'),indent=1)
    with open(f'{A.out}/results.csv','w') as f:
        k=list(R[0].keys()); f.write(','.join(k)+'\n')
        for r in sorted(by.values(),key=lambda r:r['code']): f.write(','.join(str(r.get(x,'')) for x in k)+'\n')
    worst=[r for r in sorted(R,key=lambda r:(-r['fail'],-r['xray_px'])) if r['fail']][:A.sheet]
    if worst:
        T=256; sh=Image.new('RGB',(8*T,((len(worst)+7)//8)*(T+20)),(128,128,128)); d=ImageDraw.Draw(sh)
        for i,r in enumerate(worst):
            if not os.path.exists(f"{A.out}/heat/{r['code']}.png"): continue
            im=Image.open(f"{A.out}/heat/{r['code']}.png").resize((T,T)); x,y=(i%8)*T,(i//8)*(T+20)
            sh.paste(im,(x,y)); d.text((x+4,y+T+4),f"{r['code']} px={r['xray_px']}{'' if r['gt_valid'] else ' GT!'}",fill='black')
        sh.save(f'{A.out}/worst-{A.sheet}.png')
    print(json.dumps(summ,indent=1))
    sys.exit(1 if fails else 0)
