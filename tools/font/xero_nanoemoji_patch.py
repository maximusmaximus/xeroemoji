"""Loaded into the build venv via a .pth file (see build_font.sh).
nanoemoji bakes a radial gradient's uniform scale into its circles; a few Xero Emoji gradients (radial and linear) then exceed
COLRv1's int16 range. On overflow we keep the circles k times smaller and wrap them in an exact scale(k)
PaintTransform instead, which renders identically."""
import dataclasses, math
try:
    from nanoemoji import paint as P
    from picosvg.svg_transform import Affine2D
    from picosvg.geometric_types import Point
    _orig = P.PaintRadialGradient.apply_transform
    def apply_transform(self, transform, check_overflows=True):
        try:
            return _orig(self, transform, check_overflows)
        except OverflowError:
            uni, rest = P._decompose_uniform_transform(transform)
            c0, c1 = uni.map_point(self.c0), uni.map_point(self.c1)
            sx, _ = uni.getscale(); r0, r1 = self.r0 * sx, self.r1 * sx
            m = max(abs(c0.x), abs(c0.y), abs(c1.x), abs(c1.y), r0 / 2, r1 / 2)
            k = math.ceil(m / 30000) or 1
            g = dataclasses.replace(self, c0=Point(c0.x / k, c0.y / k), c1=Point(c1.x / k, c1.y / k), r0=r0 / k, r1=r1 / k)
            g.check_overflows()
            return P.transformed(Affine2D.compose_ltr((Affine2D.identity().scale(k), rest)), g)
    P.PaintRadialGradient.apply_transform = apply_transform
    _origL = P.PaintLinearGradient.apply_transform
    def apply_transform_linear(self, transform, check_overflows=True):
        try:
            return _origL(self, transform, check_overflows)
        except OverflowError:
            pts = [transform.map_point(q) for q in (self.p0, self.p1, self.p2)]
            k = math.ceil(max(max(abs(q.x), abs(q.y)) for q in pts) / 30000) or 1
            g = dataclasses.replace(self, **{f'p{i}': Point(q.x / k, q.y / k) for i, q in enumerate(pts)})
            g.check_overflows()
            return P.transformed(Affine2D.identity().scale(k), g)
    P.PaintLinearGradient.apply_transform = apply_transform_linear
except Exception:  # never break unrelated python startup
    pass
