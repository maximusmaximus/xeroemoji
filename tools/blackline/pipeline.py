#!/usr/bin/env python3
"""Black line pipeline CLI (any SVG set: emoji or font glyphs exported as SVG, 512x512 viewBox recommended).
  pipeline.py build  --engine vector|raster --src SVG_DIR --out OUT [--map emoji-map.json] [--config cfg.json] [--codes a,b] [--workers N]
  pipeline.py diff   --a OUT_A --b OUT_B --out DIFF_DIR [--codes ..]
  pipeline.py check  --build OUT --src SVG_DIR --out QC_DIR [--codes ..]        (line weight, density, fidelity, topology, structure)
  pipeline.py select --a OUT_A --b OUT_B --diff DIFF_DIR --checks-a QC_A --checks-b QC_B --out OUT
  pipeline.py sheet  --builds label=OUT[,label=OUT..] --codes a,b|@file --out sheet.png [--size 256]
  pipeline.py golden test|approve --build OUT [--golden golden/]"""
import os,sys,json,argparse,shutil,traceback
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from multiprocessing import Pool
def _codes(a,src,M):
    if a and a.startswith('@'): return [l.strip() for l in open(a[1:]) if l.strip() and not l.startswith('#')]
    if a: return a.split(',')
    if M: return sorted(c for c in M if not M[c][6])
    return sorted(f[:-4] for f in os.listdir(src) if f.endswith('.svg'))
_G={}
def _job(code):
    import common as C,engine_vector as V,engine_raster as R,cairosvg
    a=_G['a']; E=V if a.engine=='vector' else R
    try:
        r=E.build(code,C.CFG,keephl=False); kh=False
        if 'fill="#000" d=""' in r['512']:
            r=E.build(code,C.CFG,keephl=True); kh=True
        o=a.out
        for d,s in(('svg',r['512']),('svg-72',r['72'])): open(f'{o}/{d}/{code}.svg','w').write(s)
        cairosvg.svg2png(bytestring=r['512'].encode(),write_to=f'{o}/png/512/{code}.png',output_width=512,output_height=512)
        cairosvg.svg2png(bytestring=r['72'].encode(),write_to=f'{o}/png/72/{code}.png',output_width=72,output_height=72)
        return code,dict(engine=a.engine,kept_highlights=kh,fit=r['info512']['fit'],fit72=r['info72']['fit'])
    except Exception as e:
        return code,dict(engine=a.engine,error=traceback.format_exc()[-600:])
def cmd_build(a):
    import common as C
    C.set_source(a.src); C.CFG.update(C.config(a.config))
    for d in('svg','svg-72','png/512','png/72'): os.makedirs(f'{a.out}/{d}',exist_ok=True)
    M=json.load(open(a.map)) if a.map else None
    codes=_codes(a.codes,a.src,M); _G['a']=a
    with Pool(a.workers,initializer=_init,initargs=(a,)) as P: R=dict(P.imap_unordered(_job,codes,2))
    logp=f'{a.out}/build-log.json'; L=json.load(open(logp)) if os.path.exists(logp) else {}
    L.update(R)
    if M:   # tone copies: identical files to their base
        n=0
        for c,v in M.items():
            b=v[6]
            if b and b in L and 'error' not in L[b]:
                for d,ext in(('svg','svg'),('svg-72','svg'),('png/512','png'),('png/72','png')): shutil.copy(f'{a.out}/{d}/{b}.{ext}',f'{a.out}/{d}/{c}.{ext}')
                L[c]=dict(L[b],copy_of=b); n+=1
        shutil.copy(a.map,f'{a.out}/emoji-map.json')
    json.dump(L,open(logp,'w'),indent=0)
    err=[c for c in R if 'error' in R[c]]
    print(json.dumps(dict(built=len(R),errors=len(err),error_codes=err[:20])))
def _init(a):
    import common as C; C.set_source(a.src); C.CFG.update(C.config(a.config)); _G['a']=a
def main():
    ap=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    sp=ap.add_subparsers(dest='cmd',required=True)
    b=sp.add_parser('build'); b.add_argument('--engine',choices=['vector','raster'],default='vector'); b.add_argument('--src',required=True)
    b.add_argument('--out',required=True); b.add_argument('--map'); b.add_argument('--config'); b.add_argument('--codes'); b.add_argument('--workers',type=int,default=os.cpu_count())
    import diffcheck
    diffcheck.add_parsers(sp)
    a=ap.parse_args()
    if a.cmd=='build': cmd_build(a)
    else: diffcheck.run(a)
if __name__=='__main__': main()
