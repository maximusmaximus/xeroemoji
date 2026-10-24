# Xero Emoji MCP server

This is a small [Model Context Protocol](https://modelcontextprotocol.io) server. It lets AI agents and IDEs look up Xero Emoji and get their SVG/PNG URLs.
It is plain Python 3.9+, uses stdio with JSON-RPC 2.0, and has **no dependencies**. Data comes from the repo's `demos/emoji-map.json`, the copy bundled in the wheel, or the jsDelivr CDN.

| tool | input | returns |
|---|---|---|
| `search_emoji` | `query`, optional `group`, `limit`, `include_tones` | best matches with emoji, name, group, file and `svg_url`/`png_url` |
| `get_emoji` | `emoji` (emoji, codepoints such as `1f44d-1f3ff` / `U+1F44D U+1F3FF`, file name or exact name), `include_svg` | metadata, CDN URLs, repo paths, the license line, and optionally the SVG source |
| `list_categories` | none | 9 groups with subgroups and counts (3,963 total) |
| `get_skin_tone_variants` | `emoji` | the default and every skin-tone variant |
| `emojify_text` | `text`, `format` (`html`/`markdown`), `image` (`svg`/`png`) | the text with emoji replaced by Xero images |

## Run it
Pick one:
```bash
# A) from a clone (nothing to install)
git clone https://github.com/maximusmaximus/xeroemoji && python3 xeroemoji/mcp/server.py
# B) from PyPI (bundles the emoji map)
pip install xeroemoji && xeroemoji-mcp
# C) straight from git with uv (the map is fetched from the CDN on first use)
uvx --from "git+https://github.com/maximusmaximus/xeroemoji#subdirectory=packages/python" xeroemoji-mcp
```

## Client setup
**Cursor**: `~/.cursor/mcp.json`, or `.cursor/mcp.json` in a project:
```json
{ "mcpServers": { "xeroemoji": { "command": "python3", "args": ["/ABSOLUTE/PATH/xeroemoji/mcp/server.py"] } } }
```
**Claude Desktop**: `claude_desktop_config.json`. On macOS it is in `~/Library/Application Support/Claude/`; on Windows in `%APPDATA%\Claude\`.
```json
{ "mcpServers": { "xeroemoji": { "command": "python3", "args": ["/ABSOLUTE/PATH/xeroemoji/mcp/server.py"] } } }
```
**Claude Code**: `claude mcp add xeroemoji -- python3 /ABSOLUTE/PATH/xeroemoji/mcp/server.py`

**VS Code (Copilot agent mode)**: `.vscode/mcp.json`:
```json
{ "servers": { "xeroemoji": { "type": "stdio", "command": "python3", "args": ["/ABSOLUTE/PATH/xeroemoji/mcp/server.py"] } } }
```
**Any other stdio MCP client**: the command is `python3 /path/mcp/server.py`, or `xeroemoji-mcp` once the wheel is installed.

Environment variables (optional):
- `XEROEMOJI_MAP`: path to another `emoji-map.json`.
- `XEROEMOJI_CDN_BASE`: base URL for images, e.g. your own host. The default is `https://cdn.jsdelivr.net/gh/maximusmaximus/xeroemoji@v1.0.2/`.

## Tests
```bash
python3 -m unittest discover -s packages/python/tests -v    # core + CLI + a full MCP session over stdio
pip install mcp && python3 mcp/tests/sdk_client_check.py      # interop with the official MCP Python SDK client
```

The artwork is CC BY 4.0 (credit "Xero Emoji by Max Infeld, CC BY 4.0"; see LICENSING.md). The server includes that line in its `instructions` and in every `get_emoji` result.
