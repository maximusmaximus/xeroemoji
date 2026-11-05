#!/usr/bin/env python3
"""Thin UTS #51 coverage check for a candidate dir vs an emoji-test file.
Does not modify locked svg/png. Exit 0 if every candidate filename is a valid
FQ key (FE0F stripped) present in emoji-test; exit 1 on bad names.
"""
from __future__ import annotations
import argparse, pathlib, re, sys, urllib.request

NAME = re.compile(r"^[0-9a-f]{4,6}(-[0-9a-f]{4,6})*$")

def load_fq(path_or_url: str) -> set[str]:
    if re.match(r"https?://", path_or_url):
        raw = urllib.request.urlopen(path_or_url, timeout=60).read().decode("utf-8", "replace")
    else:
        raw = pathlib.Path(path_or_url).read_text(encoding="utf-8")
    want = set()
    for line in raw.splitlines():
        if "; fully-qualified" not in line:
            continue
        cps = line.split(";")[0].split()
        key = "-".join(c.lower() for c in cps if c.upper() != "FE0F")
        want.add(key)
    return want

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidates", required=True, type=pathlib.Path)
    ap.add_argument("--emoji-test", required=True)
    args = ap.parse_args(argv)
    if not args.candidates.exists():
        print(f"no candidates dir: {args.candidates}")
        return 0
    want = load_fq(args.emoji_test)
    errs = []
    for ext in ("svg", "png"):
        for p in sorted(args.candidates.glob(f"*.{ext}")):
            if not NAME.match(p.stem):
                errs.append(f"bad name {p.name}")
            elif p.stem not in want:
                errs.append(f"not in emoji-test: {p.name}")
    print(f"candidates checked; problems: {len(errs)}")
    for e in errs[:50]:
        print(" ", e)
    return 1 if errs else 0

if __name__ == "__main__":
    raise SystemExit(main())
