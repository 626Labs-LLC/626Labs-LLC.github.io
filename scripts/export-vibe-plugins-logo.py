"""Export a Vibe Plugins co-brand logo — 626 Labs × Claude Code — in the
ACTIVE theme's raster treatment.

The plugin family belongs to 626 Labs but lives inside Claude Code, so
the mark needs both identities legible at a glance:

  - 626 Labs hex / brain / circuit icon on the left (the lab)
  - "Vibe Plugins" wordmark, cyan + ink, dominant
  - Cyan → magenta hairline divider (the brand swoosh)
  - "for Claude Code" subtitle in mono
  - Anthropic's Claude sparkle anchoring the right edge

The field, texture, glows and color bar come from the theme's `raster`
block (scripts/raster_theme.py), the same primitives export-brand.py draws.

Inputs:
  assets/brand/icon-transparent-1024.png — from export-brand.py (field-free,
                                            so always the committed one)
  assets/anthropic/claude-sparkle.png
  themes/<active>/theme.json             — the `raster` block

Outputs:
  assets/brand/vibe-plugins-banner-1500x500.png  — wide banner for
    READMEs, social cards, marketplace listings (+ 2x, 5:2 and 2:1 pairs)
  assets/brand/vibe-plugins-square-1024.png      — square version,
    works as a publication / repo avatar

Usage:
  python scripts/export-vibe-plugins-logo.py                      # active theme
  python scripts/export-vibe-plugins-logo.py --theme <slug> --out <dir>
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
    yy, xx = np.indices((height, width))
    t = xx / max(1, width - 1)
    r = (c1[0] * (1 - t) + c2[0] * t).astype(np.uint8)
    g = (c1[1] * (1 - t) + c2[1] * t).astype(np.uint8)
    b = (c1[2] * (1 - t) + c2[2] * t).astype(np.uint8)
    arr = np.stack([r, g, b], axis=-1)
    return Image.fromarray(arr, "RGB")


CLAUDE_SPARKLE_SRC = ASSETS / "anthropic" / "claude-sparkle.png"


def load_claude_sparkle(target_height: int) -> Image.Image:
    """Load Anthropic's actual Claude sparkle (transparent PNG, coral fill)
    and scale it to the requested height. Aspect ratio preserved.

    Source: assets/anthropic/claude-sparkle.png — extracted from Anthropic's
    public Claude logo via tools/bgremove and cropped to the sparkle bounds.
    """
    if not CLAUDE_SPARKLE_SRC.exists():
        raise SystemExit(
            f"missing {CLAUDE_SPARKLE_SRC} — run tools/bgremove on a Claude "
            f"logo PNG first or restore the asset"
        )
    spk = Image.open(CLAUDE_SPARKLE_SRC).convert("RGBA")
    scale = target_height / spk.height
    new_w = int(spk.width * scale)
    return spk.resize((new_w, target_height), Image.LANCZOS)


def fit_font(path: Path, target_w: int, max_size: int, weight: float,
             text: str, draw: ImageDraw.ImageDraw) -> ImageFont.FreeTypeFont:
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
    """JetBrains Mono at weight 400 (the static Regular.ttf left the tree
    on 2026-05-24; see export-medium-header.py)."""
    f = ImageFont.truetype(str(FONTS / "JetBrainsMono-Variable.ttf"), size)
    f.set_variation_by_axes([400])
    return f


def build_banner(size: tuple[int, int], icon: Image.Image, out_path: Path, raster: rt.Raster) -> None:
    W, H = size
    canvas = rt.paint_field(W, H, raster, glows=(
        (0.16, 0.28, CYAN, 84, 0.52),
        (0.86, 0.78, MAGENTA, 76, 0.55),
    ))

    # 626 Labs hex on the left.
    icon_target_h = int(H * 0.66)
    scale = icon_target_h / icon.height
    icon_w = int(icon.width * scale)
    icon_h = icon_target_h
    icon_resized = icon.resize((icon_w, icon_h), Image.LANCZOS)
    icon_x = int(W * 0.05)
    icon_y = (H - icon_h) // 2
    canvas.alpha_composite(icon_resized, dest=(icon_x, icon_y))

    # Claude sparkle on the right (Anthropic's actual mark).
    sparkle_target_h = int(H * 0.55)
    sparkle = load_claude_sparkle(sparkle_target_h)
    sparkle_x = W - sparkle.width - int(W * 0.06)
    sparkle_y = (H - sparkle.height) // 2
    canvas.alpha_composite(sparkle, dest=(sparkle_x, sparkle_y))

    # Text block between the two glyphs.
    text_x = icon_x + icon_w + int(W * 0.045)
    text_avail_w = sparkle_x - text_x - int(W * 0.04)

    draw = ImageDraw.Draw(canvas)

    cyan_part = "Vibe"
    white_part = " Plugins"
    full_word = cyan_part + white_part
    sg_bold = fit_font(
        FONTS / "SpaceGrotesk-Variable.ttf",
        target_w=int(text_avail_w * 0.95),
        max_size=int(H * 0.32),
        weight=700,
        text=full_word,
        draw=draw,
    )
    word_size = sg_bold.size

    bbox_c = draw.textbbox((0, 0), cyan_part, font=sg_bold)
    cyan_w = bbox_c[2] - bbox_c[0]
    bbox_white = draw.textbbox((0, 0), white_part, font=sg_bold)
    word_w = cyan_w + (bbox_white[2] - bbox_white[0])

    # Subtitle "for Claude Code · 626 Labs" in mono.
    sub_size = max(13, int(word_size * 0.24))
    jb_mono = mono(sub_size)
    subtitle = "for Claude Code  ·  626 Labs"

    line_h_div = max(2, int(word_size * 0.025))
    pad_to_div = int(word_size * 0.18)
    pad_div_to_sub = int(word_size * 0.20)
    block_h = word_size + pad_to_div + line_h_div + pad_div_to_sub + sub_size
    top = (H - block_h) // 2

    draw.text((text_x, top), cyan_part, font=sg_bold, fill=CYAN + (255,))
    draw.text((text_x + cyan_w, top), white_part, font=sg_bold, fill=raster.ink + (255,))

    div_y = top + word_size + pad_to_div
    grad = gradient_h(word_w, line_h_div, CYAN, MAGENTA).convert("RGBA")
    canvas.alpha_composite(grad, dest=(text_x, div_y))

    sub_y = div_y + line_h_div + pad_div_to_sub
    draw.text((text_x, sub_y), subtitle, font=jb_mono, fill=raster.dim + (255,))

    # The printer's color bar, bottom-right, under the sparkle.
    rt.place_color_bar(canvas, raster, right=W - int(W * 0.06), bottom=H - int(H * 0.08))

    canvas.convert("RGB").save(out_path, "PNG", optimize=True)
    print(f"  wrote {out_path}  ({W}x{H})")


def build_square(size: int, icon: Image.Image, out_path: Path, raster: rt.Raster) -> None:
    """Square variant — icon top, sparkle upper-right, wordmark stacked.

    Works as a GitHub repo avatar or marketplace tile.
    """
    W = H = size
    canvas = rt.paint_field(W, H, raster, glows=(
        (0.18, 0.22, CYAN, 96, 0.60),
        (0.82, 0.82, MAGENTA, 84, 0.60),
    ))

    # 626 Labs icon centered horizontally, upper third.
    icon_h = int(H * 0.44)
    scale = icon_h / icon.height
    icon_w = int(icon.width * scale)
    icon_resized = icon.resize((icon_w, icon_h), Image.LANCZOS)
    icon_x = (W - icon_w) // 2
    icon_y = int(H * 0.10)
    canvas.alpha_composite(icon_resized, dest=(icon_x, icon_y))

    # Claude sparkle in the upper-right — balances the 626 hex visually
    # and stays clear of the wordmark + subtitle stack below.
    spk_size = int(H * 0.13)
    spk = load_claude_sparkle(spk_size)
    canvas.alpha_composite(spk, dest=(W - spk.width - int(W * 0.08),
                                      int(H * 0.07)))

    draw = ImageDraw.Draw(canvas)

    # Stacked wordmark below icon.
    cyan_part = "Vibe"
    white_part = " Plugins"
    target_w = int(W * 0.78)
    sg_bold = fit_font(
        FONTS / "SpaceGrotesk-Variable.ttf",
        target_w=target_w,
        max_size=int(H * 0.16),
        weight=700,
        text=cyan_part + white_part,
        draw=draw,
    )
    word_size = sg_bold.size
    bbox_c = draw.textbbox((0, 0), cyan_part, font=sg_bold)
    cyan_w = bbox_c[2] - bbox_c[0]
    bbox_white = draw.textbbox((0, 0), white_part, font=sg_bold)
    word_w = cyan_w + (bbox_white[2] - bbox_white[0])
    word_x = (W - word_w) // 2
    word_y = icon_y + icon_h + int(H * 0.06)
    draw.text((word_x, word_y), cyan_part, font=sg_bold, fill=CYAN + (255,))
    draw.text((word_x + cyan_w, word_y), white_part, font=sg_bold, fill=raster.ink + (255,))

    # Hairline divider, centered.
    div_h = max(2, int(word_size * 0.04))
    grad = gradient_h(word_w, div_h, CYAN, MAGENTA).convert("RGBA")
    div_y = word_y + word_size + int(word_size * 0.18)
    canvas.alpha_composite(grad, dest=(word_x, div_y))

    # Subtitle, centered.
    sub_size = max(14, int(word_size * 0.30))
    jb_mono = mono(sub_size)
    subtitle = "for Claude Code  ·  626 Labs"
    sbbox = draw.textbbox((0, 0), subtitle, font=jb_mono)
    sub_x = (W - (sbbox[2] - sbbox[0])) // 2
    sub_y = div_y + div_h + int(word_size * 0.20)
    draw.text((sub_x, sub_y), subtitle, font=jb_mono, fill=raster.dim + (255,))

    # The printer's color bar, bottom-right.
    rt.place_color_bar(canvas, raster, right=W - int(W * 0.08), bottom=H - int(H * 0.07))

    canvas.convert("RGB").save(out_path, "PNG", optimize=True)
    print(f"  wrote {out_path}  ({W}x{H})")


BANNERS = [
    ((1500, 500),  "vibe-plugins-banner-1500x500.png"),    # 3:1 — Twitter classic / OG
    ((3000, 1000), "vibe-plugins-banner-3000x1000.png"),   # 3:1 @ 2x
    ((1500, 600),  "vibe-plugins-banner-1500x600.png"),    # 5:2 — X Articles
    ((3000, 1200), "vibe-plugins-banner-3000x1200.png"),   # 5:2 @ 2x
    ((1280, 640),  "vibe-plugins-banner-1280x640.png"),    # 2:1 — GitHub social preview
    ((2560, 1280), "vibe-plugins-banner-2560x1280.png"),   # 2:1 @ 2x
]


def build_all(raster: rt.Raster, out: Path = OUT) -> None:
    if not ICON_SRC.exists():
        raise SystemExit(f"missing {ICON_SRC} — run scripts/export-brand.py first")
    out.mkdir(parents=True, exist_ok=True)
    icon = Image.open(ICON_SRC).convert("RGBA")
    print(f"Building Vibe Plugins co-brand mark ({raster.slug})…")
    for size, name in BANNERS:
        build_banner(size, icon, out / name, raster)
    build_square(1024, icon, out / "vibe-plugins-square-1024.png", raster)


def main(argv: list[str]) -> int:
    slug, out_dir, rest = rt.parse_args(argv)
    if rest:
        print(f"usage: export-vibe-plugins-logo.py [--theme <slug>] [--out <dir>]  (unknown: {rest})", file=sys.stderr)
        return 2
    build_all(rt.load(slug), out=out_dir or OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
