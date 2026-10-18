#!/usr/bin/env python3
"""Xero Emoji MCP server launcher for a clone of the repo (no install, no dependencies, Python 3.9+).
Reads demos/emoji-map.json and svg/ from this repo; set XEROEMOJI_MAP to use another map, XEROEMOJI_CDN_BASE for other URLs."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'packages', 'python'))
from xeroemoji.mcp_server import serve
if __name__ == '__main__':
    serve()
