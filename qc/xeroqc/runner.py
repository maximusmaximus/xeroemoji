"""Evaluate every emoji against the registry, score, grade, and write results."""
import os,re,io,json,csv,hashlib,subprocess,datetime,collections
import numpy as np
from PIL import Image
from .paths import SET,QC,WORK,LOCKDIR
from . import VERSION, context as CX, silhouettes as SIL, requirements as RQ
G={}   # worker globals (fork)
def _tools():
    import check, hlaudit, hatfit, posecheck, mouthbowl
    return check,hlaudit,hatfit,posecheck,mouthbowl
def sg_of(row):
    if not row: return ''
    return 'PB:'+row['subgroup'] if row['group']=='People & Body' else (row['subgroup'] if row['group']=='Smileys & Emotion' else '')
def base_key(f): return '-'.join(x for x in f.split('-') if x not in CX.TONES)
def hand_families(files,svgdir):
    fam=collections.defaultdict(list)
    for f in files:
        s=open(f'{svgdir}/{f}.svg').read(); hg=RQ.hand_groups(s)
        if hg: fam[base_key(f)].append(tuple(sorted({h['ink'] for h in hg if h['ink']})))
    out={}
    for k,v in fam.items():
        if len(v)>=2:
            c=collections.Counter(v).most_common(); out[k]=list(c[0][0]) if (len(c)==1 or c[0][1]>c[1][1]) else None
    return out
def prepare(files,svgdir=SET+'/svg'):
    ctx=CX.Ctx(); C,ref=SIL.build(ctx,files)
    G.update(ctx=ctx,classes={f:k for k,fl in C.items() for f in fl},refs=ref,fam=hand_families(files,svgdir))
    G['tools']=_tools()
def evaluate(f,svg_path=None,png_path=None):
    ctx=G['ctx']; check,H,HF,PC,MB=G['tools']
    sp=svg_path or f'{SET}/svg/{f}.svg'; pp=png_path or f'{SET}/png/{f}.png'
    key,row=ctx.row(f)
    E=dict(f=f,key=key,row=row or {'group':'?','subgroup':'?','name':'?'},ctx_keep=CX.KEEP_FE0F,locks=ctx.locks,spec=ctx.spec,
           headwear=ctx.headwear,tones=ctx.tones,non_skin=CX.NON_SKIN,H=H,HF=HF,PC=PC,MB=MB,refs=G['refs'])
    E['group']=E['row']['group']; E['sg']=sg_of(row)
    E['svg']=open(sp,encoding='utf-8').read() if os.path.exists(sp) and os.path.getsize(sp) else None
    E['svg_md5']=CX.md5(sp) if E['svg'] is not None else None
    if os.path.exists(pp) and os.path.getsize(pp):
        im=Image.open(pp); E['png_mode']=im.mode; E['png']=im.convert('RGBA'); E['png_md5']=CX.md5(pp)
    else: E['png']=None; E['png_mode']=None; E['png_md5']=None
    try:
        import cairosvg
        E['render']=np.asarray(Image.open(io.BytesIO(cairosvg.svg2png(bytestring=E['svg'].encode(),output_width=512,output_height=512))).convert('RGBA'))
    except Exception: E['render']=None
    m={}
    if E['png'] is not None and E['png'].size==(512,512):
        m=check.metrics(E['png'],check.isface(E['sg']))
        if E['sg']=='monkey-face': m['yellow_face']=0.0
        if E['svg'] is not None: m.update(check.svg_metrics(sp))
        if E['svg'] is not None:
            tno=check.tone_neutral_outline(f,E['svg'],check.isface(E['sg']))   # outline measured with dark skin neutralised
            if tno is not None: m['outline_px']=tno
        if '_featpx' in m:
            cen=np.array([[int(h[i:i+2],16) for i in (1,3,5)] for h in ctx.spec['feature_palette']])
            m['offpalette_frac']=check.palette_off(m['_featpx'],cen,ctx.spec['palette_max_dist']); m.pop('_featpx')
    E['m']=m
    E['mask']=SIL.mask(f,pp) if (f in G['classes'] and E['png'] is not None) else None
    E['classes']={G['classes'][f]} if f in G['classes'] else set()
    E['tile']=E['group']=='Symbols' and E['png'] is not None and SIL.bleed(SIL.mask(f,pp))   # full-bleed symbol: tile, keycap, round sign
    E['hands']=RQ.hand_groups(E['svg'] or ''); E['hand_family']=G['fam'].get(base_key(f))
    res={}
    for r in RQ.REQ:
        try: st,meas,why=r['fn'](E)
        except Exception as e: st,meas,why=RQ.FAIL,None,f'test error: {type(e).__name__}: {str(e)[:80]}'
        if st==RQ.FAIL:
            kx=ctx.kx.get((f,r['id']))
            if kx and kx.get('svg_md5')==E['svg_md5'] and kx.get('png_md5')==E['png_md5']:
                st=RQ.KNOWN; why=(why+' | ' if why else '')+'known exception: '+kx['reason']
        res[r['id']]={'status':st,'measure':_clean(meas),'reason':why}
    return score(f,E,res)
def _clean(x):
    if isinstance(x,dict): return {k:_clean(v) for k,v in sorted(x.items())}
    if isinstance(x,(list,tuple)): return [_clean(v) for v in x]
    if isinstance(x,(np.floating,float)): return round(float(x),4)
    if isinstance(x,(np.integer,)): return int(x)
    if isinstance(x,(np.bool_,)): return bool(x)
    return x
def score(f,E,res):
    W={r['id']:r for r in RQ.REQ}; app=[k for k,v in res.items() if v['status']!=RQ.NA]
    tw=sum(W[k]['weight'] for k in app)
    ok=sum(W[k]['weight'] for k in app if res[k]['status'] in (RQ.PASS,RQ.KNOWN))
    strict=sum(W[k]['weight'] for k in app if res[k]['status']==RQ.PASS)
    hard=[k for k in app if res[k]['status']==RQ.FAIL and W[k]['severity']=='hard']
    soft=[k for k in app if res[k]['status']==RQ.FAIL and W[k]['severity']=='soft']
    known=[k for k in app if res[k]['status']==RQ.KNOWN]
    grade='FAIL' if hard else ('PASS-with-known-exceptions' if known else 'PASS')
    return {'cp':f,'name':E['row'].get('name','?'),'group':E['group'],'subgroup':E['row'].get('subgroup','?'),
            'svg_md5':E['svg_md5'],'png_md5':E['png_md5'],'score':round(100*ok/tw,2) if tw else 100.0,'score_strict':round(100*strict/tw,2) if tw else 100.0,
            'grade':grade,'hard_fails':hard,'soft_fails':soft,'known_exceptions':known,'n_applicable':len(app),'results':res}
def _one(f): return evaluate(f)
def set_checks(ctx,files):
    have=set(files); keys=collections.Counter(CX.norm(f) for f in files)
    missing=sorted(k for k in ctx.cov if k not in have and CX.norm(k) not in {CX.norm(x) for x in have})
    dup=sorted(k for k,v in keys.items() if v>1)
    orph=sorted(f for f in files if ctx.row(f)[0] is None)
    sv={x[:-4] for x in os.listdir(SET+'/svg')}; pn={x[:-4] for x in os.listdir(SET+'/png')}
    stray=sorted((sv^pn)|{x for x in os.listdir(SET+'/svg') if not x.endswith('.svg')}|{x for x in os.listdir(SET+'/png') if not x.endswith('.png')})
    vl=subprocess.run(['bash',QC+'/verify_locks.sh'],capture_output=True,text=True)
    ok_n=len(re.findall(r'^OK ',vl.stdout,re.M)); fail_n=len(re.findall(r'^FAIL ',vl.stdout,re.M))
    return {'XQ-SET-01':{'status':'PASS' if not missing else 'FAIL','measure':{'expected':len(ctx.cov),'covered':len(ctx.cov)-len(missing)},'missing':missing[:20]},
            'XQ-SET-02':{'status':'PASS' if not dup else 'FAIL','duplicates':dup},
            'XQ-SET-03':{'status':'PASS' if not (orph or stray) else 'FAIL','orphans':orph,'stray':stray},
            'XQ-SET-04':{'status':'PASS' if vl.returncode==0 else 'FAIL','measure':{'locks_ok':ok_n,'locks_fail':fail_n}}}
def tool_fingerprint():
    here=os.path.dirname(__file__); fps={}
    for p in sorted(os.listdir(here)):
        if p.endswith('.py'): fps['xeroqc/'+p]=CX.md5(f'{here}/{p}')
    for p in ('qc/check.py','work/hlaudit.py','work/hatfit.py','work/posecheck.py','work/skel9.py','work/mouthbowl.py','work/people_qc.py',
              'qc/verify_locks.sh','qc/house-spec.json','qc/skin-tones.json','qc/hlaudit-known-exceptions.json','qc/known-exceptions.json'):
        fp=f'{SET}/{p}'
        if not os.path.exists(fp) and '/' in p: fp=f'{QC}/checkers/{p.split("/")[-1]}'   # repo layout
        if os.path.exists(fp): fps[p]=CX.md5(fp)
    agg=hashlib.md5(''.join(f'{k}={v}\n' for k,v in sorted(fps.items())).encode()).hexdigest()
    return agg,fps
def run(files=None,jobs=7,out=None):
    import multiprocessing as mp
    allf=sorted(x[:-4] for x in os.listdir(SET+'/svg') if x.endswith('.svg'))
    fl=sorted(files) if files else allf
    prepare(allf)
    with mp.get_context('fork').Pool(jobs) as p: R=p.map(_one,fl,chunksize=8)
    R.sort(key=lambda r:r['cp'])
    now=datetime.datetime.now()   # box clock = America/Los_Angeles
    agg,fps=tool_fingerprint(); ctx=G['ctx']
    meta={'tool':'xeroqc','version':VERSION,'tool_md5':agg,'tool_files_md5':fps,'git':_git(),'timestamp':now.strftime('%Y-%m-%d %H:%M:%S')+' PT (America/Los_Angeles)',
          'n_files':len(fl),'lock_state':{'active_locks':len(CX.active_locks()),'locks':{l:CX.md5(f'{LOCKDIR}/{l}') for l in CX.active_locks()}},
          'known_exceptions':{'hlaudit':_n(QC+'/hlaudit-known-exceptions.json','count'),'requirement':len(ctx.kx)}}
    sc=set_checks(ctx,allf) if not files else {}
    meta['lock_state']['verify_locks']=sc.get('XQ-SET-04',{}).get('measure')
    reqs=[{k:v for k,v in r.items() if k!='fn'} for r in RQ.REQ]
    out=out or f"{QC}/results/{now.strftime('%Y%m%d-%H%M')}PT"
    os.makedirs(out,exist_ok=True)
    from . import report
    report.write(out,meta,sc,reqs,R)
    return out,meta,sc,R
def _n(p,k):
    try: return json.load(open(p))[k]
    except Exception: return None
def _git():
    r=subprocess.run(['git','-C',os.path.dirname(__file__),'rev-parse','HEAD'],capture_output=True,text=True)
    return r.stdout.strip() if r.returncode==0 else 'not a git checkout (tool_md5 identifies the tool)'
