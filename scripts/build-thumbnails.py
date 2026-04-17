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
    """16:9 thumbnail: the full 626 Labs logo in a square box + cursive
    "Writer's Studio" to its right, on navy."""
    W, H = 1280, 720
    canvas = Image.new("RGB", (W, H), (15, 24, 43))  # navy-deep

    # Clean rounded square box on the left, icon centered inside
    box_size = 520
    box_x = 90
    box_y = (H - box_size) // 2
    box_layer = Image.new("RGB", (box_size, box_size), (26, 37, 64))  # navy-mid
    box_mask = Image.new("L", (box_size, box_size), 0)
    ImageDraw.Draw(box_mask).rounded_rectangle(
        [0, 0, box_size - 1, box_size - 1], radius=28, fill=255
    )
    canvas.paste(box_layer, (box_x, box_y), box_mask)

    # Icon — center inside the box with equal padding
    icon = Image.open(icon_path).convert("RGBA")
    inner_pad = 40
    inner = box_size - 2 * inner_pad
    # Preserve aspect
    iw, ih = icon.size
    s = min(inner / iw, inner / ih)
    new = (int(iw * s), int(ih * s))
    icon = icon.resize(new, Image.LANCZOS)
    ix = box_x + (box_size - new[0]) // 2
    iy = box_y + (box_size - new[1]) // 2
    canvas.paste(icon, (ix, iy), icon)

    # Cursive text on right
    draw = ImageDraw.Draw(canvas)
    font_path = r"c:/Windows/Fonts/BRUSHSCI.TTF"
    print(f"using font: {font_path}")

    font_main = ImageFont.truetype(font_path, 180)
    text_x = box_x + box_size + 70
    draw.text((text_x, 160), "Writer's", fill=(232, 242, 255), font=font_main)
    draw.text((text_x + 70, 370), "Studio", fill=(122, 224, 245), font=font_main)

    sub_font = ImageFont.truetype(r"c:/Windows/Fonts/segoeui.ttf", 24)
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
