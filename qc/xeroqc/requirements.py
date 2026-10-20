"""The requirement registry: single source of truth for qc/REQUIREMENTS.md and the scorer.
Each test(E) -> (status, measurement, reason); status in PASS / FAIL / NA (KNOWN is assigned from the exception lists)."""
import re,io,os
import numpy as np
from .paths import SET
from . import silhouettes as SIL
PASS,FAIL,NA,KNOWN='PASS','FAIL','N/A','KNOWN-EXCEPTION'
REQ=[]
def req(id,title,severity,weight,applies,test_desc):
    def deco(fn):
        REQ.append(dict(id=id,title=title,severity=severity,weight=weight,applies=applies,test=test_desc,fn=fn,doc=(fn.__doc__ or '').strip())); return fn
    return deco
def rng(v,lo,hi): return lo<=v<=hi
# ------------------------------------------------------------------ files / canvas
@req('XQ-FILE-01','Codepoint file naming, in Unicode 18.0','hard',3,'all',
     'filename = lowercase hex codepoints joined by "-", FE0F dropped (no exceptions); maps to a fully-qualified emoji-test 18.0 entry (plan/coverage.csv)')
def t_name(E):
    """File name must be the emoji's codepoint sequence, so it maps to exactly one Unicode emoji."""
    f=E['f']
    if not re.fullmatch(r'[0-9a-f]{2,6}(-[0-9a-f]{2,6})*',f): return FAIL,f,'not lowercase hex codepoints'
    if E['key'] is None: return FAIL,f,'not a fully-qualified Unicode 18.0 emoji'
    if f!=E['key'].replace('-fe0f','') and f not in E['ctx_keep']: return FAIL,E['key'],'FE0F in the name (house naming drops FE0F)'
    return PASS,E['key'],''
@req('XQ-FILE-02','SVG and PNG both present','hard',3,'all','svg/<cp>.svg and png/<cp>.png exist and are non-empty')
def t_pair(E):
    ok=E['svg'] is not None and E['png'] is not None
    return (PASS if ok else FAIL),{'svg':E['svg'] is not None,'png':E['png'] is not None},'' if ok else 'missing svg or png'
@req('XQ-PNG-01','PNG canvas 512x512 RGBA','hard',3,'all','PIL: size == (512,512), mode RGBA, transparent background (corner alpha 0), art present')
def t_png(E):
    im=E['png']
    if im is None: return FAIL,None,'no png'
    a=np.asarray(im)[...,3]; corners=int(a[0,0])+int(a[0,-1])+int(a[-1,0])+int(a[-1,-1])
    ok=im.size==(512,512) and E['png_mode']=='RGBA' and corners==0 and (a>0).sum()>0
    return (PASS if ok else FAIL),{'size':list(im.size),'mode':E['png_mode'],'corner_alpha':corners},'' if ok else 'canvas'
@req('XQ-SVG-01','Valid square SVG','hard',3,'all','parses as XML, root <svg> in the SVG namespace with a square viewBox, renders with cairosvg')
def t_svg(E):
    import xml.etree.ElementTree as ET
    s=E['svg']
    if s is None: return FAIL,None,'no svg'
    try: root=ET.fromstring(s)
    except ET.ParseError as e: return FAIL,str(e)[:60],'XML parse error'
    if not root.tag.endswith('svg'): return FAIL,root.tag,'root is not <svg>'
    vb=root.get('viewBox')
    if not vb: return FAIL,None,'no viewBox'
    v=[float(x) for x in re.split(r'[ ,]+',vb.strip())]
    if len(v)!=4 or abs(v[2]-v[3])>1e-6: return FAIL,vb,'viewBox not square'
    if E['render'] is None: return FAIL,vb,'cairosvg render failed'
    return PASS,vb,''
@req('XQ-SVG-02','No live text','hard',3,'all','no <text>, <tspan>, <textPath> or font-family; lettering must be outlined paths (house rule no_live_text)')
def t_text(E):
    s=E['svg'] or ''; bad=[t for t in ('<text','<tspan','<textPath','font-family') if t in s]
    return (FAIL,bad,'live text: '+','.join(bad)) if bad else (PASS,0,'')
@req('XQ-SVG-03','Self-contained SVG references','hard',2,'all','every url(#id) / href="#id" is defined in the file; no external http/file/data-font references')
def t_refs(E):
    s=E['svg'] or ''; ids=set(re.findall(r'\bid="([^"]+)"',s))
    refs=set(re.findall(r'url\(#([^)]+)\)',s))|set(re.findall(r'href="#([^"]+)"',s))
    und=sorted(refs-ids); ext=re.findall(r'(?:href|src)="(?:https?:|file:)[^"]*"',s)
    if und or ext: return FAIL,{'undefined':und[:5],'n_undefined':len(und),'external':len(ext)},'undefined/external references'
    return PASS,{'refs':len(refs)},''
@req('XQ-SVG-04','PNG is the render of the SVG','hard',3,'all','cairosvg 512px render of the SVG vs the PNG: <=0.5% of pixels differ by more than 48/255 in any RGBA channel')
def t_match(E):
    if E['render'] is None or E['png'] is None: return FAIL,None,'cannot compare'
    a=E['render'].astype(int); b=np.asarray(E['png']).astype(int)
    if a.shape!=b.shape: return FAIL,None,'size differs'
    d=float((np.abs(a-b).max(2)>48).mean())
    return (PASS if d<=.005 else FAIL),round(d,5),'' if d<=.005 else f'PNG differs from the SVG render on {d:.2%} of pixels'
# ------------------------------------------------------------------ locks
@req('XQ-LOCK-01','Covered by exactly one active lock','hard',3,'all','svg and png paths each appear in exactly one lock listed in qc/verify_locks.sh')
def t_lock(E):
    L=E['locks']; s=L.get(f"svg/{E['f']}.svg",[]); p=L.get(f"png/{E['f']}.png",[])
    ok=len(s)==1 and len(p)==1
    return (PASS if ok else FAIL),{'svg_locks':[x[0] for x in s],'png_locks':[x[0] for x in p]},'' if ok else 'not covered by exactly one active lock'
@req('XQ-LOCK-02','Lock hash matches','hard',3,'all','md5 of svg and png equal the md5 recorded in the active lock')
def t_hash(E):
    L=E['locks']; s=L.get(f"svg/{E['f']}.svg",[]); p=L.get(f"png/{E['f']}.png",[])
    if not s or not p: return FAIL,None,'not locked'
    ok=all(m==E['svg_md5'] for _,m in s) and all(m==E['png_md5'] for _,m in p)
    return (PASS if ok else FAIL),{'lock':s[0][0]},'' if ok else 'md5 differs from the lock'
# ------------------------------------------------------------------ check.py metrics (house-spec ranges)
def out_range(E):
    sg=E['sg']; g=E['group']; sp=E['spec']
    if sg.startswith('PB:hand'): r=sp['metrics_hand']['outline_px']; return 'PB hand',r['min_allowed'],r['max_allowed']
    if sg=='PB:body-parts': return 'PB body part (house 6px)',5.0,8.0
    if sg.startswith('PB:'): r=sp['metrics_people']['outline_px']; return 'People',r['min_allowed'],r['max_allowed']
    if E['m'].get('is_face'):
        if E['m'].get('yellow_face'): r=sp['metrics']['outline_px']; return 'yellow face',r['min_allowed'],r['max_allowed']
        r=sp['metrics_nonyellow_face']['outline_px']; return 'non-yellow face',r['min_allowed'],r['max_allowed']
    r=sp['metrics_symbol']['outline_px']; return 'object/symbol (13px house)',r['min_allowed'],r['max_allowed']
@req('XQ-OUT-01','Outline width in the group range','hard',3,'all with a measurable outline',
     'check.metrics outline_px @512: yellow faces 8.55-12.45; non-yellow faces 4.875-14.625; PB hands 4-8; PB body parts 5-8 (house 6px); other People & Body 5-15; everything else 11-15 (house 13px). Toned files are measured tone-neutral (check.tone_neutral_outline: skin stops and the dark-tone inner contrast rim swapped for base colours, so dark skin is not counted as ink). n/a if no outline is measurable (outline_px 0)')
def t_out(E):
    v=E['m'].get('outline_px',0)
    if not v: return NA,0,''
    lab,lo,hi=out_range(E)
    return (PASS if rng(v,lo,hi) else FAIL),{'outline_px':v,'range':[lo,hi],'class':lab},'' if rng(v,lo,hi) else f'outline {v:g}px outside {lab} {lo:g}-{hi:g}'
def mar_range(E):
    sg=E['sg']; r=E['row']; sp=E['spec']
    if r['subgroup'] in ('country-flag','subdivision-flag'): return 'flag tile (by design 67px)',60.0,75.0
    if r['group']=='Flags' and r['subgroup']=='flag': return 'pennant flag (by design 47px)',40.0,50.0
    if E['tile']: return 'full-bleed symbol tile/sign (by design 4px)',2.0,8.0
    if sg.startswith('PB:'): x=sp['metrics_hand' if sg.startswith('PB:hand') else 'metrics_people']['margin_min_px']; return 'People',x['min_allowed'],x['max_allowed']
    if E['m'].get('is_face'):
        x=(sp['metrics'] if E['m'].get('yellow_face') else sp['metrics_nonyellow_face'])['margin_min_px']; return 'face',x['min_allowed'],x['max_allowed']
    x=sp['metrics_symbol']['margin_min_px']; return 'object/symbol',x['min_allowed'],x['max_allowed']
@req('XQ-MAR-01','Edge margin in the group range','hard',3,'all',
     'check.metrics margin_min_px @512: country/subdivision flags 60-75 (by-design flag tile, 67); pennant flags 40-50 (47); full-bleed Symbols (tiles, keycaps, round signs: alpha box >=94% of the canvas) 2-8 (4); People & Body 12-60; yellow faces 13.15-37.85; non-yellow faces 0.25-136.75; everything else 12-45')
def t_mar(E):
    v=E['m'].get('margin_min_px')
    if v is None: return NA,None,''
    lab,lo,hi=mar_range(E)
    return (PASS if rng(v,lo,hi) else FAIL),{'margin_px':v,'range':[lo,hi],'class':lab},'' if rng(v,lo,hi) else f'margin {v:g}px outside {lab} {lo:g}-{hi:g}'
def face_metrics(E,keys,title):
    m=E['m']
    if not (m.get('is_face') and m.get('yellow_face')) or E['sg'].startswith('PB:'): return NA,None,''
    SM=E['spec']['metrics']; bad=[]; meas={}
    for k in keys:
        if k not in m: continue
        v=m[k]; meas[k]=round(float(v),4); sp=SM[k]
        if not rng(v,sp['min_allowed'],sp['max_allowed']): bad.append(f"{sp['label']} {v:.3g} not in {sp['min_allowed']:.3g}-{sp['max_allowed']:.3g}")
    if not meas: return NA,None,''
    return (FAIL if bad else PASS),meas,'; '.join(bad)
YEL=[f'yellow_{a}_{b}' for a in ('top','mid','bot') for b in ('hue','sat','val')]
@req('XQ-FACE-01','House yellow face gradient','soft',2,'yellow faces (Smileys)','check.metrics yellow top/mid/bot hue, sat, val inside house-spec ranges (3rd-97th pct of the original art, widened 15%)')
def t_f1(E): return face_metrics(E,YEL,'yellow')
@req('XQ-FACE-02','Gloss highlight position and size','soft',1,'yellow faces','gloss_x, gloss_y, gloss_area inside house-spec ranges')
def t_f2(E): return face_metrics(E,['gloss_x','gloss_y','gloss_area'],'gloss')
@req('XQ-FACE-03','Eyes present and placed','soft',2,'yellow faces','eyes detected in the eye zone; eye_width_frac, eye_y_frac, eye_height_frac inside house-spec ranges')
def t_f3(E):
    m=E['m']
    if not (m.get('is_face') and m.get('yellow_face')) or E['sg'].startswith('PB:'): return NA,None,''
    if 'eye_width_frac' not in m: return FAIL,None,'no eyes detected in the eye zone'
    return face_metrics(E,['eye_width_frac','eye_y_frac','eye_height_frac'],'eyes')
@req('XQ-FACE-04','Mouth present and placed','soft',2,'yellow faces','mouth_width_frac, mouth_y_frac, mouth_height_frac inside house-spec ranges')
def t_f4(E): return face_metrics(E,['mouth_width_frac','mouth_y_frac','mouth_height_frac'],'mouth')
@req('XQ-FACE-05','Face diameter','soft',1,'yellow faces','face_diam_frac inside the house-spec range')
def t_f5(E): return face_metrics(E,['face_diam_frac'],'diam')
@req('XQ-FACE-06','Feature colours on the house palette','soft',1,'yellow faces','offpalette_frac (feature pixels farther than palette_max_dist from the 16-colour feature palette) <= house max')
def t_f6(E): return face_metrics(E,['offpalette_frac'],'palette')
@req('XQ-FACE-07','Colour count','soft',1,'yellow faces','distinct #rrggbb colours in the SVG inside the house-spec range')
def t_f7(E): return face_metrics(E,['svg_fills'],'fills')
# ------------------------------------------------------------------ highlights
@req('XQ-HL-01','Highlights do not touch the outline','hard',3,'files with gloss/highlight elements',
     'work/hlaudit.py (fixed outline mask, tool of record 2026-10-18) audit(svg,2) == 0 px; files on qc/hlaudit-known-exceptions.json with an unchanged md5 are KNOWN-EXCEPTION')
def t_hl(E):
    H=E['H']; s=E['svg'] or ''
    if not H.HL.search(s): return NA,0,''
    n,px=H.audit(s,2)
    if n==0: return PASS,{'hit_px':0,'hl_px':int(px)},''
    if H.known_exception(E['f'],s): return KNOWN,{'hit_px':int(n),'hl_px':int(px)},f'{n}px highlight on outline (hlaudit known-exception list)'
    return FAIL,{'hit_px':int(n),'hl_px':int(px)},f'{n}px of highlight touch the outline'
# ------------------------------------------------------------------ people
@req('XQ-MOUTH-01','Crescent mouths carry the shared mouth gradient','hard',2,'files with head-art crescent mouths',
     'work/mouthbowl.pairs: every crescent-mouth bowl uses an mbowl-* gradient, unless its crescent is <60% visible (mouthbowl.crescent_visibility; covered by visor/hands/beard) -> that mouth is n/a')
def t_mouth(E):
    MB=E['MB']; s=E['svg'] or ''; ps=MB.pairs(s)
    if not ps: return NA,0,''
    bad=0; cov=0; ok=0
    for a,b in ps:
        if 'url(#mbowl-' in a.group(0): ok+=1; continue
        if MB.crescent_visibility(s,b)<0.6: cov+=1; continue
        bad+=1
    if bad: return FAIL,{'mouths':len(ps),'gradient':ok,'covered':cov,'missing':bad},f'{bad} visible crescent mouth(s) without the mbowl gradient'
    if not ok: return NA,{'mouths':len(ps),'covered':cov},''
    return PASS,{'mouths':len(ps),'gradient':ok,'covered':cov},''
EYE=('_g459','_g460','_g492','_g493','_g441','_g442','_g409','_g410')
@req('XQ-EYE-01','Eye rims present','hard',2,'files using the house head art (template6 heads)',
     'every head-art eye-rim gradient referenced (ids *_g459/_g460/_g492/_g493/_g441/_g442/_g409/_g410) is defined, so the rims render (families/03/04 frag-cache bug)')
def t_eye(E):
    s=E['svg'] or ''
    if 'template6Artboard' not in s: return NA,None,''
    refs={r for r in re.findall(r'url\(#([^)]+)\)',s) if r.startswith('template6Artboard') and r.endswith(EYE)}
    if not refs: return NA,0,''
    ids=set(re.findall(r'\bid="([^"]+)"',s)); und=sorted(refs-ids)
    return (FAIL,{'rims':len(refs),'undefined':und},'eye-rim gradient(s) undefined') if und else (PASS,{'rims':len(refs)},'')
@req('XQ-HAT-01','Headwear fits the head (hatfit)','hard',3,'People & Body files with headwear codepoints (people_qc HEADWEAR) or data-hat markers',
     'work/hatfit.check_svg: markers present and 0 violation px of head/hair above the band')
def t_hat(E):
    s=E['svg'] or ''
    if not E['sg'].startswith('PB:'): return NA,None,''
    if not (set(E['f'].split('-'))&E['headwear'] or 'data-hat' in s): return NA,None,''
    r=E['HF'].check_svg(s)
    if r is None: return FAIL,None,'headwear without data-hat markers'
    if 'error' in r: return FAIL,r,r['error']
    return (FAIL if r['viol_px'] else PASS),{'viol_px':r['viol_px']},(f"{r['viol_px']}px head/hair above the hat band" if r['viol_px'] else '')
@req('XQ-POSE-01','Skeleton figures pass posecheck','hard',3,'files with an embedded data-skeleton',
     'work/posecheck.check_svg: every embedded skeleton inside the biomechanics ranges for its pose (qc/pose-validation.md)')
def t_pose(E):
    r=E['PC'].check_svg(E['svg'] or '')
    if r is None: return NA,None,''
    pose,rows,fails=r
    return (FAIL if fails else PASS),{'pose':pose,'fails':list(fails)[:6]},('posecheck: '+', '.join(fails[:4]) if fails else '')
HG=re.compile(r'<g transform="translate\(([-\d.]+)[ ,]([-\d.]+)\)(?: rotate\(([-\d.]+)\))? scale\(([-\d.]+)(?:[ ,]([-\d.]+))?\) translate\(-100 -120\)">')
def hand_groups(s):
    ms=list(HG.finditer(s)); out=[]
    for i,m in enumerate(ms):
        end=ms[i+1].start() if i+1<len(ms) else min(len(s),m.end()+8000)
        w=[float(x) for x in re.findall(r'stroke="#24160a" stroke-width="([\d.]+)"',s[m.end():end])]
        out.append({'scale':(round(abs(float(m.group(4))),3),round(abs(float(m.group(5) or m.group(4))),3)),'ink':max(w) if w else None})
    return out
@req('XQ-HAND-01','Paired hands are matched','soft',2,'figures with two or more house hands',
     'all house-hand groups (people4 hand frame) in a file share the same scale and the same ink stroke width')
def t_hand1(E):
    hg=E['hands']
    if len(hg)<2: return NA,len(hg),''
    sc=sorted({h['scale'] for h in hg}); ink=sorted({h['ink'] for h in hg if h['ink']})
    ok=len(sc)==1 and len(ink)<=1
    return (PASS if ok else FAIL),{'hands':len(hg),'scales':[list(x) for x in sc],'ink':ink},'' if ok else 'hands differ in '+(' and '.join(x for x,b in (('scale',len(sc)>1),('stroke',len(ink)>1)) if b))
@req('XQ-HAND-02','Hand stroke consistent across skin tones','soft',1,'house-hand figures that have tone variants',
     'the hand ink stroke width equals the modal value of the same emoji across its base + 5 tone files')
def t_hand2(E):
    fam=E['hand_family']
    if not E['hands'] or not fam: return NA,None,''
    mine=sorted({h['ink'] for h in E['hands'] if h['ink']})
    return (PASS if mine==fam else FAIL),{'ink':mine,'family_mode':fam},'' if mine==fam else f'hand stroke {mine} vs tone family {fam}'
@req('XQ-TONE-01','Skin tone correct','hard',3,'People & Body (except no-skin emoji) and every file with a tone modifier',
     'each tone named in the filename has its active-palette 4-stop skin gradient (qc/skin-tones.json) present (>=3 of 4 stops); no tone that is not named is present')
def t_tone(E):
    f=E['f']; s=(E['svg'] or '').lower(); named=[t for t in f.split('-') if t in E['tones']] or ['base']
    if not (E['sg'].startswith('PB:') or named!=['base']) or f in E['non_skin']: return NA,None,''
    pres=sorted(k for k,v in E['tones'].items() if sum(x in s for x in v)>=3)
    miss=[t for t in named if t not in pres]; extra=[t for t in pres if t not in named]
    if miss or extra: return FAIL,{'named':named,'present':pres},('missing '+','.join(miss) if miss else '')+(' extra '+','.join(extra) if extra else '')
    return PASS,{'named':named},''
# ------------------------------------------------------------------ group shapes
def sil(E,cls,thr,label):
    if cls not in E['classes']: return NA,None,''
    ref=E['refs'].get(cls)
    v=SIL.iou(E['mask'],ref)
    return (PASS if v>=thr else FAIL),round(v,4),'' if v>=thr else f'{label} silhouette IoU {v:.3f} < {thr}'
@req('XQ-KEY-01','Keycap shape','soft',2,'Symbols keycap subgroup','alpha silhouette IoU >= 0.97 against the keycap reference (majority vote of all keycaps)')
def t_key(E): return sil(E,'keycap',.97,'keycap')
@req('XQ-FLAG-01','Flag silhouette','soft',2,'country and subdivision flags','alpha silhouette IoU >= 0.90 against the flag reference (majority vote of all country/subdivision flags)')
def t_flag(E): return sil(E,'flag',.90,'flag')
@req('XQ-SYM-01','Symbol tile shape','soft',1,'Symbols drawn on a tile (art fills >=88% of a >=94% canvas box)','alpha silhouette IoU >= 0.97 against the symbol-tile reference')
def t_tile(E): return sil(E,'tile',.97,'tile')
SET_REQ=[('XQ-SET-01','Unicode 18.0 coverage','hard','every fully-qualified emoji-test 18.0 entry (plan/coverage.csv, 3,963) has a file pair'),
         ('XQ-SET-02','No duplicates','hard','no two files map to the same emoji after FE0F normalisation'),
         ('XQ-SET-03','No orphans','hard','every svg/png maps to an emoji; no stray files in svg/ or png/'),
         ('XQ-SET-04','All active locks verify','hard','bash qc/verify_locks.sh exits 0 (every active lock md5-clean)')]
MANUAL=[('XQ-MAN-01','Front-facing house heads, matched house hands (R2 style), no ponytails on body-kit figures','review sheets'),
        ('XQ-MAN-02','Reads at 32px and 24px','review sheets at 512/32/24'),
        ('XQ-MAN-03','Meaning matches the vendors (Apple/Google research columns)','vendor comparison sheets'),
        ('XQ-MAN-04','Per-emoji design decisions recorded by Max (qc/decisions, audit docs)','human review')]
