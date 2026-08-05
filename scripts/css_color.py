"""CSS color values to 8-bit sRGB, for the contrast gate.

Why this exists as its own module, and why it is more than a regex.

`theme-doctor.py`'s contrast gate resolves a theme's declared `contrastPairs`
to two colors and computes a WCAG ratio. It understood hex and `rgb()`/`rgba()`
and NOTHING ELSE, and an unresolvable pair is a gate FAILURE rather than an
advisory (deliberately — an ungraded check is a failed check). So a theme
writing a perfectly ordinary modern palette:

    :root { --fg: oklch(0.92 0.02 240); --bg: oklch(0.18 0.04 250); }

failed with "contrast: could not resolve --fg / --bg to colors", four
archetypes, exit 1, and `rotate-theme.yml` aborted the rotation at 09:00 UTC
on the 1st. The theme was correct. The gate was wrong.

That is the SAME defect class this branch already fixed once, in the dress
differential's `_css_alpha`, and the fix was then generalized in prose past
where it actually reached: the differential compares opaque strings and truly
does not care about syntax, but this module's caller does arithmetic on
channels and very much does.

So: parse the color functions CSS actually ships, rather than narrowing the
gate or downgrading its verdict.

── What is supported ────────────────────────────────────────────────────
hex (3/4/6/8 digit), `rgb()`/`rgba()`, `hsl()`/`hsla()`, `hwb()`, `lab()`,
`lch()`, `oklab()`, `oklch()`, `color()` in the CSS Color 4 predefined spaces,
the 148 CSS named colors, and `transparent`. Both the legacy comma form and
the modern space form, `none` components, percentage or number channels, and
the `/ <alpha>` slash form.

`color-mix()` over two colors in any of `srgb`, `srgb-linear`, `lab`, `lch`,
`oklab`, `oklch`, `hsl`, `hwb`, `xyz`, `xyz-d50` and `xyz-d65`, with all four
hue-interpolation methods (`shorter` — the default — `longer`, `increasing`,
`decreasing`). That list is exhaustive and is meant to be read as such: an
earlier version of this sentence said "a rectangular or polar space" while
`_to_space` handled five of the eleven and returned `None` for the rest, and
`None` reaches the contrast gate as "could not resolve", which aborts a
rotation. If a space is added to CSS, it belongs in `_to_space` AND here.

**NOT supported, stated because nothing else states it:** `light-dark()`,
relative color syntax (`rgb(from … )`), and `color-mix()` with more than two
colors. Each resolves to `None`, which the contrast gate reports as an
unresolved pair rather than guessing — the right failure, but a theme author
should learn it here rather than on the 1st.

── What is NOT modelled, and why that is unchanged ──────────────────────
ALPHA. Every value resolves to opaque sRGB. That was already true of the
`rgba()` path and the reasoning is in `theme-doctor.py`: every alpha use in
this repo's tokens is a translucent panel over a same-or-near field, where
compositing would not move a channel far enough to change an AA verdict.
Modelling true compositing needs a backdrop, which a static gate does not
have. Stated rather than hidden.

Out-of-gamut results are clipped to 0..255 per channel after conversion. A
wide-gamut `oklch()` that falls outside sRGB therefore grades as its clipped
sRGB neighbour, which is what a sRGB display shows anyway.

── How the numbers were checked ─────────────────────────────────────────
Not by reading the spec and hoping. Every conversion here was verified against
Chromium by painting the same string into a canvas and reading the pixel back
(`<scratchpad>/colorcheck.py`), across the whole supported syntax set. The
values pinned in `tests/test_css_color.py` are that browser's output, not this
module's.
"""
from __future__ import annotations

import math
import re

__all__ = ["to_rgb"]

_HEX_RE = re.compile(r"^#([0-9a-fA-F]{3,8})$")
_FUNC_RE = re.compile(r"^([a-zA-Z-]+)\((.*)\)$", re.S)

# ε and κ from CIE, and the D50 white point CSS Color 4 uses for lab()/lch().
_LAB_E = 216 / 24389
_LAB_K = 24389 / 27
_D50 = (0.3457 / 0.3585, 1.0, (1.0 - 0.3457 - 0.3585) / 0.3585)


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return lo if x < lo else hi if x > hi else x


def _srgb_encode(c: float) -> float:
    """Linear-light sRGB to gamma-encoded sRGB."""
    sign = -1.0 if c < 0 else 1.0
    c = abs(c)
    return sign * (12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055)


def _srgb_decode(c: float) -> float:
    sign = -1.0 if c < 0 else 1.0
    c = abs(c)
    return sign * (c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)


def _split_args(body: str) -> list[str]:
    """Top-level comma/space split of a color function's argument list.

    Commas and whitespace both separate; a `/` separates the alpha. Nested
    parentheses are respected so `color-mix(in oklab, oklch(...), red)` splits
    into three arguments rather than into pieces of one.
    """
    out: list[str] = []
    depth = 0
    cur = ""
    for ch in body:
        if ch == "(":
            depth += 1
            cur += ch
        elif ch == ")":
            depth -= 1
            cur += ch
        elif depth == 0 and (ch == "," or ch.isspace()):
            if cur:
                out.append(cur)
                cur = ""
        elif depth == 0 and ch == "/":
            if cur:
                out.append(cur)
                cur = ""
            out.append("/")
        else:
            cur += ch
    if cur:
        out.append(cur)
    return out


def _drop_alpha(args: list[str]) -> list[str]:
    """Everything before a top-level `/`. Alpha is not modelled — see the
    module docstring."""
    return args[: args.index("/")] if "/" in args else args


def _num(token: str, scale: float = 1.0, pct_scale: float | None = None) -> float | None:
    """A channel value. `none` is zero per CSS Color 4's missing-component
    rule. A percentage is relative to `pct_scale` (default `scale`)."""
    token = token.strip()
    if not token or token.lower() == "none":
        return 0.0
    try:
        if token.endswith("%"):
            base = scale if pct_scale is None else pct_scale
            return float(token[:-1]) / 100.0 * base
        return float(token)
    except ValueError:
        return None


_ANGLE_UNITS = {"deg": 1.0, "grad": 0.9, "rad": 180.0 / math.pi, "turn": 360.0}


def _angle(token: str) -> float | None:
    token = token.strip().lower()
    if not token or token == "none":
        return 0.0
    for unit, factor in _ANGLE_UNITS.items():
        if token.endswith(unit):
            try:
                return float(token[: -len(unit)]) * factor
            except ValueError:
                return None
    try:
        return float(token)
    except ValueError:
        return None


# ─── conversions, all producing LINEAR-LIGHT sRGB ────────────────────────
def _oklab_to_linear_srgb(lightness: float, a: float, b: float) -> tuple[float, float, float]:
    l_ = lightness + 0.3963377774 * a + 0.2158037573 * b
    m_ = lightness - 0.1055613458 * a - 0.0638541728 * b
    s_ = lightness - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    return (
        +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
        -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
        -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s,
    )


def _xyz_d50_to_linear_srgb(x: float, y: float, z: float) -> tuple[float, float, float]:
    return (
        3.1341359569958707 * x - 1.6173863321612538 * y - 0.4906619460083532 * z,
        -0.978795502912089 * x + 1.9161591709054866 * y + 0.03341714628997018 * z,
        0.07195537988411677 * x - 0.2289768264158322 * y + 1.4053777923729528 * z,
    )


def _xyz_d65_to_linear_srgb(x: float, y: float, z: float) -> tuple[float, float, float]:
    return (
        3.2409699419045226 * x - 1.537383177570094 * y - 0.4986107602930034 * z,
        -0.9692436362808796 * x + 1.8759675015077202 * y + 0.04155505740717559 * z,
        0.05563007969699366 * x - 0.20397695888897652 * y + 1.0569715142428786 * z,
    )


def _lab_to_linear_srgb(lightness: float, a: float, b: float) -> tuple[float, float, float]:
    fy = (lightness + 16) / 116
    fx = fy + a / 500
    fz = fy - b / 200
    def finv(f: float) -> float:
        return f ** 3 if f ** 3 > _LAB_E else (116 * f - 16) / _LAB_K
    y = ((lightness + 16) / 116) ** 3 if lightness > _LAB_K * _LAB_E else lightness / _LAB_K
    return _xyz_d50_to_linear_srgb(finv(fx) * _D50[0], y * _D50[1], finv(fz) * _D50[2])



def _linear_srgb_to_xyz_d65(r: float, g: float, b: float) -> tuple[float, float, float]:
    return (
        0.4123907992659595 * r + 0.35758433938387796 * g + 0.1804807884018343 * b,
        0.21263900587151036 * r + 0.7151686787677559 * g + 0.07219231536073371 * b,
        0.019330818715591851 * r + 0.11919477979462599 * g + 0.9505321522496606 * b,
    )


def _xyz_d65_to_d50(x: float, y: float, z: float) -> tuple[float, float, float]:
    """Bradford-adapted, the transform CSS Color 4 specifies for lab()/lch()."""
    return (
        1.0479298208405488 * x + 0.022946793341019088 * y - 0.05019222954313557 * z,
        0.029627815688159344 * x + 0.990434484573249 * y - 0.01707382502938514 * z,
        -0.009243058152591178 * x + 0.015055144896577895 * y + 0.7518742899580008 * z,
    )


def _xyz_d50_to_d65(x: float, y: float, z: float) -> tuple[float, float, float]:
    return (
        0.9554734527042182 * x - 0.023098536874261423 * y + 0.0632593086610217 * z,
        -0.028369706963208136 * x + 1.0099954580058226 * y + 0.021041398966943008 * z,
        0.012314001688319899 * x - 0.020507696433477912 * y + 1.3303659366080753 * z,
    )


def _xyz_d50_to_lab(x: float, y: float, z: float) -> tuple[float, float, float]:
    def f(t: float) -> float:
        return t ** (1 / 3) if t > _LAB_E else (_LAB_K * t + 16) / 116
    fx, fy, fz = (f(v / w) for v, w in zip((x, y, z), _D50))
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def _hue_to_rgb(p: float, q: float, t: float) -> float:
    t = t % 1.0
    if t < 1 / 6:
        return p + (q - p) * 6 * t
    if t < 1 / 2:
        return q
    if t < 2 / 3:
        return p + (q - p) * (2 / 3 - t) * 6
    return p


def _hsl_to_srgb(h: float, s: float, lightness: float) -> tuple[float, float, float]:
    h = (h % 360) / 360.0
    s = _clamp(s)
    lightness = _clamp(lightness)
    if s == 0:
        return (lightness, lightness, lightness)
    q = lightness * (1 + s) if lightness < 0.5 else lightness + s - lightness * s
    p = 2 * lightness - q
    return (_hue_to_rgb(p, q, h + 1 / 3), _hue_to_rgb(p, q, h), _hue_to_rgb(p, q, h - 1 / 3))


# color() predefined spaces -> linear sRGB. Each entry converts the space's
# own coordinates.
def _predefined_to_linear_srgb(space: str, c: tuple[float, float, float]):
    r, g, b = c
    if space == "srgb":
        return (_srgb_decode(r), _srgb_decode(g), _srgb_decode(b))
    if space == "srgb-linear":
        return (r, g, b)
    if space in ("xyz", "xyz-d65"):
        return _xyz_d65_to_linear_srgb(r, g, b)
    if space == "xyz-d50":
        return _xyz_d50_to_linear_srgb(r, g, b)
    mats = {
        "display-p3": ((0.4865709486482162, 0.26566769316909306, 0.1982172852343625),
                       (0.2289745640697488, 0.6917385218365064, 0.079286914093745),
                       (0.0000000000000000, 0.04511338185890264, 1.043944368900976)),
        "a98-rgb": ((0.5766690429101305, 0.1855582379065463, 0.1882286462349947),
                    (0.29734497525053605, 0.627363566242239, 0.07529145075053818),
                    (0.02703136138641234, 0.07068885253582723, 0.9913375368376388)),
        "prophoto-rgb": ((0.7977604896723027, 0.13518583717574031, 0.0313493495815248),
                         (0.2880711282292934, 0.7118432178101014, 0.00008565396060525902),
                         (0.0, 0.0, 0.8251046025104601)),
        "rec2020": ((0.6369580483012914, 0.14461690358620832, 0.1688809751641721),
                    (0.2627002120112671, 0.6779980715188708, 0.05930171646986196),
                    (0.000000000000000, 0.028072693049087428, 1.060985057710791)),
    }
    if space not in mats:
        return None
    gamma = {"display-p3": 2.4, "a98-rgb": 563 / 256, "prophoto-rgb": 1.8, "rec2020": 2.4}[space]
    if space == "display-p3":
        lin = (_srgb_decode(r), _srgb_decode(g), _srgb_decode(b))
    elif space == "prophoto-rgb":
        def pp(v):
            return v / 16.0 if abs(v) <= 16 / 512 else math.copysign(abs(v) ** 1.8, v)
        lin = (pp(r), pp(g), pp(b))
    elif space == "a98-rgb":
        lin = tuple(math.copysign(abs(v) ** gamma, v) for v in (r, g, b))
    else:  # rec2020
        alpha, beta = 1.09929682680944, 0.018053968510807
        def rr(v):
            a = abs(v)
            return math.copysign(a / 4.5 if a < beta * 4.5 else ((a + alpha - 1) / alpha) ** (1 / 0.45), v)
        lin = (rr(r), rr(g), rr(b))
    m = mats[space]
    xyz = tuple(sum(m[i][j] * lin[j] for j in range(3)) for i in range(3))
    if space == "prophoto-rgb":
        return _xyz_d50_to_linear_srgb(*xyz)
    return _xyz_d65_to_linear_srgb(*xyz)


# ─── color-mix ───────────────────────────────────────────────────────────
# Index of the HUE component in each polar space's tuple, so interpolation
# knows which coordinate takes the arc rather than the average. `hwb` and
# `lch` sat here unused while _to_space returned None for both, which is what
# gave the dead entries away.
_POLAR = {"hsl": 2, "hwb": 2, "lch": 2, "oklch": 2}

# CSS Color 5's four hue-interpolation methods. `shorter` is the default.
_HUE_METHODS = ("shorter", "longer", "increasing", "decreasing")


def _to_space(rgb01: tuple[float, float, float], space: str):
    """Gamma-encoded sRGB in 0..1 into an interpolation space. Only the spaces
    color-mix can name are supported; anything else returns None so the caller
    can bail rather than invent an answer.

    Floats, not 8-bit. Quantising each operand before interpolating cost up to
    9/255 against Chromium on `color-mix(in oklch, …)` — measured, which is why
    the whole module resolves in floats and rounds once at the end.
    """
    r, g, b = rgb01
    if space == "srgb":
        return (r, g, b)
    if space == "srgb-linear":
        return (_srgb_decode(r), _srgb_decode(g), _srgb_decode(b))
    lr, lg, lb = (_srgb_decode(r), _srgb_decode(g), _srgb_decode(b))
    if space in ("oklab", "oklch"):
        l = 0.4122214708 * lr + 0.5363325363 * lg + 0.0514459929 * lb
        m = 0.2119034982 * lr + 0.6806995451 * lg + 0.1073969566 * lb
        s = 0.0883024619 * lr + 0.2817188376 * lg + 0.6299787005 * lb
        l_, m_, s_ = (math.copysign(abs(v) ** (1 / 3), v) for v in (l, m, s))
        lab = (0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
               1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
               0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_)
        if space == "oklab":
            return lab
        return (lab[0], math.hypot(lab[1], lab[2]),
                math.degrees(math.atan2(lab[2], lab[1])) % 360)
    if space in ("hsl", "hwb"):
        mx, mn = max(r, g, b), min(r, g, b)
        d = mx - mn
        if d == 0:
            hue = 0.0
        elif mx == r:
            hue = (((g - b) / d) % 6) * 60
        elif mx == g:
            hue = ((b - r) / d + 2) * 60
        else:
            hue = ((r - g) / d + 4) * 60
        hue %= 360
        if space == "hwb":
            return (mn, 1 - mx, hue)
        light = (mx + mn) / 2
        sat = 0.0 if d == 0 else (d / (2 - mx - mn) if light > 0.5 else d / (mx + mn))
        return (sat, light, hue)
    if space in ("lab", "lch", "xyz", "xyz-d65", "xyz-d50"):
        xyz65 = _linear_srgb_to_xyz_d65(lr, lg, lb)
        if space in ("xyz", "xyz-d65"):
            return xyz65
        xyz50 = _xyz_d65_to_d50(*xyz65)
        if space == "xyz-d50":
            return xyz50
        lab = _xyz_d50_to_lab(*xyz50)
        if space == "lab":
            return lab
        return (lab[0], math.hypot(lab[1], lab[2]),
                math.degrees(math.atan2(lab[2], lab[1])) % 360)
    return None


def _from_space(c, space: str):
    if space == "srgb":
        return c
    if space == "srgb-linear":
        return tuple(_srgb_encode(v) for v in c)
    if space == "oklab":
        return tuple(_srgb_encode(v) for v in _oklab_to_linear_srgb(*c))
    if space == "oklch":
        lightness, chroma, hue = c
        a = chroma * math.cos(math.radians(hue))
        b = chroma * math.sin(math.radians(hue))
        return tuple(_srgb_encode(v) for v in _oklab_to_linear_srgb(lightness, a, b))
    if space == "hsl":
        sat, light, hue = c
        return _hsl_to_srgb(hue, sat, light)
    if space == "hwb":
        w, bl, hue = c
        if w + bl >= 1:
            grey = w / (w + bl) if (w + bl) else 0.0
            return (grey, grey, grey)
        base = _hsl_to_srgb(hue, 1.0, 0.5)
        return tuple(v * (1 - w - bl) + w for v in base)
    if space in ("lab", "lch", "xyz", "xyz-d65", "xyz-d50"):
        if space in ("xyz", "xyz-d65"):
            lin = _xyz_d65_to_linear_srgb(*c)
        elif space == "xyz-d50":
            lin = _xyz_d50_to_linear_srgb(*c)
        else:
            if space == "lch":
                lightness, chroma, hue = c
                a = chroma * math.cos(math.radians(hue))
                b2 = chroma * math.sin(math.radians(hue))
            else:
                lightness, a, b2 = c
            lin = _lab_to_linear_srgb(lightness, a, b2)
        return tuple(_srgb_encode(v) for v in lin)
    return None


def _mix_hue(h1: float, h2: float, t: float, method: str = "shorter") -> float:
    """CSS Color 5's four hue-interpolation methods. `shorter` is the default
    and was the only one implemented; naming any other in a `color-mix()` made
    the whole value unresolvable, which the contrast gate turns into a
    rotation-aborting failure."""
    h1 %= 360
    h2 %= 360
    d = h2 - h1
    # Every method branches on d against 0 and +/-180, which are knife edges —
    # and a complementary pair is EXACTLY 180 apart, so that edge is where
    # designers actually live. Operands round-trip through sRGB to reach this
    # function, and that costs about 2e-5 degrees of hue (measured:
    # oklch(... 20) comes back as 20.0000096, oklch(... 200) as 199.9999909, so
    # d lands at 179.99998 and `longer` took the wrong branch, giving a
    # blue-violet where Chromium paints yellow-green). Snapping at 1e-3 is four
    # orders above that noise and far below any distinction a theme could mean.
    for edge in (-360.0, -180.0, 0.0, 180.0, 360.0):
        if abs(d - edge) < 1e-3:
            d = edge
            break
    if method == "shorter":
        if d > 180:
            d -= 360
        elif d < -180:
            d += 360
    elif method == "longer":
        if -180 < d < 180:
            d += 360 if d >= 0 else -360
    elif method == "increasing":
        if d < 0:
            d += 360
    elif method == "decreasing":
        if d > 0:
            d -= 360
    return (h1 + d * t) % 360


def _color_mix(args: list[str]) -> tuple[float, float, float] | None:
    if len(args) < 4 or args[0].lower() != "in":
        return None
    space = args[1].lower()
    rest = args[2:]
    # `in <space> [<method> hue]` — consume the optional interpolation method.
    method = "shorter"
    if len(rest) >= 2 and rest[0].lower() in _HUE_METHODS and rest[1].lower() == "hue":
        if space not in _POLAR:
            return None       # a hue method on a rectangular space is invalid
        method, rest = rest[0].lower(), rest[2:]
    parsed: list[tuple[tuple[float, float, float], float | None]] = []
    i = 0
    while i < len(rest) and len(parsed) < 2:
        rgb = _to_rgb01(rest[i])
        if rgb is None:
            return None
        pct = None
        if i + 1 < len(rest) and rest[i + 1].endswith("%"):
            try:
                pct = float(rest[i + 1][:-1]) / 100.0
            except ValueError:
                return None
            i += 1
        parsed.append((rgb, pct))
        i += 1
    if len(parsed) != 2:
        return None
    # `color-mix()` takes exactly two colors. Taking the first two and
    # ignoring the rest turned invalid CSS into a plausible-looking color that
    # then fed a contrast ratio — `color-mix(in srgb, red, blue, green)` came
    # back as purple. An unresolvable value is reported as unresolvable.
    if i != len(rest):
        return None
    (c1, p1), (c2, p2) = parsed
    if p1 is None and p2 is None:
        p1 = p2 = 0.5
    elif p1 is None:
        p1 = 1.0 - p2
    elif p2 is None:
        p2 = 1.0 - p1
    total = p1 + p2
    if total <= 0:
        return None
    t = p2 / total
    a, b = _to_space(c1, space), _to_space(c2, space)
    if a is None or b is None:
        return None
    hue_index = _POLAR.get(space)
    mixed = []
    for k in range(3):
        if hue_index is not None and k == hue_index:
            mixed.append(_mix_hue(a[k], b[k], t, method))
        else:
            mixed.append(a[k] * (1 - t) + b[k] * t)
    return _from_space(tuple(mixed), space)


# ─── the 148 CSS named colors ────────────────────────────────────────────
_NAMED = {
    "aliceblue": "#f0f8ff", "antiquewhite": "#faebd7", "aqua": "#00ffff",
    "aquamarine": "#7fffd4", "azure": "#f0ffff", "beige": "#f5f5dc",
    "bisque": "#ffe4c4", "black": "#000000", "blanchedalmond": "#ffebcd",
    "blue": "#0000ff", "blueviolet": "#8a2be2", "brown": "#a52a2a",
    "burlywood": "#deb887", "cadetblue": "#5f9ea0", "chartreuse": "#7fff00",
    "chocolate": "#d2691e", "coral": "#ff7f50", "cornflowerblue": "#6495ed",
    "cornsilk": "#fff8dc", "crimson": "#dc143c", "cyan": "#00ffff",
    "darkblue": "#00008b", "darkcyan": "#008b8b", "darkgoldenrod": "#b8860b",
    "darkgray": "#a9a9a9", "darkgreen": "#006400", "darkgrey": "#a9a9a9",
    "darkkhaki": "#bdb76b", "darkmagenta": "#8b008b", "darkolivegreen": "#556b2f",
    "darkorange": "#ff8c00", "darkorchid": "#9932cc", "darkred": "#8b0000",
    "darksalmon": "#e9967a", "darkseagreen": "#8fbc8f", "darkslateblue": "#483d8b",
    "darkslategray": "#2f4f4f", "darkslategrey": "#2f4f4f", "darkturquoise": "#00ced1",
    "darkviolet": "#9400d3", "deeppink": "#ff1493", "deepskyblue": "#00bfff",
    "dimgray": "#696969", "dimgrey": "#696969", "dodgerblue": "#1e90ff",
    "firebrick": "#b22222", "floralwhite": "#fffaf0", "forestgreen": "#228b22",
    "fuchsia": "#ff00ff", "gainsboro": "#dcdcdc", "ghostwhite": "#f8f8ff",
    "gold": "#ffd700", "goldenrod": "#daa520", "gray": "#808080",
    "green": "#008000", "greenyellow": "#adff2f", "grey": "#808080",
    "honeydew": "#f0fff0", "hotpink": "#ff69b4", "indianred": "#cd5c5c",
    "indigo": "#4b0082", "ivory": "#fffff0", "khaki": "#f0e68c",
    "lavender": "#e6e6fa", "lavenderblush": "#fff0f5", "lawngreen": "#7cfc00",
    "lemonchiffon": "#fffacd", "lightblue": "#add8e6", "lightcoral": "#f08080",
    "lightcyan": "#e0ffff", "lightgoldenrodyellow": "#fafad2", "lightgray": "#d3d3d3",
    "lightgreen": "#90ee90", "lightgrey": "#d3d3d3", "lightpink": "#ffb6c1",
    "lightsalmon": "#ffa07a", "lightseagreen": "#20b2aa", "lightskyblue": "#87cefa",
    "lightslategray": "#778899", "lightslategrey": "#778899", "lightsteelblue": "#b0c4de",
    "lightyellow": "#ffffe0", "lime": "#00ff00", "limegreen": "#32cd32",
    "linen": "#faf0e6", "magenta": "#ff00ff", "maroon": "#800000",
    "mediumaquamarine": "#66cdaa", "mediumblue": "#0000cd", "mediumorchid": "#ba55d3",
    "mediumpurple": "#9370db", "mediumseagreen": "#3cb371", "mediumslateblue": "#7b68ee",
    "mediumspringgreen": "#00fa9a", "mediumturquoise": "#48d1cc",
    "mediumvioletred": "#c71585", "midnightblue": "#191970", "mintcream": "#f5fffa",
    "mistyrose": "#ffe4e1", "moccasin": "#ffe4b5", "navajowhite": "#ffdead",
    "navy": "#000080", "oldlace": "#fdf5e6", "olive": "#808000",
    "olivedrab": "#6b8e23", "orange": "#ffa500", "orangered": "#ff4500",
    "orchid": "#da70d6", "palegoldenrod": "#eee8aa", "palegreen": "#98fb98",
    "paleturquoise": "#afeeee", "palevioletred": "#db7093", "papayawhip": "#ffefd5",
    "peachpuff": "#ffdab9", "peru": "#cd853f", "pink": "#ffc0cb",
    "plum": "#dda0dd", "powderblue": "#b0e0e6", "purple": "#800080",
    "rebeccapurple": "#663399", "red": "#ff0000", "rosybrown": "#bc8f8f",
    "royalblue": "#4169e1", "saddlebrown": "#8b4513", "salmon": "#fa8072",
    "sandybrown": "#f4a460", "seagreen": "#2e8b57", "seashell": "#fff5ee",
    "sienna": "#a0522d", "silver": "#c0c0c0", "skyblue": "#87ceeb",
    "slateblue": "#6a5acd", "slategray": "#708090", "slategrey": "#708090",
    "snow": "#fffafa", "springgreen": "#00ff7f", "steelblue": "#4682b4",
    "tan": "#d2b48c", "teal": "#008080", "thistle": "#d8bfd8",
    "tomato": "#ff6347", "turquoise": "#40e0d0", "violet": "#ee82ee",
    "wheat": "#f5deb3", "white": "#ffffff", "whitesmoke": "#f5f5f5",
    "yellow": "#ffff00", "yellowgreen": "#9acd32",
    # `transparent` is black at alpha 0; alpha is not modelled, so black.
    "transparent": "#000000",
}


def to_rgb(value: str) -> tuple[int, int, int] | None:
    """A CSS color string to opaque 8-bit sRGB, or None if it is not a color
    this module understands. Never raises.

    The single rounding boundary. Everything below resolves in floats so a
    nested `color-mix()` does not quantise its operands before interpolating
    them."""
    rgb = _to_rgb01(value)
    if rgb is None:
        return None
    return tuple(int(round(_clamp(v) * 255)) for v in rgb)  # type: ignore[return-value]


def _to_rgb01(value: str) -> tuple[float, float, float] | None:
    """The float core: gamma-encoded sRGB in 0..1, unclamped."""
    if not value:
        return None
    value = value.strip()
    lowered = value.lower()
    if lowered in _NAMED:
        value = _NAMED[lowered]
        lowered = value

    m = _HEX_RE.match(value)
    if m:
        h = m.group(1)
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h)
        if len(h) not in (6, 8):
            return None
        return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))  # type: ignore

    m = _FUNC_RE.match(value)
    if not m:
        return None
    name, body = m.group(1).lower(), m.group(2)
    args = _split_args(body)

    if name == "color-mix":
        return _color_mix(args)

    args = _drop_alpha(args)

    try:
        if name in ("rgb", "rgba"):
            if len(args) < 3:
                return None
            vals = [_num(a, 255.0, 255.0) for a in args[:3]]
            if any(v is None for v in vals):
                return None
            return tuple(v / 255.0 for v in vals)  # type: ignore

        if name in ("hsl", "hsla"):
            if len(args) < 3:
                return None
            h = _angle(args[0])
            s = _num(args[1], 1.0, 1.0)
            lightness = _num(args[2], 1.0, 1.0)
            if None in (h, s, lightness):
                return None
            # Bare numbers for s/l are percentages in the legacy grammar.
            if not args[1].strip().endswith("%"):
                s = s / 100.0
            if not args[2].strip().endswith("%"):
                lightness = lightness / 100.0
            return _hsl_to_srgb(h, s, lightness)

        if name == "hwb":
            if len(args) < 3:
                return None
            h = _angle(args[0])
            w = _num(args[1], 1.0, 1.0)
            b = _num(args[2], 1.0, 1.0)
            if None in (h, w, b):
                return None
            if not args[1].strip().endswith("%"):
                w /= 100.0
            if not args[2].strip().endswith("%"):
                b /= 100.0
            if w + b >= 1:
                grey = w / (w + b)
                return (grey, grey, grey)
            base = _hsl_to_srgb(h, 1.0, 0.5)
            return tuple(c * (1 - w - b) + w for c in base)  # type: ignore

        if name in ("lab", "oklab", "lch", "oklch"):
            if len(args) < 3:
                return None
            ok = name.startswith("ok")
            l_scale = 1.0 if ok else 100.0
            lightness = _num(args[0], l_scale, l_scale)
            if lightness is None:
                return None
            if name in ("lab", "oklab"):
                c_scale = 0.4 if ok else 125.0
                a = _num(args[1], 1.0, c_scale)
                b = _num(args[2], 1.0, c_scale)
                if None in (a, b):
                    return None
            else:
                c_scale = 0.4 if ok else 150.0
                chroma = _num(args[1], 1.0, c_scale)
                hue = _angle(args[2])
                if None in (chroma, hue):
                    return None
                a = chroma * math.cos(math.radians(hue))
                b = chroma * math.sin(math.radians(hue))
            lin = (_oklab_to_linear_srgb(lightness, a, b) if ok
                   else _lab_to_linear_srgb(lightness, a, b))
            return tuple(_srgb_encode(v) for v in lin)  # type: ignore

        if name == "color":
            if len(args) < 4:
                return None
            space = args[0].lower()
            vals = [_num(a, 1.0, 1.0) for a in args[1:4]]
            if any(v is None for v in vals):
                return None
            lin = _predefined_to_linear_srgb(space, tuple(vals))  # type: ignore[arg-type]
            if lin is None:
                return None
            return tuple(_srgb_encode(v) for v in lin)  # type: ignore
    except (ValueError, ZeroDivisionError, OverflowError):
        # A malformed value is "not a color I understand", never a crash that
        # takes the whole doctor run down.
        return None

    return None
