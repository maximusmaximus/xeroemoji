"""xeroemoji - look up Xero Emoji (3,963 emoji, Unicode Emoji 18.0) by emoji, codepoint or name, and get SVG/PNG URLs.

    import xeroemoji as xe
    xe.get('👍🏿')            # {'file': '1f44d-1f3ff', 'svg_url': 'https://cdn.jsdelivr.net/gh/...', ...}
    xe.search('cat', limit=5)
    xe.variants('👋')        # the default + 5 skin tones
    xe.emojify('hi 👋🏽')    # HTML with <img> tags

Data: emoji-map.json, from (in order) $XEROEMOJI_MAP, the copy bundled in this package, the repo's demos/emoji-map.json,
or the jsDelivr CDN. Artwork: CC BY-NC 4.0, commercial use needs a license (see COMMERCIAL-LICENSE.md)."""
import html, json, os, re, urllib.request

__version__ = '1.0.0'
REPO = 'maximusmaximus/xeroemoji'
CDN = os.environ.get('XEROEMOJI_CDN_BASE', f'https://cdn.jsdelivr.net/gh/{REPO}@v{__version__}/')
PAGES = f'https://maximusmaximus.github.io/xeroemoji/'
LICENSE = ('Artwork CC BY-NC 4.0 (credit "Xero Emoji by Max Infeld", link https://github.com/maximusmaximus/xeroemoji); '
           'commercial use needs a separate license: https://github.com/maximusmaximus/xeroemoji/blob/main/COMMERCIAL-LICENSE.md')
TONES = {'1f3fb': 'light', '1f3fc': 'medium-light', '1f3fd': 'medium', '1f3fe': 'medium-dark', '1f3ff': 'dark'}
_TONE = re.compile(r'-1f3f[b-f]')
_HEX = re.compile(r'^(?:u\+)?[0-9a-f]{2,6}(?:[\s_+-]+(?:u\+)?[0-9a-f]{2,6})*$', re.I)
_MAP = None


def _load():
    global _MAP
    if _MAP is not None:
        return _MAP
    here = os.path.dirname(os.path.abspath(__file__))
    for p in (os.environ.get('XEROEMOJI_MAP'), os.path.join(here, 'emoji-map.json'),
              os.path.join(here, '..', '..', '..', 'demos', 'emoji-map.json')):
        if p and os.path.exists(p):
            _MAP = json.load(open(p, encoding='utf-8'))
            return _MAP
    with urllib.request.urlopen(CDN + 'demos/emoji-map.json', timeout=30) as r:
        _MAP = json.load(r)
    return _MAP


def key(emoji):
    """'👍🏿' -> '1f44d-1f3ff'; FE0F dropped, at least 4 hex digits (the emoji-map.json key)."""
    return '-'.join(f'{ord(c):04x}' for c in emoji if c != '\ufe0f')


def _key_from_codepoints(s):
    parts = [p for p in re.split(r'[\s_+-]+', s.lower().replace('u+', ' ')) if p]
    return '-'.join(p.rjust(4, '0') for p in parts if p != 'fe0f')


def _entry(k, e):
    tone = [TONES[t] for t in k.split('-') if t in TONES]
    return {'emoji': e[1], 'name': e[2], 'group': e[3], 'subgroup': e[4], 'file': e[0], 'key': k,
            'codepoints': ' '.join(f'U+{ord(c):04X}' for c in e[1]),
            'skin_tone': ', '.join(tone) if tone else None,
            'svg_url': f'{CDN}svg/{e[0]}.svg', 'png_url': f'{CDN}png/{e[0]}.png',
            'svg_path': f'svg/{e[0]}.svg', 'png_path': f'png/{e[0]}.png', 'order': e[5]}


def get(q):
    """Look up one emoji: the emoji itself, codepoints ('1f44d-1f3ff', 'U+1F44D U+1F3FF'), a file name, or an exact name."""
    m = _load(); q = (q or '').strip()
    if not q:
        return None
    for k in (key(q), _key_from_codepoints(q) if _HEX.match(q) else None, q.lower().removesuffix('.svg').removesuffix('.png').replace('-fe0f', '')):
        if k and k in m:
            return _entry(k, m[k])
    ql = q.lower()
    for k, e in m.items():
        if e[2].lower() == ql:
            return _entry(k, e)
    return None


def search(query, group=None, limit=20, include_tones=False):
    """Rank emoji by name/subgroup match: exact name, whole words, name prefix, substring, subgroup."""
    m = _load(); q = (query or '').strip().lower(); words = q.split(); out = []
    for k, e in m.items():
        if group and e[3].lower() != group.lower():
            continue
        if not include_tones and _TONE.search(k) and 'tone' not in q:
            continue
        n = e[2].lower(); ws = re.split(r'[^a-z0-9]+', n)
        if not q: s = 9
        elif n == q: s = 0
        elif all(w in ws for w in words): s = 1
        elif n.startswith(q): s = 2
        elif all(w in n for w in words): s = 3
        elif q in e[4]: s = 4
        else: continue
        out.append((s, e[5], k, e))
    out.sort(key=lambda x: (x[0], x[1]))
    return [_entry(k, e) for _, _, k, e in out[:max(1, int(limit))]]


def categories():
    """Groups and subgroups with counts, in emoji-test order."""
    res = {}
    for k, e in sorted(_load().items(), key=lambda kv: kv[1][5]):
        g = res.setdefault(e[3], {'group': e[3], 'count': 0, 'subgroups': {}})
        g['count'] += 1; g['subgroups'][e[4]] = g['subgroups'].get(e[4], 0) + 1
    return list(res.values())


def variants(q):
    """The default and every skin-tone variant of an emoji (including multi-person tone combinations)."""
    e = get(q)
    if not e:
        return []
    base = _TONE.sub('', e['key']); m = _load()
    return [_entry(k, v) for k, v in sorted(m.items(), key=lambda kv: kv[1][5]) if _TONE.sub('', k) == base]


def emojify(text, fmt='svg', size='1.35em'):
    """Replace emoji in plain text with <img> tags (HTML-escaped). Longest match first, up to 10 code points."""
    m = _load(); cps = list(text); out = []; i = 0
    while i < len(cps):
        for n in range(min(10, len(cps) - i), 0, -1):
            g = ''.join(cps[i:i + n]); e = m.get(key(g))
            if e and not (n == 1 and '\ufe0f' in e[1]):
                out.append(f'<img class="xero-emoji" src="{CDN}{fmt}/{e[0]}.{fmt}" alt="{html.escape(g)}" title="{html.escape(e[2])}" '
                           f'style="width:{size};height:{size};vertical-align:-0.3em">')
                i += n; break
        else:
            out.append(html.escape(cps[i])); i += 1
    return ''.join(out)
