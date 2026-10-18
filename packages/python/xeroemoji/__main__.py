"""xeroemoji CLI.
  python -m xeroemoji get 👍🏿            # metadata + URLs (JSON)
  python -m xeroemoji search cat --limit 5
  python -m xeroemoji variants 👋
  python -m xeroemoji categories
  python -m xeroemoji emojify "hi 👋🏽"   # HTML
  python -m xeroemoji download 🚀 --format png --out ./emoji   # fetch files from the CDN
  python -m xeroemoji mcp                 # run the MCP server on stdio"""
import argparse, json, os, sys, urllib.request
from . import get, search, variants, categories, emojify, LICENSE, __version__


def main(argv=None):
    ap = argparse.ArgumentParser(prog='xeroemoji', description=f'Xero Emoji {__version__} lookup. {LICENSE}')
    sp = ap.add_subparsers(dest='cmd', required=True)
    p = sp.add_parser('get'); p.add_argument('emoji')
    p = sp.add_parser('search'); p.add_argument('query'); p.add_argument('--group'); p.add_argument('--limit', type=int, default=20); p.add_argument('--tones', action='store_true')
    p = sp.add_parser('variants'); p.add_argument('emoji')
    sp.add_parser('categories')
    p = sp.add_parser('emojify'); p.add_argument('text'); p.add_argument('--format', default='svg', choices=['svg', 'png'])
    p = sp.add_parser('download'); p.add_argument('emoji', nargs='+'); p.add_argument('--format', default='svg', choices=['svg', 'png']); p.add_argument('--out', default='.')
    sp.add_parser('mcp')
    a = ap.parse_args(argv)
    dump = lambda o: print(json.dumps(o, ensure_ascii=False, indent=1))
    if a.cmd == 'get':
        e = get(a.emoji)
        if not e: print(f'not found: {a.emoji}', file=sys.stderr); return 1
        dump(e)
    elif a.cmd == 'search': dump(search(a.query, a.group, a.limit, a.tones))
    elif a.cmd == 'variants': dump(variants(a.emoji))
    elif a.cmd == 'categories': dump(categories())
    elif a.cmd == 'emojify': print(emojify(a.text, a.format))
    elif a.cmd == 'download':
        os.makedirs(a.out, exist_ok=True); rc = 0
        for q in a.emoji:
            e = get(q)
            if not e: print(f'not found: {q}', file=sys.stderr); rc = 1; continue
            dst = os.path.join(a.out, f"{e['file']}.{a.format}")
            with urllib.request.urlopen(e[f'{a.format}_url'], timeout=60) as r, open(dst, 'wb') as f: f.write(r.read())
            print(dst)
        return rc
    elif a.cmd == 'mcp':
        from .mcp_server import serve; serve()
    return 0


if __name__ == '__main__':
    sys.exit(main())
