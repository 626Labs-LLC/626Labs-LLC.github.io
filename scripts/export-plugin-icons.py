"""Export per-plugin banners + squares for the Vibe Plugins family.

Each plugin gets a unique line-art glyph that telegraphs its job, plus
a wide banner (for repo READMEs) and a square (for repo avatars). The
aesthetic is monochrome line-art on navy — same energy as Vibe
Cartographer's existing repo banner (a 3×3 connected-node graph).

Plugins:
  vibe-cartographer  → connected-node graph (the map)
  vibe-keystone      → keystone arch (load-bearing stone)
  vibe-doc           → lined document
  vibe-test          → bar chart with axis
  vibe-sec           → shield with center dot
  vibe-thesis        → page with footnote markers
  thesis-engine      → cog feeding a page

Outputs (under assets/brand/plugins/):
  <id>-banner-1500x500.png — repo README banner
  <id>-square-1024.png     — repo avatar / marketplace tile
"""
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
OUT = ASSETS / "brand" / "plugins"
FONTS = ROOT / "fonts"
CLAUDE_SPARKLE_SRC = ASSETS / "anthropic" / "claude-sparkle.png"

OUT.mkdir(parents=True, exist_ok=True)

CYAN = (23, 212, 250)
CYAN_DIM = (15, 168, 201)
MAGENTA = (242, 47, 137)
MAGENTA_DIM = (194, 31, 108)
NAVY = (15, 31, 49)
INK = (231, 237, 245)
DIM = (138, 153, 174)
DIM2 = (94, 107, 127)

# ──────────────────────────────────────────────────────────────────
# Backdrop primitives (shared with export-brand.py / -medium-header)
# ──────────────────────────────────────────────────────────────────

def gradient_h(width, height, c1, c2):
    yy, xx = np.indices((height, width))
    t = xx / max(1, width - 1)
    r = (c1[0] * (1 - t) + c2[0] * t).astype(np.uint8)
    g = (c1[1] * (1 - t) + c2[1] * t).astype(np.uint8)
    b = (c1[2] * (1 - t) + c2[2] * t).astype(np.uint8)
    return Image.fromarray(np.stack([r, g, b], axis=-1), "RGB")


def radial_glow(width, height, cx, cy, color, max_alpha, radius):
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


# ──────────────────────────────────────────────────────────────────
# Glyphs — each one renders into an N×N RGBA image, transparent bg.
# Stroke colors come from the plugin's accent (cyan or magenta).
# Glyphs are designed at 200×200 for crisp downsampling to any size.
# ──────────────────────────────────────────────────────────────────

GLYPH_SIZE = 200


def _new_glyph():
    return Image.new("RGBA", (GLYPH_SIZE, GLYPH_SIZE), (0, 0, 0, 0))


def glyph_cartographer(primary, secondary):
    """3×3 grid of nodes, each connected to its neighbors orthogonally and
    diagonally. Reads as 'graph' / 'map' / 'plot the course'."""
    img = _new_glyph()
    draw = ImageDraw.Draw(img)
    cx, cy = GLYPH_SIZE // 2, GLYPH_SIZE // 2
    spacing = 60
    nodes = [(cx + dx * spacing, cy + dy * spacing) for dy in (-1, 0, 1) for dx in (-1, 0, 1)]
    # Connect each node to all 8 neighbors (orthogonal + diagonal)
    for i, (x1, y1) in enumerate(nodes):
        for j, (x2, y2) in enumerate(nodes[i+1:], start=i+1):
            dx = abs((j % 3) - (i % 3))
            dy = abs((j // 3) - (i // 3))
            if dx <= 1 and dy <= 1 and (dx + dy) > 0:
                color = secondary if (dx == 1 and dy == 1) else primary
                draw.line([(x1, y1), (x2, y2)], fill=color + (255,), width=3)
    # Nodes on top
    for x, y in nodes:
        draw.ellipse([x-9, y-9, x+9, y+9], fill=NAVY + (255,), outline=primary + (255,), width=3)
    return img


def glyph_keystone(primary, secondary):
    """Architectural arch with the keystone (center wedge) emphasized."""
    img = _new_glyph()
    draw = ImageDraw.Draw(img)
    cx, cy = GLYPH_SIZE // 2, GLYPH_SIZE // 2 + 10
    # Arch stones — five trapezoid wedges fanned over the top
    # Define angles (degrees from horizontal) for stone separators
    arch_radius = 75
    arch_inner = 50
    n = 5
    angles = [180 - (i * 180 / n) for i in range(n + 1)]  # degrees
    rad = lambda a: math.radians(a)
    for i in range(n):
        a1, a2 = angles[i], angles[i+1]
        # Outer arc points + inner arc points, draw polygon
        outer1 = (cx + arch_radius * math.cos(rad(a1)), cy - arch_radius * math.sin(rad(a1)))
        outer2 = (cx + arch_radius * math.cos(rad(a2)), cy - arch_radius * math.sin(rad(a2)))
        inner1 = (cx + arch_inner * math.cos(rad(a1)), cy - arch_inner * math.sin(rad(a1)))
        inner2 = (cx + arch_inner * math.cos(rad(a2)), cy - arch_inner * math.sin(rad(a2)))
        is_keystone = (i == n // 2)
        color = secondary if is_keystone else primary
        draw.polygon([outer1, outer2, inner2, inner1], outline=color + (255,), width=3)
    # Foundation line under the arch
    draw.line([(cx - 80, cy + 8), (cx + 80, cy + 8)], fill=primary + (255,), width=3)
    return img


def glyph_doc(primary, secondary):
    """Document outline with horizontal text-lines + folded corner."""
    img = _new_glyph()
    draw = ImageDraw.Draw(img)
    L, T, R, B = 50, 30, 150, 170
    # Folded-corner detail: cut off top-right corner ~25px
    fold = 25
    page_pts = [(L, T), (R - fold, T), (R, T + fold), (R, B), (L, B)]
    draw.polygon(page_pts, outline=primary + (255,), width=3)
    # The folded corner triangle
    draw.line([(R - fold, T), (R - fold, T + fold), (R, T + fold)], fill=primary + (255,), width=3)
    # Text-lines — 4 horizontal lines representing paragraphs
    line_y = T + 50
    for i, w in enumerate([60, 70, 50, 65]):
        y = line_y + i * 22
        draw.line([(L + 14, y), (L + 14 + w, y)], fill=secondary + (255,) if i == 0 else primary + (255,), width=3)
    return img


def glyph_test(primary, secondary):
    """Bar chart — 4 vertical bars of increasing height + axis line."""
    img = _new_glyph()
    draw = ImageDraw.Draw(img)
    base_y = 160
    bar_w = 22
    spacing = 12
    heights = [40, 65, 95, 75]
    total_w = len(heights) * bar_w + (len(heights) - 1) * spacing
    start_x = (GLYPH_SIZE - total_w) // 2
    for i, h in enumerate(heights):
        x = start_x + i * (bar_w + spacing)
        color = secondary if h == max(heights) else primary
        draw.rectangle([x, base_y - h, x + bar_w, base_y], outline=color + (255,), width=3)
    # X axis
    draw.line([(start_x - 14, base_y + 4), (start_x + total_w + 14, base_y + 4)], fill=primary + (255,), width=3)
    # Y axis
    draw.line([(start_x - 14, base_y + 4), (start_x - 14, 50)], fill=primary + (255,), width=3)
    return img


def glyph_sec(primary, secondary):
    """Shield outline with center dot — security."""
    img = _new_glyph()
    draw = ImageDraw.Draw(img)
    cx = GLYPH_SIZE // 2
    top_y = 30
    sides_y = 70
    point_y = 175
    width = 70
    pts = [
        (cx, top_y),
        (cx + width, top_y + 10),
        (cx + width - 5, sides_y + 30),
        (cx, point_y),
        (cx - width + 5, sides_y + 30),
        (cx - width, top_y + 10),
    ]
    draw.polygon(pts, outline=primary + (255,), width=3)
    # Inner shield ridge
    inner = [(cx, top_y + 14)] + [(p[0] * 0.78 + cx * 0.22, p[1] * 0.85 + 18) for p in pts[1:]]
    # Center dot — the "lock"
    draw.ellipse([cx - 14, sides_y + 30, cx + 14, sides_y + 58], outline=secondary + (255,), width=3)
    draw.line([(cx, sides_y + 58), (cx, sides_y + 78)], fill=secondary + (255,), width=3)
    return img


def glyph_thesis(primary, secondary):
    """Tall page with footnote markers in the right margin."""
    img = _new_glyph()
    draw = ImageDraw.Draw(img)
    L, T, R, B = 55, 25, 145, 175
    draw.rectangle([L, T, R, B], outline=primary + (255,), width=3)
    # Body lines
    for i, w in enumerate([55, 65, 50, 60, 45, 60, 55, 50]):
        y = T + 18 + i * 16
        draw.line([(L + 10, y), (L + 10 + w, y)], fill=primary + (255,), width=2)
    # Footnote markers in the right margin (small dots)
    for i, y_off in enumerate([42, 90, 138]):
        draw.ellipse([R + 8, T + y_off - 3, R + 14, T + y_off + 3], fill=secondary + (255,))
    # Connect footnote markers vertically to suggest "annotation gutter"
    draw.line([(R + 11, T + 42), (R + 11, T + 138)], fill=secondary + (180,), width=1)
    return img


def glyph_engine(primary, secondary):
    """Cog/gear feeding into a page — research-feeder."""
    img = _new_glyph()
    draw = ImageDraw.Draw(img)
    # Gear at top
    cx, cy = GLYPH_SIZE // 2, 65
    R_outer = 38
    R_inner = 28
    teeth = 8
    pts = []
    for i in range(teeth * 2):
        theta = i * math.pi / teeth - math.pi / 2
        r = R_outer if i % 2 == 0 else R_inner
        pts.append((cx + r * math.cos(theta), cy + r * math.sin(theta)))
    draw.polygon(pts, outline=primary + (255,), width=3)
    # Inner hole
    draw.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], outline=primary + (255,), width=2)
    # Arrow down
    arrow_y = cy + R_outer + 10
    draw.line([(cx, arrow_y), (cx, arrow_y + 20)], fill=secondary + (255,), width=3)
    draw.polygon([(cx - 6, arrow_y + 18), (cx + 6, arrow_y + 18), (cx, arrow_y + 26)],
                 fill=secondary + (255,))
    # Output page
    page_T = arrow_y + 32
    page_L, page_R, page_B = cx - 32, cx + 32, page_T + 42
    draw.rectangle([page_L, page_T, page_R, page_B], outline=primary + (255,), width=3)
    for i in range(3):
        y = page_T + 10 + i * 10
        draw.line([(page_L + 6, y), (page_L + 6 + 40, y)], fill=primary + (255,), width=2)
    return img


GLYPHS = {
    "node_graph":   glyph_cartographer,
    "keystone":     glyph_keystone,
    "doc":          glyph_doc,
    "bars":         glyph_test,
    "shield":       glyph_sec,
    "scroll":       glyph_thesis,
    "engine_gear":  glyph_engine,
}


# ──────────────────────────────────────────────────────────────────
# Plugin registry
# ──────────────────────────────────────────────────────────────────

PLUGINS = [
    {
        "id": "vibe-cartographer", "name": "VIBE CARTOGRAPHER",
        "tagline": "plot your course",
        "glyph": "node_graph", "primary": MAGENTA, "secondary": CYAN,  # flagship gets the duo
    },
    {
        "id": "vibe-keystone", "name": "VIBE KEYSTONE",
        "tagline": "bootstrap any repo",
        "glyph": "keystone", "primary": CYAN, "secondary": MAGENTA,
    },
    {
        "id": "vibe-doc", "name": "VIBE DOC",
        "tagline": "the docs you keep meaning to write",
        "glyph": "doc", "primary": CYAN, "secondary": MAGENTA,
    },
    {
        "id": "vibe-test", "name": "VIBE TEST",
        "tagline": "honest coverage, real tests",
        "glyph": "bars", "primary": CYAN, "secondary": MAGENTA,
    },
    {
        "id": "vibe-sec", "name": "VIBE SEC",
        "tagline": "audit surface, built in",
        "glyph": "shield", "primary": MAGENTA, "secondary": CYAN,
    },
    {
        "id": "vibe-thesis", "name": "VIBE THESIS",
        "tagline": "long-form, with sources",
        "glyph": "scroll", "primary": CYAN, "secondary": MAGENTA,
    },
    {
        "id": "thesis-engine", "name": "THESIS ENGINE",
        "tagline": "topics, sources, ready to write",
        "glyph": "engine_gear", "primary": MAGENTA, "secondary": CYAN,
    },
]


# ──────────────────────────────────────────────────────────────────
# Composition
# ──────────────────────────────────────────────────────────────────

def load_claude_sparkle(target_height):
    if not CLAUDE_SPARKLE_SRC.exists():
        return None
    spk = Image.open(CLAUDE_SPARKLE_SRC).convert("RGBA")
    scale = target_height / spk.height
    return spk.resize((int(spk.width * scale), target_height), Image.LANCZOS)


def build_banner(plugin, out_path):
    W, H = 1500, 500
    canvas = Image.new("RGBA", (W, H), NAVY + (255,))
    canvas.alpha_composite(radial_glow(W, H, 0.16, 0.28, plugin["primary"], 70, 0.50))
    canvas.alpha_composite(radial_glow(W, H, 0.86, 0.78, plugin["secondary"], 60, 0.55))

    # Glyph card on the left — tall mono-feeling tile
    card_w, card_h = 280, 280
    card_x = int(W * 0.06)
    card_y = (H - card_h) // 2
    card_layer = Image.new("RGBA", (card_w, card_h), (255, 255, 255, 0))
    cdraw = ImageDraw.Draw(card_layer)
    cdraw.rounded_rectangle([0, 0, card_w - 1, card_h - 1], radius=14,
                            outline=DIM2 + (180,), width=1,
                            fill=(0, 0, 0, 60))
    # Render glyph centered in the card
    glyph_size = 200
    glyph = GLYPHS[plugin["glyph"]](plugin["primary"], plugin["secondary"])
    if glyph.size != (glyph_size, glyph_size):
        glyph = glyph.resize((glyph_size, glyph_size), Image.LANCZOS)
    card_layer.alpha_composite(glyph, dest=((card_w - glyph_size) // 2, (card_h - glyph_size) // 2))
    canvas.alpha_composite(card_layer, dest=(card_x, card_y))

    # Text block
    text_x = card_x + card_w + int(W * 0.05)
    sparkle_w = 64 + int(W * 0.04)  # reserve space so name doesn't run under sparkle
    text_avail_w = W - text_x - sparkle_w - int(W * 0.06)
    draw = ImageDraw.Draw(canvas)
    tag_font = ImageFont.truetype(str(FONTS / "JetBrainsMono-Regular.ttf"), 22)

    # Spaced caps: single space between letters (matches Cartographer's existing
    # repo banner aesthetic). Auto-fit the font size so long names like
    # "VIBE CARTOGRAPHER" don't overflow into the sparkle / right margin.
    spaced = " ".join(plugin["name"])
    name_size = 56
    while name_size > 22:
        name_font = ImageFont.truetype(str(FONTS / "JetBrainsMono-Regular.ttf"), name_size)
        nb = draw.textbbox((0, 0), spaced, font=name_font)
        if (nb[2] - nb[0]) <= text_avail_w:
            break
        name_size -= 2
    name_bbox = draw.textbbox((0, 0), spaced, font=name_font)
    name_w = name_bbox[2] - name_bbox[0]
    name_h = name_bbox[3] - name_bbox[1]

    tagline = plugin["tagline"]
    tag_bbox = draw.textbbox((0, 0), tagline, font=tag_font)
    tag_h = tag_bbox[3] - tag_bbox[1]

    block_h = name_h + 18 + tag_h
    block_top = (H - block_h) // 2
    draw.text((text_x, block_top), spaced, font=name_font, fill=plugin["primary"] + (255,))
    draw.text((text_x, block_top + name_h + 18), tagline, font=tag_font, fill=DIM + (255,))

    # 626 Labs lockup top-right (tiny)
    sub_font = ImageFont.truetype(str(FONTS / "JetBrainsMono-Regular.ttf"), 13)
    lockup = "626 LABS  ·  for Claude Code"
    lk_bbox = draw.textbbox((0, 0), lockup, font=sub_font)
    lk_w = lk_bbox[2] - lk_bbox[0]
    draw.text((W - lk_w - int(W * 0.04), int(H * 0.08)), lockup, font=sub_font, fill=DIM2 + (255,))

    # Claude sparkle anchored bottom-right corner — small, attribution-only
    spk = load_claude_sparkle(64)
    if spk is not None:
        canvas.alpha_composite(spk, dest=(W - spk.width - int(W * 0.04), H - spk.height - int(H * 0.10)))

    canvas.convert("RGB").save(out_path, "PNG", optimize=True)
    print(f"  banner  {plugin['id']:24s}  {out_path}")


def build_square(plugin, out_path):
    W = H = 1024
    canvas = Image.new("RGBA", (W, H), NAVY + (255,))
    canvas.alpha_composite(radial_glow(W, H, 0.18, 0.22, plugin["primary"], 96, 0.60))
    canvas.alpha_composite(radial_glow(W, H, 0.82, 0.82, plugin["secondary"], 84, 0.60))

    # Glyph centered upper-third
    glyph_size = int(H * 0.42)
    glyph = GLYPHS[plugin["glyph"]](plugin["primary"], plugin["secondary"])
    glyph = glyph.resize((glyph_size, glyph_size), Image.LANCZOS)
    canvas.alpha_composite(glyph, dest=((W - glyph_size) // 2, int(H * 0.14)))

    draw = ImageDraw.Draw(canvas)
    name_font = ImageFont.truetype(str(FONTS / "JetBrainsMono-Regular.ttf"), 56)
    tag_font = ImageFont.truetype(str(FONTS / "JetBrainsMono-Regular.ttf"), 22)
    sub_font = ImageFont.truetype(str(FONTS / "JetBrainsMono-Regular.ttf"), 16)

    spaced = " ".join(plugin["name"])
    target_w = int(W * 0.86)
    name_size = 64
    while name_size > 22:
        name_font = ImageFont.truetype(str(FONTS / "JetBrainsMono-Regular.ttf"), name_size)
        nb = draw.textbbox((0, 0), spaced, font=name_font)
        if (nb[2] - nb[0]) <= target_w:
            break
        name_size -= 2
    name_bbox = draw.textbbox((0, 0), spaced, font=name_font)
    name_w = name_bbox[2] - name_bbox[0]
    name_h = name_bbox[3] - name_bbox[1]

    tagline = plugin["tagline"]
    tag_bbox = draw.textbbox((0, 0), tagline, font=tag_font)
    tag_w = tag_bbox[2] - tag_bbox[0]
    tag_h = tag_bbox[3] - tag_bbox[1]

    name_y = int(H * 0.66)
    draw.text(((W - name_w) // 2, name_y), spaced, font=name_font, fill=plugin["primary"] + (255,))
    draw.text(((W - tag_w) // 2, name_y + name_h + 18), tagline, font=tag_font, fill=DIM + (255,))

    sub = "626 LABS  ·  FOR CLAUDE CODE"
    sub_bbox = draw.textbbox((0, 0), sub, font=sub_font)
    sub_w = sub_bbox[2] - sub_bbox[0]
    draw.text(((W - sub_w) // 2, int(H * 0.92)), sub, font=sub_font, fill=DIM2 + (255,))

    # Tiny Claude sparkle bottom-right corner
    spk = load_claude_sparkle(56)
    if spk is not None:
        canvas.alpha_composite(spk, dest=(W - spk.width - int(W * 0.05), int(H * 0.05)))

    canvas.convert("RGB").save(out_path, "PNG", optimize=True)
    print(f"  square  {plugin['id']:24s}  {out_path}")


def main():
    print(f"Building plugin icons -> {OUT}")
    for p in PLUGINS:
        build_banner(p, OUT / f"{p['id']}-banner-1500x500.png")
        build_square(p, OUT / f"{p['id']}-square-1024.png")


if __name__ == "__main__":
    main()
