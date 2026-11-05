#!/usr/bin/env python3
"""Open or update a GitHub issue from tools/watch/report.json (uses `gh`)."""
from __future__ import annotations
import json, os, pathlib, subprocess, sys, re

LABEL = "unicode-emoji-update"
TITLE_PREFIX = "[unicode] emoji update"

def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=check, text=True, capture_output=True)

def find_open_issue() -> str | None:
    cp = run(["gh", "issue", "list", "--label", LABEL, "--state", "open", "--json", "number,title", "--limit", "20"], check=False)
    if cp.returncode != 0:
        return None
    for it in json.loads(cp.stdout or "[]"):
        if it.get("title", "").startswith(TITLE_PREFIX):
            return str(it["number"])
    return None

def ensure_label() -> None:
    run(["gh", "label", "create", LABEL, "--description", "Unicode emoji watcher found new sequences", "--color", "0E8A16"], check=False)

def body_from_report(report: dict) -> str:
    lines = [
        "## Unicode emoji watch report",
        f"- Status: **{report.get('status')}**",
        f"- Run at: `{report.get('run_at')}`",
        f"- Latest released: `{report.get('latest_released')}` ({report.get('latest_released_fq_count')} FQ)",
        f"- Draft: `{report.get('draft_version')}` ({report.get('draft_fq_count')} FQ)",
        f"- Locked set: {report.get('locked_count')}",
        f"- Changed sources: `{report.get('changed_sources')}`",
        "",
        f"### Missing from locked (released): {len(report.get('missing_from_locked_released') or [])}",
    ]
    for x in (report.get("missing_from_locked_released") or [])[:100]:
        lines.append(f"- {x.get('emoji','')} `{x.get('seq')}` E{x.get('E')} {x.get('name')}")
    lines += ["", f"### Missing from locked (draft): {len(report.get('missing_from_locked_draft') or [])}"]
    for x in (report.get("missing_from_locked_draft") or [])[:100]:
        lines.append(f"- {x.get('emoji','')} `{x.get('seq')}` E{x.get('E')} {x.get('name')}")
    lines += [
        "",
        "This issue is maintained by `.github/workflows/unicode-watch.yml`.",
        "Candidate art PRs are opened by `.github/workflows/unicode-generate.yml` (manual review required; never auto-merged).",
    ]
    return "\n".join(lines) + "\n"

def main(argv: list[str] | None = None) -> int:
    repo = pathlib.Path(__file__).resolve().parents[2]
    report_path = pathlib.Path(argv[1]) if argv and len(argv) > 1 else repo / "tools/watch/report.json"
    if not report_path.exists():
        print(f"missing {report_path}", file=sys.stderr)
        return 2
    report = json.loads(report_path.read_text(encoding="utf-8"))
    status = report.get("status")
    if status in {None, "OK", "FETCH_FAILURE"} and not (report.get("missing_from_locked_released") or report.get("missing_from_locked_draft")):
        if status == "FETCH_FAILURE":
            print("fetch failure; not opening an update issue")
            return 0
        print("no new emoji; nothing to file")
        return 0
    ensure_label()
    ver = report.get("latest_released") or report.get("draft_version") or "?"
    title = f"{TITLE_PREFIX}: {ver} ({report.get('status')})"
    body = body_from_report(report)
    existing = find_open_issue()
    if existing:
        run(["gh", "issue", "edit", existing, "--title", title, "--body", body])
        # comment a short ping
        n_rel = len(report.get("missing_from_locked_released") or [])
        n_dr = len(report.get("missing_from_locked_draft") or [])
        run(["gh", "issue", "comment", existing, "--body", f"Watcher re-ran: released missing={n_rel}, draft missing={n_dr}."], check=False)
        print(f"updated issue #{existing}")
    else:
        cp = run(["gh", "issue", "create", "--title", title, "--body", body, "--label", LABEL])
        print(cp.stdout.strip())
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
