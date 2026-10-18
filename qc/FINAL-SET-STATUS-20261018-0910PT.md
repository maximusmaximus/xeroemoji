# Final whole-set status: 2026-10-18 09:10 PT (after the open-items re-lock)
Supersedes qc/FINAL-SET-STATUS-20261018-0200PT.md (kept for history; its coverage, integrity and flag notes still hold except where updated here).

## Open-items re-lock (Max: fix approved 02:03 AM PT, review approved 09:06 AM PT "Approve the fixes and re-lock")
- ps showed no stray workers before writing.
- 5 new lock versions (each covers every file of its old lock with current md5s; header cites both approvals):

| new lock | supersedes | files | changed |
|---|---|---|---|
| LOCK-people-pilot-approved-v3-20261018-0907PT.md | people-pilot v2 1721 | 228 | 44 (🤷 4, 🙅 6, 👩‍🚀 6, 🧑‍⚕️ 6 emoji) |
| LOCK-objects-batch08-approved-v2-20261018-0907PT.md | objects-batch08 0746 | 48 | 16 (8 emoji, live text → paths) |
| LOCK-objects-batch09-approved-v2-20261018-0907PT.md | objects-batch09 0803 | 46 | 4 (1f4c5, 1f4c6) |
| LOCK-people-batch03-approved-v4-20261018-0907PT.md | people-batch03 v3 1721 | 398 | 24 (🙅‍♂️/🙅‍♀️ 12) |
| LOCK-people-batch08-approved-v2-20261018-0907PT.md | people-batch08 1928 | 288 | 216 (108 pose emoji) |

- The old entries in qc/verify_locks.sh were replaced in place (backup /tmp/oi/verify_locks.bak5); the 5 old files carry a SUPERSEDED header line.
- Guards: work/people8v2.py, work/body8v2.py, work/roles_oi.py refuse to load while their lock exists (checked). The older builders (people8, people3, ...) match the v-next names by glob and stay frozen.
- Details of the fixes: qc/openitems-audit.md. Sheets: review/openitems-before-after.jpg, review/people08-pose-before-after.jpg.

## Verification
- verify_locks.sh: **75/75 OK, 0 FAIL**.
- Coverage: 3,963/3,963 emoji (7,926/7,926 files) in active locks; 0 uncovered, 0 in more than one active lock, 0 orphan entries.
- LOCK files on disk: 84 (75 active + 9 superseded, kept for history).
- check.py full run (finished 02:32 PT, no art changed since): 3,963 checked, **483 flagged** (was 497). Cleared: 10 Objects live text, 4 🤷 pilot outline. Remaining: Flags 270, Symbols 164, Smileys 34, Objects 7 (diagonal-tool margins), People & Body 8 (👶 ×5 outline 16-17 px, 👍🏿 👎🏿 ✌🏿 9-11 px); all by design or known, as in the 02:00 doc.

## hlaudit: the fixed tool is the tool of record
- work/hlaudit.py (outline mask = all ink-stroked shapes after </defs>, fixed 2026-10-18; old tool kept at review/before-openitems-20261018-0204/tools/hlaudit.py).
- Known exception list: **qc/hlaudit-known-exceptions.json, 523 files** = 441 hits first found by the fixed mask (438 People & Body, 3 Objects) + 82 that the old tool already found (79 Animals & Nature + 1f43b-200d-2744, 1f43f, 1f577). All locked, approved art.
- Each exception is keyed on the file's svg md5, so it only applies while the file is unchanged. Any new or changed file is gated normally. hlaudit.known_exception(name, svg) implements this; people_qc now reports these as "HL known exceptions" instead of failures (checked on batches 03 and 10: HL {} with 12 and 7 known). Set-wide: 0 hits outside the list.

## Known and NOT approved (left untouched)
1. **441 new hlaudit hits** in locked art (list above; by lock: people batch01 v2 126, batch02 93, batch06 60, batch04 v3 59, batch07 42, batch05 v2 24, pilot 15, batch03 12, batch10 7, objects 3). Recorded as exceptions, not fixed.
2. **Base 🤷 1f937 and 🤷🏿 1f937-1f3ff hand stroke** is still 2.3 internally (pilot tones 🏻–🏾 now 4.7). Measured outline already 7 px on all six.
3. **Walk arm swing** on the new batch 08 walking figures (±20°, passes posecheck) stays as built; not widened.
4. Still open from the 02:00 doc: 👶 / 1f3ff-hand outline-metric artifacts, the never-updated margin ranges for flags/symbols/smileys, and the smileys v1/v2 superseded locks without a SUPERSEDED header.

Packaging, fonts and GitHub: not started.
