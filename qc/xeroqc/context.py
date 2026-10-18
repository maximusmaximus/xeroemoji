"""Set-wide context: Unicode coverage, active locks, house spec, skin tones, exceptions, reference silhouettes."""
import os,re,csv,json,hashlib,ast
from .paths import ROOT,SET,QC,WORK,LOCKDIR,COVERAGE
TONES=('1f3fb','1f3fc','1f3fd','1f3fe','1f3ff')
KEEP_FE0F={'1f3f3-fe0f-200d-1f308','1f3f3-fe0f-200d-26a7-fe0f','1f3f4-200d-2620-fe0f','26d3-fe0f-200d-1f4a5'}   # Max kept these filenames
NON_SKIN={'1f463','1f464','1f465','1f5e3','1fac2','1fac6'}   # People & Body emoji with no skin (footprints, silhouettes, speaking head, hugging people, fingerprint)
def md5(p): return hashlib.md5(open(p,'rb').read()).hexdigest()
def norm(k): return k.replace('-fe0f','')
def coverage():
    """plan/coverage.csv = Unicode emoji-test 18.0 fully-qualified list (3,963) with name/group/subgroup"""
    rows={}
    for r in csv.DictReader(open(COVERAGE,encoding='utf-8')):
        k='-'.join(x.lower() for x in r['sequence'].split()); rows[k]=r
    return rows
def active_locks():
    src=open(QC+'/verify_locks.sh').read(); m=re.search(r'for f in (.*?); do',src)
    return m.group(1).split()
def lock_map():
    """path -> [(lock, md5)] over the ACTIVE locks only"""
    out={}
    for lf in active_locks():
        for l in open(f'{LOCKDIR}/{lf}',encoding='utf-8'):
            m=re.match(r'^([0-9a-f]{32})  (\S+)$',l.rstrip('\n'))
            if m: out.setdefault(m.group(2),[]).append((lf,m.group(1)))
    return out
def headwear():
    """the people_qc.py STANDING RULE headwear set, read from its source (single definition)"""
    src=open(WORK+'/people_qc.py').read(); m=re.search(r'HEADWEAR=(\{.*?\})',src,re.S); return ast.literal_eval(m.group(1))
def tone_stops():
    t=json.load(open(QC+'/skin-tones.json')); act=t['active_palette']
    return {k:[s.lower() for s in v['palettes'][act]['stops']] for k,v in t['tones'].items()}
def known_exceptions():
    p=QC+'/known-exceptions.json'
    if not os.path.exists(p): return {}
    d=json.load(open(p)); out={}
    for e in d['exceptions']: out[(e['file'],e['req'])]=e
    return out
class Ctx:
    def __init__(self):
        self.cov=coverage(); self.covn={norm(k):k for k in self.cov}
        self.locks=lock_map(); self.spec=json.load(open(QC+'/house-spec.json'))
        self.headwear=headwear(); self.tones=tone_stops(); self.kx=known_exceptions()
        self.refs={}   # silhouette references, filled by silhouettes.build()
    def row(self,f):
        k=f if f in self.cov else self.covn.get(norm(f)); return (k,self.cov.get(k)) if k else (None,None)
