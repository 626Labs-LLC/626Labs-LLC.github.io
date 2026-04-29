"""Export a 626 Labs *Publishing* header for Medium.

Sibling to scripts/export-brand.py — same visual primitives (navy field,
radial cyan + magenta glows, transparent icon left, cyan→magenta hairline
divider). Different wordmark: this one says "626Labs Publishing" instead
of the LLC banner's "626Labs LLC", so the publishing imprint reads as a
Medium-native brand without colliding with the corporate-side banner.

Outputs:
  assets/brand/medium-header-1500x500.png  — primary, matches existing
                                              banner shape; works for
                                              Medium publication header
                                              and story preview slots
  assets/brand/medium-header-3000x1000.png — 2x for HiDPI / Medium's
                                              big-display surfaces
"""
from pathlib import Path
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
    """Horizontal cyan→magenta gradient strip."""
    yy, xx = np.indices((height, width))
    t = xx / max(1, width - 1)
    r = (c1[0] * (1 - t) + c2[0] * t).astype(np.uint8)
    g = (c1[1] * (1 - t) + c2[1] * t).astype(np.uint8)
    b = (c1[2] * (1 - t) + c2[2] * t).astype(np.uint8)
    arr = np.stack([r, g, b], axis=-1)
    return Image.fromarray(arr, "RGB")


def radial_glow(width: int, height: int, cx: float, cy: float,
                color, max_alpha: int, radius: float) -> Image.Image:
    """Soft radial alpha falloff at (cx,cy) — coords as fractions of size."""
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


def build_header(size: tuple[int, int], icon: Image.Image, out_path: Path) -> None:
    W, H = size
    canvas = Image.new("RGBA", (W, H), NAVY + (255,))

    # Atmospheric glows: cyan top-left, magenta bottom-right.
    canvas.alpha_composite(radial_glow(W, H, 0.16, 0.28, CYAN, 84, 0.52))
    canvas.alpha_composite(radial_glow(W, H, 0.86, 0.78, MAGENTA, 76, 0.55))

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

    # Wordmark — "626Labs" in cyan + white; "Publishing" gets its own line as
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
    jb_mono = ImageFont.truetype(str(FONTS / "JetBrainsMono-Regular.ttf"), sub_size)
    publishing_text = "P U B L I S H I N G"  # manual letter-spacing for the mono face

    # Tagline — italic Inter, smaller again, dim white.
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
    draw.text((text_x + cyan_w, top), white_part, font=sg_bold, fill=INK + (255,))

    # Cyan→magenta hairline divider.
    div_y = top + word_size + pad_to_div
    grad = gradient_h(word_w, line_h_div, CYAN, MAGENTA).convert("RGBA")
    canvas.alpha_composite(grad, dest=(text_x, div_y))

    # PUBLISHING subtitle.
    sub_y = div_y + line_h_div + pad_div_to_sub
    draw.text((text_x, sub_y), publishing_text, font=jb_mono, fill=CYAN + (255,))

    # Tagline.
    tag_y = sub_y + sub_size + pad_sub_to_tag
    draw.text((text_x, tag_y), tagline, font=inter_italic, fill=DIM + (255,))

    # Subtle top-right kicker — keeps Medium-page feel anchored.
    kicker_size = max(11, int(H * 0.030))
    kicker_font = ImageFont.truetype(str(FONTS / "JetBrainsMono-Regular.ttf"), kicker_size)
    kicker_text = "ESSAYS  ·  NOTES  ·  THESES"
    kbbox = draw.textbbox((0, 0), kicker_text, font=kicker_font)
    kw = kbbox[2] - kbbox[0]
    draw.text((W - kw - int(W * 0.035), int(H * 0.075)), kicker_text,
              font=kicker_font, fill=DIM + (255,))

    canvas.convert("RGB").save(out_path, "PNG", optimize=True)
    print(f"  wrote {out_path}  ({W}x{H})")


def main() -> None:
    icon_src = OUT / "icon-transparent-1024.png"
    if not icon_src.exists():
        raise SystemExit(
            f"missing {icon_src} — run scripts/export-brand.py first"
        )
    icon = Image.open(icon_src).convert("RGBA")
    print("Building Medium publishing headers…")
    for size, name in [
        ((1500, 500),  "medium-header-1500x500.png"),         # 3:1 — Twitter classic / OG
        ((3000, 1000), "medium-header-3000x1000.png"),        # 3:1 @ 2x
        ((1500, 600),  "medium-header-1500x600.png"),         # 5:2 — X Articles
        ((3000, 1200), "medium-header-3000x1200.png"),        # 5:2 @ 2x
        ((1280, 640),  "medium-header-1280x640.png"),         # 2:1 — GitHub social preview
        ((2560, 1280), "medium-header-2560x1280.png"),        # 2:1 @ 2x
    ]:
        build_header(size, icon, OUT / name)


if __name__ == "__main__":
    main()
