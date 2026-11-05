#!/usr/bin/env python3
"""Create a branch + PR from staged work/candidates (never merges)."""
from __future__ import annotations
import json, os, pathlib, subprocess, sys, time

def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print("+", " ".join(cmd), flush=True)
    return subprocess.run(cmd, check=check, text=True, capture_output=True)

def main() -> int:
    repo = pathlib.Path(__file__).resolve().parents[2]
    summary_paths = sorted((repo / "work" / "candidates").glob("*/pipeline-summary.json"))
    if not summary_paths:
        print("no pipeline-summary.json under work/candidates; nothing to PR")
        return 0
    summary = json.loads(summary_paths[-1].read_text(encoding="utf-8"))
    staged = [c for c in summary.get("candidates") or [] if c.get("status") == "staged"]
    if not staged and not any((summary_paths[-1].parent).glob("*.svg")):
        print("no staged candidates; skipping PR")
        return 0
    version = summary.get("version") or "unknown"
    stamp = time.strftime("%Y%m%d-%H%M%S")
    branch = f"unicode-candidates/{version}-{stamp}"
    # Ensure we are not on main when committing
    run(["git", "config", "user.name", "xeroemoji-unicode-bot"])
    run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"])
    run(["gh", "label", "create", "unicode-emoji-update", "--description", "Unicode emoji watcher / candidates", "--color", "0E8A16"], check=False)
    run(["git", "checkout", "-B", branch])
    # Only add candidate outputs + watch report artifacts (never touch locked svg/png)
    run(["git", "add", "-A", "work/candidates", "tools/watch/report.json", "tools/watch/report.md", "tools/watch/state.json"], check=False)
    # If nothing staged, exit quietly
    st = run(["git", "status", "--porcelain"], check=False)
    if not (st.stdout or "").strip():
        print("working tree clean after add; skipping PR")
        return 0
    msg = f"unicode candidates for {version} ({len(staged)} staged)"
    run(["git", "commit", "-m", msg])
    run(["git", "push", "-u", "origin", branch])
    body = f"""## Unicode emoji candidates ({version})

Automated candidate art from `.github/workflows/unicode-generate.yml`.

- Staged: {summary.get('staged')}
- Failed: {summary.get('failed')}
- Output: `{summary.get('out_dir')}`

### Review checklist
- [ ] Visual style matches locked Xero Emoji
- [ ] Filenames are lowercase hex with FE0F stripped
- [ ] xeroqc / UTS #51 notes in the workflow log look sane
- [ ] After approval: copy into `svg/` + `png/`, add a `qc/locks` manifest, rebuild maps/font, then tag manually

**This PR must not be auto-merged.** Publishing stays on the existing tag-triggered `publish.yml` only after an explicit human tag.
"""
    cp = run([
        "gh", "pr", "create",
        "--base", "main",
        "--head", branch,
        "--title", f"[unicode] candidate art for {version}",
        "--body", body,
        "--label", "unicode-emoji-update",
    ], check=False)
    print(cp.stdout or cp.stderr)
    return 0 if cp.returncode == 0 else cp.returncode

if __name__ == "__main__":
    raise SystemExit(main())
