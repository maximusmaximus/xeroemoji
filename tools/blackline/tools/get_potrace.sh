#!/bin/sh
# fetch a static potrace 1.16 binary next to this script (used by engine_raster when potrace is not on PATH)
set -e; cd "$(dirname "$0")"
curl -sL https://potrace.sourceforge.net/download/1.16/potrace-1.16.linux-x86_64.tar.gz | tar xz
cp potrace-1.16.linux-x86_64/potrace . && rm -rf potrace-1.16.linux-x86_64 && ./potrace --version | head -1
