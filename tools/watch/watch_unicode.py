#!/usr/bin/env python3
"""Xero Emoji Unicode release watcher. Read-only on locked files.
Fetches unicode.org emoji data (with retries + mirrors), tracks hashes/versions in
state.json, diffs emoji-test.txt fully-qualified sequences against the locked set
(packages/npm/emoji-map.json). Writes report.json + report.md. Exit 0=ok/no new,
10=new emoji found, 2=fetch failure."""
import hashlib, json, re, sys, time, urllib.request, datetime, pathlib
HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
LOCKED = REPO / "packages/npm/emoji-map.json"
BLACKLINE = REPO / "blackline/svg"  # planned output layout (xero-blackline/PLAN.md)
STATE = HERE / "state.json"
UA = {"User-Agent": "xeroemoji-watcher/1.0 (+github.com/maximusmaximus/xeroemoji)"}
GH = "https://raw.githubusercontent.com/unicode-org/unicodetools/main/unicodetools/data/emoji"
SOURCES = {
 "emoji_index": ["https://unicode.org/Public/emoji/", "https://www.unicode.org/Public/emoji/"],
 "emoji_test_latest": ["https://unicode.org/Public/emoji/latest/emoji-test.txt",
                       "https://www.unicode.org/Public/emoji/latest/emoji-test.txt"],
 "draft_emoji_test": ["https://unicode.org/Public/draft/emoji/emoji-test.txt",
                      "https://www.unicode.org/Public/draft/emoji/emoji-test.txt",
                      GH + "/dev/emoji-test.txt"],
 "uts51": ["https://unicode.org/reports/tr51/", "https://www.unicode.org/reports/tr51/"],
 "uts51_proposed": ["https://www.unicode.org/reports/tr51/proposed.html"],
 "emoji_candidates": ["https://www.unicode.org/emoji/emoji-proposals-status.html",
                      "https://unicode.org/emoji/charts/emoji-proposals.html"],
 "public_index": ["https://www.unicode.org/Public/", "https://unicode.org/Public/"],
}
REQUIRED = {"emoji_index", "emoji_test_latest"}
OPTIONAL_TRIES, OPTIONAL_TIMEOUT = 1, 10

def fetch(urls, tries=3, timeout=30):
    errs = []
    for u in urls:
        for i in range(tries):
            try:
                with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=timeout) as r:
                    return u, r.read().decode("utf-8", "replace")
            except Exception as e:
                errs.append(f"{u} try{i+1}: {e}")
                if getattr(e, "code", None) == 404: break  # dead URL: next mirror
                if i + 1 < tries: time.sleep(2 ** i)
    raise RuntimeError("; ".join(errs[-3:]))

def norm(seq): return "-".join(c for c in seq.lower().split("-") if c != "fe0f")

def parse_test(txt):
    ver = re.search(r"^# Version:\s*([\d.]+)", txt, re.M)
    out = {}
    for line in txt.splitlines():
        m = re.match(r"^([0-9A-F ]+?)\s*;\s*fully-qualified\s*#\s*\S+\s+E([\d.]+)\s+(.*)$", line)
        if m: out["-".join(m.group(1).split()).lower()] = (m.group(2), m.group(3))
    return (ver.group(1) if ver else None), out

def main():
    now = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    state = json.loads(STATE.read_text()) if STATE.exists() else {"sources": {}}
    got, fails = {}, {}
    for k, urls in SOURCES.items():
        try: got[k] = fetch(urls) if k in REQUIRED else fetch(urls, OPTIONAL_TRIES, OPTIONAL_TIMEOUT)
        except Exception as e: fails[k] = str(e)
    report = {"run_at": now, "fetch_failures": fails}
    if REQUIRED & fails.keys():
        report["status"] = "FETCH_FAILURE"
        (HERE / "report.json").write_text(json.dumps(report, indent=2))
        print("ERROR: required source(s) unreachable on all mirrors: " + ", ".join(sorted(REQUIRED & fails.keys())), file=sys.stderr)
        return 2
    vers = sorted({v for v in re.findall(r'href="(\d+\.\d+)/"', got["emoji_index"][1])}, key=lambda s: tuple(map(int, s.split("."))))
    if "public_index" in got:  # Unicode 17+ publish emoji under /Public/<X.Y.Z>/emoji/
        pv = {".".join(v.split(".")[:2]) for v in re.findall(r'href="(\d+\.\d+\.\d+)/"', got["public_index"][1])}
        vers = sorted(set(vers) | {v for v in pv if int(v.split(".")[0]) >= 17}, key=lambda s: tuple(map(int, s.split("."))))
    latest_ver, latest = parse_test(got["emoji_test_latest"][1])
    draft_ver, draft = (parse_test(got["draft_emoji_test"][1]) if "draft_emoji_test" in got else (None, {}))
    locked = {norm(k) for k in json.loads(LOCKED.read_text())}
    def missing(d): return sorted([{"seq": s, "emoji": "".join(chr(int(c, 16)) for c in s.split("-")), "E": v[0], "name": v[1]}
                                   for s, v in d.items() if norm(s) not in locked], key=lambda x: x["seq"])
    m_rel, m_dr = missing(latest), (missing(draft) if draft_ver != latest_ver else [])
    TONE = re.compile(r"-1f3f[b-f]")
    def bl(items):  # every new sequence needs a blackline; tone variants can alias the base (mono collapses tones)
        out = []
        for x in items:
            n = norm(x["seq"]); base = TONE.sub("", n)
            out.append({"seq": n, "name": x["name"], "tone_alias_of": base if base != n else None,
                        "blackline_exists": (BLACKLINE / f"{n}.svg").exists()})
        return out
    extra = sorted(locked - {norm(s) for s in latest})
    changed = []
    for k, (u, body) in got.items():
        h = hashlib.sha256(body.encode()).hexdigest(); old = state["sources"].get(k, {}).get("sha256")
        if old and old != h: changed.append(k)
        state["sources"][k] = {"url": u, "sha256": h, "checked": now}
    state.update(last_run=now, index_versions=vers, latest_released=latest_ver, draft=draft_ver, locked_count=len(locked))
    STATE.write_text(json.dumps(state, indent=2))
    report.update(status="NEW_EMOJI" if m_rel or m_dr else "OK", index_versions=vers, latest_released=latest_ver,
                  latest_released_fq_count=len(latest), draft_version=draft_ver, draft_fq_count=len(draft),
                  locked_count=len(locked), missing_from_locked_released=m_rel, missing_from_locked_draft=m_dr,
                  locked_not_in_latest=extra, needs_blackline=bl(m_rel + m_dr), changed_sources=changed, sources={k: v[0] for k, v in got.items()})
    (HERE / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    md = [f"# Unicode emoji watch — {now}", f"- Status: **{report['status']}**",
          f"- Latest released: {latest_ver} ({len(latest)} fully-qualified)", f"- Draft: {draft_ver} ({len(draft)})",
          f"- Locked set: {len(locked)}", f"- Changed sources since last run: {changed or 'none'}",
          f"- Fetch failures (optional sources): {list(fails) or 'none'}",
          f"\n## Missing from locked (released): {len(m_rel)}"] + [f"- {x['emoji']} `{x['seq']}` E{x['E']} {x['name']}" for x in m_rel] + \
         [f"\n## Missing from locked (draft): {len(m_dr)}"] + [f"- {x['emoji']} `{x['seq']}` E{x['E']} {x['name']}" for x in m_dr] + \
         [f"\n## Needs blackline: {len(m_rel)+len(m_dr)}"] + [f"- `{b['seq']}` {b['name']}" + (f" (tone alias of `{b['tone_alias_of']}`)" if b['tone_alias_of'] else "") for b in bl(m_rel + m_dr)] + \
         [f"\n## Locked but not in latest: {len(extra)}"] + [f"- `{s}`" for s in extra]
    (HERE / "report.md").write_text("\n".join(md) + "\n")
    print("\n".join(md[:7]) + f"\nmissing released={len(m_rel)} draft={len(m_dr)}")
    return 10 if (m_rel or m_dr) else 0

if __name__ == "__main__": sys.exit(main())
