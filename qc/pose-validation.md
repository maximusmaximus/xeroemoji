# Pose validation for full-body figures (posecheck)

Added in People batch 09 (Oct 17, 2026) after Max's note: "the humans dont look like they are actually running -- they seem unnatural. lets review all these and have a better way to validate".
Tools: `work/skel9.py` (skeleton, kinematics, measuring), `work/posecheck.py` (ranges and checks), `work/pose_legacy.py` (read-only skeletons for figures built before this existed), `work/pose_sheets.py` (review sheets). `work/people_qc.py` runs posecheck on every file that carries a skeleton.

## 1. The skeleton is the source of truth
Every body-kit figure is built from an explicit joint skeleton. The joints are: head, neck, shoulder-mid, hip-mid, near/far (side view) or left/right (front view) shoulder, elbow, wrist, hip, knee, ankle and toe.
- **Side views** come from forward kinematics (`skel9.side`): a hip position, a trunk lean, and per-limb joint angles (thigh, knee flexion and foot plantarflexion; shoulder and elbow flexion), plus optional shoulder/hip counter-rotation.
- **Hand contacts** (push rim, joystick) use two-link IK (`skel9.ik_arm`), which always picks the anatomical elbow solution (flexing forward).
- **Front views** use `skel9.front`: abduction and bend per limb.
- **Segment lengths** follow Winter's anthropometric ratios with torso T = 46 units: upper arm 30, forearm 23, thigh 39, shin 39, foot 20. Front views use 36 for the thigh and shin, so the tall standing figures keep their fit scale.
- **Head:** the house head stays big. Only the body has to be internally proportional.
- **Drawing:** `people9` draws limbs along these joints (`leg9`, `arm9` and `body9.limb`), the torso and trouser seat rotated with the trunk lean (`torso9`, `seat9`), shoes turned to the ankle→toe vector (`shoe9`), and hands from `hand_at` on the elbow→wrist line. Paired hands come from the same function at the same scale.
- **Embedding:** the skeleton goes into the SVG as an invisible `<g data-skeleton='{json}'/>` in drawn (figure-unit) coordinates, with `pose`, `view`, `facing` and `contact`. Facing-right files store mirrored joints, and posecheck un-mirrors them before measuring.

## 2. Angle conventions (degrees; side views are measured facing left)

| metric | definition |
|---|---|
| trunk_lean | hip-mid → shoulder-mid from vertical, + = forward |
| thigh_s | hip → knee from straight down, + = forward (hip flexion), − = behind (extension) |
| knee_s | thigh angle − shin angle (0 = straight, + = flexed; < 0 = hyperextended) |
| foot_s | plantarflexion: toe line vs perpendicular to the shin (+ = pointed) |
| shoulder_s | shoulder → elbow from straight down, + = forward |
| elbow_s | included angle at the elbow (180 = straight); `elbow_flex` keeps the sign |
| head_ahead | (hip-mid x − head x) / torso length, + = head ahead of the hips |
| counter_rot | near/far shoulder offset sign is opposite the near/far hip offset sign |
| front: abd_s / leg_abd_s | shoulder → elbow (hip → knee) from straight down, + = away from the midline |
| front: stance | ankle spread / hip width |

**Roles** are resolved from the skeleton:
- F/B = front/back leg (larger/smaller thigh angle)
- AF/AB = forward/back arm
- C/X = cane arm / free arm
- S/W = supporting/working leg
- U/O = raised/other arm

## 3. Ranges (FAIL when outside)

| pose | checks |
|---|---|
| **run** (mid-flight) | trunk lean 5–15; front thigh 40–60, front knee 20–40; back thigh −35–0, back knee 90–120 (shin kicked up), back foot 15–75; arm swing forward 15–60 / back −60…−15, both elbows 75–100; arms opposite the legs (forward arm on the back-leg side); head 0–0.5 T ahead of the hips; shoulders counter-rotated |
| **cane_walk** | lean 0–8; front thigh 18–35, knee 0–15, foot −25–5 (heel strike); back thigh −25…−5, knee 10–45, foot 10–50 (toe-off); cane arm shoulder 15–55, elbow 120–170; free arm −35…−3, elbow 140–180; free arm swings back on the front-leg side (contralateral); cane tip on the ground ahead of the leading toe; head −0.1–0.3 T |
| **seated** (wheelchair) | lean −12–8; thighs 78–102 (hip ~90); knees 75–105; foot −20–25; both soles within 4 of the footplate; torso back within 6 of the backrest; hand centre within 8 of the push rim or joystick knob; reach elbow 85–165 |
| **kneel** | lean −5–10; front thigh 75–105, knee 75–105; back thigh −20–20, knee 75–110; head −0.15–0.3 T |
| **arabesque** | lean 0–25; supporting thigh −12–12, knee 0–10, foot 55–95 (pointe); working thigh −105…−70, knee 0–15; front arm 80–165, back arm −115…−55, elbows 140–180 |
| **flamenco** (front) | tilt ±15; raised-arm abduction 150–185, elbow 100–165; other arm 25–85, elbow 90–175; knees 150–180 |
| **disco** (front) | tilt ±12; pointing arm 120–160, elbow 158–180; other arm 3–45 with the hand below the shoulder; stance 1.4–3.2; knees 140–176 |
| **stand** (front) | tilt ±5; arms 0–15, elbows 150–180; knees 170–180; stance 0.6–1.6 |
| **levitate** (front) | tilt ±5; arms 0–15, elbows 160–180; knees 170–180; stance 0.5–1.3; hover gap ≥ 4 units between the soles and the shadow |
| **all side views** | elbow flexion −5–150 (no backward break); knee flexion −5–160 (no hyperextension) |

## 4. Proportion check (every pose)
Segment/torso ratios must be within ±25% of Winter (2009, Table 4.1).

| check | target | allowed range |
|---|---|---|
| upper arm / torso | .65 | .48–.81 |
| forearm / torso | .51 | .38–.63 |
| thigh / torso | .85 | .64–1.06 |
| shin / torso | .85 | .64–1.07 |
| forearm / upper arm | .79 | ±25% |
| shin / thigh | 1.0 | ±25% |
| paired near/far (left/right) segments | same length | within 10% |

## 5. Signals and sheets (not gates)
- **Silhouette sheet** (`review/people09-pose-before-after.jpg`): old, new, Apple and Google as solid black silhouettes at 64 and 24 px. The IoU column is the bbox-normalised silhouette overlap at 64 px. It is a shape signal only; vendors draw different proportions, props and dress.
- **Skeleton overlay** (`review/people09-skeleton-overlay.jpg`): the art with its skeleton and angle labels (red = FAIL) for the old builder (joints read by `pose_legacy`) and for the new file (embedded skeleton), next to a reference stick figure at the middle of the target ranges.
- **Judge by eye** against Apple and Google at 512/32/24 as before. posecheck catches broken anatomy; it does not replace looking.

## 6. References
- Novacheck TF. The biomechanics of running. *Gait & Posture* 7 (1998) 77–95. Running kinematics: trunk lean, hip flexion ~50° at mid-swing, swing knee flexion 90–130°, arm swing.
- Mann RA, Hagy J. Biomechanics of walking, running, and sprinting. *Am J Sports Med* 8 (1980) 345–350.
- Dugan SA, Bhat KP. Biomechanics and analysis of running gait. *Phys Med Rehabil Clin N Am* 16 (2005) 603–621. Forward lean, ~90° elbows, contralateral arm swing, counter-rotation.
- Perry J, Burnfield JM. *Gait Analysis: Normal and Pathological Function*, 2nd ed. (2010). Walking angles at initial contact and pre-swing.
- Winter DA. *Biomechanics and Motor Control of Human Movement*, 4th ed. (2009), Table 4.1. Segment lengths.
- RESNA position on wheelchair seating, and the clinical 90-90-90 sitting guideline (hips, knees and ankles at ~90°, feet supported, back supported).
- Vaganova A. *Basic Principles of Classical Ballet* (1934; Dover ed. 1969). First arabesque.

## 7. Usage
```
python3 work/posecheck.py svg/<file>.svg ...     # angle table + PASS/FAIL, exit 1 on any fail
python3 work/people_qc.py <batch>               # includes "POSECHECK n skeleton files, fails k"
python3 work/pose_sheets.py                      # regenerates both review sheets
```
Figures built before batch 09 have no embedded skeleton. People_qc skips them and reports them as "no skeleton". `work/pose_legacy.py` reconstructs their joints read-only from the builders' constants, for the reports.

## 8. Batch 10 poses (activity ending in sport), added 2026-10-17

New pose specs in `work/posecheck.py`. Each pose was built skeleton-first (`work/skel10.py`), the skeleton is embedded in the SVG
(`data-skeleton`, several per file when there are several figures), and posecheck gates every embedded skeleton. Batch 09 still
passes 150/150 with these changes; batch 08 results are unchanged (old v1 builder, locked as is).

**Changes to the checker:**
- **More than one skeleton per file** (`skeletons_of`): both bunny-ear dancers are checked; the horse rides inside the jockey's skeleton (`horse` key).
- **Body-relative angles:** `shoulder_rel = (shoulder + lean) % 360` and `thigh_rel` wrapped to (-180, 180], for horizontal or crouched trunks (swim, jockey, ski).
- **Coronal-plane exemption:** an arm flagged `coronal` (abducted out to the side, e.g. the fencer's back arm, the swimmer's recovery arm) shows a side-view projection that cannot tell elbow direction, so `elbow_dir` is reported N/A for that arm instead of PASS/FAIL. All other arms and every knee stay gated.
- **New roles:** H/D = hand-on-hip arm / hanging arm; L/T = golf lead/trail side; P/S = posed/standing leg (bunny); AF/AB for the swimmer picked by |shoulder_rel - 180| (the arm nearest straight-ahead is the reaching arm).
- **New contact gates** (1 = true, computed from the drawn geometry when the file is built): hand_on_hip, holds, feet_in_stirrups, hands_on_reins, on_skis, pole_back, on_board, hands_together, hands_on_oar, blade_in_water.
- **Horse checks:** `horse_not_flying` (no phase with the forelegs reaching forward and the hind legs reaching back at the same time, the "flying gallop" that Muybridge 1878 showed never happens), `fore_knees_forward` (the carpus folds with its point forward), `hind_hocks_back` (the hock points backward).

**Ranges** (FAIL outside):

**bunny**

| metric | range | why / source |
|---|---|---|
| `trunk_tilt` | -6 .. 6 | upright stance |
| `abd_l` | 25 .. 65 | hands on hips: elbows out |
| `abd_r` | 25 .. 65 | hands on hips: elbows out |
| `elbow_l` | 55 .. 115 | hands-on-hips elbow bent |
| `elbow_r` | 55 .. 115 | hands-on-hips elbow bent |
| `hand_on_hip` | 1 .. 1 | both hands resting on the hips |
| `knee_S` | 165 .. 180 | standing knee straight |
| `knee_P` | 115 .. 165 | posed leg: knee bent, toe pointed across (Google/Samsung) |
| `stance` | 0.3 .. 1.6 | feet under the hips |

**climb**

| metric | range | why / source |
|---|---|---|
| `trunk_lean` | -15 .. 20 | trunk close to the wall (Draper 2011; Sibella 2007) |
| `shoulder_AF` | 125 .. 185 | reaching arm overhead |
| `elbow_AF` | 140 .. 180 | reaching arm long |
| `shoulder_AB` | 20 .. 110 | holding arm at chest/shoulder height |
| `elbow_AB` | 55 .. 130 | holding arm bent (lock-off) |
| `thigh_F` | 45 .. 105 | high-step thigh |
| `knee_F` | 70 .. 130 | high-step knee |
| `thigh_B` | -20 .. 25 | standing leg under the hip |
| `knee_B` | 0 .. 45 | standing knee |
| `holds` | 1 .. 1 | both hands and both feet on holds |

**fence**

| metric | range | why / source |
|---|---|---|
| `trunk_lean` | -8 .. 15 | trunk upright in the lunge (Roi & Bianchedi 2008; Chen 2017) |
| `thigh_F` | 65 .. 100 | front thigh near horizontal |
| `knee_F` | 60 .. 105 | front shin ~vertical over the ankle |
| `thigh_B` | -55 .. -20 | back leg extended |
| `knee_B` | 0 .. 20 | back knee straight |
| `shoulder_AF` | 70 .. 110 | weapon arm extended forward at shoulder height |
| `elbow_AF` | 155 .. 180 | weapon arm straight |
| `shoulder_AB` | -175 .. -110 | back arm raised behind |
| `elbow_AB` | 60 .. 140 | back arm bent |

**gallop**

| metric | range | why / source |
|---|---|---|
| `trunk_lean` | 55 .. 95 | jockey crouch: trunk near horizontal (Pfau et al. 2009) |
| `thigh_rel_n` | 85 .. 145 | hip deeply flexed |
| `knee_n` | 95 .. 150 | knee deeply flexed (short stirrups) |
| `elbow_n` | 80 .. 165 | arms forward to the reins |
| `feet_in_stirrups` | 1 .. 1 | foot in the stirrup |
| `hands_on_reins` | 1 .. 1 | hands on the reins at the neck |
| `horse_not_flying` | 1 .. 1 | no "flying gallop" (Muybridge 1878): fore and hind legs never all extended at once |
| `fore_knees_forward` | 1 .. 1 | horse carpus (knee) folds forward-pointing only |
| `hind_hocks_back` | 1 .. 1 | horse hock points backward |

**ski**

| metric | range | why / source |
|---|---|---|
| `trunk_lean` | 15 .. 45 | athletic stance: trunk forward (Hintermeister 1995; Federolf 2012) |
| `thigh_rel_n` | 40 .. 95 | hips flexed |
| `knee_n` | 35 .. 80 | knees flexed |
| `knee_f` | 35 .. 80 | knees flexed |
| `shin_n` | -40 .. -12 | shin pressed forward into the boot |
| `shoulder_n` | 10 .. 70 | arms forward |
| `elbow_n` | 85 .. 150 | elbows bent |
| `on_skis` | 1 .. 1 | both boots on the skis |
| `pole_back` | 1 .. 1 | pole tip behind the hand, on the slope |

**board**

| metric | range | why / source |
|---|---|---|
| `trunk_tilt` | -20 .. 20 | trunk (Delorme 2005; Klous 2010) |
| `knee_l` | 105 .. 165 | knees bent |
| `knee_r` | 105 .. 165 | knees bent |
| `stance` | 1.6 .. 3.2 | feet at binding width |
| `abd_l` | 25 .. 95 | arms out for balance |
| `abd_r` | 25 .. 95 | arms out for balance |
| `on_board` | 1 .. 1 | both feet on the board |

**golf**

| metric | range | why / source |
|---|---|---|
| `trunk_tilt` | -22 .. 22 | finish: trunk over the lead leg (Hume 2005; McHardy 2006) |
| `abd_L` | 75 .. 150 | lead arm up by the lead shoulder |
| `elbow_L` | 40 .. 130 | lead elbow folded at the finish |
| `abd_T` | -175 .. -100 | trail arm across the chest, up |
| `elbow_T` | 70 .. 175 | trail arm |
| `knee_lead` | 160 .. 180 | lead leg straight (posted) |
| `knee_trail` | 130 .. 172 | trail knee bent, released |
| `stance` | 0.9 .. 2.2 | stance ~shoulder width |
| `hands_together` | 1 .. 1 | both hands on the grip |

**surf**

| metric | range | why / source |
|---|---|---|
| `trunk_tilt` | -25 .. 25 | trunk (Mendez-Villanueva & Bishop 2005) |
| `knee_l` | 95 .. 160 | knees bent low |
| `knee_r` | 95 .. 160 | knees bent low |
| `stance` | 1.8 .. 3.4 | wide stance on the board |
| `abd_l` | 35 .. 120 | arms out for balance |
| `abd_r` | 35 .. 120 | arms out for balance |
| `on_board` | 1 .. 1 | both feet on the board |

**row**

| metric | range | why / source |
|---|---|---|
| `trunk_lean` | -25 .. 25 | trunk between catch (+) and finish (-) (Kleshnev 2016; Soper & Hume 2004) |
| `shoulder_n` | 30 .. 110 | arms toward the oar handle |
| `elbow_n` | 95 .. 180 | elbow |
| `hands_on_oar` | 1 .. 1 | hands on the oar handle |
| `blade_in_water` | 1 .. 1 | blade in the water |

**swim**

| metric | range | why / source |
|---|---|---|
| `trunk_lean` | 70 .. 105 | body horizontal, streamlined (Maglischo 2003; Seifert 2010) |
| `shoulder_rel_AF` | 155 .. 200 | extended arm reaching forward past the head |
| `elbow_AF` | 145 .. 180 | extended arm long |
| `shoulder_rel_AB` | 195 .. 300 | recovering arm: upper arm above the back |
| `elbow_AB` | 60 .. 140 | high-elbow recovery |
| `thigh_rel_n` | -25 .. 25 | legs in line (flutter) |
| `thigh_rel_f` | -25 .. 25 | legs in line (flutter) |
| `knee_n` | 0 .. 45 | flutter knee |
| `knee_f` | 0 .. 45 | flutter knee |

**References for section 8:**
- Draper, C. et al. 2011, *Sports Biomechanics*: climbing reach and lock-off arm angles. Sibella, F. et al. 2007, *Hum Mov Sci*: climbing trunk-to-wall distance and leg positions.
- Roi, G.S. & Bianchedi, D. 2008, *Sports Med*: fencing lunge biomechanics. Chen, T.L. et al. 2017, *Sports Biomech*: lunge kinematics (front knee over the ankle, back knee straight).
- Pfau, T. et al. 2009, *J Exp Biol*: jockey posture at the gallop. Muybridge, E. 1878, *The Horse in Motion*: gallop phases (no flying gallop). Clayton, H. 2004, *The Dynamic Horse*; Back, W. & Clayton, H. 2013, *Equine Locomotion*: carpus and hock flexion directions.
- Hintermeister, R. et al. 1995, *Med Sci Sports Exerc*; Federolf, P. 2012, *J Biomech*: alpine ski stance (trunk, hip, knee and ankle flexion).
- Delorme, S. et al. 2005, *Clin J Sport Med*; Klous, M. et al. 2010, *J Appl Biomech*: snowboard stance and knee flexion.
- Hume, P. et al. 2005, *Sports Med*; McHardy, A. et al. 2006, *Sports Med*: golf swing finish positions.
- Mendez-Villanueva, A. & Bishop, D. 2005, *Sports Med*: surfing stance.
- Kleshnev, V. 2016, *The Biomechanics of Rowing*; Soper, C. & Hume, P. 2004, *Sports Med*: catch-to-finish trunk and arm ranges.
- Maglischo, E. 2003, *Swimming Fastest*; Seifert, L. et al. 2010, *Hum Mov Sci*: front-crawl arm phases (long reach, high-elbow recovery) and flutter-kick knee range.
- **Bunny ears** pose (both hands on the hips, one leg bent with the toe pointed across) follows the vendor art: Google, Samsung, WhatsApp and Facebook all draw it that way.

**Not gated:** the steamy-room busts have no limbs to check (same as the accepted massage/steam busts). The horse body is drawn from the joint chains in the skeleton, and only its leg directions and gait phase are gated.

## 9. Batch 11 poses (sport 2), added 2026-10-17

New pose specs in `work/posecheck.py`. Every pose was built skeleton-first (`work/skel11.py`, a copy of the frozen skel10), and the skeleton is
embedded in the SVG (both wrestlers are checked). After these changes batch 09 still passes 150/150 and batch 10 passes 182/182.

**Changes to the checker:**
- **Cartwheel, trunk-frame measurement:** the inverted skeleton is rotated by -trunk_tilt about the hips before measuring, which gives `abd_rel_*` (arms relative to the trunk) and `legabd_rel_*` (straddle); `trunk_inv = |trunk tilt|`.
- **New side-view roles from `contact`:** `dribble` gives D (dribbling arm); `down_leg` gives D/U (pedal leg at bottom/top dead centre); `throw` gives T/O (throwing/other arm).
- **New contact flags:** ball_under_hand, ball_ahead, bar_overhead, on_saddle, feet_on_pedals, pedals_opposite, hands_on_bars, hand_on_ground, hands_on_opponent, ball_in_hand, head_above_water, airborne.
- The handball throwing arm is coronal (cocked beside the head), so it is exempt from `elbow_dir`, the same as other coronal arms.

**dribble**

| metric | range | why / source |
|---|---|---|
| `trunk_lean` | 10 .. 35 | dribbling crouch: trunk forward, low centre of mass (Chan et al. 2009) |
| `thigh_F` | 25 .. 65 | front hip flexed ~50-60 while dribbling (Chan et al. 2009: 51-61) |
| `knee_F` | 20 .. 60 | front knee flexed ~40 (Chan et al. 2009: 40+-9.5; 15-45 in directional dribbling, MCB 2025) |
| `thigh_B` | -40 .. 5 | back leg pushing off behind |
| `knee_B` | 20 .. 110 | back knee (stride) |
| `shoulder_D` | -5 .. 50 | dribbling arm down and forward over the ball |
| `elbow_D` | 100 .. 175 | dribbling elbow (wrist/elbow push the ball down) |
| `ball_under_hand` | 1 .. 1 | ball below the dribbling hand |
| `ball_ahead` | 1 .. 1 | ball ahead of the hips (protected in front, beside the lead foot) |

**lift**

| metric | range | why / source |
|---|---|---|
| `trunk_tilt` | -6 .. 6 | trunk upright under the bar |
| `abd_l` | 145 .. 180 | arms overhead (max shoulder angle 165-167 at the catch, IMU snatch study 2022) |
| `abd_r` | 145 .. 180 | arms overhead |
| `elbow_l` | 160 .. 180 | elbows locked out under the bar |
| `elbow_r` | 160 .. 180 | elbows locked out |
| `knee_l` | 85 .. 150 | receiving squat: knees bent (front projection, thighs out) |
| `knee_r` | 85 .. 150 | receiving squat: knees bent |
| `stance` | 1.6 .. 3.6 | feet wider than the hips (catch base of support) |
| `bar_overhead` | 1 .. 1 | bar level above the head, both hands on it |

**bike**

| metric | range | why / source |
|---|---|---|
| `trunk_lean` | 35 .. 72 | riding position: trunk forward to the bars (cycling position review, J Sports Sci 2024) |
| `knee_D` | 25 .. 50 | leg near bottom dead centre: knee flexion 33-43 dynamic (Acta Bioeng Biomech 2020) |
| `knee_U` | 85 .. 135 | leg near top dead centre: knee deeply flexed |
| `elbow_n` | 130 .. 180 | arms to the bars, elbows soft |
| `on_saddle` | 1 .. 1 | pelvis on the saddle |
| `feet_on_pedals` | 1 .. 1 | both feet on the pedals |
| `pedals_opposite` | 1 .. 1 | pedals 180 deg apart on one crank circle |
| `hands_on_bars` | 1 .. 1 | hands on the bars |

**cartwheel**

| metric | range | why / source |
|---|---|---|
| `trunk_inv` | 100 .. 180 | body inverted past horizontal (|trunk tilt|) |
| `abd_rel_l` | 140 .. 185 | arms in line overhead (trunk frame) (Farana et al. 2019; MU "Safe gymnastics") |
| `abd_rel_r` | 140 .. 185 | arms in line overhead |
| `elbow_l` | 155 .. 180 | support arms straight |
| `elbow_r` | 155 .. 180 | support arms straight |
| `legabd_rel_l` | 25 .. 85 | wide straddle split |
| `legabd_rel_r` | 25 .. 85 | wide straddle split |
| `knee_l` | 155 .. 180 | legs straight |
| `knee_r` | 155 .. 180 | legs straight |
| `hand_on_ground` | 1 .. 1 | support hand on the floor |

**wrestle**

| metric | range | why / source |
|---|---|---|
| `trunk_lean` | 30 .. 68 | wrestling stance: trunk forward, hips back (Denning 2019) |
| `thigh_F` | 25 .. 85 | lead hip flexed (level change) |
| `knee_F` | 45 .. 115 | lead knee bent |
| `thigh_B` | -25 .. 40 | rear leg |
| `knee_B` | 15 .. 95 | rear knee bent |
| `shoulder_n` | 35 .. 125 | arms forward to the opponent (tie-up) |
| `shoulder_f` | 35 .. 125 | arms forward to the opponent |
| `elbow_n` | 55 .. 160 | arms bent in the tie |
| `elbow_f` | 55 .. 160 | arms bent in the tie |
| `hands_on_opponent` | 1 .. 1 | hands on the opponent (neck/shoulder/arm tie) |

**polo**

| metric | range | why / source |
|---|---|---|
| `trunk_tilt` | -15 .. 15 | upright in the water on the eggbeater (Sanders 1999) |
| `abd_U` | 110 .. 178 | throwing arm raised (follow-through shoulder 143+-6, Melchiorri et al. 2011) |
| `elbow_U` | 130 .. 180 | throwing elbow near extension (151.6+-3.6 at release) |
| `abd_O` | 15 .. 95 | other arm sculling out to the side |
| `elbow_O` | 90 .. 178 | sculling arm |
| `knee_l` | 60 .. 130 | eggbeater kick: knees bent (Sanders 1999) |
| `knee_r` | 60 .. 130 | eggbeater kick: knees bent |
| `ball_in_hand` | 1 .. 1 | ball in the raised hand |
| `head_above_water` | 1 .. 1 | head and shoulders above the waterline (Sanders 1999: vertex 0.22-0.42 m) |

**handball**

| metric | range | why / source |
|---|---|---|
| `trunk_lean` | -20 .. 15 | cocking phase in flight: trunk upright to leaning back (Wagner et al. 2010) |
| `thigh_F` | 45 .. 105 | swing knee driven up |
| `knee_F` | 55 .. 125 | swing knee bent |
| `thigh_B` | -35 .. 15 | take-off leg trailing |
| `knee_B` | 5 .. 85 | take-off knee |
| `shoulder_O` | 25 .. 125 | free arm forward for balance |
| `ball_in_hand` | 1 .. 1 | ball in the throwing hand, above shoulder height |
| `airborne` | 1 .. 1 | both feet off the ground (jump throw) |

**References (batch 11):**
- Chan et al. 2009, basketball dribbling kinematics (hip 51-61, knee 40+-9.5); directional dribbling knee 15-45 (Motor Control/Biomech 2025).
- Weightlifting snatch catch: IMU snatch study 2022 (max shoulder angle 165-167); overhead-squat references for stance.
- Cycling: Acta Bioeng Biomech 2020 (dynamic knee flexion 33-43 at BDC); J Sports Sci 2024 review of riding position (trunk 35-70 deg forward).
- Cartwheel: Farana et al. 2019 (round-off/cartwheel hand support); MU "Safe gymnastics" coaching notes (arms in line with the trunk, straight legs in straddle).
- Wrestling: Denning 2019 (stance and level change: trunk forward, hips back, staggered stance).
- Water polo: Sanders 1999 (eggbeater kick; vertex height 0.22-0.42 m); Melchiorri et al. 2011 (throw: shoulder 143+-6, elbow 151.6+-3.6 at release).
- Handball: Wagner et al. 2010 (jump throw: cocking phase, trunk upright to leaning back, swing knee driven up).
- Segment proportions: Winter (Biomechanics and Motor Control of Human Movement), +-25%, unchanged.

## 10. Batch 12 poses (juggling, lotus, fairy), added 2026-10-17

New pose specs in `work/posecheck.py`. The three full-body bases were built skeleton-first with `work/skel12.py`, a copy of the frozen skel11. After these changes batch 09 still passes 150/150, batch 10 182/182 and batch 11 204/204.
The other batch 12 bases (bath and bed scenes, the Claus family, superheroes, supervillains, mages and the baby angel) are busts or scenes with no limbs drawn. They carry no skeleton, so posecheck is N/A, as for the accepted steamy-room bust.

**Changes to the checker:** new contact flags only: balls_above_hands, ball_over_head, hands_on_knees, feet_together, wand_in_hand (airborne was already there). The roles and measurements are unchanged.

**juggle**

| metric | range | why / source |
|---|---|---|
| `trunk_tilt` | -6 .. 6 | standing upright, trunk still (Beek & Lewbel 1995) |
| `abd_l` | 15 .. 60 | upper arms hang near the trunk, slightly out |
| `abd_r` | 15 .. 60 | upper arms hang near the trunk |
| `elbow_l` | 55 .. 125 | elbows flexed ~90 (front projection of the forward forearm reads 60-120) (Beek & Lewbel 1995) |
| `elbow_r` | 55 .. 125 | elbows flexed ~90 |
| `knee_l` | 165 .. 180 | standing, knees straight |
| `knee_r` | 165 .. 180 | standing, knees straight |
| `stance` | 0.8 .. 2.4 | feet about hip to shoulder width |
| `balls_above_hands` | 1 .. 1 | balls in the air above the hands |
| `ball_over_head` | 1 .. 1 | apex of the cascade over the head |

**lotus**

| metric | range | why / source |
|---|---|---|
| `trunk_tilt` | -5 .. 5 | seated upright (spine vertical) |
| `leg_abd_l` | 60 .. 95 | thighs out to the sides: hip flexion + abduction + external rotation (Kapandji, Physiology of the Joints vol. 2) |
| `leg_abd_r` | 60 .. 95 | thighs out to the sides |
| `knee_l` | 10 .. 60 | knees fully flexed, shins folded back in front (Kapandji) |
| `knee_r` | 10 .. 60 | knees fully flexed |
| `abd_l` | 20 .. 70 | arms down to the knees |
| `abd_r` | 20 .. 70 | arms down to the knees |
| `elbow_l` | 120 .. 180 | elbows nearly straight, relaxed |
| `elbow_r` | 120 .. 180 | elbows nearly straight |
| `hands_on_knees` | 1 .. 1 | hands resting on the knees |
| `feet_together` | 1 .. 1 | shins folded in front, the feet meeting at the centre (front projection of the crossed shins; the 2-D skeleton keeps true segment lengths so the crossing reads as the feet overlapping) |

**fairy**

| metric | range | why / source |
|---|---|---|
| `trunk_tilt` | -10 .. 10 | hovering upright |
| `abd_r` | 110 .. 175 | wand arm raised overhead-out |
| `elbow_r` | 140 .. 180 | wand arm nearly straight |
| `abd_l` | 25 .. 95 | free arm out to the side for balance |
| `elbow_l` | 130 .. 180 | free arm soft |
| `leg_abd_l` | 0 .. 20 | supporting leg straight down, toe pointed |
| `knee_l` | 165 .. 180 | supporting leg straight |
| `leg_abd_r` | 10 .. 60 | gesture leg: knee out (retire/passe) (Grieg 1994, Inside Ballet Technique) |
| `knee_r` | 50 .. 110 | passe: knee flexed, toe at the other knee |
| `wand_in_hand` | 1 .. 1 | wand held in the raised hand |
| `airborne` | 1 .. 1 | feet clear of the ground shadow (hovering) |

**References (batch 12):**
- Beek PJ & Lewbel A (1995), The science of juggling, Scientific American 273(5): the three-ball cascade (hands below the apex, elbows bent about 90 with the forearms forward, balls crossing over a central apex).
- Kapandji IA, The Physiology of the Joints vol. 2 (lower limb): ranges of hip flexion, abduction and external rotation and of knee flexion, used for the lotus and cross-legged seat.
- Grieg V (1994), Inside Ballet Technique: the retire/passe position (gesture knee turned out, toe at the supporting knee), used for the fairy's hovering pose.
- Segment proportions: Winter (2009), Biomechanics and Motor Control of Human Movement, +-25%, unchanged. The lotus thighs and shins are 40 (Winter target 39).
- Front projection: in the lotus pose the shins cross toward the viewer. The 2-D skeleton keeps true segment lengths, so the crossing is checked as the feet meeting at the centre (`feet_together`).

## 11. Batch 13 (merperson, hairy creature)

Skeletons: the merperson files (18, `merperson` spec, new) and the hairy creature (1, the existing `walk` spec). The busts and the
person-symbol glyphs have no skeleton. New contact keys: `tail_closed` and `trident_in_hand`. Regression after the posecheck
change: batch 09 150/150, 10 182/182, 11 204/204, 12 54/54, 13 19/19.

**merperson** (new)

| metric | range | why / source |
|---|---|---|
| `trunk_tilt` | -10 .. 10 | upper body upright, sitting on the tail (Apple/Google/WhatsApp/Samsung) |
| `abd_r` | 120 .. 175 | trident arm raised overhead-out (Apple/Google/WhatsApp/OpenMoji) |
| `elbow_r` | 140 .. 180 | trident arm nearly straight |
| `abd_l` | 20 .. 80 | free arm out to the side, resting (Apple); Microsoft/Facebook wave |
| `elbow_l` | 120 .. 180 | free arm soft |
| `leg_abd_l` | 10 .. 35 | legs swept together to one side (side-sit / "mermaid pose"); hip abduction <= 45 (Kapandji, Physiology of the Joints vol. 2) |
| `leg_abd_r` | -35 .. -10 | far leg adducted to the same side; hip adduction <= 30 (Kapandji vol. 2) |
| `knee_l`, `knee_r` | 95 .. 140 | knees flexed so the tail curls back up to the fluke |
| `tail_closed` | 1 | both legs parallel inside the tail (ankles no wider than the hips) |
| `trident_in_hand` | 1 | trident shaft through the raised fist |

Measured: trunk 0, abd_r 150, elbow_r 168, abd_l 42, elbow_l 152, leg_abd 22/-22, knees 122/122. Proportions: Winter (2009) +-25%, all PASS.

**hairy creature** (`walk`, Perry & Burnfield 2010 heel strike)

Measured: trunk_lean 8 [0,8], thigh_F 30 [18,35], knee_F 6 [0,15], thigh_B -16 [-25,-5], knee_B 34 [10,45],
shoulder_AF 28 [5,35], shoulder_AB -26 [-35,-5], opposition 1, head_ahead .18.

Long arms (Bigfoot): ua 34 and fa 27 against the house T 46, which gives ua/T .74 and fa/T .59. Both are inside Winter +25%, and
fa/ua .79 matches Winter's .785.


## 12. Batch 08 v2 (open items, Oct 18 02:33 PT)
Walking/standing/kneeling/white cane rebuilt skeleton-first (work/people8v2.py); posecheck 0 fails on 108/108. Details: qc/openitems-audit.md section 5.
