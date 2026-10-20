#!/usr/bin/env bash
# Build XeroEmoji COLRv1 TTF + WOFF2 from COPIES of the locked svg/ files (svg/ is never modified).
# Needs: python3 -m venv .venv && .venv/bin/pip install nanoemoji ninja brotli
# Usage: tools/font/build_font.sh [workdir]   -> fonts/XeroEmoji-COLRv1.ttf, fonts/XeroEmoji-COLRv1.woff2
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"; WORK="${1:-/tmp/xeroemoji-font}"; mkdir -p "$WORK"
export PATH="$REPO/tools/font/bin:$PATH"          # patched picosvg wrapper first
# radial-gradient overflow fix, loaded into the venv python via a .pth file
SP="$(python3 -c 'import site;print(site.getsitepackages()[0])')"
cp "$REPO/tools/font/xero_nanoemoji_patch.py" "$SP/" && echo "import xero_nanoemoji_patch" > "$SP/xero_patch.pth"
python3 "$REPO/tools/font/prep_svgs.py" "$REPO/svg" "$WORK/svg"
cd "$WORK"
nanoemoji --family XeroEmoji --color_format glyf_colr_1 --upem 1024 --build_dir build --output_file XeroEmoji.ttf svg/*.svg
python3 "$REPO/tools/font/finish_font.py" build/XeroEmoji.ttf "$REPO/fonts" "$REPO/tools/ci/emoji-test-18.0.txt"
python3 "$REPO/tools/font/verify_font.py" "$REPO/fonts/XeroEmoji-COLRv1.ttf" "$REPO/svg" "$REPO/tools/ci/emoji-test-18.0.txt"
