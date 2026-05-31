"""Build a 1280x640 branded GitHub social-preview for any 626 Labs repo.

GitHub's social preview (repo Settings -> Social preview) is 1280x640 and is
used on every shared repo/release link. The vibe-* plugins already get one from
their plugin-page banner; this generates the same brand signature for the repos
that aren't plugins (RORORO, Sanduhr, the mod launcher, games, apps) from
explicit copy — no per-product icon required.

Brand signature: navy field, cyan (top-left) + magenta (bottom-right) glow, the
626 Labs lockup, a hero line, a cyan->magenta hairline, a tagline, and a footer
(626labs.dev + optional right meta).

Not wired into CI. Run by hand:

  python scripts/build-repo-preview.py --name "RORORO" \
      --tagline "Mac-native multi-Roblox. Account vault, multi-instance." \
      --eyebrow "626 LABS  ·  for Roblox" --foot-right "macOS" \
      --out assets/social/github-previews/rororo-mac.png

GitHub has no API to set a social preview — upload each PNG by hand at
github.com/<owner>/<repo>/settings -> Social preview.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
FONTS = ROOT / "fonts"
ICON = ASSETS / "brand" / "icon-transparent-512.png"

# Brand tokens — mirror scripts/build-og-cards.py / export-brand.py.
CYAN = (23, 212, 250)
MAGENTA = (242, 47, 137)
NAVY = (15, 31, 49)
INK = (231, 237, 245)
DIM = (138, 153, 174)

W, H = 1280, 640          # GitHub social-preview spec (2:1)
MARGIN = 64

SG = FONTS / "SpaceGrotesk-Variable.ttf"
INTER_IT = FONTS / "Inter-Italic-Variable.ttf"
MONO = FONTS / "JetBrainsMono-Variable.ttf"


def _font(path: Path, size: int, axes: list[int] | None = None) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(path), size)
    if axes:
        try:
            f.set_variation_by_axes(axes)
        except Exception:
            pass
    return f


def _radial_glow(cx: float, cy: float, color, max_alpha: int, radius: float) -> Image.Image:
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    yy, xx = np.indices((H, W))
    dist = np.sqrt((xx - cx * W) ** 2 + (yy - cy * H) ** 2)
    falloff = np.clip(1 - dist / (radius * max(W, H)), 0, 1) ** 2
    arr[..., 0], arr[..., 1], arr[..., 2] = color
    arr[..., 3] = (falloff * max_alpha).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def _gradient_strip(width: int, height: int, c1, c2) -> Image.Image:
    t = np.linspace(0, 1, max(1, width))[None, :, None]
    row = (np.array(c1) * (1 - t) + np.array(c2) * t).astype(np.uint8)
    arr = np.repeat(row, height, axis=0)
    return Image.fromarray(arr, "RGB").convert("RGBA")


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_w: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if draw.textlength(trial, font=font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def build_preview(name: str, tagline: str, eyebrow: str, foot_right: str) -> Image.Image:
    canvas = Image.new("RGBA", (W, H), NAVY + (255,))
    canvas.alpha_composite(_radial_glow(0.14, 0.22, CYAN, 84, 0.52))
    canvas.alpha_composite(_radial_glow(0.88, 0.84, MAGENTA, 72, 0.54))
    draw = ImageDraw.Draw(canvas)

    # --- top band: icon + "626 Labs" lockup (left), eyebrow (right) ---
    icon = Image.open(ICON).convert("RGBA").resize((52, 52), Image.LANCZOS)
    top_y = MARGIN
    canvas.alpha_composite(icon, dest=(MARGIN, top_y - 2))

    word_font = _font(SG, 31, [700])
    wx = MARGIN + 52 + 16
    wmy = top_y + 26 - 23
    draw.text((wx, wmy), "626", font=word_font, fill=CYAN + (255,))
    c_w = draw.textlength("626", font=word_font)
    draw.text((wx + c_w, wmy), " Labs", font=word_font, fill=INK + (255,))

    if eyebrow:
        eb_font = _font(MONO, 19, [500])
        eb_w = draw.textlength(eyebrow, font=eb_font)
        draw.text((W - MARGIN - eb_w, top_y + 8), eyebrow, font=eb_font, fill=DIM + (255,))

    # --- centered stack: hero -> hairline -> tagline ---
    band_top = top_y + 52 + 36
    footer_top = H - MARGIN - 28
    avail_w = W - 2 * MARGIN
    avail_h = footer_top - band_top - 24

    dek_size = 27
    dek_font = _font(INTER_IT, dek_size, [14, 400]) if tagline else None
    dek_lines = _wrap(draw, tagline, dek_font, avail_w)[:2] if tagline else []
    dek_gap = int(dek_size * 0.28)
    dek_pad_top = 26 if dek_lines else 0
    dek_h = (len(dek_lines) * dek_size + (len(dek_lines) - 1) * dek_gap) if dek_lines else 0

    rule_pad_top, rule_h, rule_w = 28, 5, 300
    rule_block = rule_pad_top + rule_h

    def _hero_at(size):
        f = _font(SG, size, [700])
        ls = _wrap(draw, name, f, avail_w)
        lg = int(size * 0.14)
        return f, ls, lg, len(ls) * size + (len(ls) - 1) * lg

    t_size = 104
    while t_size > 44:
        hero_font, lines, line_gap, hero_h = _hero_at(t_size)
        if len(lines) <= 2 and hero_h + rule_block + dek_pad_top + dek_h <= avail_h:
            break
        t_size -= 2
    else:
        hero_font, lines, line_gap, _ = _hero_at(44)
        lines = lines[:2]
        hero_h = len(lines) * 44 + (len(lines) - 1) * line_gap

    stack_h = hero_h + rule_block + dek_pad_top + dek_h
    y = band_top + max(0, (avail_h - stack_h) // 2)

    for ln in lines:
        draw.text((MARGIN, y), ln, font=hero_font, fill=INK + (255,))
        y += t_size + line_gap
    y += rule_pad_top - line_gap
    canvas.alpha_composite(_gradient_strip(rule_w, rule_h, CYAN, MAGENTA), dest=(MARGIN, y))
    y += rule_h + dek_pad_top
    for ln in dek_lines:
        draw.text((MARGIN, y), ln, font=dek_font, fill=DIM + (255,))
        y += dek_size + dek_gap

    # --- footer: domain (left), optional meta (right) ---
    dom_font = _font(SG, 25, [600])
    draw.text((MARGIN, footer_top), "626labs.dev", font=dom_font, fill=INK + (255,))
    if foot_right:
        fr_font = _font(MONO, 19, [400])
        fr_w = draw.textlength(foot_right, font=fr_font)
        draw.text((W - MARGIN - fr_w, footer_top + 3), foot_right, font=fr_font, fill=DIM + (255,))

    return canvas.convert("RGB")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Build a 1280x640 branded GitHub social-preview.")
    ap.add_argument("--name", required=True, help="Hero text (product name)")
    ap.add_argument("--tagline", default="", help="Tagline (dek)")
    ap.add_argument("--eyebrow", default="626 LABS", help="Top-right mono label")
    ap.add_argument("--foot-right", default="", help="Optional bottom-right meta (platform, repo)")
    ap.add_argument("--out", required=True, help="Output PNG path")
    a = ap.parse_args(argv)

    img = build_preview(a.name, a.tagline, a.eyebrow, a.foot_right)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG", optimize=True)
    print(f"wrote {out}  ({W}x{H}, 2:1)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
