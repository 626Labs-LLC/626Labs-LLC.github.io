"""Thumbnail generation for the 'Also from the lab' shelf.

Three jobs:
  1. Crop white borders (top/bottom) off Beat That Shook.jpg.
  2. Extract first frame of level_3 Este.gif as a static L.A.D.D.E.R. thumbnail.
  3. Compose a Writer's Studio logo = 626 Labs icon + "Writer's Studio" in cursive.
"""
from PIL import Image, ImageDraw, ImageFont
import os

HUB = r"c:/Users/estev/Projects/626labs-hub"
ASSETS = os.path.join(HUB, "assets")


# ── 1. Crop white from book cover ─────────────────────────────────────
def crop_white_borders(src_path, out_path, threshold=240):
    im = Image.open(src_path).convert("RGB")
    w, h = im.size
    px = im.load()

    def is_white_row(y):
        whites = sum(1 for x in range(w) if min(px[x, y]) > threshold)
        return whites / w > 0.85

    top = 0
    while top < h and is_white_row(top):
        top += 1
    bot = h - 1
    while bot > top and is_white_row(bot):
        bot -= 1

    cropped = im.crop((0, top, w, bot + 1))
    cropped.save(out_path, quality=92)
    print(f"book cover: {(w,h)} -> cropped top={top} bot={h-1-bot} -> {cropped.size}")


# ── 2. Extract first frame of gif ─────────────────────────────────────
def first_frame(src_path, out_path, max_side=1280):
    im = Image.open(src_path)
    im.seek(0)
    frame = im.convert("RGB")
    if max(frame.size) > max_side:
        ratio = max_side / max(frame.size)
        new = (int(frame.size[0] * ratio), int(frame.size[1] * ratio))
        frame = frame.resize(new, Image.LANCZOS)
    frame.save(out_path, quality=88)
    print(f"gif frame: saved {out_path} {frame.size}")


# ── 3. Writer's Studio logo ───────────────────────────────────────────
def writer_studio_logo(icon_path, out_path):
    """16:9 thumbnail: 626 Labs icon + cursive "Writer's Studio" on navy."""
    W, H = 1280, 720
    canvas = Image.new("RGB", (W, H), (15, 24, 43))  # navy-deep

    # Radial-ish gradient feel via simple vignette layer
    vignette = Image.new("RGB", (W, H), (26, 37, 64))  # navy-hi
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    for r in range(0, max(W, H), 4):
        alpha = max(0, 120 - r // 6)
        md.ellipse(
            [W / 2 - r, H / 2 - r, W / 2 + r, H / 2 + r],
            fill=alpha,
        )
    canvas.paste(vignette, (0, 0), mask)

    # Paste icon on left
    icon = Image.open(icon_path).convert("RGBA")
    icon_h = 480
    ratio = icon_h / icon.size[1]
    icon = icon.resize((int(icon.size[0] * ratio), icon_h), Image.LANCZOS)
    icon_x = 110
    icon_y = (H - icon.size[1]) // 2
    canvas.paste(icon, (icon_x, icon_y), icon)

    # Cursive text on right
    draw = ImageDraw.Draw(canvas)
    font_candidates = [
        r"c:/Windows/Fonts/BRUSHSCI.TTF",
        r"c:/Windows/Fonts/Gabriola.ttf",
        r"c:/Windows/Fonts/Inkfree.ttf",
        r"c:/Windows/Fonts/KUNSTLER.TTF",
    ]
    font_path = next((p for p in font_candidates if os.path.exists(p)), None)
    if not font_path:
        raise RuntimeError("no cursive font found")
    print(f"using font: {font_path}")

    # Two-line layout: "Writer's" then "Studio" — cursive pairs well stacked
    font_main = ImageFont.truetype(font_path, 170)
    text_x = icon_x + icon.size[0] + 60
    # top line
    draw.text((text_x, 170), "Writer's", fill=(232, 242, 255), font=font_main)
    draw.text((text_x + 60, 360), "Studio", fill=(122, 224, 245), font=font_main)

    # Small 626 Labs subline at bottom-right
    sub_font_candidates = [
        r"c:/Windows/Fonts/segoeuisl.ttf",
        r"c:/Windows/Fonts/segoeui.ttf",
        r"c:/Windows/Fonts/arial.ttf",
    ]
    sub_font_path = next((p for p in sub_font_candidates if os.path.exists(p)), None)
    sub_font = ImageFont.truetype(sub_font_path, 24)
    draw.text(
        (W - 220, H - 60),
        "a 626 Labs studio",
        fill=(106, 132, 158),
        font=sub_font,
    )

    canvas.save(out_path, quality=92)
    print(f"writer-studio logo: saved {out_path} {canvas.size}")


if __name__ == "__main__":
    crop_white_borders(
        os.path.join(ASSETS, "Beat That Shook.jpg"),
        os.path.join(ASSETS, "thumb-beat-that-shook.jpg"),
    )
    first_frame(
        os.path.join(ASSETS, "level_3 Este.gif"),
        os.path.join(ASSETS, "thumb-replit-cert.jpg"),
    )
    writer_studio_logo(
        os.path.join(ASSETS, "icon-626.png"),
        os.path.join(ASSETS, "thumb-writer-studio.jpg"),
    )
