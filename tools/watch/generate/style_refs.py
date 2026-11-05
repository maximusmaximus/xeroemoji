"""Pick style-reference PNGs from the locked set for a new emoji."""
from __future__ import annotations
import json, pathlib, random
from typing import Optional

def load_map(repo: pathlib.Path) -> dict:
    for rel in ("packages/npm/emoji-map.json", "demos/emoji-map.json"):
        p = repo / rel
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    raise FileNotFoundError("emoji-map.json not found")

def pick_style_refs(
    repo: pathlib.Path,
    *,
    name: str = "",
    group: str = "",
    subgroup: str = "",
    n: int = 3,
    rng: Optional[random.Random] = None,
) -> list[pathlib.Path]:
    """Return up to n PNG paths from the same subgroup (fallback: group, then smiling faces)."""
    m = load_map(repo)
    png_dir = repo / "png"
    by_sub, by_grp = [], []
    for key, row in m.items():
        # row: [file, emoji, name, group, subgroup, order]
        if not isinstance(row, list) or len(row) < 5:
            continue
        path = png_dir / f"{row[0]}.png"
        if not path.exists():
            continue
        if subgroup and row[4] == subgroup:
            by_sub.append(path)
        elif group and row[3] == group:
            by_grp.append(path)
    pool = by_sub or by_grp
    if not pool:
        # stable fallback: first few face-smiling
        for key, row in m.items():
            if isinstance(row, list) and len(row) >= 5 and row[4] == "face-smiling":
                p = png_dir / f"{row[0]}.png"
                if p.exists():
                    pool.append(p)
                if len(pool) >= 20:
                    break
    if not pool:
        return []
    r = rng or random.Random(f"{name}|{group}|{subgroup}")
    if len(pool) <= n:
        return list(pool)
    return r.sample(pool, n)
