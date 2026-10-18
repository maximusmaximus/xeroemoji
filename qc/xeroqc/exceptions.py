"""Known-exception list (qc/known-exceptions.json): requirement failures in locked art that Max accepted or declined to fix.
Every entry is pinned to the file's svg+png md5: if the file changes, the exception no longer applies.
The policy below is the ONLY source of entries; each rule cites where the acceptance is recorded.
Build:  python -m xeroqc bootstrap-exceptions <results.json of a run made without the list>"""
import json,datetime
from .paths import QC
FACE_REQS={'XQ-OUT-01','XQ-MAR-01','XQ-FACE-01','XQ-FACE-02','XQ-FACE-03','XQ-FACE-04','XQ-FACE-05','XQ-FACE-06','XQ-FACE-07'}
EVID=QC+'/results/evidence/checkpy-flags-20261018-0151PT.json'   # check.py full run 01:51 PT, the flag table in qc/FINAL-SET-STATUS-20261018-0200PT.md
def policy(r,req,flagged):
    f=r['cp']; g=r['group']; kinds=flagged.get(f,[])
    if g=='Smileys & Emotion' and f in flagged and req in FACE_REQS:
        return 'smileys v3 lock: shape meant to differ, accepted as is (FINAL-SET-STATUS-20261018-0200PT, Smileys row)'
    if req=='XQ-MAR-01' and g in ('Flags','Symbols','Objects') and 'margin_min_px' in kinds:
        return f'{g} edge margin by design (FINAL-SET-STATUS-20261018-0200PT, {g} row; locked)'
    if req=='XQ-FLAG-01' and f=='1f1f3-1f1f5':
        return 'Nepal: the real flag is non-rectangular, so it cannot match the rectangle silhouette (flags lock)'
    if req=='XQ-HAND-02' and f in ('1f937','1f937-1f3ff'):
        return 'base/darkest 🤷 keep the 2.3 hand stroke: Max declined the fix 2026-10-18 09:06 PT (FINAL-SET-STATUS-20261018-0910PT)'
    return None
def bootstrap(results_json):
    R=json.load(open(results_json))['results']
    flagged={x['cp']:x['kinds'] for x in json.load(open(EVID))}
    E=[]
    for r in R:
        for k in r['hard_fails']+r['soft_fails']:
            why=policy(r,k,flagged)
            if why: E.append({'file':r['cp'],'req':k,'svg_md5':r['svg_md5'],'png_md5':r['png_md5'],'reason':why,'measured':r['results'][k]['reason']})
    E.sort(key=lambda e:(e['file'],e['req']))
    json.dump({'note':'Requirement-level known exceptions for xeroqc (hlaudit hits live in qc/hlaudit-known-exceptions.json). '
               'Each applies only while the file md5s match. Built by xeroqc/exceptions.py from '+results_json.split('/qc/')[-1],
               'built':datetime.datetime.now().strftime('%Y-%m-%d %H:%M PT'),'count':len(E),'exceptions':E},open(QC+'/known-exceptions.json','w'),indent=1,ensure_ascii=False)
    return E
