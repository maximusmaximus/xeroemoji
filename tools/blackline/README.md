# tools/blackline

Converts Xero colour SVGs (or any SVG glyph set) to black line art with two independent engines, differential
testing and QC. See PIPELINE.md.

```
pip install -r requirements.txt   # plus potrace (apt-get install potrace, or tools/get_potrace.sh)
python pipeline.py build --engine vector --src ../../svg --out out/V --map ../../packages/npm/emoji-map.json
python pipeline.py build --engine raster --src ../../svg --out out/R --map ../../packages/npm/emoji-map.json
python xray_test.py --build out/V --log out/V/build-log.json --out out/xrV
python pipeline.py check --build out/V --src ../../svg --out out/qcV
python -m pytest -q tests/
```

## Tests
`python3 -m pytest -q` from `tools/blackline`. The colour sources default to `<repo>/svg`; set `BL_SRC` to use
another folder. The raster engine needs potrace (`tools/get_potrace.sh`, or point `POTRACE` at a binary).
