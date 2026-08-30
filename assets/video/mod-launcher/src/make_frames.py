"""Build the 626 Mod Launcher still frames at 9x16, 4x5, 1x1 and 16x9 into frames/<size>/.

Brand: navy field #0f1f31, cyan #17d4fa + magenta #f22f89 always paired,
Space Grotesk display, Inter body, JetBrains Mono uppercase meta labels.
Mirrors assets/video/rororo/src/make_frames.py; the shared parts should lift
to a package the day a third product video needs them.
"""
import os
import qrcode
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
FONTS = os.path.join(ROOT, "fonts")
TILE_SRC = os.path.join(HERE, "app-icon-512.png")
QR_URL = "https://626labs.dev/mod-launcher-games.html?ref=tiktok"

NAVY, CYAN, MAG = (15, 31, 49), (23, 212, 250), (242, 47, 137)
INK0, INK200, INK300 = (255, 255, 255), (196, 205, 218), (164, 174, 189)
SIZES = {"9x16": (1080, 1920), "4x5": (1080, 1350), "1x1": (1080, 1080), "16x9": (1920, 1080)}


def scale(W, H):
    """Type scale: full at 9:16 and landscape, shrinking as a PORTRAIT canvas squares off."""
    if W > H:
        return min(W, H)
    return min(W, H) * min(1.0, (H / W) / 1.6)


def fit_font(name, weight, text, max_w, start):
    """Largest font size <= start whose rendered text fits max_w."""
    size = start
    while size > 12:
        f = font(name, size, weight)
        if f.getlength(text) <= max_w:
            return f
        size -= 4
    return font(name, size, weight)


def font(name, size, weight):
    f = ImageFont.truetype(os.path.join(FONTS, name), size)
    try:
        if "Inter" in name:
            f.set_variation_by_axes([14, weight])
        else:
            f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def field(W, H):
    im = Image.new("RGB", (W, H), NAVY)
    glow = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(glow)
    r = int(max(W, H) * 0.55)
    d.ellipse([-r * 0.4, -r * 0.5, r * 0.9, r * 0.8], fill=(20, 70, 95))
    d.ellipse([W - r * 0.9, H - r * 0.7, W + r * 0.4, H + r * 0.5], fill=(70, 30, 60))
    glow = glow.filter(ImageFilter.GaussianBlur(r * 0.35))
    return Image.blend(im, glow, 0.9)


def lerp(t):
    return tuple(int(CYAN[i] + (MAG[i] - CYAN[i]) * t) for i in range(3))


def gradient_text(im, text, f, cx, cy):
    bbox = f.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    mask = Image.new("L", (tw, th), 0)
    ImageDraw.Draw(mask).text((-bbox[0], -bbox[1]), text, font=f, fill=255)
    grad = Image.new("RGB", (tw, th))
    gd = ImageDraw.Draw(grad)
    for x in range(tw):
        gd.line([(x, 0), (x, th)], fill=lerp(x / max(tw - 1, 1)))
    im.paste(grad, (int(cx - tw / 2), int(cy - th / 2)), mask)
    return th


def hairline(d, cx, y, w):
    x0 = cx - w / 2
    for x in range(int(x0), int(x0 + w)):
        d.line([(x, y), (x, y + 3)], fill=lerp((x - x0) / w))


def meta(d, text, f, cx, y, fill=INK300):
    text = text.upper()
    track = f.size * 0.12
    widths = [f.getlength(c) for c in text]
    total = sum(widths) + track * (len(text) - 1)
    x = cx - total / 2
    for c, w in zip(text, widths):
        d.text((x, y), c, font=f, fill=fill)
        x += w + track


def center(d, text, f, cx, y, fill=INK0):
    d.text((cx - f.getlength(text) / 2, y), text, font=f, fill=fill)


def rounded_mask(size, radius):
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return m


def app_tile(size):
    c = Image.open(TILE_SRC).convert("RGBA").resize((size, size), Image.LANCZOS)
    c.putalpha(rounded_mask(size, size // 8))
    return c


def brand_footer(d, W, H, u):
    meta(d, "626 Labs  /  Imagine Something Else.",
         font("JetBrainsMono-Variable.ttf", int(u * 0.022), 500), W / 2, H - u * 0.07)


def title(W, H):
    im = field(W, H)
    d = ImageDraw.Draw(im)
    u = scale(W, H)
    mono = font("JetBrainsMono-Variable.ttf", int(u * 0.03), 500)
    if H >= W:
        big = fit_font("SpaceGrotesk-Variable.ttf", 700, "MOD LAUNCHER", W * 0.9, int(u * 0.135))
        meta(d, "626 Labs  /  Mod Launcher", mono, W / 2, H * 0.09)
        tile = app_tile(int(u * 0.42))
        ty = H * (0.2 if H / W > 1.5 else 0.16)
        im.paste(tile, (int(W / 2 - tile.width / 2), int(ty)), tile)
        y = ty + tile.height + u * 0.13
        th = gradient_text(im, "MOD LAUNCHER", big, W / 2, y)
        y += th / 2 + u * 0.05
        center(d, "Flip switches. Keep everything.", font("SpaceGrotesk-Variable.ttf", int(u * 0.06), 500), W / 2, y)
        y += u * 0.12
        hairline(d, W / 2, y, u * 0.3)
        y += u * 0.05
        meta(d, "Free  ·  No ads  ·  No account", mono, W / 2, y, INK200)
    else:
        tile = app_tile(int(u * 0.62))
        tx = int(W * 0.11)
        im.paste(tile, (tx, int(H / 2 - tile.height / 2)), tile)
        cx = tx + tile.width + (W - tx - tile.width) / 2
        big = fit_font("SpaceGrotesk-Variable.ttf", 700, "MOD LAUNCHER", (W - tx - tile.width) * 0.92, int(u * 0.135))
        meta(d, "626 Labs  /  Mod Launcher", mono, cx, H * 0.22)
        gradient_text(im, "MOD LAUNCHER", big, cx, H * 0.43)
        center(d, "Flip switches. Keep everything.", font("SpaceGrotesk-Variable.ttf", int(u * 0.055), 500), cx, H * 0.56)
        hairline(d, cx, H * 0.7, u * 0.3)
        meta(d, "Free  ·  No ads  ·  No account", mono, cx, H * 0.75, INK200)
    brand_footer(d, W, H, u)
    return im


def bullets(W, H, kicker, heading, rows):
    im = field(W, H)
    d = ImageDraw.Draw(im)
    u = scale(W, H)
    portrait = H >= W
    meta(d, kicker, font("JetBrainsMono-Variable.ttf", int(u * 0.03), 500), W / 2, H * (0.09 if portrait else 0.1))
    hy = H * (0.14 if portrait else 0.17)
    hf = font("SpaceGrotesk-Variable.ttf", int(u * 0.07), 700)
    lines = [l + "." for l in heading.rstrip(".").split(". ")] if portrait else [heading]
    for i, l in enumerate(lines):
        center(d, l, hf, W / 2, hy + i * u * 0.085)
    hairline(d, W / 2, hy + u * (0.085 * len(lines) + 0.03), u * 0.2)
    tf = font("SpaceGrotesk-Variable.ttf", int(u * (0.05 if portrait else 0.048)), 500)
    bf = font("Inter-Variable.ttf", int(u * 0.030), 400)
    n = len(rows)
    top = hy + u * (0.085 * len(lines) + 0.12)
    if portrait:
        gap = (H * 0.9 - top) / n
        x0 = W / 2 - u * 0.82 / 2
        for i, (t, b) in enumerate(rows):
            y = top + i * gap
            d.ellipse([x0, y + u * 0.014, x0 + u * 0.026, y + u * 0.04], fill=CYAN if i % 2 == 0 else MAG)
            d.text((x0 + u * 0.06, y), t, font=tf, fill=INK0)
            d.text((x0 + u * 0.06, y + tf.size * 1.25), b, font=bf, fill=INK200)
    else:
        per_col = (n + 1) // 2
        gap = (H * 0.94 - top) / per_col
        for i, (t, b) in enumerate(rows):
            col, row = divmod(i, per_col)
            x0 = W * (0.09 if col == 0 else 0.53)
            y = top + row * gap
            d.ellipse([x0, y + u * 0.014, x0 + u * 0.026, y + u * 0.04], fill=CYAN if i % 2 == 0 else MAG)
            d.text((x0 + u * 0.06, y), t, font=tf, fill=INK0)
            d.text((x0 + u * 0.06, y + tf.size * 1.25), b, font=bf, fill=INK200)
    brand_footer(d, W, H, u)
    return im


def cta(W, H):
    im = field(W, H)
    d = ImageDraw.Draw(im)
    u = scale(W, H)
    portrait = H >= W
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=2)
    q.add_data(QR_URL)
    q.make(fit=True)
    qi = q.make_image(fill_color="#0f1f31", back_color="white").convert("RGB")
    qs = int(u * (0.5 if portrait else 0.55))
    qi = qi.resize((qs, qs), Image.NEAREST)
    m = rounded_mask(qs, qs // 20)
    mono = font("JetBrainsMono-Variable.ttf", int(u * 0.03), 500)
    big = font("SpaceGrotesk-Variable.ttf", int(u * 0.062), 700)
    url = font("SpaceGrotesk-Variable.ttf", int(u * 0.05), 500)
    small = font("Inter-Variable.ttf", int(u * 0.027), 400)
    sub = "Microsoft Store and the full GitHub build are on the page."
    legal = "Independent tool. Game names belong to their owners."
    if portrait:
        meta(d, "Free  ·  Windows native", mono, W / 2, H * 0.09)
        center(d, "Scan. Save. Install on desktop.", big, W / 2, H * 0.14)
        qy = H * 0.14 + u * 0.16
        im.paste(qi, (int(W / 2 - qs / 2), int(qy)), m)
        y = qy + qs + u * 0.08
        hairline(d, W / 2, y, u * 0.3)
        y += u * 0.06
        center(d, "626labs.dev/mod-launcher-games.html", url, W / 2, y, CYAN)
        center(d, sub, small, W / 2, y + u * 0.11, INK300)
        center(d, legal, small, W / 2, H - u * 0.14, INK300)
    else:
        qx = int(W * 0.12)
        im.paste(qi, (qx, int(H / 2 - qs / 2)), m)
        cx = qx + qs + (W - qx - qs) / 2
        meta(d, "Free  ·  Windows native", mono, cx, H * 0.22)
        center(d, "Scan. Save. Install on desktop.", big, cx, H * 0.3)
        hairline(d, cx, H * 0.48, u * 0.3)
        center(d, "626labs.dev/mod-launcher-games.html", url, cx, H * 0.53, CYAN)
        center(d, sub, small, cx, H * 0.64, INK300)
        center(d, legal, small, cx, H * 0.7, INK300)
    brand_footer(d, W, H, u)
    return im


FEATURES = [
    ("Atomic writes", "Lose power mid-toggle and your library survives."),
    ("Holding folder", "Disabling a mod moves it aside. Never deletes."),
    ("Engine-aware", "Bethesda, Unreal, FromSoft, BepInEx, SMAPI and more."),
    ("Config editor", "Edit INIs with a previous version you can restore."),
    ("Profiles + restore points", "Switch setups. Undo a bad afternoon."),
    ("Themes", "The whole app, to taste."),
]

if __name__ == "__main__":
    for size, (W, H) in SIZES.items():
        out = os.path.join(HERE, "frames", size)
        os.makedirs(out, exist_ok=True)
        title(W, H).save(os.path.join(out, "01-title.png"))
        bullets(W, H, "Quality of life", "Your files are yours. Provably.", FEATURES).save(
            os.path.join(out, "02-features.png"))
        cta(W, H).save(os.path.join(out, "04-cta.png"))
        print("built", size)
