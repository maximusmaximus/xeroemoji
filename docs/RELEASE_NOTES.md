# Xero Emoji v1.0.2: now CC BY 4.0

**The emoji artwork is now licensed under CC BY 4.0.** Use it anywhere, including commercial apps and open-source projects under any license, with the credit line "Xero Emoji by Max Infeld, CC BY 4.0" and a link to https://github.com/maximusmaximus/xeroemoji. See `LICENSING.md` for exactly what is covered.

- **CC BY 4.0:** every image in `svg/` and `png/`, the release zips, the CDN images, `emoji-map.json`, `xero-emoji.js`, and the `xeroemoji` npm and PyPI packages.
- **Not CC BY:** the Xero Emoji color font (`fonts/`, free for non-commercial use under CC BY-NC 4.0, commercial use needs a license), the book (Xero Emoji Specimen Guide) and merch/stickers. See `COMMERCIAL-LICENSE.md`.
- **Earlier releases:** v1.0.0 and the 1.0.1 packages were published under CC BY-NC 4.0; the same artwork is now also available under CC BY 4.0.
- **Packages:** `xeroemoji` 1.0.2 on npm and PyPI, SPDX `CC-BY-4.0`. Image URLs now point at the `v1.0.2` tag: `https://cdn.jsdelivr.net/gh/maximusmaximus/xeroemoji@v1.0.2/svg/<name>.svg`.
- **Art:** unchanged since v1.0.0 (3,963 emoji, Unicode Emoji 18.0). Every zip now also contains `LICENSING.md`.

| asset | contents |
|---|---|
| `xeroemoji-svg.zip` | 3,963 SVG (viewBox 512) |
| `xeroemoji-png-512.zip` | 3,963 PNG 512×512, the approved renders |
| `xeroemoji-png-128.zip`, `xeroemoji-png-72.zip` | 128 and 72 px PNGs, downscaled from the 512s |
| `emoji-map.json` | emoji → file, name, group, subgroup, order |
| `xero-emoji.js` | the browser replacer (Unicode emoji → `<img>`) |
| `xeroemoji-1.0.2.tgz`, `xeroemoji-1.0.2-py3-none-any.whl`, `xeroemoji-1.0.2.tar.gz` | the npm and Python packages (also on npm and PyPI) |
| `SHA256SUMS.txt` | checksums |

---

# Xero Emoji v1.0.0

This is the first public release of **Xero Emoji**: all **3,963** fully-qualified emoji of **Unicode Emoji 18.0**, by Max Infeld. The project was started in 2016 and first previewed as "Xeromoji" on Steemit on World Emoji Day 2017. Created by maxi.grok.me.

## Downloads (stable `latest` URLs)
| asset | contents |
|---|---|
| `xeroemoji-svg.zip` | 3,963 SVG (viewBox 512) |
| `xeroemoji-png-512.zip` | 3,963 PNG 512×512, the approved renders |
| `xeroemoji-png-128.zip`, `xeroemoji-png-72.zip` | 128 and 72 px PNGs, downscaled from the 512s |
| `emoji-map.json` | emoji → file, name, group, subgroup, order |
| `xero-emoji.js` | the browser replacer (Unicode emoji → `<img>`) |
| `xeroemoji-1.0.0.tgz`, `xeroemoji-1.0.0-py3-none-any.whl` | npm and Python packages: lookup, CLI and the MCP server (Python). |
| `SHA256SUMS.txt` | checksums |

```bash
curl -fLO https://github.com/maximusmaximus/xeroemoji/releases/latest/download/xeroemoji-svg.zip
```
CDN: `https://cdn.jsdelivr.net/gh/maximusmaximus/xeroemoji@v1.0.0/svg/<name>.svg`. File names are explained in the README section "For app developers".

## Quality
- **xeroqc:** 3,386 PASS · 577 PASS-with-known-exceptions · 0 FAIL.
- **Locks:** 75/75 lock manifests verify.
- **Coverage:** 3,963/3,963.

## For agents
`AGENTS.md`, `llms.txt` and a zero-dependency MCP server (`mcp/`) with search_emoji, get_emoji, list_categories, get_skin_tone_variants and emojify_text.

## Build
The assets are reproducible with `python3 tools/build_release.py`, which gives sorted entries, fixed timestamps and byte-identical output.

## License
v1.0.0 was released under CC BY-NC 4.0. Since October 2026 the artwork is CC BY 4.0 (the font, book and merch stay under a commercial license), see LICENSING.md.
