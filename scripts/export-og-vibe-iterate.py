"""
Generate the OG card for the vibe-iterate landing page.
Run: python scripts/export-og-vibe-iterate.py
Output: assets/og-vibe-iterate.png  (1200x630)

Uses the repo's variable fonts (fonts/*.ttf), setting the weight axis
on Space Grotesk for the bold title and regular subtitle.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1200, 630
NAVY = (15, 31, 49)
CYAN = (23, 212, 250)
INK_0 = (255, 255, 255)
INK_200 = (192, 202, 216)
INK_300 = (138, 152, 173)

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "fonts"
SPACE = FONTS / "SpaceGrotesk-Variable.ttf"
MONO = FONTS / "JetBrainsMono-Regular.ttf"
OUT = ROOT / "assets" / "og-vibe-iterate.png"


def grotesk(size, weight=400):
    f = ImageFont.truetype(str(SPACE), size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def main():
    img = Image.new("RGB", (W, H), NAVY)

    # Soft cyan glow, bottom-right, blurred for a clean falloff.
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for r, alpha in [(520, 16), (380, 26), (250, 38)]:
        gd.ellipse([W - 180 - r, H - 80 - r, W - 180 + r, H - 80 + r],
                   fill=(23, 212, 250, alpha))
    glow = glow.filter(ImageFilter.GaussianBlur(70))
    img.paste(glow, (0, 0), glow)

    draw = ImageDraw.Draw(img, "RGBA")

    # Eyebrow (mono, uppercase, cyan)
    eyebrow = ImageFont.truetype(str(MONO), 20)
    draw.text((80, 196), "626 LABS   ·   CLAUDE CODE PLUGIN", font=eyebrow, fill=CYAN)

    # Title (Space Grotesk bold)
    draw.text((78, 236), "vibe-iterate", font=grotesk(104, 700), fill=INK_0)

    # Subtitle (Space Grotesk regular)
    draw.text((80, 372), "Maintain your Atlas.", font=grotesk(42, 400), fill=INK_200)

    # Footer URL (mono)
    footer = ImageFont.truetype(str(MONO), 18)
    draw.text((80, H - 62), "626labs.dev/vibe-iterate", font=footer, fill=INK_300)

    # 626 Labs logo, top-right (transparent variant — no box behind it)
    logo_path = ROOT / "assets" / "brand" / "icon-transparent-256.png"
    if logo_path.exists():
        logo = Image.open(logo_path).convert("RGBA")
        logo.thumbnail((64, 64))
        img.paste(logo, (W - logo.width - 80, 64), logo)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
