"""Joint skeletons for full-body figures (People batch 09+) and the pose measurements used by work/posecheck.py.
A skeleton is the source of truth: people9 builds every full-body figure from one (forward kinematics from joint angles,
two-link IK for hand contacts), body9 draws the limbs along its joints, and the skeleton is embedded in the SVG
(<g data-skeleton='{json}'/>) so posecheck can measure the file itself. Coordinates: figure frame, y down; side views are
defined facing LEFT (forward = -x); facing-right files store their drawn (mirrored) joints plus "facing":"right" and are
un-mirrored before measuring. Angle conventions (degrees), all in posecheck's report:
  side view  trunk_lean   hip-mid -> shoulder-mid from vertical, + = forward
             thigh        hip -> knee from straight down, + = forward (hip flexion), - = behind (extension)
             knee         knee flexion = thigh angle - shin angle (0 straight, + = shin folded back; - = hyperextended)
             shoulder     shoulder -> elbow from straight down, + = forward (flexion), - = behind (extension)
             elbow        included angle at the elbow (180 straight); flexion must be forward (no backward break)
             foot         plantarflexion of the toe line vs. perpendicular-to-shin (0 neutral, + toe pointed down/back)
  front view abduction    shoulder -> elbow (hip -> knee) from straight down, + = away from the midline
             elbow/knee   included angle"""
# FROZEN with the batch-09 lock (people9 builds from it; posecheck measures with it). Batch 10+ builds with skel10.py.
import math,json
L0=dict(T=46,ua=30,fa=23,th=39,sh=39,ft=20,neck=9,head=30,shw=22,hpw=11)
# Winter DA, Biomechanics and Motor Control of Human Movement, 4th ed. (2009), Table 4.1 segment lengths / height H:
# upper arm .186H, forearm .146H, thigh .245H, leg (shank) .246H; shoulder .818H - hip (greater trochanter) .530H = torso .288H
WINTER=dict(ua=.186/.288,fa=.146/.288,th=.245/.288,sh=.246/.288)
def dvec(a):            # direction from straight down, + = forward (facing left: forward = -x)
    r=math.radians(a); return (-math.sin(r),math.cos(r))
def add(p,v,s=1): return (p[0]+v[0]*s,p[1]+v[1]*s)
def side(hip,lean,legs,arms,rot_s=0,rot_h=0,L=L0):
    """legs/arms: {'n':(thigh,knee,foot_pf)} / {'n':(shoulder,elbow_flex)} for near (viewer side) and far"""
    p=(-1,0); u=(-math.sin(math.radians(lean)),-math.cos(math.radians(lean)))
    sk={'view':'side','facing':'left'}
    shm=add(hip,u,L['T']); sk['neck']=add(shm,u,L['neck']); sk['head']=(sk['neck'][0]-math.sin(math.radians(lean))*6,sk['neck'][1]-L['head'])
    sk['hip_mid']=hip; sk['sh_mid']=shm
    for s,sg in (('n',1),('f',-1)):
        H=add(hip,p,sg*rot_h); th,kf,pf=legs[s]
        K=add(H,dvec(th),L['th']); A=add(K,dvec(th-kf),L['sh']); T=add(A,dvec(th-kf+90-pf),L['ft'])
        sk['hip_'+s],sk['knee_'+s],sk['ankle_'+s],sk['toe_'+s]=H,K,A,T
        S=add(shm,p,-sg*rot_s)
        if s in arms and arms[s] is not None:
            sa,ef=arms[s]; E=add(S,dvec(sa),L['ua']); W=add(E,dvec(sa+ef),L['fa'])
            sk['elbow_'+s],sk['wrist_'+s]=E,W
        sk['sh_'+s]=S
    return sk
def ik_arm(sk,s,target,reach=0,L=L0):
    """two-link IK: the hand centre (wrist + reach along the forearm) on target, elbow flexing FORWARD (anatomical; the
    other solution would break the elbow backward). Clamps to full reach."""
    S=sk['sh_'+s]; t=target
    for _ in range(6):
        dx,dy=t[0]-S[0],t[1]-S[1]; D=max(1e-3,min(math.hypot(dx,dy),L['ua']+L['fa']-.01))
        a=math.acos(max(-1,min(1,(L['ua']**2+D**2-L['fa']**2)/(2*L['ua']*D)))); base=math.atan2(dy,dx)
        best=None
        for sg in (1,-1):
            E=(S[0]+math.cos(base+sg*a)*L['ua'],S[1]+math.sin(base+sg*a)*L['ua'])
            vx,vy=t[0]-E[0],t[1]-E[1]; l=math.hypot(vx,vy) or 1; W=(E[0]+vx/l*L['fa'],E[1]+vy/l*L['fa'])
            fl=((_ang_down(E,W)-_ang_down(S,E)+180)%360)-180
            if best is None or (fl>=0)>(best[2]>=0): best=(E,W,fl)
        E,W,_=best; vx,vy=W[0]-E[0],W[1]-E[1]; l=math.hypot(vx,vy) or 1
        t=(target[0]-vx/l*reach,target[1]-vy/l*reach)
    sk['elbow_'+s]=E; sk['wrist_'+s]=W
    return sk
def front(hip,legs,arms,L=L0,tilt=0):
    """front view: legs {'l':(abd,knee_bend)}, arms {'l':(abd,elbow_bend)}; bends turn the distal segment toward the midline.
    'l' = viewer's left (x smaller)."""
    sk={'view':'front','facing':'front','hip_mid':hip}
    shm=(hip[0],hip[1]-L['T']); sk['sh_mid']=shm; sk['neck']=(shm[0],shm[1]-L['neck']); sk['head']=(shm[0],shm[1]-L['neck']-L['head'])
    for s,sg in (('l',-1),('r',1)):
        v=lambda a: (sg*math.sin(math.radians(a)),math.cos(math.radians(a)))
        H=(hip[0]+sg*L['hpw'],hip[1]); ab,kb=legs[s]
        K=add(H,v(ab),L['th']); A=add(K,v(ab-kb),L['sh']); T=add(A,(sg,0),L['ft']*.6)
        S=(shm[0]+sg*L['shw'],shm[1]); aa,eb=arms[s]
        E=add(S,v(aa),L['ua']); W=add(E,v(aa+eb),L['fa'])
        for j,P in (('hip',H),('knee',K),('ankle',A),('toe',T),('sh',S),('elbow',E),('wrist',W)): sk[f'{j}_{s}']=P
    return sk
def shift(sk,dx,dy):
    for k,v in sk.items():
        if isinstance(v,tuple): sk[k]=(v[0]+dx,v[1]+dy)
    return sk
def ground(sk,y,keys=('toe_n','toe_f','ankle_n','ankle_f','toe_l','toe_r','ankle_l','ankle_r'),pad=8):
    lo=max(sk[k][1]+(pad if k.startswith('ankle') else 2) for k in keys if k in sk); return shift(sk,0,y-lo)
def mirror(sk,m):
    if m==1: return sk
    o={k:((200-v[0],v[1]) if isinstance(v,tuple) else v) for k,v in sk.items()}; o['facing']='right'
    if isinstance(o.get('contact'),dict) and o['contact'].get('cane_tip'):
        c=dict(o['contact']); c['cane_tip']=[200-c['cane_tip'][0],c['cane_tip'][1]]; o['contact']=c
    return o
def to_json(sk,pose,extra=None):
    d={k:([round(v[0],2),round(v[1],2)] if isinstance(v,tuple) else v) for k,v in sk.items()}; d['pose']=pose
    if extra: d['contact']=extra
    return json.dumps(d,separators=(',',':'))
def from_json(s):
    d=json.loads(s); return {k:(tuple(v) if isinstance(v,list) and len(v)==2 and all(isinstance(x,(int,float)) for x in v) else v) for k,v in d.items()}
# ---------------- measuring ----------------
def _ang_down(a,b,fwd=-1):
    """angle of a->b from straight down, + toward fwd (-1 = -x)"""
    dx,dy=b[0]-a[0],b[1]-a[1]; return math.degrees(math.atan2(dx*fwd,dy))
def _incl(a,b,c):
    v1=(a[0]-b[0],a[1]-b[1]); v2=(c[0]-b[0],c[1]-b[1])
    cs=(v1[0]*v2[0]+v1[1]*v2[1])/((math.hypot(*v1)*math.hypot(*v2)) or 1); return math.degrees(math.acos(max(-1,min(1,cs))))
def _dist(a,b): return math.hypot(a[0]-b[0],a[1]-b[1])
def measure(sk):
    sk=dict(sk)
    if sk.get('facing')=='right': sk={k:((200-v[0],v[1]) if isinstance(v,tuple) else v) for k,v in sk.items()}
    m={}
    if sk['view']=='side':
        hm,sm=sk['hip_mid'],sk['sh_mid']; T=_dist(hm,sm)
        m['trunk_lean']=math.degrees(math.atan2(-(sm[0]-hm[0]),-(sm[1]-hm[1])))
        for s in 'nf':
            if 'knee_'+s in sk:
                th=_ang_down(sk['hip_'+s],sk['knee_'+s]); shn=_ang_down(sk['knee_'+s],sk['ankle_'+s])
                m['thigh_'+s]=th; m['knee_'+s]=th-shn
                if 'toe_'+s in sk:
                    ft=_ang_down(sk['ankle_'+s],sk['toe_'+s]); m['foot_'+s]=(shn+90)-ft
            if 'elbow_'+s in sk:
                ua=_ang_down(sk['sh_'+s],sk['elbow_'+s]); fa=_ang_down(sk['elbow_'+s],sk['wrist_'+s])
                fl=((fa-ua+180)%360)-180
                m['shoulder_'+s]=ua; m['elbow_flex_'+s]=fl; m['elbow_'+s]=180-abs(fl)
        m['head_ahead']=(hm[0]-sk['head'][0])/T          # + = head ahead of the hips (facing left)
        if 'sh_n' in sk:
            m['counter_rot']=((sk['sh_f'][0]-sk['sh_n'][0]),(sk['hip_f'][0]-sk['hip_n'][0]))
    else:
        hm,sm=sk['hip_mid'],sk['sh_mid']; T=_dist(hm,sm); m['trunk_tilt']=math.degrees(math.atan2(sm[0]-hm[0],hm[1]-sm[1]))
        for s,sg in (('l',-1),('r',1)):
            m['abd_'+s]=_ang_down(sk['sh_'+s],sk['elbow_'+s],sg); m['elbow_'+s]=_incl(sk['sh_'+s],sk['elbow_'+s],sk['wrist_'+s])
            m['leg_abd_'+s]=_ang_down(sk['hip_'+s],sk['knee_'+s],sg); m['knee_'+s]=_incl(sk['hip_'+s],sk['knee_'+s],sk['ankle_'+s])
        m['stance']=abs(sk['ankle_r'][0]-sk['ankle_l'][0])/abs(sk['hip_r'][0]-sk['hip_l'][0])
        m['wrist_below_sh_r']=sk['wrist_r'][1]-sk['sh_r'][1]; m['wrist_below_sh_l']=sk['wrist_l'][1]-sk['sh_l'][1]
    # proportions (relative to the torso = hip-mid -> shoulder-mid)
    P={}
    for s in ('n','f','l','r'):
        if 'elbow_'+s in sk: P['ua_'+s]=_dist(sk['sh_'+s],sk['elbow_'+s])/T; P['fa_'+s]=_dist(sk['elbow_'+s],sk['wrist_'+s])/T
        if 'knee_'+s in sk: P['th_'+s]=_dist(sk['hip_'+s],sk['knee_'+s])/T; P['sh_'+s]=_dist(sk['knee_'+s],sk['ankle_'+s])/T
    m['prop']=P
    return m,sk
