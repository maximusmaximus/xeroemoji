# xeroqc results: 2026-10-18 12:24:47 PT (America/Los_Angeles)

Tool xeroqc 1.0.0 (tool_md5 `e5dfb4c59a36e061bc559624ec2cbdeb`), 3963 emoji, 29 scored requirements. Locks: 75 active, verify_locks {'locks_ok': 75, 'locks_fail': 0}. Spec: qc/REQUIREMENTS.md.

## Grades
| grade | emoji |
|---|---|
| PASS | 3386 |
| PASS-with-known-exceptions | 577 |
| FAIL | 0 |

## Score (0-100, weighted passes over applicable requirements; known exceptions count as met)
mean 99.92, median 100.0, min 95.0, 5th pct 100.0, max 100.0; 3890 emoji at 100. Strict score (known exceptions not counted as met): mean 98.85, min 86.49.

| score | emoji |
|---|---|
| 90-100 | 3963 |

## By group
| group | emoji | PASS | PASS-known | FAIL | mean score |
|---|---|---|---|---|---|
| Activities | 85 | 85 | 0 | 0 | 100.00 |
| Animals & Nature | 161 | 79 | 82 | 0 | 100.00 |
| Flags | 270 | 268 | 2 | 0 | 100.00 |
| Food & Drink | 132 | 132 | 0 | 0 | 100.00 |
| Objects | 268 | 258 | 10 | 0 | 100.00 |
| People & Body | 2430 | 1990 | 440 | 0 | 99.88 |
| Smileys & Emotion | 172 | 138 | 34 | 0 | 100.00 |
| Symbols | 224 | 215 | 9 | 0 | 100.00 |
| Travel & Places | 221 | 221 | 0 | 0 | 100.00 |

## Requirements: results
| id | title | sev | w | applicable | pass | known-exc | fail |
|---|---|---|---|---|---|---|---|
| XQ-FILE-01 | Codepoint file naming, in Unicode 18.0 | hard | 3 | 3963 | 3963 | 0 | 0 |
| XQ-FILE-02 | SVG and PNG both present | hard | 3 | 3963 | 3963 | 0 | 0 |
| XQ-PNG-01 | PNG canvas 512x512 RGBA | hard | 3 | 3963 | 3963 | 0 | 0 |
| XQ-SVG-01 | Valid square SVG | hard | 3 | 3963 | 3963 | 0 | 0 |
| XQ-SVG-02 | No live text | hard | 3 | 3963 | 3963 | 0 | 0 |
| XQ-SVG-03 | Self-contained SVG references | hard | 2 | 3963 | 3963 | 0 | 0 |
| XQ-SVG-04 | PNG is the render of the SVG | hard | 3 | 3963 | 3963 | 0 | 0 |
| XQ-LOCK-01 | Covered by exactly one active lock | hard | 3 | 3963 | 3963 | 0 | 0 |
| XQ-LOCK-02 | Lock hash matches | hard | 3 | 3963 | 3963 | 0 | 0 |
| XQ-OUT-01 | Outline width in the group range | hard | 3 | 3961 | 3957 | 4 | 0 |
| XQ-MAR-01 | Edge margin in the group range | hard | 3 | 3963 | 3935 | 28 | 0 |
| XQ-FACE-01 | House yellow face gradient | soft | 2 | 111 | 103 | 8 | 0 |
| XQ-FACE-02 | Gloss highlight position and size | soft | 1 | 90 | 85 | 5 | 0 |
| XQ-FACE-03 | Eyes present and placed | soft | 2 | 111 | 109 | 2 | 0 |
| XQ-FACE-04 | Mouth present and placed | soft | 2 | 111 | 103 | 8 | 0 |
| XQ-FACE-05 | Face diameter | soft | 1 | 111 | 111 | 0 | 0 |
| XQ-FACE-06 | Feature colours on the house palette | soft | 1 | 111 | 110 | 1 | 0 |
| XQ-FACE-07 | Colour count | soft | 1 | 111 | 110 | 1 | 0 |
| XQ-HL-01 | Highlights do not touch the outline | hard | 3 | 2591 | 2068 | 523 | 0 |
| XQ-MOUTH-01 | Crescent mouths carry the shared mouth gradient | hard | 2 | 1917 | 1917 | 0 | 0 |
| XQ-EYE-01 | Eye rims present | hard | 2 | 1996 | 1996 | 0 | 0 |
| XQ-HAT-01 | Headwear fits the head (hatfit) | hard | 3 | 548 | 548 | 0 | 0 |
| XQ-POSE-01 | Skeleton figures pass posecheck | hard | 3 | 717 | 717 | 0 | 0 |
| XQ-HAND-01 | Paired hands are matched | soft | 2 | 813 | 740 | 0 | 73 |
| XQ-HAND-02 | Hand stroke consistent across skin tones | soft | 1 | 1316 | 1314 | 2 | 0 |
| XQ-TONE-01 | Skin tone correct | hard | 3 | 2424 | 2424 | 0 | 0 |
| XQ-KEY-01 | Keycap shape | soft | 2 | 13 | 13 | 0 | 0 |
| XQ-FLAG-01 | Flag silhouette | soft | 2 | 262 | 261 | 1 | 0 |
| XQ-SYM-01 | Symbol tile shape | soft | 1 | 122 | 122 | 0 | 0 |

## Set-level checks
- XQ-SET-01: **PASS** {"measure": {"expected": 3963, "covered": 3963}, "missing": []}
- XQ-SET-02: **PASS** {"duplicates": []}
- XQ-SET-03: **PASS** {"orphans": [], "stray": []}
- XQ-SET-04: **PASS** {"measure": {"locks_ok": 75, "locks_fail": 0}}

## Top failing requirements
| id | emoji failing |
|---|---|
| XQ-HAND-01 | 73 |

## Every FAIL (0), with reasons (hard fails decide the grade; soft fails listed too)
| cp | name | group | score | reasons |
|---|---|---|---|---|

## Passing emoji with soft fails (73)
| cp | name | score | soft fails |
|---|---|---|---|
| 1f3ca | person swimming | 96.08 | XQ-HAND-01: hands differ in scale |
| 1f3ca-1f3fb | person swimming: light skin tone | 96.08 | XQ-HAND-01: hands differ in scale |
| 1f3ca-1f3fb-200d-2640 | woman swimming: light skin tone | 96.08 | XQ-HAND-01: hands differ in scale |
| 1f3ca-1f3fb-200d-2642 | man swimming: light skin tone | 96.08 | XQ-HAND-01: hands differ in scale |
| 1f3ca-1f3fc | person swimming: medium-light skin tone | 96.08 | XQ-HAND-01: hands differ in scale |
| 1f3ca-1f3fc-200d-2640 | woman swimming: medium-light skin tone | 96.08 | XQ-HAND-01: hands differ in scale |
| 1f3ca-1f3fc-200d-2642 | man swimming: medium-light skin tone | 96.08 | XQ-HAND-01: hands differ in scale |
| 1f3ca-1f3fd | person swimming: medium skin tone | 96.08 | XQ-HAND-01: hands differ in scale |
| 1f3ca-1f3fd-200d-2640 | woman swimming: medium skin tone | 96.08 | XQ-HAND-01: hands differ in scale |
| 1f3ca-1f3fd-200d-2642 | man swimming: medium skin tone | 96.08 | XQ-HAND-01: hands differ in scale |
| 1f3ca-1f3fe | person swimming: medium-dark skin tone | 96.08 | XQ-HAND-01: hands differ in scale |
| 1f3ca-1f3fe-200d-2640 | woman swimming: medium-dark skin tone | 96.08 | XQ-HAND-01: hands differ in scale |
| 1f3ca-1f3fe-200d-2642 | man swimming: medium-dark skin tone | 96.08 | XQ-HAND-01: hands differ in scale |
| 1f3ca-1f3ff | person swimming: dark skin tone | 96.08 | XQ-HAND-01: hands differ in scale |
| 1f3ca-1f3ff-200d-2640 | woman swimming: dark skin tone | 96.08 | XQ-HAND-01: hands differ in scale |
| 1f3ca-1f3ff-200d-2642 | man swimming: dark skin tone | 96.08 | XQ-HAND-01: hands differ in scale |
| 1f3ca-200d-2640 | woman swimming | 96.08 | XQ-HAND-01: hands differ in scale |
| 1f3ca-200d-2642 | man swimming | 96.08 | XQ-HAND-01: hands differ in scale |
| 1f485 | nail polish | 95.12 | XQ-HAND-01: hands differ in scale and stroke |
| 1f485-1f3fb | nail polish: light skin tone | 95.12 | XQ-HAND-01: hands differ in scale and stroke |
| 1f485-1f3fc | nail polish: medium-light skin tone | 95.12 | XQ-HAND-01: hands differ in scale and stroke |
| 1f485-1f3fd | nail polish: medium skin tone | 95.12 | XQ-HAND-01: hands differ in scale and stroke |
| 1f485-1f3fe | nail polish: medium-dark skin tone | 95.12 | XQ-HAND-01: hands differ in scale and stroke |
| 1f485-1f3ff | nail polish: dark skin tone | 95.12 | XQ-HAND-01: hands differ in scale and stroke |
| 1f4aa | flexed biceps | 95.12 | XQ-HAND-01: hands differ in scale and stroke |
| 1f4aa-1f3fb | flexed biceps: light skin tone | 95.12 | XQ-HAND-01: hands differ in scale and stroke |
| 1f4aa-1f3fc | flexed biceps: medium-light skin tone | 95.12 | XQ-HAND-01: hands differ in scale and stroke |
| 1f4aa-1f3fd | flexed biceps: medium skin tone | 95.12 | XQ-HAND-01: hands differ in scale and stroke |
| 1f4aa-1f3fe | flexed biceps: medium-dark skin tone | 95.12 | XQ-HAND-01: hands differ in scale and stroke |
| 1f4aa-1f3ff | flexed biceps: dark skin tone | 95.12 | XQ-HAND-01: hands differ in scale and stroke |
| 1f646 | person gesturing OK | 95.56 | XQ-HAND-01: hands differ in stroke |
| 1f646-1f3fb | person gesturing OK: light skin tone | 95.56 | XQ-HAND-01: hands differ in stroke |
| 1f646-1f3fc | person gesturing OK: medium-light skin tone | 95.56 | XQ-HAND-01: hands differ in stroke |
| 1f646-1f3fd | person gesturing OK: medium skin tone | 95.56 | XQ-HAND-01: hands differ in stroke |
| 1f646-1f3fe | person gesturing OK: medium-dark skin tone | 95.56 | XQ-HAND-01: hands differ in stroke |
| 1f646-1f3ff | person gesturing OK: dark skin tone | 95.56 | XQ-HAND-01: hands differ in stroke |
| 1f6b4 | person biking | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f6b4-1f3fb | person biking: light skin tone | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f6b4-1f3fb-200d-2640 | woman biking: light skin tone | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f6b4-1f3fb-200d-2642 | man biking: light skin tone | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f6b4-1f3fc | person biking: medium-light skin tone | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f6b4-1f3fc-200d-2640 | woman biking: medium-light skin tone | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f6b4-1f3fc-200d-2642 | man biking: medium-light skin tone | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f6b4-1f3fd | person biking: medium skin tone | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f6b4-1f3fd-200d-2640 | woman biking: medium skin tone | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f6b4-1f3fd-200d-2642 | man biking: medium skin tone | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f6b4-1f3fe | person biking: medium-dark skin tone | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f6b4-1f3fe-200d-2640 | woman biking: medium-dark skin tone | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f6b4-1f3fe-200d-2642 | man biking: medium-dark skin tone | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f6b4-1f3ff | person biking: dark skin tone | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f6b4-1f3ff-200d-2640 | woman biking: dark skin tone | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f6b4-1f3ff-200d-2642 | man biking: dark skin tone | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f6b4-200d-2640 | woman biking | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f6b4-200d-2642 | man biking | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f6b5 | person mountain biking | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f6b5-1f3fb | person mountain biking: light skin tone | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f6b5-1f3fb-200d-2640 | woman mountain biking: light skin tone | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f6b5-1f3fb-200d-2642 | man mountain biking: light skin tone | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f6b5-1f3fc | person mountain biking: medium-light skin tone | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f6b5-1f3fc-200d-2640 | woman mountain biking: medium-light skin tone | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f6b5-1f3fc-200d-2642 | man mountain biking: medium-light skin tone | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f6b5-1f3fd | person mountain biking: medium skin tone | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f6b5-1f3fd-200d-2640 | woman mountain biking: medium skin tone | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f6b5-1f3fd-200d-2642 | man mountain biking: medium skin tone | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f6b5-1f3fe | person mountain biking: medium-dark skin tone | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f6b5-1f3fe-200d-2640 | woman mountain biking: medium-dark skin tone | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f6b5-1f3fe-200d-2642 | man mountain biking: medium-dark skin tone | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f6b5-1f3ff | person mountain biking: dark skin tone | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f6b5-1f3ff-200d-2640 | woman mountain biking: dark skin tone | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f6b5-1f3ff-200d-2642 | man mountain biking: dark skin tone | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f6b5-200d-2640 | woman mountain biking | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f6b5-200d-2642 | man mountain biking | 96.08 | XQ-HAND-01: hands differ in stroke |
| 1f9be | mechanical arm | 95.0 | XQ-HAND-01: hands differ in scale and stroke |

## Known exceptions (accepted, do not fail)
| id | emoji |
|---|---|
| XQ-HL-01 | 523 |
| XQ-MAR-01 | 28 |
| XQ-FACE-04 | 8 |
| XQ-FACE-01 | 8 |
| XQ-FACE-02 | 5 |
| XQ-OUT-01 | 4 |
| XQ-FACE-03 | 2 |
| XQ-HAND-02 | 2 |
| XQ-FLAG-01 | 1 |
| XQ-FACE-06 | 1 |
| XQ-FACE-07 | 1 |
