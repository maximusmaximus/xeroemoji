import sys,json
sys.path.insert(0,'/workspace/xerographer-emojis/set/qc'); sys.path.insert(0,'/workspace/xerographer-emojis/set/work')
import check, hlaudit as H, hatfit as HF, posecheck as PC
from PIL import Image
SET='/workspace/xerographer-emojis/set'
b=sys.argv[1]; plan=json.load(open(f'{SET}/qc/people-review-plan.json'))[b]; files=[f for x in plan for f in x['files']]
RNG={f:((4,8) if x['sg'].startswith('hand') else (5,15)) for x in plan for f in x['files']}   # same split as check.py: PB:hand* -> metrics_hand 4-8, every other People & Body subgroup -> metrics_people 5-15
spec=json.load(open(f'{SET}/qc/house-spec.json'))
bad=[];hl={};hlk={};hat=[];undef=[];pose=[];npose=0
# STANDING RULE (Max, batch 05): headwear must fit the head - no head/hair above the crown or beside it above the band.
# Any figure whose codepoints imply headwear must carry the data-headart / data-hat / data-band markers and pass hatfit.
HEADWEAR={'1f33e','1f373','1f527','1f3ed','1f393','1f477','1f46e','1f482','1f472','1f473','1f9d5','1f470','1f934','1f478',
          '1fac5','1f385','1f936','1f575','1f9d9','1f9d1-200d-1f384','1f3a9','1f452','1f9e2','26d1','1f451','1f468-200d-2708','2708','1f680','1f692'}
for f in files:
    m=check.metrics(Image.open(f'{SET}/png/{f}.png').convert('RGBA'),force_face=False)
    w=m.get('outline_px',0); mg=m.get('margin_min_px',0)
    if not RNG[f][0]<=w<=RNG[f][1] or not 12<=mg<=60: bad.append((f,w,mg))
    _s=open(f'{SET}/svg/{f}.svg').read(); v=H.audit(_s,2)
    if v[0]>0:
        if H.known_exception(f,_s): hlk[f]=v   # recorded exception (qc/hlaudit-known-exceptions.json), unchanged locked art
        else: hl[f]=v
    sv=open(f'{SET}/svg/{f}.svg').read()
    import re as _re
    und=set(_re.findall(r'url\(#([^)]+)\)',sv))-set(_re.findall(r' id="([^"]+)"',sv))
    if und: undef.append((f,sorted(und)[:3]))
    # POSE RULE (Max, batch 09): every body-kit figure carries its joint skeleton and must pass work/posecheck.py
    pr=PC.check_svg(sv)
    if pr is not None:
        npose+=1
        if pr[2]: pose.append((f,pr[0],pr[2]))
    if set(f.split('-'))&HEADWEAR or 'data-hat' in sv:
        r=HF.check_svg(sv)
        if r is None: hat.append((f,'headwear without data-hat markers'))
        elif 'error' in r or r['viol_px']: hat.append((f,r))
print('n',len(files),'outline/margin fails',bad); print('HL',hl); print('HL known exceptions',len(hlk)); print('HATFIT fails',len(hat),hat); print('UNDEFINED gradient refs',len(undef),undef[:5]); print('POSECHECK',npose,'skeleton files, fails',len(pose),pose[:6])
