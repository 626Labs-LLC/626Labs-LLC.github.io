#!/usr/bin/env python3
"""Generate the admin favicon — gradient rounded square with "626" text.

Mirrors the small brand tile in the admin's TopBar so the browser tab
reads as the admin without looking like the main 626labs.dev favicon.
Matches the design-system tokens: cyan #17d4fa → magenta #f22f89 on navy text.
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

HUB = Path(__file__).resolve().parent.parent
OUT = HUB / "assets" / "favicon-admin.png"

SIZE = 512
RADIUS = int(SIZE * 0.22)

# Brand endpoints (match colors_and_type.css tokens)
CYAN = (23, 212, 250)
MAGENTA = (242, 47, 137)
TEXT_NAVY = (7, 9, 13)  # admin's A.bg

# Build diagonal gradient top-left cyan → bottom-right magenta
canvas = Image.new("RGBA", (SIZE, SIZE))
px = canvas.load()
for y in range(SIZE):
    for x in range(SIZE):
        t = (x + y) / (2 * SIZE - 2)
        r = int(CYAN[0] + (MAGENTA[0] - CYAN[0]) * t)
        g = int(CYAN[1] + (MAGENTA[1] - CYAN[1]) * t)
        b = int(CYAN[2] + (MAGENTA[2] - CYAN[2]) * t)
        px[x, y] = (r, g, b, 255)

# Pick a mono font — prefer JetBrains Mono if the system has it,
# otherwise fall back to Consolas Bold which Windows always ships.
FONT_CANDIDATES = [
    r"C:/Windows/Fonts/JetBrainsMono-Bold.ttf",
    r"C:/Windows/Fonts/JetBrainsMono-ExtraBold.ttf",
    r"C:/Windows/Fonts/consolab.ttf",
    r"C:/Windows/Fonts/CascadiaMono-Bold.ttf",
    r"C:/Windows/Fonts/arialbd.ttf",
]
font_path = next((p for p in FONT_CANDIDATES if Path(p).exists()), None)
if not font_path:
    raise RuntimeError("no suitable bold mono font found")
print(f"font: {font_path}")

# "626" centered and filling the tile
text = "626"
# Size the font so the glyphs span roughly 60% of the tile width.
font_size = int(SIZE * 0.48)
font = ImageFont.truetype(font_path, font_size)

draw = ImageDraw.Draw(canvas)
bbox = draw.textbbox((0, 0), text, font=font)
tw = bbox[2] - bbox[0]
th = bbox[3] - bbox[1]
tx = (SIZE - tw) // 2 - bbox[0]
ty = (SIZE - th) // 2 - bbox[1]
draw.text((tx, ty), text, fill=TEXT_NAVY + (255,), font=font)

# Round the corners
mask = Image.new("L", (SIZE, SIZE), 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, SIZE - 1, SIZE - 1], radius=RADIUS, fill=255)

result = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
result.paste(canvas, (0, 0), mask)

OUT.parent.mkdir(exist_ok=True)
result.save(OUT)
print(f"wrote: {OUT.relative_to(HUB)} ({OUT.stat().st_size} bytes)")
