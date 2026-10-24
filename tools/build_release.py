#!/usr/bin/env python3
"""Build the GitHub Release assets into dist/ (reproducible: sorted entries, fixed timestamps, stable names).
  python3 tools/build_release.py [--version 1.0.0] [--no-packages | --packages-only]
Assets (stable names, so https://github.com/maximusmaximus/xeroemoji/releases/latest/download/<asset> always works):
  xeroemoji-svg.zip      all 3,963 SVGs         xeroemoji-png-512.zip  512x512 PNGs (the approved renders)
  xeroemoji-png-128.zip  128x128 PNGs           xeroemoji-png-72.zip   72x72 PNGs (both downscaled from the 512s, Lanczos)
  emoji-map.json         emoji -> file map      xero-emoji.js          browser replacer
  xeroemoji-<v>.tgz      npm package (npm pack; not published)   xeroemoji-<v>-py3-none-any.whl  Python wheel (+ sdist when `build` is installed)
  SHA256SUMS.txt
Every zip holds xeroemoji/<files>, LICENSE, LICENSING.md, COMMERCIAL-LICENSE.md, emoji-map.json and README.txt. Art is only read, never changed."""
import hashlib, io, json, os, re, shutil, subprocess, sys, zipfile
try:
    from PIL import Image  # only needed for the PNG zips
except ImportError:
    Image = None
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D = R + '/dist'
args = sys.argv[1:]
VER = args[args.index('--version') + 1].lstrip('v') if '--version' in args else re.search(r"__version__ = '([^']+)'", open(R + '/packages/python/xeroemoji/__init__.py').read()).group(1)
TS = (2026, 10, 18, 0, 0, 0)          # fixed zip timestamp -> byte-identical zips for the same inputs
MAP = R + '/demos/emoji-map.json'

def zwrite(z, name, data, store=False):
    zi = zipfile.ZipInfo(name, TS); zi.external_attr = 0o644 << 16; zi.create_system = 3
    z.writestr(zi, data, compress_type=zipfile.ZIP_STORED if store else zipfile.ZIP_DEFLATED, compresslevel=9)

def readme(kind):
    return (f'Xero Emoji {VER} - {kind}\nAll 3,963 emoji of Unicode Emoji 18.0, by Max Infeld (started in 2016). Created by maxi.grok.me.\n'
            'Files are named by codepoint: lowercase hex joined by "-", FE0F dropped except 4 names (see emoji-map.json).\n'
            'License: artwork CC BY 4.0 (LICENSE, LICENSING.md). Credit: "Xero Emoji by Max Infeld, CC BY 4.0". The color font, book and merch are not CC BY (COMMERCIAL-LICENSE.md).\n'
            'https://github.com/maximusmaximus/xeroemoji\n').encode()

def build_zip(name, kind, files):   # files: list of (arcname, bytes, store)
    p = f'{D}/{name}'
    with zipfile.ZipFile(p, 'w') as z:
        for n in ('LICENSE', 'LICENSING.md', 'COMMERCIAL-LICENSE.md'): zwrite(z, f'xeroemoji/{n}', open(f'{R}/{n}', 'rb').read())
        zwrite(z, 'xeroemoji/README.txt', readme(kind)); zwrite(z, 'xeroemoji/emoji-map.json', open(MAP, 'rb').read())
        for a, b, st in sorted(files): zwrite(z, 'xeroemoji/' + a, b, st)
    print(f'{name:34s} {len(files):5d} files {os.path.getsize(p)/2**20:7.1f} MiB')

def png_small(src, n):
    b = io.BytesIO(); Image.open(src).convert('RGBA').resize((n, n), Image.LANCZOS).save(b, 'PNG', optimize=True); return b.getvalue()

def main():
    shutil.rmtree(D, ignore_errors=True); os.makedirs(D)
    m = json.load(open(MAP, encoding='utf-8')); names = sorted(e[0] for e in m.values()); assert len(names) == 3963
    if '--packages-only' not in args:
        build_art(names)
    build_rest()

def build_art(names):
    build_zip('xeroemoji-svg.zip', 'SVG', [(f'svg/{f}.svg', open(f'{R}/svg/{f}.svg', 'rb').read(), False) for f in names])
    build_zip('xeroemoji-png-512.zip', 'PNG 512x512', [(f'png/{f}.png', open(f'{R}/png/{f}.png', 'rb').read(), True) for f in names])
    for n in (128, 72):
        build_zip(f'xeroemoji-png-{n}.zip', f'PNG {n}x{n}', [(f'png-{n}/{f}.png', png_small(f'{R}/png/{f}.png', n), True) for f in names])

def build_rest():
    shutil.copy(MAP, D + '/emoji-map.json'); shutil.copy(R + '/demos/xero-emoji.js', D + '/xero-emoji.js')
    if '--no-packages' not in args:
        npm = R + '/packages/npm'
        subprocess.run(['npm', 'pack', '--pack-destination', D], cwd=npm, check=True, capture_output=True)
        py = R + '/packages/python'; shutil.copy(MAP, py + '/xeroemoji/emoji-map.json')
        env = dict(os.environ, SOURCE_DATE_EPOCH='1792281600')
        for n in ('LICENSE', 'LICENSING.md', 'COMMERCIAL-LICENSE.md'):   # packages/python keeps copies (needed for git installs); they must match
            assert open(f'{R}/{n}', 'rb').read() == open(f'{py}/{n}', 'rb').read(), f'packages/python/{n} differs from the repo root'
        try:
            import build  # noqa: F401  (pip install build) -> wheel + sdist
            subprocess.run([sys.executable, '-m', 'build', '--sdist', '--wheel', '--outdir', D, py], check=True, env=env, capture_output=True)
        except ImportError:
            subprocess.run([sys.executable, '-m', 'pip', 'wheel', '--no-deps', '-q', '-w', D, py], check=True, env=env)
        for p in ('build', 'xeroemoji.egg-info'): shutil.rmtree(f'{py}/{p}', ignore_errors=True)
    sums = ''.join(f'{hashlib.sha256(open(f"{D}/{f}", "rb").read()).hexdigest()}  {f}\n' for f in sorted(os.listdir(D)))
    open(D + '/SHA256SUMS.txt', 'w').write(sums); print(sums)

if __name__ == '__main__':
    main()
