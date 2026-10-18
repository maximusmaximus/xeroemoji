# Xero Emoji house requirements (codified spec, xeroqc 1.0.0)
Written 2026-10-18 PT. This is the single list of every house requirement established with Max (house-spec.json rules, skin-tones.json,
the batch audits, the pose/hat/mouth/eye-rim/highlight rules and the lock process). The scorer `qc/xeroqc` implements every
automated row below from the registry in `qc/xeroqc/requirements.py` (this table is generated from it, so the two cannot drift).

## How an emoji is scored
- Every requirement is evaluated per emoji as **PASS**, **FAIL**, **KNOWN-EXCEPTION** or **N/A** (not applicable).
- **Score** (0-100) = 100 × (sum of weights of PASS + KNOWN-EXCEPTION) / (sum of weights of applicable requirements). `score_strict` counts KNOWN-EXCEPTION as not met.
- **Grade**: any *hard* FAIL → **FAIL** (whatever the score). Otherwise any KNOWN-EXCEPTION → **PASS-with-known-exceptions**. Otherwise **PASS**.
  Soft FAILs lower the score and are listed in the summary, but do not fail the emoji.
- **Known exceptions** are failures in locked art that Max accepted (or declined to fix). They live in two lists, both pinned to the file's md5,
  so an exception disappears the moment the file changes, and a new file is always gated normally:
  - `qc/hlaudit-known-exceptions.json` (523 highlight-on-outline files; the fixed hlaudit is the tool of record, 2026-10-18 09:06 PT)
  - `qc/known-exceptions.json` (requirement-level; built only by the cited policy in `qc/xeroqc/exceptions.py`)
- Reused checkers (not duplicated): `qc/check.py` (metrics + house-spec ranges), `work/hlaudit.py`, `work/hatfit.py`, `work/posecheck.py`,
  `work/mouthbowl.py`, the people_qc headwear rule, `qc/verify_locks.sh` and its active-lock list.
- Deterministic: sorted inputs, no randomness; results record the tool version, tool md5 (every tool/config file), timestamp (PT) and the md5 of every active lock.
- Run: `cd set/qc && python3 -m xeroqc run` → `qc/results/<YYYYMMDD-HHMM>PT/` (results.json, results.csv, summary.md, report.html). Tests: `python3 -m unittest discover -s tests -v`.

## Per-emoji requirements (scored)
| id | requirement | severity | weight | applies to | automated test |
|---|---|---|---|---|---|
| XQ-FILE-01 | Codepoint file naming, in Unicode 18.0 | hard | 3 | all | filename = lowercase hex codepoints joined by "-", FE0F dropped (except the 4 names Max kept: 1f3f3-fe0f-200d-1f308, 1f3f3-fe0f-200d-26a7-fe0f, 1f3f4-200d-2620-fe0f, 26d3-fe0f-200d-1f4a5); maps to a fully-qualified emoji-test 18.0 entry (plan/coverage.csv) |
| XQ-FILE-02 | SVG and PNG both present | hard | 3 | all | svg/<cp>.svg and png/<cp>.png exist and are non-empty |
| XQ-PNG-01 | PNG canvas 512x512 RGBA | hard | 3 | all | PIL: size == (512,512), mode RGBA, transparent background (corner alpha 0), art present |
| XQ-SVG-01 | Valid square SVG | hard | 3 | all | parses as XML, root <svg> in the SVG namespace with a square viewBox, renders with cairosvg |
| XQ-SVG-02 | No live text | hard | 3 | all | no <text>, <tspan>, <textPath> or font-family; lettering must be outlined paths (house rule no_live_text) |
| XQ-SVG-03 | Self-contained SVG references | hard | 2 | all | every url(#id) / href="#id" is defined in the file; no external http/file/data-font references |
| XQ-SVG-04 | PNG is the render of the SVG | hard | 3 | all | cairosvg 512px render of the SVG vs the PNG: <=0.5% of pixels differ by more than 48/255 in any RGBA channel |
| XQ-LOCK-01 | Covered by exactly one active lock | hard | 3 | all | svg and png paths each appear in exactly one lock listed in qc/verify_locks.sh |
| XQ-LOCK-02 | Lock hash matches | hard | 3 | all | md5 of svg and png equal the md5 recorded in the active lock |
| XQ-OUT-01 | Outline width in the group range | hard | 3 | all with a measurable outline | check.metrics outline_px @512: yellow faces 8.55-12.45; non-yellow faces 4.875-14.625; PB hands 4-8; PB body parts 5-8 (house 6px); other People & Body 5-15; everything else 11-15 (house 13px). n/a if no outline is measurable (outline_px 0) |
| XQ-MAR-01 | Edge margin in the group range | hard | 3 | all | check.metrics margin_min_px @512: country/subdivision flags 60-75 (by-design flag tile, 67); pennant flags 40-50 (47); full-bleed Symbols (tiles, keycaps, round signs: alpha box >=94% of the canvas) 2-8 (4); People & Body 12-60; yellow faces 13.15-37.85; non-yellow faces 0.25-136.75; everything else 12-45 |
| XQ-FACE-01 | House yellow face gradient | soft | 2 | yellow faces (Smileys) | check.metrics yellow top/mid/bot hue, sat, val inside house-spec ranges (3rd-97th pct of the original art, widened 15%) |
| XQ-FACE-02 | Gloss highlight position and size | soft | 1 | yellow faces | gloss_x, gloss_y, gloss_area inside house-spec ranges |
| XQ-FACE-03 | Eyes present and placed | soft | 2 | yellow faces | eyes detected in the eye zone; eye_width_frac, eye_y_frac, eye_height_frac inside house-spec ranges |
| XQ-FACE-04 | Mouth present and placed | soft | 2 | yellow faces | mouth_width_frac, mouth_y_frac, mouth_height_frac inside house-spec ranges |
| XQ-FACE-05 | Face diameter | soft | 1 | yellow faces | face_diam_frac inside the house-spec range |
| XQ-FACE-06 | Feature colours on the house palette | soft | 1 | yellow faces | offpalette_frac (feature pixels farther than palette_max_dist from the 16-colour feature palette) <= house max |
| XQ-FACE-07 | Colour count | soft | 1 | yellow faces | distinct #rrggbb colours in the SVG inside the house-spec range |
| XQ-HL-01 | Highlights do not touch the outline | hard | 3 | files with gloss/highlight elements | work/hlaudit.py (fixed outline mask, tool of record 2026-10-18) audit(svg,2) == 0 px; files on qc/hlaudit-known-exceptions.json with an unchanged md5 are KNOWN-EXCEPTION |
| XQ-MOUTH-01 | Crescent mouths carry the shared mouth gradient | hard | 2 | files with head-art crescent mouths | work/mouthbowl.pairs: every crescent-mouth bowl uses an mbowl-* gradient, unless its crescent is <60% visible (mouthbowl.crescent_visibility; covered by visor/hands/beard) -> that mouth is n/a |
| XQ-EYE-01 | Eye rims present | hard | 2 | files using the house head art (template6 heads) | every head-art eye-rim gradient referenced (ids *_g459/_g460/_g492/_g493/_g441/_g442/_g409/_g410) is defined, so the rims render (families/03/04 frag-cache bug) |
| XQ-HAT-01 | Headwear fits the head (hatfit) | hard | 3 | People & Body files with headwear codepoints (people_qc HEADWEAR) or data-hat markers | work/hatfit.check_svg: markers present and 0 violation px of head/hair above the band |
| XQ-POSE-01 | Skeleton figures pass posecheck | hard | 3 | files with an embedded data-skeleton | work/posecheck.check_svg: every embedded skeleton inside the biomechanics ranges for its pose (qc/pose-validation.md) |
| XQ-HAND-01 | Paired hands are matched | soft | 2 | figures with two or more house hands | all house-hand groups (people4 hand frame) in a file share the same scale and the same ink stroke width |
| XQ-HAND-02 | Hand stroke consistent across skin tones | soft | 1 | house-hand figures that have tone variants | the hand ink stroke width equals the modal value of the same emoji across its base + 5 tone files |
| XQ-TONE-01 | Skin tone correct | hard | 3 | People & Body (except no-skin emoji) and every file with a tone modifier | each tone named in the filename has its active-palette 4-stop skin gradient (qc/skin-tones.json) present (>=3 of 4 stops); no tone that is not named is present |
| XQ-KEY-01 | Keycap shape | soft | 2 | Symbols keycap subgroup | alpha silhouette IoU >= 0.97 against the keycap reference (majority vote of all keycaps) |
| XQ-FLAG-01 | Flag silhouette | soft | 2 | country and subdivision flags | alpha silhouette IoU >= 0.90 against the flag reference (majority vote of all country/subdivision flags) |
| XQ-SYM-01 | Symbol tile shape | soft | 1 | Symbols drawn on a tile (art fills >=88% of a >=94% canvas box) | alpha silhouette IoU >= 0.97 against the symbol-tile reference |

## Set-level requirements (checked once per run)
| id | requirement | severity | test |
|---|---|---|---|
| XQ-SET-01 | Unicode 18.0 coverage | hard | every fully-qualified emoji-test 18.0 entry (plan/coverage.csv, 3,963) has a file pair |
| XQ-SET-02 | No duplicates | hard | no two files map to the same emoji after FE0F normalisation |
| XQ-SET-03 | No orphans | hard | every svg/png maps to an emoji; no stray files in svg/ or png/ |
| XQ-SET-04 | All active locks verify | hard | bash qc/verify_locks.sh exits 0 (every active lock md5-clean) |

## Manual requirements (review sheets; not scored automatically)
| id | requirement | how checked |
|---|---|---|
| XQ-MAN-01 | Front-facing house heads, matched house hands (R2 style), no ponytails on body-kit figures | review sheets |
| XQ-MAN-02 | Reads at 32px and 24px | review sheets at 512/32/24 |
| XQ-MAN-03 | Meaning matches the vendors (Apple/Google research columns) | vendor comparison sheets |
| XQ-MAN-04 | Per-emoji design decisions recorded by Max (qc/decisions, audit docs) | human review |

## Notes on ranges and house values
- Canvas: 512×512 RGBA PNG + SVG per emoji, named by codepoints (lowercase hex, `-` joined, FE0F dropped except the 4 names Max kept), Unicode emoji-test 18.0 (3,963 fully-qualified).
- Outline: yellow faces ~10.5px (8.55-12.45); hands ~5.5px (4-8; house hand stroke 4.7 units in the people4 hand frame, ≈4.6px on busts); body parts 6px (5-8); people 5-15; objects/symbols 13px (11-15).
- Margins: faces 13.15-37.85; people/hands 12-60; objects/symbols 12-45; by-design tiles: country/subdivision flags 67 (60-75), pennant flags 47 (40-50), full-bleed symbol tiles/keycaps/round signs 4 (2-8).
- Highlights may not touch any ink stroke (2px dilation). Mouth gradient: crescent mouths use `mbowl-*` unless <60% visible. Eye rims: head-art rim gradients defined.
- Skin tones: palette "balanced" (skin-tones.json, Max 2026-10-14 21:26 PT), 4-stop gloss; no-skin People emoji (footprints, silhouettes, speaking head, people hugging, fingerprint) are n/a.
- Headwear: hatfit markers + 0 px above the band (Max, batch 05). Skeleton figures: posecheck ranges (Max, batch 09; qc/pose-validation.md).
- Paired hands: same scale and stroke within a figure; same stroke across the tone family (soft: perspective pairs such as swimmers/cyclists are listed for review).
