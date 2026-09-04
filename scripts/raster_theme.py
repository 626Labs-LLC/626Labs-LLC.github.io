"""The raster treatment a theme declares, and the field primitives every
brand-asset generator paints with.

Every raster the site puts in front of the world off-site (the X and
Discord banners, the Medium and Vibe Plugins headers, the animated server
icon, the browser-tab favicon, the per-story OG cards) was baked in
Phosphor Blueprint's look on 2026-07-07: black field, two-scale drafting
grid, cyan and magenta radial glows, a bloomed mark. Este's ruling
(2026-09-04): they follow the theme. The generators read their treatment
from the ACTIVE theme's `theme.json` instead of hardcoding one month's.

The block, optional in `themes/<slug>/theme.json`:

    "raster": {
      "field":    "#3A4350",   any CSS color scripts/css_color.py parses
      "ink":      "#F7F5F0",   primary text on the field (title, wordmark)
      "dim":      "#C3C1BA",   secondary text (dek, dateline, kicker)
      "texture":  "grain",     "grain" | "grid" | "none"
      "glow":     false,       radial glows on fields, bloom under the favicon
      "colorBar": true,        the printer's color bar (cyan, magenta, paper)
      "bodyFace": "serif"      OPTIONAL: the dek's face on the OG card,
                               "sans" (Inter italic) | "serif" (Source Serif 4);
                               defaults to "sans"
    }

A theme with no block gets RASTER_DEFAULTS, which IS Phosphor Blueprint's
block, so a theme that never thought about rasters regresses nothing.
theme-doctor validates the block for every registered theme (active and
queued) via `validate_block`; `load` raises on a malformed block so a
generator fails loudly rather than drawing from a half-read palette.

Determinism: `paper_grain` is seeded (GRAIN_SEED) and built from numpy's
Generator plus PIL resizes only, so two runs on one box produce identical
bytes. rebuild-hub.yml's OG-card `--check` byte-compares and depends on it.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT = SCRIPTS_DIR.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
import css_color       # noqa: E402 — sibling module in scripts/ — CSS color -> sRGB
import theme_registry  # noqa: E402 — sibling module in scripts/

# Brand constants. The mark is the brand; the field is the month.
CYAN = (23, 212, 250)
MAGENTA = (242, 47, 137)

TEXTURES = ("grain", "grid", "none")
BODY_FACES = ("sans", "serif")
REQUIRED_KEYS = ("field", "ink", "dim", "texture", "glow", "colorBar")
OPTIONAL_KEYS = ("bodyFace",)

# Phosphor Blueprint's treatment, exactly as export-brand.py drew it from
# 2026-07-07 until the block existed: PB_FIELD (0,0,0), INK (231,237,245),
# DIM (138,153,174), the drafting grid, the two glows, no color bar. A theme
# with no `raster` block draws this. Changing a value here changes what a
# block-less theme ships, so tests pin it to phosphor-blueprint's own block.
RASTER_DEFAULTS = {
    "field": "#000000",
    "ink": "#E7EDF5",
    "dim": "#8A99AE",
    "texture": "grid",
    "glow": True,
    "colorBar": False,
    "bodyFace": "sans",
}

# Stone grain: the theme lays fractal noise (white at half alpha) at 7
# percent, a worst case of 3.5 percent paper over the ground. Same numbers
# here: peak opacity .07, mean .035.
GRAIN_SEED = 626
GRAIN_OPACITY = 0.07


@dataclass(frozen=True)
class Raster:
    slug: str
    field: tuple[int, int, int]
    ink: tuple[int, int, int]
    dim: tuple[int, int, int]
    texture: str
    glow: bool
    color_bar: bool
    body_face: str

    @property
    def is_default(self) -> bool:
        """True when this is exactly the Phosphor Blueprint treatment."""
        return from_block(self.slug, RASTER_DEFAULTS) == self


# ─── the block ───────────────────────────────────────────────────────────
def validate_block(block) -> list[str]:
    """Every error names the offending key (`raster.<key>: ...`). An empty
    list means the block parses into a Raster."""
    if not isinstance(block, dict):
        return [f"raster: must be an object, got {type(block).__name__}"]
    errs: list[str] = []
    for key in ("field", "ink", "dim"):
        if key not in block:
            errs.append(f"raster.{key}: missing")
        elif not isinstance(block[key], str) or css_color.to_rgb(block[key]) is None:
            errs.append(f"raster.{key}: not a CSS color: {block[key]!r}")
    if "texture" not in block:
        errs.append("raster.texture: missing")
    elif block["texture"] not in TEXTURES:
        errs.append(
            f"raster.texture: must be one of {', '.join(TEXTURES)}, got {block['texture']!r}"
        )
    for key in ("glow", "colorBar"):
        if key not in block:
            errs.append(f"raster.{key}: missing")
        elif not isinstance(block[key], bool):
            errs.append(f"raster.{key}: must be true or false, got {block[key]!r}")
    if "bodyFace" in block and block["bodyFace"] not in BODY_FACES:
        errs.append(
            f"raster.bodyFace: must be one of {', '.join(BODY_FACES)}, got {block['bodyFace']!r}"
        )
    for key in block:
        if key not in REQUIRED_KEYS and key not in OPTIONAL_KEYS:
            errs.append(f"raster.{key}: unknown key")
    return errs


def from_block(slug: str, block: dict) -> Raster:
    errs = validate_block(block)
    if errs:
        raise ValueError(f"theme {slug}: malformed raster block: " + "; ".join(errs))
    return Raster(
        slug=slug,
        field=css_color.to_rgb(block["field"]),
        ink=css_color.to_rgb(block["ink"]),
        dim=css_color.to_rgb(block["dim"]),
        texture=block["texture"],
        glow=block["glow"],
        color_bar=block["colorBar"],
        body_face=block.get("bodyFace", RASTER_DEFAULTS["bodyFace"]),
    )


def read_block(slug: str, root: Path = ROOT) -> dict | None:
    """The raw `raster` block from themes/<slug>/theme.json, or None when the
    theme declares none. Raises if the theme has no theme.json at all."""
    meta = json.loads((theme_registry.theme_dir(slug, root) / "theme.json").read_text(encoding="utf-8"))
    return meta.get("raster")


def load(slug: str | None = None, root: Path = ROOT) -> Raster:
    """The Raster for `slug`, or for the ACTIVE theme when slug is None. A
    theme with no block gets RASTER_DEFAULTS."""
    if slug is None:
        slug = theme_registry.active_slug(theme_registry.load(root))
    block = read_block(slug, root)
    return from_block(slug, RASTER_DEFAULTS if block is None else block)


def parse_args(argv: list[str]) -> tuple[str | None, Path | None, list[str]]:
    """`--theme <slug>` and `--out <dir>` for a generator's argv. Returns
    (slug or None for the active theme, out dir or None for the committed
    location, the remaining args)."""
    slug: str | None = None
    out: Path | None = None
    rest: list[str] = []
    it = iter(argv)
    for a in it:
        if a == "--theme":
            slug = next(it, None)
            if not slug:
                raise SystemExit("--theme needs a slug")
        elif a == "--out":
            val = next(it, None)
            if not val:
                raise SystemExit("--out needs a directory")
            out = Path(val)
        else:
            rest.append(a)
    return slug, out, rest


# ─── contrast ────────────────────────────────────────────────────────────
def _srgb_to_linear(channel: int) -> float:
    c = channel / 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb: tuple[int, int, int]) -> float:
    r, g, b = (_srgb_to_linear(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    """WCAG 2.1, the same math theme-doctor grades contrastPairs with."""
    la, lb = relative_luminance(a), relative_luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def grained_field(raster: Raster) -> tuple[int, int, int]:
    """The field at the grain's PEAK: GRAIN_OPACITY of ink over the field,
    the lightest pixel the grain can put behind a letter; the field itself
    when there is no grain. Text is graded against this, not the bare field
    and not the mean (GRAIN_OPACITY / 2): a dek graded at the mean can sit
    under 4.5:1 on the peak pixels and pass."""
    if raster.texture != "grain":
        return raster.field
    a = GRAIN_OPACITY
    return tuple(int(round(f * (1 - a) + i * a)) for f, i in zip(raster.field, raster.ink))  # type: ignore[return-value]


# ─── primitives ──────────────────────────────────────────────────────────
def drafting_grid(width: int, height: int) -> Image.Image:
    """Phosphor Blueprint two-scale drafting grid (adopted 2026-07-07):
    24px cyan lines at ~5% alpha + 120px at ~11%. Composite over the field
    before the glows. Page-texture only — icons stay grid-free."""
    arr = np.zeros((height, width, 4), dtype=np.uint8)
    for step, alpha in ((24, 13), (120, 28)):
        arr[::step, :, :3] = CYAN
        arr[::step, :, 3] = np.maximum(arr[::step, :, 3], alpha)
        arr[:, ::step, :3] = CYAN
        arr[:, ::step, 3] = np.maximum(arr[:, ::step, 3], alpha)
    return Image.fromarray(arr, "RGBA")


def paper_grain(
    width: int, height: int, ink: tuple[int, int, int],
    seed: int = GRAIN_SEED, opacity: float = GRAIN_OPACITY,
) -> Image.Image:
    """Stone grain: three octaves of seeded uniform noise (full, half and
    quarter resolution, bilinear upscaled) in the ink color, alpha ramped to
    `opacity` at peak so the mean coverage is opacity/2 (3.5 percent at the
    default). Deterministic for a given (width, height, seed)."""
    rng = np.random.default_rng(seed)
    acc = np.zeros((height, width), dtype=np.float32)
    total = 0.0
    for div, weight in ((1, 0.5), (2, 0.3), (4, 0.2)):
        w, h = max(1, width // div), max(1, height // div)
        octave = rng.random((h, w), dtype=np.float32)
        if div != 1:
            octave = np.asarray(
                Image.fromarray(octave, "F").resize((width, height), Image.BILINEAR),
                dtype=np.float32,
            )
        acc += octave * weight
        total += weight
    acc /= total
    arr = np.zeros((height, width, 4), dtype=np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = ink
    arr[..., 3] = np.clip(acc * opacity * 255, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def radial_glow(
    width: int, height: int, cx: float, cy: float, color, max_alpha: int, radius: float,
) -> Image.Image:
    """Soft radial alpha falloff at (cx,cy) — coords as fractions of size."""
    arr = np.zeros((height, width, 4), dtype=np.uint8)
    yy, xx = np.indices((height, width))
    dx = xx - cx * width
    dy = yy - cy * height
    dist = np.sqrt(dx * dx + dy * dy)
    falloff = np.clip(1 - dist / (radius * max(width, height)), 0, 1) ** 2
    arr[..., 0] = color[0]
    arr[..., 1] = color[1]
    arr[..., 2] = color[2]
    arr[..., 3] = (falloff * max_alpha).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def color_bar(raster: Raster, swatch: int, gap: int | None = None) -> Image.Image:
    """The printer's color bar the slate sheet puts in its ears and its
    footer: three square swatches, cyan, magenta, paper (the ink), on a
    transparent ground. The one place magenta sits on a slate raster."""
    if gap is None:
        gap = max(2, round(swatch * 0.44))
    swatches = (CYAN, MAGENTA, raster.ink)
    w = swatch * len(swatches) + gap * (len(swatches) - 1)
    bar = Image.new("RGBA", (w, swatch), (0, 0, 0, 0))
    for i, c in enumerate(swatches):
        x = i * (swatch + gap)
        bar.paste(c + (255,), (x, 0, x + swatch, swatch))
    return bar


def color_bar_size(height: int) -> int:
    """Swatch side for a canvas of `height`: 9px on the sheet's 1280 page,
    ~2.4 percent of the canvas height on a raster, never under 8."""
    return max(8, round(height * 0.024))


def paint_field(
    width: int, height: int, raster: Raster,
    glows: tuple = (), texture: bool = True,
) -> Image.Image:
    """A canvas painted with the theme's field: flat color, then the texture
    (grid or grain, when `texture` is allowed at this scale), then each
    radial glow in `glows` ((cx, cy, color, max_alpha, radius) tuples) when
    the theme glows. The order is the order export-brand.py drew in before
    the block existed, so Phosphor Blueprint's output is unchanged."""
    canvas = Image.new("RGBA", (width, height), raster.field + (255,))
    if texture and raster.texture == "grid":
        canvas.alpha_composite(drafting_grid(width, height))
    elif texture and raster.texture == "grain":
        canvas.alpha_composite(paper_grain(width, height, raster.ink))
    if raster.glow:
        for cx, cy, color, max_alpha, radius in glows:
            canvas.alpha_composite(radial_glow(width, height, cx, cy, color, max_alpha, radius))
    return canvas


def place_color_bar(canvas: Image.Image, raster: Raster, *, right: int, bottom: int) -> None:
    """Composite the color bar with its bottom-right corner at (right,
    bottom), when the theme carries one. Where the magenta glow used to sit."""
    if not raster.color_bar:
        return
    bar = color_bar(raster, color_bar_size(canvas.height))
    canvas.alpha_composite(bar, dest=(right - bar.width, bottom - bar.height))
