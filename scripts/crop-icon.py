"""Generate an icon-only 626 Labs mark from logo.png.

Detects the text band by finding the low-density horizontal gap
below the hexagon mark, crops to a centered square above it, and
exports favicon + icon assets.
"""
from PIL import Image
import os

HUB = r"c:/Users/estev/Projects/626labs-hub"
ASSETS = os.path.join(HUB, "assets")
SRC = os.path.join(HUB, "logo.png")

src = Image.open(SRC).convert("RGB")
w, h = src.size
print(f"source: {w}x{h}")

gray = src.convert("L")
gp = gray.load()

# Foreground density per row (pixels brighter than navy background)
row_density = []
for y in range(h):
    c = 0
    for x in range(w):
        if gp[x, y] > 80:
            c += 1
    row_density.append(c)

# Find the lowest-density row band between 45% and 78% of height —
# that's the gap between the hexagon and the "626Labs LLC" text.
mid_start = int(h * 0.45)
mid_end = int(h * 0.78)
best_y = mid_start
best_score = float("inf")
for y in range(mid_start, mid_end):
    window = row_density[max(0, y - 8):y + 9]
    avg = sum(window) / len(window)
    if avg < best_score:
        best_score = avg
        best_y = y
print(f"gap row: y={best_y}  avg density: {best_score:.1f}")

# Crop square from the top, using the gap as the bottom edge.
crop_bottom = best_y
crop_size = crop_bottom
left = (w - crop_size) // 2
right = left + crop_size
mark = src.crop((left, 0, right, crop_bottom))
print(f"cropped: {mark.size}")

# Exports
mark.resize((512, 512), Image.LANCZOS).save(os.path.join(HUB, "favicon-626.png"))
mark.resize((256, 256), Image.LANCZOS).save(os.path.join(ASSETS, "icon-626.png"))
mark.resize((64, 64), Image.LANCZOS).save(os.path.join(ASSETS, "icon-626-64.png"))
print("wrote: favicon-626.png, assets/icon-626.png, assets/icon-626-64.png")
