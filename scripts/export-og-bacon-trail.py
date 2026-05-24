"""
Generate the OG card for the Birthday Bacon Trail standalone page.
Run: python scripts/export-og-bacon-trail.py
Output: assets/og-bacon-trail.png  (1200x630)

Sibling to export-og-vibe-iterate.py — same navy field + variable-font
treatment, but pairs the cyan glow with a magenta one (brand rule: the
two accents always travel together).
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1200, 630
NAVY = (15, 31, 49)
CYAN = (23, 212, 250)
MAGENTA = (242, 47, 137)
INK_0 = (255, 255, 255)
INK_200 = (192, 202, 216)
INK_300 = (138, 152, 173)

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "fonts"
SPACE = FONTS / "SpaceGrotesk-Variable.ttf"
MONO = FONTS / "JetBrainsMono-Regular.ttf"
OUT = ROOT / "assets" / "og-bacon-trail.png"

MARGIN = 80


def grotesk(size, weight=400):
    f = ImageFont.truetype(str(SPACE), size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def corner_glow(img, color, cx, cy):
    """Soft blurred radial glow centered at (cx, cy)."""
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for r, alpha in [(520, 16), (380, 26), (250, 38)]:
        gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*color, alpha))
    glow = glow.filter(ImageFilter.GaussianBlur(70))
    img.paste(glow, (0, 0), glow)


def main():
    img = Image.new("RGB", (W, H), NAVY)

    # Paired glows — magenta top-left, cyan bottom-right.
    corner_glow(img, MAGENTA, 140, 70)
    corner_glow(img, CYAN, W - 180, H - 80)

    draw = ImageDraw.Draw(img, "RGBA")

    # Eyebrow (mono, uppercase, cyan)
    eyebrow = ImageFont.truetype(str(MONO), 20)
    draw.text((MARGIN, 150), "626 LABS   ·   LOBBY GAME", font=eyebrow, fill=CYAN)

    # Title (Space Grotesk bold, two lines for impact)
    title = grotesk(112, 700)
    draw.text((MARGIN - 2, 196), "Birthday", font=title, fill=INK_0)
    draw.text((MARGIN - 2, 318), "Bacon Trail", font=title, fill=INK_0)

    # Subtitle (Space Grotesk regular)
    draw.text((MARGIN, 462), "One film chain to Kevin Bacon.",
              font=grotesk(38, 400), fill=INK_200)

    # Footer URL (mono)
    footer = ImageFont.truetype(str(MONO), 18)
    draw.text((MARGIN, H - 62), "626labs.dev/bacon-trail", font=footer, fill=INK_300)

    # 626 Labs logo, top-right (transparent variant — no box behind it)
    logo_path = ROOT / "assets" / "brand" / "icon-transparent-256.png"
    if logo_path.exists():
        logo = Image.open(logo_path).convert("RGBA")
        logo.thumbnail((64, 64))
        img.paste(logo, (W - logo.width - MARGIN, 64), logo)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
