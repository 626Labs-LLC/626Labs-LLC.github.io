"""Export 626 Labs brand assets — transparent icon + banner.

Inputs:
  assets/icon-626.png            — 256x256 baked-on-navy icon
  assets/logo-portrait-720x1080.png — higher-res icon + wordmark on navy
  fonts/SpaceGrotesk-Bold.ttf, fonts/Inter-Italic.ttf, etc.

Outputs (under assets/brand/):
  icon-transparent-256.png   — color-keyed transparent icon
  icon-transparent-512.png   — same, upscaled (Lanczos)
  icon-transparent-1024.png  — same, upscaled
  banner-1500x500.png        — Twitter / X header
  banner-1280x640.png        — GitHub repo header / generic OG-ish
  banner-1200x630.png        — OG image / generic social
"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
OUT = ASSETS / "brand"
FONTS = ROOT / "fonts"

OUT.mkdir(parents=True, exist_ok=True)

BG_NAVY = np.array([25, 46, 69], dtype=np.int16)  # the field color we strip
KEY_LO = 25   # within this distance → fully transparent
KEY_HI = 70   # beyond this distance → fully opaque
                # in between → ramped alpha (anti-aliased edge recovery)

CYAN = (23, 212, 250)
MAGENTA = (242, 47, 137)
NAVY = (15, 31, 49)
INK = (231, 237, 245)
DIM = (138, 153, 174)


def color_key(img: Image.Image, bg=BG_NAVY, lo=KEY_LO, hi=KEY_HI) -> Image.Image:
    """Soft color-key: bg pixels → transparent, edges ramp."""
    arr = np.array(img.convert("RGBA"))
    rgb = arr[..., :3].astype(np.int16)
    dist = np.sqrt(((rgb - bg) ** 2).sum(axis=-1))
    alpha = np.clip((dist - lo) / (hi - lo) * 255, 0, 255).astype(np.uint8)
    arr[..., 3] = np.minimum(arr[..., 3], alpha)
    return Image.fromarray(arr, "RGBA")


def autocrop_alpha(img: Image.Image, margin: int = 4) -> Image.Image:
    """Trim transparent edges, leaving `margin` px of padding."""
    bbox = img.getbbox()
    if not bbox:
        return img
    l, t, r, b = bbox
    l = max(0, l - margin); t = max(0, t - margin)
    r = min(img.width, r + margin); b = min(img.height, b + margin)
    return img.crop((l, t, r, b))


def square_pad(img: Image.Image) -> Image.Image:
    """Pad to a square with transparent fill, image centered."""
    side = max(img.width, img.height)
    out = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    out.paste(img, ((side - img.width) // 2, (side - img.height) // 2), img)
    return out


def find_icon_bottom(keyed: Image.Image, gap_rows: int = 8) -> int:
    """Locate the y where the icon ends and the wordmark begins.

    The portrait has icon ↑, blank gap, wordmark ↓. We scan rows of the
    alpha channel from the top and stop at the first contiguous band of
    `gap_rows` empty rows — that's the boundary between the icon and the
    wordmark/slogan below.
    """
    arr = np.array(keyed)
    alpha = arr[..., 3]
    row_has_content = (alpha > 8).any(axis=1)
    in_content = False
    empty_run = 0
    last_content_y = 0
    for y, has in enumerate(row_has_content):
        if has:
            if not in_content and y > 50:
                # Skipped top blank — entered content. Reset empty counter.
                pass
            in_content = True
            empty_run = 0
            last_content_y = y
        else:
            if in_content:
                empty_run += 1
                if empty_run >= gap_rows:
                    return last_content_y + 1
    return keyed.height


def build_transparent_icon():
    """Use the higher-res portrait as the source — cleaner edges than 256."""
    portrait = Image.open(ASSETS / "logo-portrait-720x1080.png").convert("RGBA")
    keyed_full = color_key(portrait)
    # Find the gap between icon and wordmark, crop just above it.
    icon_bottom_y = find_icon_bottom(keyed_full, gap_rows=10)
    icon_region = keyed_full.crop((0, 0, keyed_full.width, icon_bottom_y))
    cropped = autocrop_alpha(icon_region, margin=12)
    squared = square_pad(cropped)

    # Save at 256, 512, 1024 (downsample from native, upsample only if needed).
    native = squared.width
    for size in (1024, 512, 256):
        if size <= native:
            resized = squared.resize((size, size), Image.LANCZOS)
        else:
            resized = squared.resize((size, size), Image.LANCZOS)
        resized.save(OUT / f"icon-transparent-{size}.png", optimize=True)
        print(f"  wrote {OUT / f'icon-transparent-{size}.png'}  ({size}x{size})")
    return squared  # full-res transparent icon for compositing into banners


def gradient_h(width: int, height: int, c1, c2) -> Image.Image:
    """Horizontal cyan→magenta gradient strip."""
    grad = Image.new("RGB", (width, height))
    pixels = []
    for x in range(width):
        t = x / max(1, width - 1)
        r = int(c1[0] * (1 - t) + c2[0] * t)
        g = int(c1[1] * (1 - t) + c2[1] * t)
        b = int(c1[2] * (1 - t) + c2[2] * t)
        pixels.append((r, g, b))
    for y in range(height):
        for x in range(width):
            grad.putpixel((x, y), pixels[x])
    return grad


def radial_glow(width: int, height: int, cx: float, cy: float, color, max_alpha: int, radius: float) -> Image.Image:
    """Soft radial alpha falloff at (cx,cy) — coords as fractions of size."""
    layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
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


def build_banner(size: tuple[int, int], icon: Image.Image, out_path: Path):
    """Compose a brand banner.

    Layout: navy bg + radial glows, transparent icon left, wordmark + tagline
    right of the icon, hairline cyan→magenta gradient under the wordmark.
    """
    W, H = size
    canvas = Image.new("RGBA", (W, H), NAVY + (255,))

    # Brand mood: cyan glow top-left, magenta glow bottom-right.
    canvas.alpha_composite(radial_glow(W, H, 0.18, 0.30, CYAN, 80, 0.50))
    canvas.alpha_composite(radial_glow(W, H, 0.85, 0.75, MAGENTA, 70, 0.55))

    # Icon — sized to ~70% of banner height, padded inside.
    icon_target_h = int(H * 0.70)
    scale = icon_target_h / icon.height
    icon_w = int(icon.width * scale)
    icon_h = icon_target_h
    icon_resized = icon.resize((icon_w, icon_h), Image.LANCZOS)

    # Position icon: left padding ~ 0.06 * W, vertically centered.
    icon_x = int(W * 0.06)
    icon_y = (H - icon_h) // 2
    canvas.alpha_composite(icon_resized, dest=(icon_x, icon_y))

    # Text block right of icon.
    text_x = icon_x + icon_w + int(W * 0.045)
    text_avail_w = W - text_x - int(W * 0.06)  # right padding

    # Wordmark size: scale Space Grotesk Bold so "626Labs LLC" fits ~88% of avail width,
    # but cap at H * 0.26 so the banner doesn't look top-heavy on tall canvases.
    full_word = "626Labs LLC"
    target_word_w = int(text_avail_w * 0.88)
    word_size = int(H * 0.26)
    while word_size > 24:
        f = ImageFont.truetype(str(FONTS / "SpaceGrotesk-Variable.ttf"), word_size)
        f.set_variation_by_axes([700])
        bbox = f.getbbox(full_word)
        if (bbox[2] - bbox[0]) <= target_word_w:
            sg_bold = f
            break
        word_size -= 2
    else:
        sg_bold = ImageFont.truetype(str(FONTS / "SpaceGrotesk-Variable.ttf"), 24)
        sg_bold.set_variation_by_axes([700])

    # Tagline + kicker scale off wordmark size for proportional rhythm.
    tag_size = max(14, int(word_size * 0.36))
    inter_italic = ImageFont.truetype(str(FONTS / "Inter-Italic-Variable.ttf"), tag_size)
    inter_italic.set_variation_by_axes([14, 400])
    kicker_size = max(11, int(word_size * 0.18))
    jb_mono = ImageFont.truetype(str(FONTS / "JetBrainsMono-Regular.ttf"), kicker_size)

    draw = ImageDraw.Draw(canvas)

    # Wordmark: "626" in cyan, "Labs LLC" in white. Measure widths.
    cyan_part = "626"
    white_part = "Labs LLC"
    bbox_c = draw.textbbox((0, 0), cyan_part, font=sg_bold)
    cyan_w = bbox_c[2] - bbox_c[0]
    bbox_w_white = draw.textbbox((0, 0), white_part, font=sg_bold)
    word_w = cyan_w + (bbox_w_white[2] - bbox_w_white[0])

    # Vertically center the (wordmark + divider + tagline) stack within the canvas.
    line_h_div = max(2, int(word_size * 0.025))
    pad_to_div = int(word_size * 0.18)
    pad_div_to_tag = int(word_size * 0.10)
    block_h = word_size + pad_to_div + line_h_div + pad_div_to_tag + tag_size
    word_top = (H - block_h) // 2

    draw.text((text_x, word_top), cyan_part, font=sg_bold, fill=CYAN + (255,))
    draw.text((text_x + cyan_w, word_top), white_part, font=sg_bold, fill=INK + (255,))

    # Hairline cyan→magenta divider just under the wordmark.
    line_y = word_top + word_size + pad_to_div
    grad_strip = gradient_h(word_w, line_h_div, CYAN, MAGENTA).convert("RGBA")
    canvas.alpha_composite(grad_strip, dest=(text_x, line_y))

    # Tagline: "Imagine Something Else." in italic Inter.
    tagline = "Imagine Something Else."
    tag_y = line_y + line_h_div + pad_div_to_tag
    draw.text((text_x, tag_y), tagline, font=inter_italic, fill=INK + (255,))

    # Mono kicker top-right: "626LABS · FORT WORTH" with cyan dot.
    kicker = "626LABS · FORT WORTH · TX"
    kbbox = draw.textbbox((0, 0), kicker, font=jb_mono)
    kw = kbbox[2] - kbbox[0]
    kx = W - kw - int(W * 0.03)
    ky = int(H * 0.07)
    draw.text((kx, ky), kicker, font=jb_mono, fill=DIM + (255,))

    # Save flat (RGB) for max compatibility on social platforms.
    canvas.convert("RGB").save(out_path, "PNG", optimize=True)
    print(f"  wrote {out_path}  ({W}x{H})")


def main():
    print("Building transparent icon…")
    icon = build_transparent_icon()

    print("\nBuilding banners…")
    for size, name in [
        ((1500, 500), "banner-1500x500.png"),       # X / Twitter header
        ((1280, 640), "banner-1280x640.png"),       # GitHub repo header
        ((1200, 630), "banner-1200x630.png"),       # OG / generic social
    ]:
        build_banner(size, icon, OUT / name)


if __name__ == "__main__":
    main()
