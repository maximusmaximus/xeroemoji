"""Xero Emoji MCP server (stdio, JSON-RPC 2.0, newline-delimited; no dependencies).
Run:  python3 -m xeroemoji mcp     or     python3 mcp/server.py   (from a clone of the repo)
Tools: search_emoji, get_emoji, list_categories, get_skin_tone_variants, emojify_text."""
import json, os, sys, urllib.request
from . import get, search, variants, categories, emojify, LICENSE, CDN, __version__, _load

PROTOCOLS = ['2025-06-18', '2025-03-26', '2024-11-05']
_S = {'type': 'string'}
TOOLS = [
    {'name': 'search_emoji', 'title': 'Search Xero Emoji',
     'description': 'Find Xero Emoji by name or keyword (e.g. "cat", "thumbs up", "flag japan"). Returns emoji, name, group, file name and SVG/PNG URLs, best match first.',
     'inputSchema': {'type': 'object', 'properties': {'query': _S, 'group': {**_S, 'description': 'optional group filter, e.g. "Animals & Nature" (see list_categories)'},
                     'limit': {'type': 'integer', 'minimum': 1, 'maximum': 100, 'default': 10},
                     'include_tones': {'type': 'boolean', 'default': False, 'description': 'also return skin-tone variants'}}, 'required': ['query']}},
    {'name': 'get_emoji', 'title': 'Get one Xero Emoji',
     'description': 'Look up one emoji by the emoji character ("👍🏿"), codepoints ("1f44d-1f3ff" or "U+1F44D U+1F3FF"), file name, or exact CLDR name. Returns metadata, SVG/PNG CDN URLs and repo paths; optionally the SVG source.',
     'inputSchema': {'type': 'object', 'properties': {'emoji': _S, 'include_svg': {'type': 'boolean', 'default': False}}, 'required': ['emoji']}},
    {'name': 'list_categories', 'title': 'List emoji categories',
     'description': 'The 9 Unicode emoji groups with their subgroups and counts (3,963 emoji in total).',
     'inputSchema': {'type': 'object', 'properties': {}}},
    {'name': 'get_skin_tone_variants', 'title': 'Skin-tone variants',
     'description': 'The default (yellow) and all skin-tone variants of an emoji, including multi-person tone combinations. Empty if the emoji has no tones.',
     'inputSchema': {'type': 'object', 'properties': {'emoji': _S}, 'required': ['emoji']}},
    {'name': 'emojify_text', 'title': 'Render text with Xero Emoji',
     'description': 'Replace the Unicode emoji in a text with Xero Emoji images, as HTML <img> tags or Markdown images.',
     'inputSchema': {'type': 'object', 'properties': {'text': _S, 'format': {'type': 'string', 'enum': ['html', 'markdown'], 'default': 'html'},
                     'image': {'type': 'string', 'enum': ['svg', 'png'], 'default': 'svg'}}, 'required': ['text']}},
]


def _svg_source(e):
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', e['svg_path'])
    if os.path.exists(p):
        return open(p, encoding='utf-8').read()
    with urllib.request.urlopen(e['svg_url'], timeout=30) as r:
        return r.read().decode('utf-8')


def _markdown(text, image):
    from . import key
    m = _load(); out = []; cps = list(text); i = 0
    while i < len(cps):
        for n in range(min(10, len(cps) - i), 0, -1):
            g = ''.join(cps[i:i + n]); e = m.get(key(g))
            if e and not (n == 1 and '\ufe0f' in e[1]):
                out.append(f'![{g}]({CDN}{image}/{e[0]}.{image} "{e[2]}")'); i += n; break
        else:
            out.append(cps[i]); i += 1
    return ''.join(out)


def call_tool(name, a):
    if name == 'search_emoji':
        r = search(a.get('query', ''), a.get('group'), a.get('limit', 10), a.get('include_tones', False))
        return {'count': len(r), 'results': r}
    if name == 'get_emoji':
        e = get(a.get('emoji', ''))
        if not e:
            raise ValueError(f"no Xero Emoji for {a.get('emoji')!r}; try search_emoji")
        if a.get('include_svg'):
            e['svg'] = _svg_source(e)
        e['license'] = LICENSE
        return e
    if name == 'list_categories':
        return {'total': sum(c['count'] for c in categories()), 'groups': categories()}
    if name == 'get_skin_tone_variants':
        v = variants(a.get('emoji', ''))
        return {'count': len(v), 'variants': v}
    if name == 'emojify_text':
        t, img = a.get('text', ''), a.get('image', 'svg')
        return {'format': a.get('format', 'html'), 'output': _markdown(t, img) if a.get('format') == 'markdown' else emojify(t, img)}
    raise KeyError(name)


def handle(msg):
    mid, method, params = msg.get('id'), msg.get('method'), msg.get('params') or {}
    if mid is None:                       # notification (e.g. notifications/initialized): no reply
        return None
    try:
        if method == 'initialize':
            want = params.get('protocolVersion')
            res = {'protocolVersion': want if want in PROTOCOLS else PROTOCOLS[0], 'capabilities': {'tools': {'listChanged': False}},
                   'serverInfo': {'name': 'xeroemoji', 'title': 'Xero Emoji', 'version': __version__},
                   'instructions': 'Look up Xero Emoji (3,963 emoji, Unicode 18.0) and get SVG/PNG URLs. ' + LICENSE}
        elif method == 'ping':
            res = {}
        elif method == 'tools/list':
            res = {'tools': TOOLS}
        elif method == 'tools/call':
            name = params.get('name')
            if name not in {t['name'] for t in TOOLS}:
                return {'jsonrpc': '2.0', 'id': mid, 'error': {'code': -32602, 'message': f'unknown tool {name}'}}
            try:
                out = call_tool(name, params.get('arguments') or {})
                res = {'content': [{'type': 'text', 'text': json.dumps(out, ensure_ascii=False)}], 'structuredContent': out, 'isError': False}
            except Exception as ex:   # tool errors are results, not protocol errors
                res = {'content': [{'type': 'text', 'text': str(ex)}], 'isError': True}
        else:
            return {'jsonrpc': '2.0', 'id': mid, 'error': {'code': -32601, 'message': f'method not found: {method}'}}
        return {'jsonrpc': '2.0', 'id': mid, 'result': res}
    except Exception as ex:
        return {'jsonrpc': '2.0', 'id': mid, 'error': {'code': -32603, 'message': str(ex)}}


def serve(stdin=sys.stdin, stdout=sys.stdout):
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            stdout.write(json.dumps({'jsonrpc': '2.0', 'id': None, 'error': {'code': -32700, 'message': 'parse error'}}) + '\n'); stdout.flush(); continue
        batch = msg if isinstance(msg, list) else [msg]
        replies = [r for r in (handle(m) for m in batch) if r is not None]
        if replies:
            stdout.write(json.dumps(replies if isinstance(msg, list) else replies[0], ensure_ascii=False) + '\n'); stdout.flush()


if __name__ == '__main__':
    serve()
