"""Build the RORORO still frames at 9x16, 16x9 and 1x1 into frames/<size>/.

Brand: navy field #0f1f31, cyan #17d4fa + magenta #f22f89 always paired,
Space Grotesk display, Inter body, JetBrains Mono uppercase meta labels.
"""
import os
import qrcode
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
FONTS = os.path.join(ROOT, "fonts")
CUBE = os.path.join(ROOT, "assets/thumb-rororo.png")
STORE = "https://apps.microsoft.com/detail/9NMJCS390KWB"
QR_URL = "https://626labs.dev/rororo.html?ref=tiktok"

NAVY, CYAN, MAG = (15, 31, 49), (23, 212, 250), (242, 47, 137)
INK0, INK200, INK300 = (255, 255, 255), (196, 205, 218), (164, 174, 189)
SIZES = {"9x16": (1080, 1920), "4x5": (1080, 1350), "1x1": (1080, 1080), "16x9": (1920, 1080)}

# ---- localization -------------------------------------------------------
# English is the in-code default (byte-stable when no --lang is given).
# Other languages load from card-text.json, extracted from ROROROblox
# docs/videos/launch-video-script.md by assets/video/tools/extract_card_text.py.
EN_TEXT = {
    "tagline": "Every alt. One click.",
    "badge": "Free  ·  Windows + macOS",
    "kicker": "Quality of life",
    "features_heading": "Runs the clients. Babysits them too.",
    "f1_label": "Encrypted vault", "f1_body": "Roblox's own login page. Your password stays there.",
    "f2_label": "Memory watchdog", "f2_body": "Warns before a leak kills a client. One-click Recycle.",
    "f3_label": "Streamer mode", "f3_body": "Fake names and avatars everywhere while you're live.",
    "f4_label": "Keyboard shortcuts", "f4_body": "Ctrl+L launches the roster. F1 shows the rest.",
    "f5_label": "Live status + RAM", "f5_body": "See the game and cost of every client at a glance.",
    "f6_label": "Auto-update", "f6_body": "Always current, Windows and Mac.",
    "cta_badge": "Free  ·  Windows + macOS",
    "cta_heading": "Scan. Save. Install on desktop.",
    "cta_note": "Microsoft Store and Mac links are on the page.",
    "cta_legal": "Independent tool. Not affiliated with Roblox Corporation.",
}
LANG = "en"
T = dict(EN_TEXT)


def set_lang(lang):
    """Switch the card text; en keeps the in-code defaults."""
    global LANG, T
    LANG = lang
    T = dict(EN_TEXT)
    if lang != "en":
        import json as _json
        data = _json.load(open(os.path.join(HERE, "card-text.json"), encoding="utf-8"))
        T.update(data[lang])
        # de badge order differs in the doc but keeps the same tokens; the
        # doc's badge is uppercase and meta() letterspaces as-is.
        T["badge"] = T["badge"].replace(" · ", "  ·  ")
        T["cta_badge"] = T.get("cta_badge", T["badge"]).replace(" · ", "  ·  ")


def fit_font(name, size, weight, texts, max_w):
    """Shrink a font until every text fits max_w — translations never clip.
    One size for the whole group, so a card keeps uniform typography."""
    if isinstance(texts, str):
        texts = [texts]
    # Space Grotesk carries no Cyrillic — Russian display text falls back
    # to Inter (full Cyrillic set) at the same size and weight.
    if name.startswith("SpaceGrotesk") and any(
            "\u0400" <= ch <= "\u04ff" for t in texts for ch in t):
        name = "Inter-Variable.ttf"
    f = font(name, size, weight)
    while size > 10 and max(f.getlength(t) for t in texts) > max_w:
        size = int(size * 0.95)
        f = font(name, size, weight)
    return f


def scale(W, H):
    """Type scale: full at 9:16 and landscape, shrinking as a PORTRAIT canvas squares off."""
    if W > H:
        return min(W, H)
    return min(W, H) * min(1.0, (H / W) / 1.6)


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
    """Navy field with a cyan glow top-left and a magenta glow bottom-right."""
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
    """Cyan-to-magenta text, centered on (cx, cy). Returns text height."""
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
    """Uppercase mono label with +0.12em tracking, centered."""
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


def cube_tile(size):
    c = Image.open(CUBE).convert("RGBA").resize((size, size), Image.LANCZOS)
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
        meta(d, "626 Labs  /  RORORO", mono, W / 2, H * 0.09)
        tile = cube_tile(int(u * 0.42))
        ty = H * (0.2 if H / W > 1.5 else 0.16)
        im.paste(tile, (int(W / 2 - tile.width / 2), int(ty)), tile)
        y = ty + tile.height + u * 0.14
        th = gradient_text(im, "RORORO", font("SpaceGrotesk-Variable.ttf", int(u * 0.2), 700), W / 2, y)
        y += th / 2 + u * 0.05
        center(d, T["tagline"], fit_font("SpaceGrotesk-Variable.ttf", int(u * 0.07), 500, T["tagline"], W * 0.9), W / 2, y)
        y += u * 0.13
        hairline(d, W / 2, y, u * 0.3)
        y += u * 0.05
        meta(d, T["badge"], mono, W / 2, y, INK200)
    else:
        tile = cube_tile(int(u * 0.62))
        tx = int(W * 0.11)
        im.paste(tile, (tx, int(H / 2 - tile.height / 2)), tile)
        cx = tx + tile.width + (W - tx - tile.width) / 2
        meta(d, "626 Labs  /  RORORO", mono, cx, H * 0.22)
        gradient_text(im, "RORORO", font("SpaceGrotesk-Variable.ttf", int(u * 0.2), 700), cx, H * 0.43)
        center(d, T["tagline"], fit_font("SpaceGrotesk-Variable.ttf", int(u * 0.065), 500, T["tagline"], (W - tx - tile.width) * 0.92), cx, H * 0.56)
        hairline(d, cx, H * 0.7, u * 0.3)
        meta(d, T["badge"], mono, cx, H * 0.75, INK200)
    brand_footer(d, W, H, u)
    return im


def bullets(W, H, kicker, heading, rows):
    im = field(W, H)
    d = ImageDraw.Draw(im)
    u = scale(W, H)
    portrait = H >= W
    top_k = H * (0.09 if portrait else 0.1)
    meta(d, kicker, font("JetBrainsMono-Variable.ttf", int(u * 0.03), 500), W / 2, top_k)
    hy = H * (0.14 if portrait else 0.17)
    lines = [l + "." for l in heading.rstrip(".").split(". ")] if portrait else [heading]
    hf = fit_font("SpaceGrotesk-Variable.ttf", int(u * 0.07), 700, lines, W * 0.92)
    for i, l in enumerate(lines):
        center(d, l, hf, W / 2, hy + i * u * 0.085)
    hairline(d, W / 2, hy + u * (0.085 * len(lines) + 0.03), u * 0.2)
    col_w = (u * 0.82 - u * 0.06) if portrait else (W * 0.44)
    tf = fit_font("SpaceGrotesk-Variable.ttf", int(u * (0.05 if portrait else 0.048)), 500,
                  [t for t, _ in rows], col_w)
    bf = fit_font("Inter-Variable.ttf", int(u * 0.030), 400, [b for _, b in rows], col_w)
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
    url = font("SpaceGrotesk-Variable.ttf", int(u * 0.055), 500)
    small = font("Inter-Variable.ttf", int(u * 0.027), 400)
    mac = T["cta_note"]
    legal = T["cta_legal"]
    if portrait:
        meta(d, T["cta_badge"], mono, W / 2, H * 0.09)
        center(d, T["cta_heading"], fit_font("SpaceGrotesk-Variable.ttf", int(u * 0.062), 700, T["cta_heading"], W * 0.92), W / 2, H * 0.14)
        qy = H * 0.14 + u * 0.16
        im.paste(qi, (int(W / 2 - qs / 2), int(qy)), m)
        y = qy + qs + u * 0.08
        hairline(d, W / 2, y, u * 0.3)
        y += u * 0.06
        center(d, "626labs.dev/rororo.html", url, W / 2, y, CYAN)
        sf = fit_font("Inter-Variable.ttf", int(u * 0.027), 400, [mac, legal], W * 0.92)
        center(d, mac, sf, W / 2, y + u * 0.11, INK300)
        center(d, legal, sf, W / 2, H - u * 0.14, INK300)
    else:
        qx = int(W * 0.12)
        im.paste(qi, (qx, int(H / 2 - qs / 2)), m)
        cx = qx + qs + (W - qx - qs) / 2
        meta(d, T["cta_badge"], mono, cx, H * 0.22)
        center(d, T["cta_heading"], fit_font("SpaceGrotesk-Variable.ttf", int(u * 0.062), 700, T["cta_heading"], (W - qx - qs) * 0.9), cx, H * 0.3)
        hairline(d, cx, H * 0.48, u * 0.3)
        center(d, "626labs.dev/rororo.html", url, cx, H * 0.53, CYAN)
        sf = fit_font("Inter-Variable.ttf", int(u * 0.027), 400, [mac, legal], (W - qx - qs) * 0.92)
        center(d, mac, sf, cx, H * 0.64, INK300)
        center(d, legal, sf, cx, H * 0.7, INK300)
    brand_footer(d, W, H, u)
    return im


def features():
    return [(T[f"f{i}_label"], T[f"f{i}_body"]) for i in range(1, 7)]


if __name__ == "__main__":
    import sys
    lang = "en"
    args = sys.argv[1:]
    if "--lang" in args:
        lang = args[args.index("--lang") + 1]
    set_lang(lang)
    frames_root = "frames" if lang == "en" else f"frames-{lang}"
    for size, (W, H) in SIZES.items():
        out = os.path.join(HERE, frames_root, size)
        os.makedirs(out, exist_ok=True)
        title(W, H).save(os.path.join(out, "01-title.png"))
        bullets(W, H, T["kicker"], T["features_heading"], features()).save(
            os.path.join(out, "02-features.png"))
        cta(W, H).save(os.path.join(out, "04-cta.png"))
        print("built", lang, size)
