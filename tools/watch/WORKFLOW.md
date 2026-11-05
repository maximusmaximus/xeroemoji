# Unicode watch + candidate generation

Commands run from the repo root. Locked files (`svg/`, `png/`, `qc/locks/`, package emoji maps) stay read-only until a maintainer copies approved candidates in by hand.

## Watch

```bash
python3 tools/watch/watch_unicode.py   # 0 = current, 10 = new emoji, 2 = fetch failure
```

Writes `tools/watch/report.{json,md}` and `state.json`. GitHub Actions: `.github/workflows/unicode-watch.yml`.

## Generate candidates (needs secrets)

```bash
export VENICE_API_KEY=... RECRAFT_API_KEY=...
python3 -m tools.watch.generate.pipeline --repo .
```

Stages under `work/candidates/<version>/`. GitHub Actions: `.github/workflows/unicode-generate.yml` (opens a PR; never merges).

## Spec check on a candidate folder

```bash
python3 tools/watch/run_uts_audit.py \
  --candidates work/candidates/<version> \
  --emoji-test https://www.unicode.org/Public/emoji/latest/emoji-test.txt
```

## After a human approves a candidate PR

Copy approved SVG/PNG into `svg/` and `png/`, add a `qc/locks` manifest, update `qc/coverage.csv`, run `python3 tools/build_emoji_map.py`, rebuild the COLRv1 font, then tag only when ready to publish via the existing `publish.yml`.
