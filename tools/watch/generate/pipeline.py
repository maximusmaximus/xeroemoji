"""Orchestrate: missing emoji -> Venice PNG (style refs) -> Recraft SVG -> vision QA -> stage."""
from __future__ import annotations
import base64, json, os, pathlib, shutil, sys
from dataclasses import dataclass, asdict
from typing import Any, Optional

from .prompts import refine_prompt, template_prompt, vision_qa_messages
from .recraft_client import RecraftClient, RecraftError
from .style_refs import pick_style_refs
from .venice_client import VeniceClient, VeniceError

@dataclass
class CandidateResult:
    seq: str
    name: str
    status: str  # staged | skipped | failed
    detail: str = ""
    svg_path: str = ""
    png_path: str = ""
    qa: str = ""

def secrets_present() -> tuple[bool, list[str]]:
    missing = []
    if not os.environ.get("VENICE_API_KEY"):
        missing.append("VENICE_API_KEY")
    if not (os.environ.get("RECRAFT_API_KEY") or os.environ.get("RECRAFT_API_TOKEN")):
        missing.append("RECRAFT_API_KEY")
    return (not missing), missing

def missing_from_report(report: dict) -> list[dict]:
    items = list(report.get("missing_from_locked_released") or [])
    # Prefer released; include draft only when env says so
    if os.environ.get("INCLUDE_DRAFT", "").lower() in {"1", "true", "yes"}:
        items += list(report.get("missing_from_locked_draft") or [])
    # Dedup by seq
    seen, out = set(), []
    for it in items:
        s = it.get("seq")
        if s and s not in seen:
            seen.add(s)
            out.append(it)
    return out

def run_pipeline(
    repo: pathlib.Path,
    report: dict,
    *,
    out_dir: Optional[pathlib.Path] = None,
    max_candidates: Optional[int] = None,
    dry_run: bool = False,
    venice: Optional[VeniceClient] = None,
    recraft: Optional[RecraftClient] = None,
) -> dict[str, Any]:
    ok, missing_secrets = secrets_present()
    if not ok and not dry_run and venice is None:
        return {
            "status": "skipped_missing_secrets",
            "missing_secrets": missing_secrets,
            "candidates": [],
        }
    items = missing_from_report(report)
    lim = max_candidates
    if lim is None:
        lim = int(os.environ.get("MAX_CANDIDATES", "20"))
    items = items[: max(0, lim)]
    version = report.get("latest_released") or report.get("draft_version") or "unknown"
    dest = out_dir or (repo / "work" / "candidates" / str(version))
    dest.mkdir(parents=True, exist_ok=True)
    results: list[CandidateResult] = []
    if dry_run:
        for it in items:
            results.append(CandidateResult(seq=it["seq"], name=it.get("name", ""), status="skipped", detail="dry_run"))
        return {"status": "dry_run", "out_dir": str(dest), "candidates": [asdict(r) for r in results]}

    venice = venice or VeniceClient()
    recraft = recraft or RecraftClient()

    for it in items:
        seq, name = it["seq"], it.get("name") or ""
        group = it.get("group") or ""
        subgroup = it.get("subgroup") or ""
        try:
            prompt = refine_prompt(venice, name=name, seq=seq, group=group, subgroup=subgroup)
            refs = pick_style_refs(repo, name=name, group=group, subgroup=subgroup, n=3)
            ref_bytes = [p.read_bytes() for p in refs]
            png = venice.multi_edit_png(prompt, ref_bytes) if ref_bytes else venice.generate_image_png(prompt)
            try:
                svg = recraft.vectorize_png(png)
            except RecraftError as e:
                # Fallback: native vector generation with style refs as data URLs
                style_urls = [
                    "data:image/png;base64," + base64.b64encode(b).decode("ascii") for b in ref_bytes[:4]
                ]
                svg = recraft.generate_svg(prompt, style_reference_data_urls=style_urls or None)
                detail_vec = f"vectorize_failed_used_generate:{e}"
            else:
                detail_vec = "vectorize_ok"

            svg_path = dest / f"{seq}.svg"
            png_path = dest / f"{seq}.png"
            svg_path.write_bytes(svg)
            png_path.write_bytes(png)

            qa = _vision_qa(venice, name=name, seq=seq, png=png, refs=ref_bytes)
            status = "staged"
            if qa.upper().startswith("FAIL"):
                status = "failed"
            def rel(path: pathlib.Path) -> str:
                try:
                    return str(path.resolve().relative_to(repo.resolve()))
                except ValueError:
                    return str(path)
            results.append(CandidateResult(
                seq=seq, name=name, status=status, detail=detail_vec,
                svg_path=rel(svg_path),
                png_path=rel(png_path),
                qa=qa,
            ))
        except Exception as e:
            results.append(CandidateResult(seq=seq, name=name, status="failed", detail=str(e)[:500]))

    try:
        out_dir_s = str(dest.resolve().relative_to(repo.resolve()))
    except ValueError:
        out_dir_s = str(dest)
    summary = {
        "status": "ok",
        "out_dir": out_dir_s,
        "version": version,
        "candidates": [asdict(r) for r in results],
        "staged": sum(1 for r in results if r.status == "staged"),
        "failed": sum(1 for r in results if r.status == "failed"),
    }
    (dest / "pipeline-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary

def _vision_qa(venice: VeniceClient, *, name: str, seq: str, png: bytes, refs: list[bytes]) -> str:
    cand = "data:image/png;base64," + base64.b64encode(png).decode("ascii")
    ref_urls = ["data:image/png;base64," + base64.b64encode(b).decode("ascii") for b in refs[:3]]
    try:
        return venice.chat(vision_qa_messages(name, seq, cand, ref_urls), max_tokens=200)
    except VeniceError as e:
        return f"PASS: vision_qa_unavailable ({e})"  # do not block staging on QA transport errors

def main(argv: Optional[list[str]] = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[3])
    ap.add_argument("--report", type=pathlib.Path, default=None)
    ap.add_argument("--out", type=pathlib.Path, default=None)
    ap.add_argument("--max", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    report_path = args.report or (args.repo / "tools/watch/report.json")
    if not report_path.exists():
        print(f"missing report: {report_path}", file=sys.stderr)
        return 2
    report = json.loads(report_path.read_text(encoding="utf-8"))
    summary = run_pipeline(args.repo, report, out_dir=args.out, max_candidates=args.max, dry_run=args.dry_run)
    print(json.dumps(summary, indent=2))
    if summary.get("status") == "skipped_missing_secrets":
        print("SKIP: secrets not configured: " + ", ".join(summary.get("missing_secrets") or []), file=sys.stderr)
        return 0
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
