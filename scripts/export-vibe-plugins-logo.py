"""Export a Vibe Plugins co-brand logo — 626 Labs × Claude Code.

The plugin family belongs to 626 Labs but lives inside Claude Code, so
the mark needs both identities legible at a glance:

  - 626 Labs hex / brain / circuit icon on the left (the lab)
  - "Vibe Plugins" wordmark, cyan + white, dominant
  - Cyan → magenta hairline divider (the brand swoosh)
  - "for Claude Code" subtitle in cyan mono
  - Anthropic-style sparkle (4-pointed) anchoring the right edge,
    rendered in the brand's cyan→magenta gradient so the Claude
    attribution still reads in 626 Labs voice

Outputs:
  assets/brand/vibe-plugins-banner-1500x500.png  — wide banner for
    READMEs, social cards, marketplace listings
  assets/brand/vibe-plugins-banner-3000x1000.png — 2x for HiDPI
  assets/brand/vibe-plugins-square-1024.png      — square version,
    works as a publication / repo avatar
"""
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
OUT = ASSETS / "brand"
FONTS = ROOT / "fonts"

OUT.mkdir(parents=True, exist_ok=True)

CYAN = (23, 212, 250)
MAGENTA = (242, 47, 137)
NAVY = (15, 31, 49)
INK = (231, 237, 245)
DIM = (138, 153, 174)


def gradient_h(width: int, height: int, c1, c2) -> Image.Image:
    yy, xx = np.indices((height, width))
    t = xx / max(1, width - 1)
    r = (c1[0] * (1 - t) + c2[0] * t).astype(np.uint8)
    g = (c1[1] * (1 - t) + c2[1] * t).astype(np.uint8)
    b = (c1[2] * (1 - t) + c2[2] * t).astype(np.uint8)
    arr = np.stack([r, g, b], axis=-1)
    return Image.fromarray(arr, "RGB")


def radial_glow(width: int, height: int, cx: float, cy: float,
                color, max_alpha: int, radius: float) -> Image.Image:
    yy, xx = np.indices((height, width))
    dx = xx - cx * width
    dy = yy - cy * height
    dist = np.sqrt(dx * dx + dy * dy)
    falloff = np.clip(1 - dist / (radius * max(width, height)), 0, 1) ** 2
    arr = np.zeros((height, width, 4), dtype=np.uint8)
    arr[..., 0] = color[0]
    arr[..., 1] = color[1]
    arr[..., 2] = color[2]
    arr[..., 3] = (falloff * max_alpha).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


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


def build_banner(size: tuple[int, int], icon: Image.Image, out_path: Path) -> None:
    W, H = size
    canvas = Image.new("RGBA", (W, H), NAVY + (255,))

    canvas.alpha_composite(radial_glow(W, H, 0.16, 0.28, CYAN, 84, 0.52))
    canvas.alpha_composite(radial_glow(W, H, 0.86, 0.78, MAGENTA, 76, 0.55))

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

    # Subtitle "for Claude Code · 626 Labs" in mono cyan.
    sub_size = max(13, int(word_size * 0.24))
    jb_mono = ImageFont.truetype(str(FONTS / "JetBrainsMono-Regular.ttf"), sub_size)
    subtitle = "for Claude Code  ·  626 Labs"

    line_h_div = max(2, int(word_size * 0.025))
    pad_to_div = int(word_size * 0.18)
    pad_div_to_sub = int(word_size * 0.20)
    block_h = word_size + pad_to_div + line_h_div + pad_div_to_sub + sub_size
    top = (H - block_h) // 2

    draw.text((text_x, top), cyan_part, font=sg_bold, fill=CYAN + (255,))
    draw.text((text_x + cyan_w, top), white_part, font=sg_bold, fill=INK + (255,))

    div_y = top + word_size + pad_to_div
    grad = gradient_h(word_w, line_h_div, CYAN, MAGENTA).convert("RGBA")
    canvas.alpha_composite(grad, dest=(text_x, div_y))

    sub_y = div_y + line_h_div + pad_div_to_sub
    draw.text((text_x, sub_y), subtitle, font=jb_mono, fill=DIM + (255,))

    canvas.convert("RGB").save(out_path, "PNG", optimize=True)
    print(f"  wrote {out_path}  ({W}x{H})")


def build_square(size: int, icon: Image.Image, out_path: Path) -> None:
    """Square variant — icon top, sparkle bottom-right, wordmark stacked.

    Works as a GitHub repo avatar or marketplace tile.
    """
    W = H = size
    canvas = Image.new("RGBA", (W, H), NAVY + (255,))

    canvas.alpha_composite(radial_glow(W, H, 0.18, 0.22, CYAN, 96, 0.60))
    canvas.alpha_composite(radial_glow(W, H, 0.82, 0.82, MAGENTA, 84, 0.60))

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
    draw.text((word_x + cyan_w, word_y), white_part, font=sg_bold, fill=INK + (255,))

    # Hairline divider, centered.
    div_h = max(2, int(word_size * 0.04))
    grad = gradient_h(word_w, div_h, CYAN, MAGENTA).convert("RGBA")
    div_y = word_y + word_size + int(word_size * 0.18)
    canvas.alpha_composite(grad, dest=(word_x, div_y))

    # Subtitle, centered.
    sub_size = max(14, int(word_size * 0.30))
    jb_mono = ImageFont.truetype(str(FONTS / "JetBrainsMono-Regular.ttf"), sub_size)
    subtitle = "for Claude Code  ·  626 Labs"
    sbbox = draw.textbbox((0, 0), subtitle, font=jb_mono)
    sub_x = (W - (sbbox[2] - sbbox[0])) // 2
    sub_y = div_y + div_h + int(word_size * 0.20)
    draw.text((sub_x, sub_y), subtitle, font=jb_mono, fill=DIM + (255,))

    canvas.convert("RGB").save(out_path, "PNG", optimize=True)
    print(f"  wrote {out_path}  ({W}x{H})")


def main() -> None:
    icon_src = OUT / "icon-transparent-1024.png"
    if not icon_src.exists():
        raise SystemExit(f"missing {icon_src} — run scripts/export-brand.py first")
    icon = Image.open(icon_src).convert("RGBA")
    print("Building Vibe Plugins co-brand mark…")
    for size, name in [
        ((1500, 500),  "vibe-plugins-banner-1500x500.png"),    # 3:1
        ((3000, 1000), "vibe-plugins-banner-3000x1000.png"),   # 3:1 @ 2x
        ((1500, 600),  "vibe-plugins-banner-1500x600.png"),    # 5:2 — X Articles
        ((3000, 1200), "vibe-plugins-banner-3000x1200.png"),   # 5:2 @ 2x
    ]:
        build_banner(size, icon, OUT / name)
    build_square(1024, icon, OUT / "vibe-plugins-square-1024.png")


if __name__ == "__main__":
    main()
