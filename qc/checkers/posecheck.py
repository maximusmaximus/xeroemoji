"""Pose validation for full-body figures (method + references: qc/pose-validation.md).
  python3 posecheck.py svg/<name>.svg ...      -> per-file angle table, PASS/FAIL
  check_svg(svg) -> None (no skeleton: not a body-kit file) or (pose, rows, fails)
A file built from the body kit carries <g data-skeleton='{json}'/> (work/skel9.py). Every metric is measured from those
joints and compared with the pose's biomechanics range (SPEC). Proportions are checked against Winter (2009) segment ratios."""
import sys,re,math,json
sys.path.insert(0,'/workspace/xerographer-emojis/set/work')
import skel9 as S
# (metric, lo, hi, why).  Roles resolved per skeleton: F/B = front/back leg (larger/smaller thigh angle);
# AF/AB = forward/back arm (larger/smaller shoulder angle); C = cane arm (contact 'cane'); X = free arm.
SPEC={
 'run':[('trunk_lean',5,15,'trunk lean forward (Novacheck 1998; Mann & Hagy 1980)'),
        ('thigh_F',40,60,'front thigh above vertical (hip flexion, mid-flight)'),
        ('knee_F',20,40,'front knee bent'),
        ('thigh_B',-35,0,'back thigh behind vertical'),
        ('knee_B',90,120,'back shin kicked up toward the buttock (swing knee flexion)'),
        ('foot_B',15,75,'back foot pointed (toe-off plantarflexion)'),
        ('shoulder_AF',15,60,'forward arm swing'),('shoulder_AB',-60,-15,'back arm swing'),
        ('elbow_AF',75,100,'forward elbow ~80-90'),('elbow_AB',75,100,'back elbow ~80-90'),
        ('opposition',1,1,'arm forward on the side of the back leg (contralateral)'),
        ('head_ahead',0,.5,'head over / slightly ahead of the hips (x torso)'),
        ('counter_rot',1,1,'shoulders counter-rotated against the hips')],
 'cane_walk':[('trunk_lean',0,8,'trunk ~upright, slight forward (Perry & Burnfield 2010)'),
        ('thigh_F',18,35,'front hip flexion at initial contact'),('knee_F',0,15,'front knee ~straight at heel strike'),
        ('foot_F',-25,5,'front foot dorsiflexed (heel strike)'),
        ('thigh_B',-25,-5,'back hip extension (terminal stance)'),('knee_B',10,45,'back knee pre-swing flexion'),
        ('foot_B',10,50,'back foot toe-off'),
        ('shoulder_C',15,55,'cane arm forward'),('elbow_C',120,170,'cane elbow slightly bent'),
        ('shoulder_X',-35,-3,'free arm swings back'),('elbow_X',140,180,'free elbow relaxed'),
        ('opposition',1,1,'free arm swings back on the side of the FRONT leg (contralateral; cane arm = back-leg side)'),
        ('cane_ahead',1,1,'cane tip on the ground ahead of the front toe'),('head_ahead',-.1,.3,'head over the hips')],
 'walk':[('trunk_lean',0,8,'trunk ~upright'),('thigh_F',18,35,'front hip flexion'),('knee_F',0,15,'front knee ~straight'),
        ('thigh_B',-25,-5,'back hip extension'),('knee_B',10,45,'back knee'),('shoulder_AF',5,35,'forward arm'),
        ('shoulder_AB',-35,-5,'back arm'),('opposition',1,1,'contralateral arm swing'),('head_ahead',-.1,.3,'head over the hips')],
 'seated':[('trunk_lean',-12,8,'upright / slightly reclined against the backrest (90-90-90 seating, RESNA 2015)'),
        ('thigh_n',78,102,'hip ~90 (thigh level on the cushion)'),('thigh_f',78,102,'hip ~90'),
        ('knee_n',75,105,'knee ~90'),('knee_f',75,105,'knee ~90'),('foot_n',-20,25,'foot ~90 to the shin, flat'),
        ('feet_on_plate',1,1,'feet on the footplate'),('back_on_rest',1,1,'back against the backrest'),
        ('hand_contact',1,1,'hand on the push rim / joystick'),('elbow_n',85,165,'arm reach elbow')],
 'kneel':[('trunk_lean',-5,10,'upright trunk'),('thigh_F',75,105,'front thigh level'),('knee_F',75,105,'front shin vertical'),
        ('thigh_B',-20,20,'back thigh ~vertical'),('knee_B',75,110,'back shin on the ground'),('head_ahead',-.15,.3,'head over the hips')],
 'arabesque':[('trunk_lean',0,25,'trunk may incline forward with a high leg (Vaganova 1934)'),
        ('thigh_S',-12,12,'supporting thigh vertical'),('knee_S',0,10,'supporting knee straight'),
        ('foot_S',55,95,'supporting foot on pointe'),
        ('thigh_W',-105,-70,'working leg extended behind ~90 (arabesque)'),('knee_W',0,15,'working knee straight'),
        ('shoulder_AF',80,165,'front arm forward-up'),('elbow_AF',140,180,'soft long arm'),
        ('shoulder_AB',-115,-55,'back arm out behind/side'),('elbow_AB',140,180,'soft long arm')],
 'flamenco':[('trunk_tilt',-15,15,'trunk'),('abd_U',150,185,'raised arm overhead (braceo)'),('elbow_U',100,165,'curved overhead arm'),
        ('abd_O',25,85,'other arm out'),('elbow_O',90,175,'other arm'),('knee_l',150,180,'knee'),('knee_r',150,180,'knee')],
 'disco':[('trunk_tilt',-12,12,'trunk'),('abd_U',120,160,'pointing arm up and out'),('elbow_U',158,180,'pointing arm straight'),
        ('abd_O',3,45,'other arm down'),('wrist_O_low',1,1,'other hand below the shoulder'),
        ('stance',1.4,3.2,'legs apart (ankles / hip width)'),('knee_l',140,176,'knees bent'),('knee_r',140,176,'knees bent')],
 'stand':[('trunk_tilt',-5,5,'upright'),('abd_l',0,15,'arms hang'),('abd_r',0,15,'arms hang'),('elbow_l',150,180,'relaxed'),
        ('elbow_r',150,180,'relaxed'),('knee_l',170,180,'straight'),('knee_r',170,180,'straight'),('stance',.6,1.6,'feet hip-width')],
 'levitate':[('trunk_tilt',-5,5,'upright'),('abd_l',0,15,'arms at the sides'),('abd_r',0,15,'arms at the sides'),
        ('elbow_l',160,180,'straight'),('elbow_r',160,180,'straight'),('knee_l',170,180,'straight'),('knee_r',170,180,'straight'),
        ('stance',.5,1.3,'feet together'),('hover',1,1,'gap between the shoes and the shadow')],
}

# ---------------- batch 10 poses (sources: qc/pose-validation.md section 6/8) ----------------
SPEC.update({
 'bunny':[('trunk_tilt',-6,6,'upright stance'),('abd_l',25,65,'hands on hips: elbows out'),('abd_r',25,65,'hands on hips: elbows out'),
          ('elbow_l',55,115,'hands-on-hips elbow bent'),('elbow_r',55,115,'hands-on-hips elbow bent'),('hand_on_hip',1,1,'both hands resting on the hips'),
          ('knee_S',165,180,'standing knee straight'),('knee_P',115,165,'posed leg: knee bent, toe pointed across (Google/Samsung)'),('stance',.3,1.6,'feet under the hips')],
 'climb':[('trunk_lean',-15,20,'trunk close to the wall (Draper 2011; Sibella 2007)'),
          ('shoulder_AF',125,185,'reaching arm overhead'),('elbow_AF',140,180,'reaching arm long'),
          ('shoulder_AB',20,110,'holding arm at chest/shoulder height'),('elbow_AB',55,130,'holding arm bent (lock-off)'),
          ('thigh_F',45,105,'high-step thigh'),('knee_F',70,130,'high-step knee'),
          ('thigh_B',-20,25,'standing leg under the hip'),('knee_B',0,45,'standing knee'),
          ('holds',1,1,'both hands and both feet on holds')],
 'fence':[('trunk_lean',-8,15,'trunk upright in the lunge (Roi & Bianchedi 2008; Chen 2017)'),
          ('thigh_F',65,100,'front thigh near horizontal'),('knee_F',60,105,'front shin ~vertical over the ankle'),
          ('thigh_B',-55,-20,'back leg extended'),('knee_B',0,20,'back knee straight'),
          ('shoulder_AF',70,110,'weapon arm extended forward at shoulder height'),('elbow_AF',155,180,'weapon arm straight'),
          ('shoulder_AB',-175,-110,'back arm raised behind'),('elbow_AB',60,140,'back arm bent')],
 'gallop':[('trunk_lean',55,95,'jockey crouch: trunk near horizontal (Pfau et al. 2009)'),('thigh_rel_n',85,145,'hip deeply flexed'),
          ('knee_n',95,150,'knee deeply flexed (short stirrups)'),('elbow_n',80,165,'arms forward to the reins'),
          ('feet_in_stirrups',1,1,'foot in the stirrup'),('hands_on_reins',1,1,'hands on the reins at the neck'),
          ('horse_not_flying',1,1,'no "flying gallop" (Muybridge 1878): fore and hind legs never all extended at once'),
          ('fore_knees_forward',1,1,'horse carpus (knee) folds forward-pointing only'),('hind_hocks_back',1,1,'horse hock points backward')],
 'ski':[('trunk_lean',15,45,'athletic stance: trunk forward (Hintermeister 1995; Federolf 2012)'),('thigh_rel_n',40,95,'hips flexed'),
          ('knee_n',35,80,'knees flexed'),('knee_f',35,80,'knees flexed'),('shin_n',-40,-12,'shin pressed forward into the boot'),
          ('shoulder_n',10,70,'arms forward'),('elbow_n',85,150,'elbows bent'),('on_skis',1,1,'both boots on the skis'),('pole_back',1,1,'poles angled back: tip behind and below the hand')],
 'board':[('trunk_tilt',-20,20,'trunk (Delorme 2005; Klous 2010)'),('knee_l',105,165,'knees bent'),('knee_r',105,165,'knees bent'),
          ('stance',1.6,3.2,'feet at binding width'),('abd_l',25,95,'arms out for balance'),('abd_r',25,95,'arms out for balance'),('on_board',1,1,'both feet on the board')],
 'golf':[('trunk_tilt',-22,22,'finish: trunk over the lead leg (Hume 2005; McHardy 2006)'),('abd_L',75,150,'lead arm up by the lead shoulder'),
          ('elbow_L',40,130,'lead elbow folded at the finish'),('abd_T',-175,-100,'trail arm across the chest, up'),('elbow_T',70,175,'trail arm'),
          ('knee_lead',160,180,'lead leg straight (posted)'),('knee_trail',130,172,'trail knee bent, released'),('stance',.9,2.2,'stance ~shoulder width'),
          ('hands_together',1,1,'both hands on the grip')],
 'surf':[('trunk_tilt',-25,25,'trunk (Mendez-Villanueva & Bishop 2005)'),('knee_l',95,160,'knees bent low'),('knee_r',95,160,'knees bent low'),
          ('stance',1.8,3.4,'wide stance on the board'),('abd_l',35,120,'arms out for balance'),('abd_r',35,120,'arms out for balance'),('on_board',1,1,'both feet on the board')],
 'row':[('trunk_lean',-25,25,'trunk between catch (+) and finish (-) (Kleshnev 2016; Soper & Hume 2004)'),('shoulder_n',30,110,'arms toward the oar handle'),
          ('elbow_n',95,180,'elbow'),('hands_on_oar',1,1,'hands on the oar handle'),('blade_in_water',1,1,'blade in the water')],
 'swim':[('trunk_lean',70,105,'body horizontal, streamlined (Maglischo 2003; Seifert 2010)'),
          ('shoulder_rel_AF',155,200,'extended arm reaching forward past the head'),('elbow_AF',145,180,'extended arm long'),
          ('shoulder_rel_AB',195,300,'recovering arm: upper arm above the back'),('elbow_AB',60,140,'high-elbow recovery'),
          ('thigh_rel_n',-25,25,'legs in line (flutter)'),('thigh_rel_f',-25,25,'legs in line (flutter)'),('knee_n',0,45,'flutter knee'),('knee_f',0,45,'flutter knee')],
})

# ---------------- batch 11 poses (sources: qc/pose-validation.md section 9) ----------------
SPEC.update({
 'dribble':[('trunk_lean',10,35,'dribbling crouch: trunk forward, low centre of mass (Chan et al. 2009)'),
          ('thigh_F',25,65,'front hip flexed ~50-60 while dribbling (Chan et al. 2009: 51-61)'),
          ('knee_F',20,60,'front knee flexed ~40 (Chan et al. 2009: 40+-9.5; 15-45 in directional dribbling, MCB 2025)'),
          ('thigh_B',-40,5,'back leg pushing off behind'),('knee_B',20,110,'back knee (stride)'),
          ('shoulder_D',-5,50,'dribbling arm down and forward over the ball'),('elbow_D',100,175,'dribbling elbow (wrist/elbow push the ball down)'),
          ('ball_under_hand',1,1,'ball below the dribbling hand'),('ball_ahead',1,1,'ball ahead of the hips (protected in front, beside the lead foot)')],
 'lift':[('trunk_tilt',-6,6,'trunk upright under the bar'),
          ('abd_l',145,180,'arms overhead (max shoulder angle 165-167 at the catch, IMU snatch study 2022)'),('abd_r',145,180,'arms overhead'),
          ('elbow_l',160,180,'elbows locked out under the bar'),('elbow_r',160,180,'elbows locked out'),
          ('knee_l',85,150,'receiving squat: knees bent (front projection, thighs out)'),('knee_r',85,150,'receiving squat: knees bent'),
          ('stance',1.6,3.6,'feet wider than the hips (catch base of support)'),('bar_overhead',1,1,'bar level above the head, both hands on it')],
 'bike':[('trunk_lean',35,72,'riding position: trunk forward to the bars (cycling position review, J Sports Sci 2024)'),
          ('knee_D',25,50,'leg near bottom dead centre: knee flexion 33-43 dynamic (Acta Bioeng Biomech 2020)'),
          ('knee_U',85,135,'leg near top dead centre: knee deeply flexed'),('elbow_n',130,180,'arms to the bars, elbows soft'),
          ('on_saddle',1,1,'pelvis on the saddle'),('feet_on_pedals',1,1,'both feet on the pedals'),
          ('pedals_opposite',1,1,'pedals 180 deg apart on one crank circle'),('hands_on_bars',1,1,'hands on the bars')],
 'cartwheel':[('trunk_inv',100,180,'body inverted past horizontal (|trunk tilt|)'),
          ('abd_rel_l',140,185,'arms in line overhead (trunk frame) (Farana et al. 2019; MU "Safe gymnastics")'),('abd_rel_r',140,185,'arms in line overhead'),
          ('elbow_l',155,180,'support arms straight'),('elbow_r',155,180,'support arms straight'),
          ('legabd_rel_l',25,85,'wide straddle split'),('legabd_rel_r',25,85,'wide straddle split'),
          ('knee_l',155,180,'legs straight'),('knee_r',155,180,'legs straight'),('hand_on_ground',1,1,'support hand on the floor')],
 'wrestle':[('trunk_lean',30,68,'wrestling stance: trunk forward, hips back (Denning 2019)'),
          ('thigh_F',25,85,'lead hip flexed (level change)'),('knee_F',45,115,'lead knee bent'),
          ('thigh_B',-25,40,'rear leg'),('knee_B',15,95,'rear knee bent'),
          ('shoulder_n',35,125,'arms forward to the opponent (tie-up)'),('shoulder_f',35,125,'arms forward to the opponent'),
          ('elbow_n',55,160,'arms bent in the tie'),('elbow_f',55,160,'arms bent in the tie'),('hands_on_opponent',1,1,'hands on the opponent (neck/shoulder/arm tie)')],
 'polo':[('trunk_tilt',-15,15,'upright in the water on the eggbeater (Sanders 1999)'),
          ('abd_U',110,178,'throwing arm raised (follow-through shoulder 143+-6, Melchiorri et al. 2011)'),('elbow_U',130,180,'throwing elbow near extension (151.6+-3.6 at release)'),
          ('abd_O',15,95,'other arm sculling out to the side'),('elbow_O',90,178,'sculling arm'),
          ('knee_l',60,130,'eggbeater kick: knees bent (Sanders 1999)'),('knee_r',60,130,'eggbeater kick: knees bent'),
          ('ball_in_hand',1,1,'ball in the raised hand'),('head_above_water',1,1,'head and shoulders above the waterline (Sanders 1999: vertex 0.22-0.42 m)')],
 'handball':[('trunk_lean',-20,15,'cocking phase in flight: trunk upright to leaning back (Wagner et al. 2010)'),
          ('thigh_F',45,105,'swing knee driven up'),('knee_F',55,125,'swing knee bent'),
          ('thigh_B',-35,15,'take-off leg trailing'),('knee_B',5,85,'take-off knee'),
          ('shoulder_O',25,125,'free arm forward for balance'),('ball_in_hand',1,1,'ball in the throwing hand, above shoulder height'),
          ('airborne',1,1,'both feet off the ground (jump throw)')],
})
SPEC.update({   # batch 12 (sources: qc/pose-validation.md section 10)
 'juggle':[('trunk_tilt',-6,6,'standing upright, trunk still (Beek & Lewbel 1995)'),
          ('abd_l',15,60,'upper arms hang near the trunk, slightly out'),('abd_r',15,60,'upper arms hang near the trunk'),
          ('elbow_l',55,125,'elbows flexed ~90 (front projection of the forward forearm reads 60-120) (Beek & Lewbel 1995)'),('elbow_r',55,125,'elbows flexed ~90'),
          ('knee_l',165,180,'standing, knees straight'),('knee_r',165,180,'standing, knees straight'),('stance',.8,2.4,'feet about hip to shoulder width'),
          ('balls_above_hands',1,1,'balls in the air above the hands'),('ball_over_head',1,1,'apex of the cascade over the head')],
 'lotus':[('trunk_tilt',-5,5,'seated upright (spine vertical)'),
          ('leg_abd_l',60,95,'thighs out to the sides: hip flexion + abduction + external rotation (Kapandji, Physiology of the Joints vol. 2)'),('leg_abd_r',60,95,'thighs out to the sides'),
          ('knee_l',10,60,'knees fully flexed, shins folded back in front (Kapandji)'),('knee_r',10,60,'knees fully flexed'),
          ('abd_l',20,70,'arms down to the knees'),('abd_r',20,70,'arms down to the knees'),
          ('elbow_l',120,180,'elbows nearly straight, relaxed'),('elbow_r',120,180,'elbows nearly straight'),
          ('hands_on_knees',1,1,'hands resting on the knees'),('feet_together',1,1,'shins folded in front, the feet meeting at the centre (front projection of the crossed shins; the 2-D skeleton keeps true segment lengths so the crossing reads as the feet overlapping)')],
 'fairy':[('trunk_tilt',-10,10,'hovering upright'),
          ('abd_r',110,175,'wand arm raised overhead-out'),('elbow_r',140,180,'wand arm nearly straight'),
          ('abd_l',25,95,'free arm out to the side for balance'),('elbow_l',130,180,'free arm soft'),
          ('leg_abd_l',0,20,'supporting leg straight down, toe pointed'),('knee_l',165,180,'supporting leg straight'),
          ('leg_abd_r',10,60,'gesture leg: knee out (retire/passe) (Grieg 1994, Inside Ballet Technique)'),('knee_r',50,110,'passe: knee flexed, toe at the other knee'),
          ('wand_in_hand',1,1,'wand held in the raised hand'),('airborne',1,1,'feet clear of the ground shadow (hovering)')],
 'merperson':[('trunk_tilt',-10,10,'upper body upright, sitting on the tail (Apple/Google/WhatsApp/Samsung merperson)'),
          ('abd_r',120,175,'trident arm raised overhead-out (Apple/Google/WhatsApp/OpenMoji hold the trident up)'),('elbow_r',140,180,'trident arm nearly straight'),
          ('abd_l',20,80,'free arm out to the side, resting (Microsoft/Facebook wave, Apple rests)'),('elbow_l',120,180,'free arm soft'),
          ('leg_abd_l',10,35,'legs swept together to one side (side-sit / "mermaid pose": hip abduction <=45, Kapandji vol. 2)'),
          ('leg_abd_r',-35,-10,'far leg adducted to the same side (hip adduction <=30, Kapandji vol. 2)'),
          ('knee_l',95,140,'knees flexed: the tail curls back up to the fluke'),('knee_r',95,140,'knees flexed, parallel to the other leg'),
          ('tail_closed',1,1,'both legs parallel inside the tail (ankles no wider than the hips)'),('trident_in_hand',1,1,'trident shaft through the raised fist')],
})
def _rel(x): return ((x+90)%360)-90
PROP_TOL=.25   # +-25% around Winter's ratios (the house head is big; the body itself must stay proportional)
def roles(m,sk,pose):
    r={}
    if sk['view']=='side':
        legs=[s for s in 'nf' if 'thigh_'+s in m]
        if len(legs)==2:
            F,B=sorted(legs,key=lambda s:-m['thigh_'+s]); r.update(F=F,B=B)
        arms=[s for s in 'nf' if 'shoulder_'+s in m]
        c=(sk.get('contact') or {}).get('cane')
        if c: r['C']=c; r['X']=[s for s in arms if s!=c][0] if len(arms)>1 else None
        if len(arms)==2:
            AF,AB=sorted(arms,key=lambda s:-m['shoulder_'+s]); r.update(AF=AF,AB=AB)
        c=sk.get('contact') or {}
        if c.get('dribble'): r['D']=c['dribble']
        if c.get('down_leg'): r['D']=c['down_leg']; r['U']='f' if c['down_leg']=='n' else 'n'
        if c.get('throw'): r['T']=c['throw']; r['O']='f' if c['throw']=='n' else 'n'
        if pose=='arabesque' and len(legs)==2:
            W=min(legs,key=lambda s:m['thigh_'+s]); r.update(W=W,S=[s for s in legs if s!=W][0])
    else:
        U=max('lr',key=lambda s:m['abd_'+s]); r.update(U=U,O='r' if U=='l' else 'l')
        c=sk.get('contact') or {}
        if c.get('hip_hand'): r['H']=c['hip_hand']; r['D']='r' if c['hip_hand']=='l' else 'l'
        if c.get('lead'): r['L']=c['lead']; r['T']='r' if c['lead']=='l' else 'l'
        if c.get('pose_leg'): r['P']=c['pose_leg']; r['S']='r' if c['pose_leg']=='l' else 'l'
    return r
def evaluate(sk,pose=None):
    pose=pose or sk.get('pose'); m,sku=S.measure(sk); rows=[]; fails=[]
    if sku['view']=='side':
        for s in 'nf':
            if 'shoulder_'+s in m: m['shoulder_rel_'+s]=(m['shoulder_'+s]+m['trunk_lean'])%360          # 0 = along the trunk to the hips, 180 = overhead
            if 'thigh_'+s in m: m['thigh_rel_'+s]=((m['thigh_'+s]+m['trunk_lean']+180)%360)-180; m['shin_'+s]=m['thigh_'+s]-m['knee_'+s]
    R=roles(m,sku,pose)
    if pose=='swim':   # forward/back arm by body-relative shoulder angle
        a=[s for s in 'nf' if 'shoulder_rel_'+s in m]
        if len(a)==2: R['AF'],R['AB']=sorted(a,key=lambda s:abs(m['shoulder_rel_'+s]-180))
    if pose=='cartwheel':   # measure arms/legs in the trunk frame (the skeleton rotated upright about the hips)
        t=m['trunk_tilt']; m['trunk_inv']=abs(t); r=math.radians(-t); hm=sku['hip_mid']
        rot=lambda q:(hm[0]+(q[0]-hm[0])*math.cos(r)-(q[1]-hm[1])*math.sin(r),hm[1]+(q[0]-hm[0])*math.sin(r)+(q[1]-hm[1])*math.cos(r))
        up={k:(rot(v) if isinstance(v,tuple) else v) for k,v in sku.items()}
        mu,_=S.measure(up)
        for s in 'lr': m['abd_rel_'+s]=mu['abd_'+s]; m['legabd_rel_'+s]=mu['leg_abd_'+s]
    c0=sk.get('contact') or {}
    if 'lead' in c0: m['knee_lead']=m['knee_'+c0['lead']]; m['knee_trail']=m['knee_'+('r' if c0['lead']=='l' else 'l')]
    con=dict(sk.get('contact') or {})
    if sk.get('facing')=='right' and con.get('cane_tip'): con['cane_tip']=[200-con['cane_tip'][0],con['cane_tip'][1]]
    for key,lo,hi,why in SPEC[pose]:
        base,_,role=key.rpartition('_') if key.count('_') and key.split('_')[-1] in ('F','B','AF','AB','C','X','S','W','U','O','H','D','L','T','P') else (key,'','')
        if key=='opposition':
            if pose=='cane_walk': ok=R.get('C')==R.get('B')
            else: ok=R.get('AF')==R.get('B')
            v=1 if ok else 0
        elif key=='counter_rot':
            a,b=m['counter_rot']; v=1 if (a*b<0 and abs(a)>=1 and abs(b)>=1) else 0
        elif key=='cane_ahead':
            v=1 if con.get('cane_tip') and con['cane_tip'][0]<min(sku['toe_n'][0],sku['toe_f'][0]) and abs(con['cane_tip'][1]-con.get('ground',con['cane_tip'][1]))<4 else 0
        elif key in ('feet_on_plate','back_on_rest','hand_contact','hover','hand_on_hip','holds','feet_in_stirrups','hands_on_reins','on_skis','pole_back',
                     'on_board','hands_together','hands_on_oar','blade_in_water',
                     'ball_under_hand','ball_ahead','bar_overhead','on_saddle','feet_on_pedals','pedals_opposite','hands_on_bars','hand_on_ground',
                     'hands_on_opponent','ball_in_hand','head_above_water','airborne',
                     'balls_above_hands','ball_over_head','hands_on_knees','feet_together','wand_in_hand',
                     'tail_closed','trident_in_hand'): v=1 if con.get(key) else 0
        elif key in ('horse_not_flying','fore_knees_forward','hind_hocks_back'): v=1 if horse_check(sk.get('horse'),key) else 0
        elif key=='wrist_O_low': v=1 if m['wrist_below_sh_'+R['O']]>0 else 0
        elif role:
            s=R.get(role); mk=f'{base}_{s}'
            if s is None or mk not in m: rows.append((key,None,lo,hi,'n/a',why)); fails.append(key+' (missing)'); continue
            v=m[mk]
        else: v=m.get(key)
        ok=v is not None and lo-1e-6<=v<=hi+1e-6
        rows.append((key,v,lo,hi,'PASS' if ok else 'FAIL',why))
        if not ok: fails.append(key)
    # anatomical joint limits, every side-view figure: elbows and knees only flex forward/backward the anatomical way
    if sku['view']=='side':
        cor=(sk.get('contact') or {}).get('coronal',[])
        for s in 'nf':
            if 'elbow_flex_'+s in m and s in cor:
                rows.append((f'elbow_dir_{s}',m['elbow_flex_'+s],-5,150,'N/A','arm moves in the coronal plane (abducted); its side-view projection cannot show elbow direction'))
            elif 'elbow_flex_'+s in m:
                v=m['elbow_flex_'+s]; ok=-5<=v<=150; rows.append((f'elbow_dir_{s}',v,-5,150,'PASS' if ok else 'FAIL','elbow flexes forward only (no backward break)'))
                if not ok: fails.append(f'elbow_dir_{s}')
            if 'knee_'+s in m:
                v=m['knee_'+s]; ok=-5<=v<=160; rows.append((f'knee_dir_{s}',v,-5,160,'PASS' if ok else 'FAIL','knee flexes backward only (no hyperextension)'))
                if not ok: fails.append(f'knee_dir_{s}')
    # proportions
    P=m['prop']
    for k,v in P.items():
        seg=k.split('_')[0]; tgt=S.WINTER[seg]; ok=tgt*(1-PROP_TOL)<=v<=tgt*(1+PROP_TOL)
        rows.append(('prop_'+k,v,tgt*(1-PROP_TOL),tgt*(1+PROP_TOL),'PASS' if ok else 'FAIL','segment/torso vs Winter 2009'))
        if not ok: fails.append('prop_'+k)
    for a,b,tgt in (('fa','ua',S.WINTER['fa']/S.WINTER['ua']),('sh','th',S.WINTER['sh']/S.WINTER['th'])):
        for s in 'nflr':
            if f'{a}_{s}' in P:
                v=P[f'{a}_{s}']/P[f'{b}_{s}']; ok=tgt*(1-PROP_TOL)<=v<=tgt*(1+PROP_TOL)
                rows.append((f'ratio_{a}/{b}_{s}',v,tgt*(1-PROP_TOL),tgt*(1+PROP_TOL),'PASS' if ok else 'FAIL','distal/proximal'))
                if not ok: fails.append(f'ratio_{a}/{b}_{s}')
    for a in ('ua','fa','th','sh'):
        for x,y in (('n','f'),('l','r')):
            if f'{a}_{x}' in P and f'{a}_{y}' in P:
                v=P[f'{a}_{x}']/P[f'{a}_{y}']; ok=.9<=v<=1/.9
                rows.append((f'pair_{a}_{x}{y}',v,.9,1/.9,'PASS' if ok else 'FAIL','paired limbs the same length'))
                if not ok: fails.append(f'pair_{a}_{x}{y}')
    return pose,rows,fails
SKRE=re.compile(r"<g data-skeleton='([^']+)'/>")
def skeleton_of(svg):
    m=SKRE.search(svg); return S.from_json(m.group(1)) if m else None
def skeletons_of(svg): return [S.from_json(x) for x in SKRE.findall(svg)]
def check_svg(svg):
    """every embedded skeleton is checked (two-person figures carry two); one skeleton -> exactly the batch-09 behaviour"""
    sks=skeletons_of(svg)
    if not sks: return None
    if len(sks)==1: return evaluate(sks[0])
    pose=None; rows=[]; fails=[]
    for i,sk in enumerate(sks):
        p_,r_,f_=evaluate(sk); pose=pose or p_
        rows+=[(f'#{i+1} '+r[0],)+tuple(r[1:]) for r in r_]; fails+=[f'#{i+1} {x}' for x in f_]
    return pose,rows,fails
def horse_check(h,key):
    """horse legs (facing left): h = {'fore_n':[elbow,knee,fetlock,hoof],'fore_f':...,'hind_n':[stifle,hock,fetlock,hoof],'hind_f':...,
    'shoulder':pt,'hip':pt}. Anatomy (Clayton 2004; Back & Clayton 2013): the carpus ('knee') flexes so it points FORWARD, the
    hock always points BACKWARD. Muybridge (1878): the gallop's airborne phase is gathered; fore legs reaching forward and
    hind legs stretched back at the same time ('flying gallop') never happens."""
    if not h: return False
    def side(a,b,c):  # >0: b lies forward (-x side) of the line a->c
        return ((c[0]-a[0])*(b[1]-a[1])-(c[1]-a[1])*(b[0]-a[0]))*(-1 if c[1]>a[1] else 1)
    if key=='fore_knees_forward':
        return all((h[k][1][0]-(h[k][0][0]+(h[k][2][0]-h[k][0][0])*(h[k][1][1]-h[k][0][1])/max(1e-6,h[k][2][1]-h[k][0][1])))<=1.5 for k in ('fore_n','fore_f'))
    if key=='hind_hocks_back':
        return all((h[k][1][0]-(h[k][0][0]+(h[k][2][0]-h[k][0][0])*(h[k][1][1]-h[k][0][1])/max(1e-6,h[k][2][1]-h[k][0][1])))>=-1.5 for k in ('hind_n','hind_f'))
    if key=='horse_not_flying':
        fore_out=all(h[k][3][0]<h['shoulder'][0]-10 for k in ('fore_n','fore_f'))
        hind_out=all(h[k][3][0]>h['hip'][0]+10 for k in ('hind_n','hind_f'))
        return not (fore_out and hind_out)
    return False
def fmt(rows):
    o=[]
    for key,v,lo,hi,st,why in rows:
        vs='n/a' if v is None else (f'{v:.2f}' if isinstance(v,float) and abs(v)<10 else f'{v:.0f}' if isinstance(v,(int,float)) else str(v))
        o.append(f'  {st:4} {key:22} {vs:>7}  [{lo:g}..{hi:g}]  {why}')
    return '\n'.join(o)
if __name__=='__main__':
    bad=0
    for p in sys.argv[1:]:
        r=check_svg(open(p).read())
        if r is None: print(p,'no skeleton (not a body-kit file)'); continue
        pose,rows,fails=r; print(p,pose,'PASS' if not fails else 'FAIL '+','.join(fails)); print(fmt(rows)); bad+=bool(fails)
    sys.exit(1 if bad else 0)
