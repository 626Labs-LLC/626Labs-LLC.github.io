"""Export a 626 Labs *Publishing* header for Medium, in the ACTIVE theme's
raster treatment.

Sibling to scripts/export-brand.py — same field primitives (scripts/
raster_theme.py: the theme's field, texture, glows and color bar),
transparent icon left, cyan→magenta hairline divider. Different wordmark:
this one says "626Labs Publishing" instead of the LLC banner's "626Labs
LLC", so the publishing imprint reads as a Medium-native brand without
colliding with the corporate-side banner.

Inputs:
  assets/brand/icon-transparent-1024.png — from export-brand.py (field-free,
                                            so always the committed one)
  themes/<active>/theme.json             — the `raster` block

Outputs:
  assets/brand/medium-header-1500x500.png  — primary, matches existing
                                              banner shape; works for
                                              Medium publication header
                                              and story preview slots
  assets/brand/medium-header-3000x1000.png — 2x for HiDPI / Medium's
                                              big-display surfaces
  ...and the 5:2 (X Articles) and 2:1 (GitHub social preview) pairs.

Usage:
  python scripts/export-medium-header.py                      # active theme
  python scripts/export-medium-header.py --theme <slug> --out <dir>
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
import raster_theme as rt  # noqa: E402 — sibling module in scripts/

ASSETS = ROOT / "assets"
OUT = ASSETS / "brand"
ICON_SRC = ASSETS / "brand" / "icon-transparent-1024.png"
FONTS = ROOT / "fonts"

CYAN = rt.CYAN
MAGENTA = rt.MAGENTA


def gradient_h(width: int, height: int, c1, c2) -> Image.Image:
    """Horizontal cyan→magenta gradient strip."""
    yy, xx = np.indices((height, width))
    t = xx / max(1, width - 1)
    r = (c1[0] * (1 - t) + c2[0] * t).astype(np.uint8)
    g = (c1[1] * (1 - t) + c2[1] * t).astype(np.uint8)
    b = (c1[2] * (1 - t) + c2[2] * t).astype(np.uint8)
    arr = np.stack([r, g, b], axis=-1)
    return Image.fromarray(arr, "RGB")


def fit_font(path: Path, target_w: int, max_size: int, weight: float,
             text: str, draw: ImageDraw.ImageDraw) -> ImageFont.FreeTypeFont:
    """Pick the largest variable-font size whose `text` width <= target_w."""
    size = max_size
    while size > 12:
        f = ImageFont.truetype(str(path), size)
        try:
            f.set_variation_by_axes([weight])
        except (OSError, AttributeError):
            pass
        bbox = draw.textbbox((0, 0), text, font=f)
        if (bbox[2] - bbox[0]) <= target_w:
            return f
        size -= 2
    f = ImageFont.truetype(str(path), 12)
    try:
        f.set_variation_by_axes([weight])
    except (OSError, AttributeError):
        pass
    return f


def mono(size: int) -> ImageFont.FreeTypeFont:
    """JetBrains Mono at weight 400. The static Regular.ttf this script used
    to open left the tree on 2026-05-24 (perf: self-host fonts, variable
    only), which is why the committed headers date from April."""
    f = ImageFont.truetype(str(FONTS / "JetBrainsMono-Variable.ttf"), size)
    f.set_variation_by_axes([400])
    return f


def build_header(size: tuple[int, int], icon: Image.Image, out_path: Path, raster: rt.Raster) -> None:
    W, H = size
    # Atmospheric glows under a glowing theme: cyan top-left, magenta bottom-right.
    canvas = rt.paint_field(W, H, raster, glows=(
        (0.16, 0.28, CYAN, 84, 0.52),
        (0.86, 0.78, MAGENTA, 76, 0.55),
    ))

    # Icon — slightly smaller than the LLC banner so the longer "Publishing"
    # wordmark has room to breathe.
    icon_target_h = int(H * 0.66)
    scale = icon_target_h / icon.height
    icon_w = int(icon.width * scale)
    icon_h = icon_target_h
    icon_resized = icon.resize((icon_w, icon_h), Image.LANCZOS)
    icon_x = int(W * 0.06)
    icon_y = (H - icon_h) // 2
    canvas.alpha_composite(icon_resized, dest=(icon_x, icon_y))

    # Text block right of icon.
    text_x = icon_x + icon_w + int(W * 0.045)
    text_avail_w = W - text_x - int(W * 0.06)

    draw = ImageDraw.Draw(canvas)

    # Wordmark — "626Labs" in cyan + ink; "Publishing" gets its own line as
    # a smaller subtitle below the divider so the imprint reads as the
    # downstream brand of the lab, not a flat compound.
    cyan_part = "626"
    white_part = "Labs"
    full_word = cyan_part + white_part
    sg_bold = fit_font(
        FONTS / "SpaceGrotesk-Variable.ttf",
        target_w=int(text_avail_w * 0.78),
        max_size=int(H * 0.30),
        weight=700,
        text=full_word,
        draw=draw,
    )
    word_size = sg_bold.size

    bbox_c = draw.textbbox((0, 0), cyan_part, font=sg_bold)
    cyan_w = bbox_c[2] - bbox_c[0]
    bbox_white = draw.textbbox((0, 0), white_part, font=sg_bold)
    word_w = cyan_w + (bbox_white[2] - bbox_white[0])

    # Subtitle "PUBLISHING" — mono, uppercase with letter-spacing, in cyan.
    sub_size = max(14, int(word_size * 0.26))
    jb_mono = mono(sub_size)
    publishing_text = "P U B L I S H I N G"  # manual letter-spacing for the mono face

    # Tagline — italic Inter, smaller again, dim ink.
    tag_size = max(13, int(word_size * 0.22))
    inter_italic = ImageFont.truetype(str(FONTS / "Inter-Italic-Variable.ttf"), tag_size)
    try:
        inter_italic.set_variation_by_axes([14, 400])
    except (OSError, AttributeError):
        pass
    tagline = "Imagine Something Else."

    # Vertical rhythm.
    line_h_div = max(2, int(word_size * 0.025))
    pad_to_div = int(word_size * 0.18)
    pad_div_to_sub = int(word_size * 0.18)
    pad_sub_to_tag = int(word_size * 0.18)
    block_h = (
        word_size
        + pad_to_div + line_h_div
        + pad_div_to_sub + sub_size
        + pad_sub_to_tag + tag_size
    )
    top = (H - block_h) // 2

    # Wordmark.
    draw.text((text_x, top), cyan_part, font=sg_bold, fill=CYAN + (255,))
    draw.text((text_x + cyan_w, top), white_part, font=sg_bold, fill=raster.ink + (255,))

    # Cyan→magenta hairline divider.
    div_y = top + word_size + pad_to_div
    grad = gradient_h(word_w, line_h_div, CYAN, MAGENTA).convert("RGBA")
    canvas.alpha_composite(grad, dest=(text_x, div_y))

    # PUBLISHING subtitle.
    sub_y = div_y + line_h_div + pad_div_to_sub
    draw.text((text_x, sub_y), publishing_text, font=jb_mono, fill=CYAN + (255,))

    # Tagline.
    tag_y = sub_y + sub_size + pad_sub_to_tag
    draw.text((text_x, tag_y), tagline, font=inter_italic, fill=raster.dim + (255,))

    # Subtle top-right kicker — keeps Medium-page feel anchored.
    kicker_size = max(11, int(H * 0.030))
    kicker_font = mono(kicker_size)
    kicker_text = "ESSAYS  ·  NOTES  ·  THESES"
    kbbox = draw.textbbox((0, 0), kicker_text, font=kicker_font)
    kw = kbbox[2] - kbbox[0]
    draw.text((W - kw - int(W * 0.035), int(H * 0.075)), kicker_text,
              font=kicker_font, fill=raster.dim + (255,))

    # The printer's color bar, bottom-right, where the magenta glow sat.
    rt.place_color_bar(canvas, raster, right=W - int(W * 0.035), bottom=H - int(H * 0.075))

    canvas.convert("RGB").save(out_path, "PNG", optimize=True)
    print(f"  wrote {out_path}  ({W}x{H})")


HEADERS = [
    ((1500, 500),  "medium-header-1500x500.png"),         # 3:1 — Twitter classic / OG
    ((3000, 1000), "medium-header-3000x1000.png"),        # 3:1 @ 2x
    ((1500, 600),  "medium-header-1500x600.png"),         # 5:2 — X Articles
    ((3000, 1200), "medium-header-3000x1200.png"),        # 5:2 @ 2x
    ((1280, 640),  "medium-header-1280x640.png"),         # 2:1 — GitHub social preview
    ((2560, 1280), "medium-header-2560x1280.png"),        # 2:1 @ 2x
]


def build_all(raster: rt.Raster, out: Path = OUT) -> None:
    if not ICON_SRC.exists():
        raise SystemExit(f"missing {ICON_SRC} — run scripts/export-brand.py first")
    out.mkdir(parents=True, exist_ok=True)
    icon = Image.open(ICON_SRC).convert("RGBA")
    print(f"Building Medium publishing headers ({raster.slug})…")
    for size, name in HEADERS:
        build_header(size, icon, out / name, raster)


def main(argv: list[str]) -> int:
    slug, out_dir, rest = rt.parse_args(argv)
    if rest:
        print(f"usage: export-medium-header.py [--theme <slug>] [--out <dir>]  (unknown: {rest})", file=sys.stderr)
        return 2
    build_all(rt.load(slug), out=out_dir or OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
