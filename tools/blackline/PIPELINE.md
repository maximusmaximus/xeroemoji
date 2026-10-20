# Black line pipeline

This turns any set of colour SVGs (emoji, or font glyphs exported as SVG on a 512x512 viewBox) into black line art.
Each output is one white path (the fill) plus one black path (the lines), with a transparent outside. It also makes
a heavier-line 72px variant.

## Rules (`common.py`, shared by both engines and the tests)
- **Layers** are taken in paint order. Translucent or hidden layers are dropped (`gt.load`), and low-contrast
  shading pairs are merged (`gt.merges`).
  - Opacity is accumulated through *all* ancestors, including nested `<svg>` viewports (drop-shadow copies of
    hands inside a nested svg were previously read as opaque and drawn as fat black).
  - A semi-opaque (0.6–0.9) stroke-only line that is *darker than the paint drawn before it* is drawing, not a
    highlight (racket/cart mesh, parachute cords). Lines lighter than what is under them stay highlights.
  - A path with an implicit fill made only of 2-point segments has no area: it is a stroked line set.
- **Fill** layers become white regions. Their outline is `outer` on the silhouette and `inner` on visible
  internal edges.
- **Stroke-only** layers:
  - *Border pair*: a later stroke on the same geometry with a narrower width is the core of a wire whose dark
    outline is the earlier, wider stroke. The two are merged into one wire (footprint = wide, core = narrow,
    painted at the core's position).
  - *Thin wire*: the core is narrower than `thin_factor * outer` (30px @512). It stays a **single black line**
    of weight `min(thin_weight, footprint)` (10px default), with the source caps and joins. It is never inflated
    into a ribbon.
  - *Body width*: a wire with 3+ chained members (outline + body + highlight) is judged on its middle width, not
    the highlight core (snake coil, pretzel).
  - *Small dense wires*: weight ≤ skeleton extent / 12 (never below 4px), so a snowflake or spark stays readable
    instead of filling solid.
  - *Banded body*: ≥3 thin wires, each ≥80px long, whose centrelines never meet and run >80% of their length
    beside another band (rainbow arcs) are one banded body and are drawn as wide strokes.
  - *Wide stroke*: treated as an opaque ribbon, the same way as a fill.
- **Over/under**: a back wire gets a `gap` break only where a later wire's outline is painted over it in the
  source *and* the front wire really crosses it (it continues on both sides). T-junctions join without a break,
  and wires drawn in one paint pass (for example a spider web) join without a break. A wire clipped by a path
  ends on the wire drawn along that path (racket strings on the rim): a T-junction, never a crossing.
- **Pinholes / notches**: enclosed holes and thin notches (< 60px² @512) inside one layer, from degenerate folds in
  the source outline (1f504 arrow tips), take the enclosing layer in both engines.
- **Occlusion**: later layers hide earlier ones. A later thin wire also hides the wide edges under its footprint.

## Engines (independent geometry)
| | engine_vector | engine_raster |
|---|---|---|
| input | svgelements parse; own transform / clip-path / mask / dash handling | the source rendered by cairosvg into flat ID maps at 2048px (1024px for the 72px variant) |
| ops | Clipper (pyclipper) integer polygon booleans and offsets | pixel distance transforms on the ownership maps |
| output | polygons (0.05px flattening) | potrace-traced Béziers |

skia-pathops was tried first for the vector engine. It gave wrong unions (filled holes, half-plane fills) on
curved input, so it was replaced by Clipper.

## Commands
```
pipeline.py build  --engine vector|raster --src SVG_DIR --out OUT [--map emoji-map.json] [--config cfg.json] [--codes a,b|@file]
pipeline.py diff   --a OUT_V --b OUT_R --out DIFF          # black/opaque agreement with a 2px tolerance; flags < 0.93
pipeline.py check  --build OUT --src SVG_DIR --out QC      # rule checks (below)
pipeline.py select --a OUT_V --b OUT_R --diff DIFF --checks-a QC_V --checks-b QC_R --xray-a XR_V --xray-b XR_R --out FINAL
pipeline.py sheet  --builds v4=DIR,v5=DIR,v6=DIR --codes @list --out sheet.png --names emoji-map.json
pipeline.py golden test|approve --build OUT
xray_test.py --build OUT --log OUT/build-log.json --out XR   # independent x-ray test: 0 failures required
qc.py --build FINAL --emoji-test emoji-test.txt               # checks + x-ray + audit + golden
```
`--map` (emoji-map.json, where field 6 is the tone base) builds only the base emoji and copies the files to
their tone variants. Without a map, every `*.svg` file in `--src` is built.

Config keys (JSON) and their defaults: `inner 6`, `outer 15`, `inner72 7.5`, `outer72 18.8`, `fit 0.99`,
`fit72 0.97`, `thin_factor 2`, `thin_weight 10`, `gap 6`, `small_div 12`, `small_min 4`, `band_overlap 0.8`,
`band_min 3`, `band_len 80`. If an emoji's outer line would touch the frame, its
fit is reduced for that emoji only.

## Checks (`pipeline.py check`)
- **structure**: exactly 1 white path then 1 black path, with no strokes, opacity, gradients or filters, plus
  the same for the 72px SVG. Also checks that PNG pixels are untinted, that outputs are non-empty and do not
  touch the frame (512 and 72), and that tone copies are identical.
- **line weight**: a histogram of black thickness (2 × the distance transform on the skeleton).
  - `thin_inflated`: more than 25% of a thin wire's centreline is white, meaning it was turned into a ribbon.
  - `thin_blob`: the 90th percentile of black thickness on thin wires is above `thin_weight + 4`.
  - Both are measured on the centreline of the wire *cores*. Tuned in v6-final: adjacent wires' dark border members
    merge into one band whose skeleton runs between the cores (lab-coat pens), which falsely read as white.
  - `thin_blob` ignores points where two wire cores converge within `thin_weight + 4` (A-frame legs meeting at a
    shared vertex legitimately merge) and needs at least 60px of centreline (sharp outline tips alone are not a blob).
- **white between lines** (`solid_black_over_gaps`): black blobs of 30px or more lying farther from any source
  paint than half the outer line (+2px).
- **shape fidelity**: output inside the source dilated by half the outer line (≥ 98.5%), and the source covered
  by the output (≥ 97%). Silhouette IoU is also reported.
- **topology** of thin art: the number of loops and the number of skeleton ends must match a reference made
  from the source core centrelines at wire weight. Crossing breaks are healed by a closing of gap size first.
  Tuned in v6-final: both the reference and the output get the fills' outer-line band (fill dilated by outer/2+1)
  *before* the closing. The fill outline legitimately reaches beyond the source edge, and a wire ending on a fill
  joins it in both, so a pole meeting a sign is not a new loop.
- **x-ray** (`xray_test.py`): ownership map of the original colour art, and black pixels must lie on visible
  edges. The ID map is validated against the colour render.

## Differential process
1. Build with both engines.
2. Run `diff`, `check` and `xray_test.py` on each.
3. Run `select`: take vector if it passes everything, otherwise raster if that passes. If neither passes,
   use vector and list the emoji for review.
4. Review every flagged disagreement on the diff heatmaps (red = vector only, blue = raster only).

## Golden set
`golden/codes.txt` lists 24 samples, 55 line-art emoji and 30 tricky cases. Once a build is approved, run
`pipeline.py golden approve --build FINAL`. CI then runs `pytest tests/`, which covers the sheet-label test and
rebuilds the golden set with both engines to compare against the references (tolerant agreement ≥ 0.97).

## Reviewed waivers
`golden/reviewed.json` lists `{code: {check: reason}}` for failures that were visually reviewed and judged correct.
A waived failure is still reported under `reviewed` in checks.json. v6-final has one: 1f9ec (DNA) topology_loops,
because the strands pass within one line weight and the output keeps the small lens between them open.
