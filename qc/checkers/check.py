"""Xerographer artistic-continuity checker.
  python3 check.py --derive   -> house-spec.json (from 103 original-art emoji + 10 reference crops)
  python3 check.py            -> report.csv, flagged-sheet.jpg, review-pack.pdf
"""
import sys,os,re,json,csv,glob,colorsys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import imagehash
from skimage.metrics import structural_similarity as ssim
ROOT='/workspace/xerographer-emojis'; SET=ROOT+'/set'; QC=SET+'/qc'
sys.path.insert(0,SET+'/work')
def subgroups():
    return {'-'.join(x.lower() for x in r['sequence'].split() if x!='FE0F'):(r['subgroup'] if r['group']!='People & Body' else 'PB:'+r['subgroup']) for r in csv.DictReader(open(ROOT+'/plan/coverage.csv',encoding='utf-8')) if r['group'] in ('Smileys & Emotion','People & Body')}
isface=lambda sg: sg.startswith('face') or sg in ('cat-face','monkey-face')
def originals():
    import ast
    src=open(SET+'/work/recipes.py').read(); m=re.search(r'DIRECT=(\{.*?\})\nR=',src,re.S)
    return set(ast.literal_eval(m.group(1)))
def load_png(p,ref=False):
    im=Image.open(p).convert('RGBA')
    if ref:
        a=np.array(im.convert('RGB')).astype(int); al=(a.min(2)<235).astype(np.uint8)*255
        im=Image.fromarray(np.dstack([a.astype(np.uint8),al]),'RGBA'); im=im.crop(im.getbbox())
        s=480/max(im.size); im=im.resize((max(1,int(im.width*s)),max(1,int(im.height*s))),Image.LANCZOS)
        c=Image.new('RGBA',(512,512),(0,0,0,0)); c.paste(im,((512-im.width)//2,(512-im.height)//2)); im=c
    return im
def hsv(a):
    r,g,b=[a[...,i]/255. for i in range(3)]; mx=np.max(a[...,:3],2)/255.; mn=np.min(a[...,:3],2)/255.; d=mx-mn+1e-9
    h=np.where(mx==r,((g-b)/d)%6,np.where(mx==g,(b-r)/d+2,(r-g)/d+4))/6
    return h,np.where(mx>0,d/(mx+1e-9),0),mx
YY,XX=np.mgrid[0:512,0:512]
def metrics(im,force_face=None):
    a=np.array(im).astype(float); al=a[...,3]>128; h,s,v=hsv(a)
    yellow=al&(h>0.09)&(h<0.18)&(s>0.45)&(v>0.55)
    m={}; ys,xs=np.nonzero(al)
    if len(xs)==0: return m
    m['margin_min_px']=float(min(xs.min(),ys.min(),511-xs.max(),511-ys.max()))
    cx,cy=(xs.min()+xs.max())/2,(ys.min()+ys.max())/2
    dark=al&(v<0.32); runs=[]
    for ang in np.linspace(0,2*np.pi,16,endpoint=False):
        dx,dy=np.cos(ang),np.sin(ang); run=0
        for r in range(255,0,-1):
            x,y=int(cx+dx*r),int(cy+dy*r)
            if not(0<=x<512 and 0<=y<512) or not al[y,x]:
                if run: break
                continue
            if dark[y,x]: run+=1
            else: break
        if 0<run<=24: runs.append(run)   # runs >24px are solid dark fills, not outline
    m['outline_px']=float(np.median(runs)) if runs else 0.
    yel=yellow.sum()>0.25*al.sum()
    m['is_face']=float(yel if force_face is None else force_face); m['yellow_face']=float(bool(m['is_face']) and yel)
    if m['is_face'] and not yel:
        R=(xs.max()-xs.min()+ys.max()-ys.min())/4; m['face_diam_frac']=2*R/512
    if m['yellow_face']:
        yy,xx=np.nonzero(yellow); fx0,fx1,fy0,fy1=xx.min(),xx.max(),yy.min(),yy.max(); R=(fx1-fx0+fy1-fy0)/4; fcx,fcy=(fx0+fx1)/2,(fy0+fy1)/2
        m['face_diam_frac']=2*R/512; rr=np.hypot(XX-fcx,YY-fcy)/R; dy=(YY-fcy)/R
        for nm,band in (('top',(-0.75,-0.45)),('mid',(-0.15,0.15)),('bot',(0.45,0.75))):
            sel=yellow&(dy>band[0])&(dy<band[1])
            if sel.sum()>50:
                c=np.median(a[sel][:,:3],0); hh,ss,vv=colorsys.rgb_to_hsv(*(c/255))
                m[f'yellow_{nm}_hue']=hh*360; m[f'yellow_{nm}_sat']=ss; m[f'yellow_{nm}_val']=vv
        L=a[...,:3].mean(2); facein=al&(rr<0.95)
        thr=np.percentile(L[facein],98); gl=facein&(L>=thr)&(s<0.5)
        if gl.sum()>20:
            gy,gx=np.nonzero(gl); m['gloss_x']=(gx.mean()-fcx)/R; m['gloss_y']=(gy.mean()-fcy)/R; m['gloss_area']=gl.sum()/(np.pi*R*R)
        feat=al&(rr<0.88)&~yellow&~gl
        for nm,cond in (('eye',(dy<0.08)&(dy>-0.8)),('mouth',dy>0.12)):
            f=feat&cond&(((YY-fcy)/R<0.08) if nm=='eye' else True)
            if f.sum()>40:
                fy,fx=np.nonzero(f); lo,hi=np.percentile(fx,[2,98]); m[f'{nm}_width_frac']=(hi-lo)/(2*R); m[f'{nm}_y_frac']=(fy.mean()-fcy)/R
                lo,hi=np.percentile(fy,[2,98]); m[f'{nm}_height_frac']=(hi-lo)/(2*R)
        px=a[feat][:,:3]
    else: px=a[al&~dark][:,:3]
    if len(px)>50: m['_featpx']=px[np.random.RandomState(0).choice(len(px),min(800,len(px)),replace=False)]
    return m
def svg_metrics(p):
    s=open(p).read()
    return {'svg_kb':len(s)/1024,'svg_fills':len(set(re.findall(r'#[0-9a-fA-F]{6}',s))),'svg_has_text':float('<text' in s)}
RULES={'decided':'2026-10-14 by Max Infeld',
 'faces_outline':'face emoji keep the house outline (~10.5px @512, range in metrics.outline_px)',
 'symbols_outline':'hearts and emotion symbols use a 13px outline @512 (metrics_symbol.outline_px)',
 'hearts_shading':'hearts use the rich 4-stop radial gloss: white -> light -> base -> dark rim (#3a0010), plus white gloss ellipse upper-left',
 'symbol_size':'emotion-subgroup symbols are fitted to a ~30px margin @512',
 'no_live_text':'no <text> elements; lettering is converted to outlines (DejaVu Sans Bold, upright, no italic)',
 'motion_faces':'head-shaking/shaking faces keep the faded ghost copies',
 'hands':'hands are ~18% larger than the base part, with a ~5.5px dark (#24160a) outline and a soft 22% drop shadow; ALL hand faces (1fae3, 1fae1, 1fae2, 1f914) put the hands beside the eyes (variant C, Max 2026-10-14 20:52, overrides the earlier per-meaning exception), face expression parts kept intact, composite scaled to 86% so hands stay inside the margin',
 'mouths':'every face needs a visible mouth in house style (tapered dark arc for slight smile/frown)',
 'pensive_vs_disappointed':'1f614 pensive = sad-slanted brows + small flat mouth; 1f61e disappointed = no brows + deep wide frown',
 'checker':'face metrics only for face subgroups; non-yellow faces use metrics_nonyellow_face and skip yellow/gloss; dark runs >24px count as fill, not outline'}
NUMS=['outline_px','margin_min_px','face_diam_frac','yellow_top_hue','yellow_top_sat','yellow_top_val','yellow_mid_hue','yellow_mid_sat','yellow_mid_val','yellow_bot_hue','yellow_bot_sat','yellow_bot_val',
      'gloss_x','gloss_y','gloss_area','eye_width_frac','eye_y_frac','eye_height_frac','mouth_width_frac','mouth_y_frac','mouth_height_frac','svg_fills']
LABEL={'outline_px':'outline width (px @512)','margin_min_px':'edge margin (px)','face_diam_frac':'face diameter / canvas','gloss_x':'gloss highlight x','gloss_y':'gloss highlight y','gloss_area':'gloss highlight size',
       'eye_width_frac':'eye span / face','eye_y_frac':'eye vertical position','eye_height_frac':'eye height / face','mouth_width_frac':'mouth width / face','mouth_y_frac':'mouth vertical position','mouth_height_frac':'mouth height / face','svg_fills':'number of distinct colours'}
def palette_off(px,cen,thr): return float((np.min(np.linalg.norm(px[:,None]-cen[None],axis=2),1)>thr).mean())
def derive():
    from sklearn.cluster import KMeans
    orig=sorted(originals()); rows=[]
    SG=subgroups()
    for cp in orig:
        m=metrics(load_png(f'{SET}/png/{cp}.png'),isface(SG.get(cp,''))); m.update(svg_metrics(f'{SET}/svg/{cp}.svg')); rows.append(m)
    for p in sorted(glob.glob(ROOT+'/exploded/layout/artboard-*-piece-01.png')): rows.append(metrics(load_png(p,True),True))
    spec={'source':f'{len(orig)} original-art emoji in set/ + 10 reference crops (exploded/layout, = reference JPGs 01-10)','range_rule':'3rd-97th percentile of originals, widened by 15% of that span','metrics':{}}
    for k in NUMS:
        face_only=k not in ('outline_px','margin_min_px','svg_fills')
        v=np.array([r[k] for r in rows if k in r and (not face_only or r.get('yellow_face'))])
        if len(v)<5: continue
        lo,hi=np.percentile(v,[3,97]); pad=0.15*(hi-lo)+1e-6
        spec['metrics'][k]={'label':LABEL.get(k,k.replace('_',' ')),'mean':round(float(v.mean()),4),'sd':round(float(v.std()),4),'min_allowed':round(float(lo-pad),4),'max_allowed':round(float(hi+pad),4),'n':int(len(v)),'face_only':face_only}
    spec['metrics_nonyellow_face']={}
    for k in ('outline_px','margin_min_px','face_diam_frac'):
        v=np.array([r[k] for r in rows if k in r and r.get('is_face') and not r.get('yellow_face')])
        if len(v)>=5:
            lo,hi=v.min(),v.max(); pad=0.15*(hi-lo)+1e-6
            spec['metrics_nonyellow_face'][k]={'label':LABEL.get(k,k),'mean':round(float(v.mean()),4),'sd':round(float(v.std()),4),'min_allowed':round(float(lo-pad),4),'max_allowed':round(float(hi+pad),4),'n':int(len(v)),'face_only':True}
    spec['metrics_symbol']={'outline_px':{'label':'symbol outline width (px @512)','mean':13.0,'sd':1.0,'min_allowed':11.0,'max_allowed':15.0,'n':0,'face_only':False},
                            'margin_min_px':{'label':'symbol edge margin (px)','mean':30.0,'sd':6.0,'min_allowed':12.0,'max_allowed':45.0,'n':0,'face_only':False}}
    spec['rules']=RULES
    pal=np.vstack([r['_featpx'] for r in rows if '_featpx' in r]); km=KMeans(16,n_init=5,random_state=0).fit(pal); cen=km.cluster_centers_
    d=np.min(np.linalg.norm(pal[:,None]-cen[None],axis=2),1)
    spec['feature_palette']=['#%02x%02x%02x'%tuple(int(x) for x in c) for c in cen]; spec['palette_max_dist']=round(float(np.percentile(d,90)),1)
    offs=[palette_off(r['_featpx'],cen,spec['palette_max_dist']) for r in rows if '_featpx' in r]
    spec['metrics']['offpalette_frac']={'label':'share of feature pixels off the house palette','mean':round(float(np.mean(offs)),4),'sd':round(float(np.std(offs)),4),'min_allowed':0,'max_allowed':round(float(np.percentile(offs,97)*1.15),4),'n':len(offs),'face_only':False}
    json.dump(spec,open(QC+'/house-spec.json','w'),indent=1); print('spec metrics',len(spec['metrics']))
def run():
    spec=json.load(open(QC+'/house-spec.json')); SM=spec['metrics']; cen=np.array([[int(h[i:i+2],16) for i in (1,3,5)] for h in spec['feature_palette']])
    orig=originals(); cps=sorted(os.path.basename(p)[:-4] for p in glob.glob(SET+'/svg/*.svg'))
    imgs={cp:load_png(f'{SET}/png/{cp}.png') for cp in cps}
    flat=lambda im: Image.alpha_composite(Image.new('RGBA',im.size,'white'),im).convert('L')
    ph={cp:imagehash.phash(flat(imgs[cp])) for cp in cps}; small={cp:np.array(flat(imgs[cp]).resize((128,128))) for cp in cps}
    out=[]
    global SPEC_PB; SPEC_PB=spec
    SG=subgroups(); SN=spec.get('metrics_nonyellow_face',{}); SS=spec.get('metrics_symbol',{})
    for cp in cps:
        sg=SG.get(cp,''); m=metrics(imgs[cp],isface(sg))
        if sg=='monkey-face': m['yellow_face']=0.0
        m.update(svg_metrics(f'{SET}/svg/{cp}.svg'))
        if '_featpx' in m: m['offpalette_frac']=palette_off(m['_featpx'],cen,spec['palette_max_dist'])
        near=min((o for o in orig if o!=cp),key=lambda o:ph[cp]-ph[o])
        m['nearest_original']=near; m['phash_dist']=int(ph[cp]-ph[near]); m['ssim']=float(ssim(small[cp],small[near],data_range=255))
        reasons=[]; sev=0; kinds=[]
        if sg.startswith('PB:'): ranges={**SPEC_PB['metrics_hand' if sg.startswith('PB:hand') else 'metrics_people']}
        elif not m.get('is_face'): ranges={**{k:v for k,v in SM.items() if not v['face_only'] and k!='svg_fills'},**SS}
        elif not m.get('yellow_face'): ranges={**{k:v for k,v in SM.items() if not v['face_only'] and k!='svg_fills'},**SN}
        else: ranges=SM
        for k,sp in ranges.items():
            if k not in m or (k=='outline_px' and m[k]==0): continue
            if k=='offpalette_frac' and not m.get('yellow_face'): continue
            if sg.startswith('PB:') and k not in ranges: continue
            v=m[k]
            if v<sp['min_allowed'] or v>sp['max_allowed']:
                sev+=min(abs(v-sp['mean'])/(sp['sd']+1e-9),6); kinds.append(k)
                reasons.append(f"{sp['label']} {v:.3g} {'below' if v<sp['min_allowed'] else 'above'} house range {sp['min_allowed']:.3g}-{sp['max_allowed']:.3g}")
        if m.get('svg_has_text'): reasons.append('uses live <text> (font-dependent, not house vector art)'); sev+=2; kinds.append('text')
        if m.get('yellow_face') and not sg.startswith('PB:') and 'eye_width_frac' not in m: reasons.append('no eyes detected in eye zone'); sev+=2; kinds.append('noeyes')
        m.update(origin='original' if cp in orig else 'built',cp=cp,reasons=reasons,kinds=kinds,severity=round(sev,2),n_flags=len(reasons)); out.append(m)
    cols=['cp','origin','severity','n_flags','is_face','nearest_original','phash_dist','ssim','offpalette_frac']+[k for k in NUMS if k!='svg_fills']+['svg_fills','svg_kb','reasons']
    w=csv.writer(open(QC+'/report.csv','w',newline='')); w.writerow(cols)
    out.sort(key=lambda m:-m['severity'])
    for m in out: w.writerow([('; '.join(m[c]) if c=='reasons' else (round(m[c],4) if isinstance(m.get(c),float) else m.get(c,''))) for c in cols])
    json.dump([{k:v for k,v in m.items() if k!='_featpx'} for m in out],open(QC+'/report.json','w'),indent=0)
    fl=[m for m in out if m['reasons']]; sheet(fl,imgs); return out,fl
def sheet(fl,imgs):
    f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20); fb=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',26)
    pages=[]; per=4; RH=600; W=1900
    for i in range(0,len(fl),per):
        pg=Image.new('RGB',(W,60+RH*per),'white'); D=ImageDraw.Draw(pg); D.text((20,15),f'Xerographer continuity check - flagged, worst first (page {i//per+1}). candidate 512 | nearest original 512 | 72px pair | reasons',font=f,fill='black')
        for j,m in enumerate(fl[i:i+per]):
            y=60+j*RH; D.line((0,y,W,y),fill='#ccc',width=2)
            D.text((20,y+8),f"#{i+j+1}  {m['cp']}  ({m['origin']})  severity {m['severity']}  nearest {m['nearest_original']}  pHash {m['phash_dist']}  SSIM {m['ssim']:.2f}",font=fb,fill='#b00')
            for k,cp in enumerate((m['cp'],m['nearest_original'])):
                e=imgs[cp]; pg.paste(e,(20+k*530,y+48),e); s=e.resize((72,72),Image.LANCZOS); pg.paste(s,(1080+k*90,y+60),s)
            ty=y+150
            for r in m['reasons'][:14]:
                for n,x in enumerate(range(0,len(r),62)): D.text((1080,ty),('• ' if n==0 else '   ')+r[x:x+62],font=f,fill='black'); ty+=26
        pages.append(pg)
    tall=Image.new('RGB',(W,sum(p.height for p in pages)),'white'); y=0
    for p in pages: tall.paste(p,(0,y)); y+=p.height
    (tall.crop((0,0,tall.width,min(tall.height,64000)))).save(QC+'/flagged-sheet.jpg',quality=80)  # capped; full list in review-pack.pdf
    pages[0].save(QC+'/review-pack.pdf',save_all=True,append_images=pages[1:],resolution=150)
if __name__=='__main__':
    if '--derive' in sys.argv: derive()
    else:
        out,fl=run(); print('checked',len(out),'flagged',len(fl))
        for m in fl[:20]: print(m['cp'],m['origin'],m['severity'],'|','; '.join(m['reasons'][:4]))
