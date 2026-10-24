# AGENTS.md: working with Xero Emoji

This file is for coding agents (Cursor, Claude Code, Codex, Copilot and others) that use or change this repository.

## What this repo is
- **Xero Emoji**: all 3,963 fully-qualified emoji of Unicode Emoji 18.0, by Max Infeld (started in 2016). Created by maxi.grok.me.
- **Files:** each emoji is an SVG in `svg/<name>.svg` (viewBox 512) and a PNG render in `png/<name>.png` (512×512 RGBA).
- **Approved art:** every svg and png is locked by md5 in `qc/locks/` (75 manifests).

## Layout
| path | what |
|---|---|
| `svg/`, `png/` | the art. **Do not edit, rename, re-render or optimise these files.** Locks must keep verifying 75/75. |
| `demos/emoji-map.json` | emoji → file map: `{key: [file, emoji, name, group, subgroup, order]}` (3,963 entries) |
| `demos/xero-emoji.js` | browser replacer (Unicode emoji → `<img>`) |
| `demos/*.html`, `index.html` | GitHub Pages site: https://maximusmaximus.github.io/xeroemoji/ |
| `packages/python/` | `xeroemoji` Python lib + CLI + MCP server (no dependencies) |
| `packages/npm/` | `xeroemoji` npm lib + CLI (prepared; **not published**) |
| `mcp/` | MCP server launcher and setup docs |
| `qc/` | `xeroqc` scorer, requirements, checkers, locks, latest results |
| `tools/` | `build_emoji_map.py`, `build_release.py`, `make_showcase.py`, `ci/release.yml` |
| `docs/` | `USAGE.md`, `HISTORY.md`, `RELEASE_NOTES.md`, showcase images |

## Looking up an emoji
- **Key:** the emoji's codepoints in lowercase hex, at least 4 digits, joined by `-`, with every U+FE0F removed. Examples: `👍🏿` → `1f44d-1f3ff`; `©️` → `00a9`.
- **File:** `emoji-map.json[key][0]`. It always equals the key (FE0F is dropped from every filename).
- **Skin tones:** U+1F3FB…1F3FF go right after the person or hand codepoint, before any ZWJ: `1f9d1-1f3fd-200d-1f373`.
- **Helpers:** `python3 -m xeroemoji get 👍🏿` (run from `packages/python`, or after `pip install`), `node packages/npm/cli.js get 👍🏿` (after `cd packages/npm && node test.js` once, which bundles the map), or the MCP tools.
- **URLs:** `https://cdn.jsdelivr.net/gh/maximusmaximus/xeroemoji@v1.0.2/svg/<file>.svg` (pinned) or `@latest`.

## License rules (tell users when you use the art)
- **Artwork** (`svg/`, `png/`, release zips, CDN images, `emoji-map.json`, npm/PyPI packages): **CC BY 4.0** (`LICENSE`, scope in `LICENSING.md`). Any use, including commercial, is allowed with credit: "Xero Emoji by Max Infeld, CC BY 4.0" plus a link to the repo.
- **Not CC BY:** the color font in `fonts/` (CC BY-NC 4.0 for non-commercial use, commercial use needs a license), the book (Xero Emoji Specimen Guide) and merch/stickers. Do not tell users the font, book or merch can be used commercially without a license (`COMMERCIAL-LICENSE.md`).
- Releases up to v1.0.0 were CC BY-NC 4.0; the same artwork is now also CC BY 4.0.
- Keep the license files when you redistribute.

## Checks before any commit
```bash
bash qc/verify_locks.sh                                     # must print 75 OK lines, exit 0
python3 -m unittest discover -s packages/python/tests -v    # lib + CLI + MCP
(cd packages/npm && node test.js)                           # npm lib
cd qc && python3 -m unittest discover -s tests && python3 -m xeroqc run --out /tmp/xq   # full QC, about 3 min; expect 0 FAIL
```
QC needs numpy, Pillow, cairosvg, scikit-image and imagehash. The demos need no build step. After changing `qc/coverage.csv`, regenerate the map with `python3 tools/build_emoji_map.py`.

## Do not
- Change files in `svg/`, `png/` or `qc/locks/`, or add exceptions to `qc/*known-exceptions.json`, without the maintainer's explicit approval.
- Publish to npm, PyPI or any registry; that is the maintainer's call.
- Force-push `main`, or move or delete release tags.
