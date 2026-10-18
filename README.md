# Xero Emoji

A complete emoji set in the Xerographer house style: all **3,963** fully-qualified emoji of Unicode emoji-test 18.0,
each as an SVG and a 512×512 PNG, with skin-tone variants and ZWJ sequences.

Xero Emoji was started in 2016. Created by maxi.grok.me.

## Layout
| path | contents |
|---|---|
| `svg/` | 3,963 SVG files, named by codepoints (lowercase hex joined by `-`, FE0F dropped except 4 names), e.g. `1f600.svg`, `1f469-1f3fd-200d-1f680.svg` |
| `png/` | 3,963 PNG renders of the SVGs, 512×512 RGBA, same names |
| `qc/REQUIREMENTS.md` | the codified house requirements (29 scored per emoji, 4 set-level, 4 manual) |
| `qc/xeroqc/` | the QC scorer (`python3 -m xeroqc run`), version 1.0.0 |
| `qc/tests/` | unit tests for the scorer |
| `qc/checkers/` | the checkers xeroqc reuses (check.py, hlaudit, hatfit, posecheck, skel9, mouthbowl, people_qc), as of this snapshot |
| `qc/results/` | the latest full QC run (results.json/.csv, summary.md, report.html, tests.log) and evidence files |
| `qc/locks/` + `qc/verify_locks.sh` | the 75 approved lock manifests (md5 of every file) |
| `qc/*.json` | house spec, skin tones, known-exception lists |
| `qc/coverage.csv` | the Unicode emoji-test 18.0 coverage list the set is checked against (3,963 entries) |
| `qc/FINAL-SET-STATUS-*.md` | the current whole-set status |

## Quality control
Latest run (2026-10-18 12:24 PT, xeroqc 1.0.0): 3,386 PASS, 577 PASS-with-known-exceptions, 0 FAIL; mean score 99.92.
Set checks: coverage 3,963/3,963, no duplicates or orphans, 75/75 locks verify. See `qc/results/20261018-1224PT/summary.md`
and `qc/FINAL-SET-STATUS-*.md`.

Run it from the repo: `cd qc && python3 -m xeroqc run` (results go to `qc/results/<timestamp>PT/`; `--out DIR` to write elsewhere),
tests: `cd qc && python3 -m unittest discover -s tests`, locks: `bash qc/verify_locks.sh`. Paths resolve from the repo layout
(override with `XEROQC_SET` and `XEROQC_COVERAGE`). Needs Python 3 with numpy, Pillow, cairosvg, scikit-image, imagehash.

## License
The artwork is licensed under **Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)**, see `LICENSE`.
Commercial use needs a separate license, see `COMMERCIAL-LICENSE.md`.
