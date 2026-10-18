# xeroemoji (Python), prepared but not published to PyPI yet

A zero-dependency lookup library, CLI and MCP server for [Xero Emoji](https://github.com/maximusmaximus/xeroemoji).
```python
import xeroemoji as xe
xe.get('👍🏿')['png_url']     # https://cdn.jsdelivr.net/gh/maximusmaximus/xeroemoji@v1.0.0/png/1f44d-1f3ff.png
xe.search('pizza', limit=3)
xe.variants('👋')
xe.emojify('hi 👋🏽')          # HTML with <img> tags
```
CLI: `python -m xeroemoji get 🚀` · `search cat` · `variants 👋` · `download 🚀 --format png --out emoji/` · `mcp` (MCP server on stdio).
Install from a clone with `pip install ./packages/python`; the map is bundled when the wheel is built by `tools/build_release.py`. The release also carries the wheel.
Artwork: CC BY-NC 4.0. Commercial use needs a license, see [COMMERCIAL-LICENSE.md](https://github.com/maximusmaximus/xeroemoji/blob/main/COMMERCIAL-LICENSE.md).
