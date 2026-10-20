#!/usr/bin/env python3
"""Full QC for one black line build: rule checks (pipeline check), x-ray test, spec audit, golden regression.
usage: qc.py --build OUT [--src ../../svg] [--out OUT/qc] [--golden golden]   exit 0 = all pass"""
import os,sys,json,argparse,subprocess
H=os.path.dirname(os.path.abspath(__file__))
ap=argparse.ArgumentParser(); ap.add_argument('--build',required=True); ap.add_argument('--src',default=os.path.join(H,'..','..','svg'))
ap.add_argument('--out'); ap.add_argument('--golden',default=os.path.join(H,'golden')); ap.add_argument('--emoji-test',default=None); a=ap.parse_args()
out=a.out or os.path.join(a.build,'qc'); os.makedirs(out,exist_ok=True); env=dict(os.environ,BL_SRC=a.src); R={}
def run(name,cmd):
    p=subprocess.run([sys.executable]+cmd,env=env,capture_output=True,text=True); R[name]=dict(rc=p.returncode,tail=p.stdout[-1500:]+p.stderr[-500:]); return p.returncode
run('checks',[f'{H}/pipeline.py','check','--build',a.build,'--src',a.src,'--out',f'{out}/checks'])
ck=json.load(open(f'{out}/checks/checks.json'))['summary']; R['checks']['failed']=ck['failed']
run('xray',[f'{H}/xray_test.py','--build',a.build,'--log',f'{a.build}/build-log.json','--out',f'{out}/xray'])
if os.path.isdir(os.path.join(a.build,'png','512')):
    view=f'{out}/auditview'; os.makedirs(view,exist_ok=True)
    for n,t in(('svg','svg'),('png','png/512'),('emoji-map.json','emoji-map.json')):
        p=f'{view}/{n}'
        if not os.path.lexists(p): os.symlink(os.path.abspath(os.path.join(a.build,t)),p)
    if a.emoji_test: run('audit',[f'{H}/audit.py','--repo',view,'--map','emoji-map.json','--out',f'{out}/audit','--emoji-test',a.emoji_test])
if os.path.isdir(f'{a.golden}/ref'): run('golden',[f'{H}/pipeline.py','golden','test','--build',a.build,'--golden',a.golden])
ok=all(v['rc']==0 for v in R.values()) and ck['failed']==0
json.dump(R,open(f'{out}/qc-summary.json','w'),indent=1); print(json.dumps({k:{'rc':v['rc']} for k,v in R.items()},indent=0),'PASS' if ok else 'FAIL'); sys.exit(0 if ok else 1)
