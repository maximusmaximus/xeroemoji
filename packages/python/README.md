# xeroemoji

A zero-dependency lookup library, CLI and MCP server for [Xero Emoji](https://github.com/maximusmaximus/xeroemoji) by Max Infeld: 3,963 Unicode Emoji 18.0 emoji, including every skin tone. The package bundles the emoji map; images are served from jsDelivr (pinned to the `v1.0.0` art tag), or from your own host via `XEROEMOJI_CDN_BASE`.

```sh
pip install xeroemoji
```

```python
import xeroemoji as xe
xe.get('👍🏿')['png_url']     # https://cdn.jsdelivr.net/gh/maximusmaximus/xeroemoji@v1.0.0/png/1f44d-1f3ff.png
xe.search('pizza', limit=3)
xe.variants('👋')            # the default + 5 skin tones
xe.emojify('hi 👋🏽')          # HTML with <img> tags
```

CLI: `xeroemoji get 🚀` · `xeroemoji search cat` · `xeroemoji variants 👋` · `xeroemoji download 🚀 --format png --out emoji/`

MCP server for AI agents (stdio): `xeroemoji-mcp`, or `uvx --from xeroemoji xeroemoji-mcp`. Tools: `search_emoji`, `get_emoji`, `list_categories`, `get_skin_tone_variants`, `emojify_text`. Client setup: [mcp/README.md](https://github.com/maximusmaximus/xeroemoji/blob/main/mcp/README.md).

The full image sets (SVG, PNG 512/128/72) are zips on the [latest GitHub release](https://github.com/maximusmaximus/xeroemoji/releases/latest). Demos: https://maximusmaximus.github.io/xeroemoji/

## License

CC BY 4.0 (SPDX `CC-BY-4.0`). Free for any use, including commercial, with credit: "Xero Emoji by Max Infeld, CC BY 4.0" and a link to https://github.com/maximusmaximus/xeroemoji. The Xero Emoji color font, the book and merch are not covered and need a commercial license; see [LICENSING.md](https://github.com/maximusmaximus/xeroemoji/blob/main/LICENSING.md) (also included in this package). Versions up to 1.0.0 were CC BY-NC 4.0.
