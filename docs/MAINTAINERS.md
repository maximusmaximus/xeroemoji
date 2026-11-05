# Maintainers: Unicode update tooling

How the repository stays aligned with Unicode emoji releases. This describes what is in the tree today.

## Watcher (Phase 0)

- Script: `tools/watch/watch_unicode.py`
- Workflow: `.github/workflows/unicode-watch.yml` (weekly Monday 15:00 UTC, plus `workflow_dispatch`)
- Behaviour: fetches `emoji-test.txt` (released + draft mirrors), diffs fully-qualified sequences against `packages/npm/emoji-map.json`, writes `tools/watch/report.json`, `report.md`, and `state.json`
- Exit codes: `0` = up to date, `10` = new emoji found, `2` = required fetch failed
- On exit `10`, the workflow opens or updates a GitHub issue labeled `unicode-emoji-update` via `tools/watch/issue_from_report.py`, then triggers `unicode-generate.yml`

## Candidate generation

- Workflow: `.github/workflows/unicode-generate.yml` (`workflow_dispatch`, and triggered from the watcher)
- Orchestrator: `python3 -m tools.watch.generate.pipeline`
- Venice (`VENICE_API_KEY`): image model `gpt-image-2-5-flare` with style-reference PNGs from the locked set; text/vision model `z-ai-glm-5-3-flash` for prompt refine + QA
- Recraft (`RECRAFT_API_KEY`): `POST /images/vectorize` (PNG → SVG), with `recraftv4_vector` as fallback
- Outputs land under `work/candidates/<version>/` only — locked `svg/`, `png/`, and `qc/locks/` are never overwritten by the workflow
- The workflow opens a pull request for human review. It does not merge, tag, or publish
- If either secret is missing, the workflow skips API calls and exits successfully after a dry-run inventory

## Spec and QC gates used by the pipeline

- Filename / FQ check: `tools/watch/run_uts_audit.py` (UTS #51 naming vs an `emoji-test.txt`)
- Full locked-set CI remains `.github/workflows/ci.yml` (`tools/ci/check_spec.py`, `qc/verify_locks.sh`, package tests)
- Package publish remains `.github/workflows/publish.yml` on an explicit `v*.*.*` tag only

## Secrets (repo Settings → Secrets and variables → Actions)

| Name | Used by | Purpose |
|---|---|---|
| `VENICE_API_KEY` | `unicode-generate` | Venice inference (image + vision) |
| `RECRAFT_API_KEY` | `unicode-generate` | Recraft vectorize / SVG generation |
| `NPM_TOKEN` | `publish` | npm publish on tag (existing) |
| `PYPI_TOKEN` | `publish` | PyPI upload on tag (existing) |

Never paste secret values into chat, issues, or pull requests. Add them only in the GitHub UI (or the Grok Build phone Secrets flow for Build apps).

## Local commands

```bash
python3 tools/watch/watch_unicode.py
python3 -m tools.watch.generate.pipeline --dry-run
python3 -m unittest discover -s tools/watch/tests -v
```

## Dependency updates

Dependabot is configured in `.github/dependabot.yml` for GitHub Actions, `packages/npm`, `packages/python`, and `tools/blackline`.
