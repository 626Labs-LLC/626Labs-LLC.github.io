#!/usr/bin/env python3
"""Export per-app banners + squares for 626 Labs native apps.

Sibling to scripts/export-plugin-icons.py — same banner shape (glyph card
on left, spaced-caps name + tagline center, Claude sparkle + lockup
right) but the "glyph" slot loads the app's existing icon from the
sibling source repo under C:/Users/estev/Projects instead of being
drawn procedurally.

This is the right move for apps that already have polished, on-brand
icons: Sanduhr (hourglass with cyan/magenta sand), RTClickPng (PNG
document with magenta corner fold + cursor). Both render at the icon
size with no extra glyph styling needed.

For apps without a good icon (RBX15), we fall back to the 626 Labs
transparent hex from assets/brand/icon-transparent-1024.png.

Outputs (under assets/brand/apps/):
  <id>-banner-1500x500.png   3:1 — Twitter classic / OG / README banner
  <id>-banner-1280x640.png   2:1 — GitHub social preview
  <id>-square-1024.png       1:1 — repo avatar / marketplace tile
"""
from pathlib import Path

import math
from PIL import Image, ImageDraw, ImageFont
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
BRAND = ASSETS / "brand"
OUT = BRAND / "apps"
FONTS = ROOT / "fonts"
ANTHROPIC = ASSETS / "anthropic"
PROJECTS = Path(r"C:/Users/estev/Projects")

OUT.mkdir(parents=True, exist_ok=True)

NAVY = (15, 31, 49)
NAVY_DEEP = (10, 21, 36)
CYAN = (23, 212, 250)
MAGENTA = (242, 47, 137)
INK = (231, 237, 245)
DIM = (138, 153, 174)
DIM2 = (94, 107, 127)


# Each app: id, source-icon path (resolved from PROJECTS), display name,
# tagline, accent pair (primary glow, secondary glow). Tagline is the
# short marketing tagline used as the secondary line under the name.
APPS = [
    {
        "id": "sanduhr",
        # icon-512.png is RGBA (transparent corners). icon-1024-rgb.png is
        # RGB-only and would leave white corners on the navy banner.
        "icon_path": PROJECTS / "Sanduhr" / "docs" / "images" / "icon-512.png",
        "name": "SANDUHR",
        "tagline": "pace your Claude.ai usage",
        "primary": MAGENTA,    # the magenta sand below the pinch point
        "secondary": CYAN,     # the cyan sand above
    },
    {
        "id": "rtclickpng",
        "icon_path": PROJECTS / "RTClickPng" / "src" / "Package" / "Assets" / "Square300x300Logo.png",
        "name": "RIGHT CLICK PNG",
        "tagline": "convert any image to PNG, in File Explorer",
        "primary": CYAN,
        "secondary": MAGENTA,
    },
    {
        "id": "rbx15-shirt-pants",
        "icon_path": BRAND / "icon-transparent-1024.png",  # fallback to 626 Labs hex
        "name": "RBX15 MAKER",
        "tagline": "Roblox shirt and pants editor",
        "primary": MAGENTA,
        "secondary": CYAN,
    },
]


def radial_glow(width, height, cx, cy, color, max_alpha, radius):
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


def load_app_icon(path: Path, target_size: int) -> Image.Image:
    """Load an app's icon and resize to fit a square slot.

    Preserves the icon's existing transparency / background. Apps that
    ship their icon with the navy backdrop baked in (Sanduhr, RTClickPng)
    will render that baked-in card-style. Apps with transparent PNGs
    (the 626 Labs hex fallback for RBX15) will render glyph-only on
    the banner's navy.
    """
    img = Image.open(path).convert("RGBA")
    if img.size != (target_size, target_size):
        img = img.resize((target_size, target_size), Image.LANCZOS)
    return img


def load_claude_sparkle(target_h: int) -> Image.Image | None:
    src = ANTHROPIC / "claude-sparkle.png"
    if not src.exists():
        return None
    spk = Image.open(src).convert("RGBA")
    scale = target_h / spk.height
    return spk.resize((int(spk.width * scale), target_h), Image.LANCZOS)


def build_banner(app, out_path, size=(1500, 500)):
    """Render an app banner at the requested size.

    Layout values derive from H so a single function produces both the
    3:1 (1500x500) Twitter-classic banner and the 2:1 (1280x640) GitHub
    social-preview card.
    """
    W, H = size
    canvas = Image.new("RGBA", (W, H), NAVY + (255,))
    canvas.alpha_composite(radial_glow(W, H, 0.16, 0.28, app["primary"], 70, 0.50))
    canvas.alpha_composite(radial_glow(W, H, 0.86, 0.78, app["secondary"], 60, 0.55))

    # Icon card on the left — square tile sized to ~64% of banner height.
    # Slightly larger than plugin glyphs because app icons are full
    # branded marks, not abstract glyphs — they earn the pixels.
    card_side = int(H * 0.64)
    card_x = int(W * 0.05)
    card_y = (H - card_side) // 2

    # Load the app's icon at the card size and paste directly.
    icon = load_app_icon(app["icon_path"], card_side)

    # If the icon is fully opaque (Sanduhr-style with navy bg baked in),
    # add a subtle outer rounded-rect mask so it sits cleanly. If the
    # icon already has rounded corners (most app store icons do), the
    # mask is a near-no-op but still feathers any hard edge.
    canvas.alpha_composite(icon, dest=(card_x, card_y))

    # Text block
    text_x = card_x + card_side + int(W * 0.045)
    sparkle_target_h = max(40, int(H * 0.13))
    sparkle_w = sparkle_target_h + int(W * 0.04)
    text_avail_w = W - text_x - sparkle_w - int(W * 0.06)
    draw = ImageDraw.Draw(canvas)
    tag_font = ImageFont.truetype(str(FONTS / "JetBrainsMono-Regular.ttf"), max(14, int(H * 0.044)))

    # Spaced caps for the name; auto-fit if it would overflow.
    spaced = " ".join(app["name"])
    max_name = max(28, int(H * 0.112))
    name_size = max_name
    while name_size > 18:
        name_font = ImageFont.truetype(str(FONTS / "JetBrainsMono-Regular.ttf"), name_size)
        nb = draw.textbbox((0, 0), spaced, font=name_font)
        if (nb[2] - nb[0]) <= text_avail_w:
            break
        name_size -= 2
    name_bbox = draw.textbbox((0, 0), spaced, font=name_font)
    name_h = name_bbox[3] - name_bbox[1]

    tag_bbox = draw.textbbox((0, 0), app["tagline"], font=tag_font)
    tag_h = tag_bbox[3] - tag_bbox[1]

    gap = max(10, int(H * 0.036))
    block_h = name_h + gap + tag_h
    block_top = (H - block_h) // 2
    draw.text((text_x, block_top), spaced, font=name_font, fill=app["primary"] + (255,))
    draw.text((text_x, block_top + name_h + gap), app["tagline"], font=tag_font, fill=DIM + (255,))

    # 626 Labs lockup top-right (tiny mono)
    sub_font = ImageFont.truetype(str(FONTS / "JetBrainsMono-Regular.ttf"), max(11, int(H * 0.026)))
    lockup = "626 LABS  ·  native"
    lk_bbox = draw.textbbox((0, 0), lockup, font=sub_font)
    lk_w = lk_bbox[2] - lk_bbox[0]
    draw.text((W - lk_w - int(W * 0.04), int(H * 0.08)), lockup, font=sub_font, fill=DIM2 + (255,))

    # Claude sparkle bottom-right (small attribution — applies to Sanduhr +
    # any app that uses Claude. RBX15 + RTClickPng could go either way; we
    # include it on all for visual consistency since they all live under
    # 626 Labs's "Claude-adjacent" umbrella.)
    spk = load_claude_sparkle(sparkle_target_h)
    if spk is not None:
        canvas.alpha_composite(spk, dest=(W - spk.width - int(W * 0.04), H - spk.height - int(H * 0.10)))

    canvas.convert("RGB").save(out_path, "PNG", optimize=True)
    print(f"  banner  {app['id']:24s}  {size[0]}x{size[1]}  {out_path}")


def build_square(app, out_path, size=1024):
    """Render a square avatar — icon centered + name + tagline + lockup."""
    W = H = size
    canvas = Image.new("RGBA", (W, H), NAVY + (255,))
    canvas.alpha_composite(radial_glow(W, H, 0.18, 0.22, app["primary"], 96, 0.60))
    canvas.alpha_composite(radial_glow(W, H, 0.82, 0.82, app["secondary"], 84, 0.60))

    # Icon: large, centered upper-third, ~46% of canvas width
    icon_side = int(W * 0.46)
    icon = load_app_icon(app["icon_path"], icon_side)
    icon_x = (W - icon_side) // 2
    icon_y = int(H * 0.16)
    canvas.alpha_composite(icon, dest=(icon_x, icon_y))

    draw = ImageDraw.Draw(canvas)

    # Name — auto-fit
    spaced = " ".join(app["name"])
    text_avail_w = int(W * 0.86)
    name_size = int(H * 0.07)
    while name_size > 24:
        name_font = ImageFont.truetype(str(FONTS / "JetBrainsMono-Regular.ttf"), name_size)
        nb = draw.textbbox((0, 0), spaced, font=name_font)
        if (nb[2] - nb[0]) <= text_avail_w:
            break
        name_size -= 2
    name_bbox = draw.textbbox((0, 0), spaced, font=name_font)
    name_w = name_bbox[2] - name_bbox[0]
    name_h = name_bbox[3] - name_bbox[1]

    tag_font = ImageFont.truetype(str(FONTS / "JetBrainsMono-Regular.ttf"), int(H * 0.026))
    tag_bbox = draw.textbbox((0, 0), app["tagline"], font=tag_font)
    tag_w = tag_bbox[2] - tag_bbox[0]
    tag_h = tag_bbox[3] - tag_bbox[1]

    gap = int(H * 0.02)
    block_top = icon_y + icon_side + int(H * 0.06)
    draw.text(((W - name_w) // 2, block_top), spaced, font=name_font, fill=app["primary"] + (255,))
    draw.text(((W - tag_w) // 2, block_top + name_h + gap), app["tagline"], font=tag_font, fill=DIM + (255,))

    # Lockup at the bottom, lockup-style
    sub_font = ImageFont.truetype(str(FONTS / "JetBrainsMono-Regular.ttf"), int(H * 0.018))
    lockup = "626 LABS  ·  NATIVE"
    lk_bbox = draw.textbbox((0, 0), lockup, font=sub_font)
    lk_w = lk_bbox[2] - lk_bbox[0]
    draw.text(((W - lk_w) // 2, H - int(H * 0.06)), lockup, font=sub_font, fill=DIM2 + (255,))

    # Sparkle bottom-right
    spk = load_claude_sparkle(int(H * 0.07))
    if spk is not None:
        canvas.alpha_composite(spk, dest=(W - spk.width - int(W * 0.05), H - spk.height - int(H * 0.05)))

    canvas.convert("RGB").save(out_path, "PNG", optimize=True)
    print(f"  square  {app['id']:24s}  {size}x{size}  {out_path}")


def main():
    print(f"Building app icons -> {OUT}")
    for app in APPS:
        if not app["icon_path"].exists():
            print(f"  ! missing icon for {app['id']}: {app['icon_path']}")
            continue
        # 3:1 — Twitter classic / OG / README banner
        build_banner(app, OUT / f"{app['id']}-banner-1500x500.png", size=(1500, 500))
        # 2:1 — GitHub social preview (Settings → Social preview)
        build_banner(app, OUT / f"{app['id']}-banner-1280x640.png", size=(1280, 640))
        # 1:1 — repo avatar / marketplace tile
        build_square(app, OUT / f"{app['id']}-square-1024.png")


if __name__ == "__main__":
    main()
