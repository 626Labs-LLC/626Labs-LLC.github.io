"""Build a 5:2 (1500x600) branded header image for a Field Note.

For X Articles / social covers that want a 5:2 aspect ratio (X's article header,
LinkedIn covers, etc.). Same brand signature as the OG card (navy field +
cyan/magenta glow, the 626 Labs lockup, a hero line, a cyan->magenta hairline,
a dek, and a footer) retuned for the wide 5:2 format.

NOT wired into CI. Outputs under assets/social/, which CI never regenerates —
so a Windows-rendered PNG is safe to commit here (unlike assets/og/, where the
ubuntu workflow is the byte-stable source of truth). Run by hand:

  python scripts/build-x-header.py 2026-05-29-same-code-triple-thinking
  python scripts/build-x-header.py <slug> --hero "Short punchy line"
  python scripts/build-x-header.py <slug> --dek "Override dek" --out path.png

By default the hero is the story title and the dek is its tagline (falling back
to the subtitle). For a wide 5:2 banner a short hero usually reads stronger than
a full sentence title — override with --hero when the title is long.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
OUT_DIR = ASSETS / "social"
FONTS = ROOT / "fonts"
ICON = ASSETS / "brand" / "icon-transparent-512.png"

# Brand tokens — mirror scripts/build-og-cards.py / export-brand.py.
CYAN = (23, 212, 250)
MAGENTA = (242, 47, 137)
NAVY = (15, 31, 49)
INK = (231, 237, 245)
DIM = (138, 153, 174)

W, H = 1500, 600          # 5:2
MARGIN = 64

SG = FONTS / "SpaceGrotesk-Variable.ttf"
INTER_IT = FONTS / "Inter-Italic-Variable.ttf"
MONO = FONTS / "JetBrainsMono-Variable.ttf"


def _load_render_hub():
    """Reuse render-hub's story discovery / slug / reading-time so this never
    drifts from the renderer."""
    spec = importlib.util.spec_from_file_location("render_hub", ROOT / "scripts" / "render-hub.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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


def build_header(hero: str, dek: str, published: str, author: str, read_min: int) -> Image.Image:
    canvas = Image.new("RGBA", (W, H), NAVY + (255,))
    canvas.alpha_composite(_radial_glow(0.13, 0.24, CYAN, 82, 0.50))
    canvas.alpha_composite(_radial_glow(0.89, 0.82, MAGENTA, 70, 0.52))
    draw = ImageDraw.Draw(canvas)

    # --- top band: icon + "626 Labs" lockup (left), FIELD NOTE eyebrow (right) ---
    icon = Image.open(ICON).convert("RGBA").resize((50, 50), Image.LANCZOS)
    top_y = MARGIN
    canvas.alpha_composite(icon, dest=(MARGIN, top_y - 2))

    word_font = _font(SG, 30, [700])
    wx = MARGIN + 50 + 16
    wmy = top_y + 25 - 22
    draw.text((wx, wmy), "626", font=word_font, fill=CYAN + (255,))
    c_w = draw.textlength("626", font=word_font)
    draw.text((wx + c_w, wmy), " Labs", font=word_font, fill=INK + (255,))

    eyebrow = f"FIELD NOTE  ·  {published}" if published else "FIELD NOTE"
    eb_font = _font(MONO, 19, [500])
    eb_w = draw.textlength(eyebrow, font=eb_font)
    draw.text((W - MARGIN - eb_w, top_y + 6), eyebrow, font=eb_font, fill=DIM + (255,))

    # --- centered stack: hero -> hairline -> dek ---
    band_top = top_y + 50 + 34
    footer_top = H - MARGIN - 26
    avail_w = W - 2 * MARGIN
    bottom_gap = 22
    avail_h = footer_top - band_top - bottom_gap

    dek_size = 26
    dek_font = _font(INTER_IT, dek_size, [14, 400]) if dek else None
    dek_lines = _wrap(draw, dek, dek_font, avail_w)[:2] if dek else []
    dek_gap = int(dek_size * 0.28)
    dek_pad_top = 24 if dek_lines else 0
    dek_h = (len(dek_lines) * dek_size + (len(dek_lines) - 1) * dek_gap) if dek_lines else 0

    rule_pad_top, rule_h, rule_w = 26, 5, 300
    rule_block = rule_pad_top + rule_h

    def _hero_at(size):
        f = _font(SG, size, [700])
        ls = _wrap(draw, hero, f, avail_w)
        lg = int(size * 0.14)
        return f, ls, lg, len(ls) * size + (len(ls) - 1) * lg

    t_size = 96
    while t_size > 40:
        hero_font, lines, line_gap, hero_h = _hero_at(t_size)
        if len(lines) <= 3 and hero_h + rule_block + dek_pad_top + dek_h <= avail_h:
            break
        t_size -= 2
    else:
        hero_font, lines, line_gap, _ = _hero_at(40)
        lines = lines[:3]
        hero_h = len(lines) * 40 + (len(lines) - 1) * line_gap

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

    # --- footer: domain (left), author + reading time (right) ---
    dom_font = _font(SG, 24, [600])
    draw.text((MARGIN, footer_top), "626labs.dev", font=dom_font, fill=INK + (255,))
    foot_r = f"{author}  ·  {read_min} min read"
    fr_font = _font(MONO, 19, [400])
    fr_w = draw.textlength(foot_r, font=fr_font)
    draw.text((W - MARGIN - fr_w, footer_top + 2), foot_r, font=fr_font, fill=DIM + (255,))

    return canvas.convert("RGB")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Build a 5:2 branded header for a Field Note.")
    ap.add_argument("slug", help="Field Note slug (filename stem under content/stories/)")
    ap.add_argument("--hero", default=None, help="Override hero text (default: story title)")
    ap.add_argument("--dek", default=None, help="Override dek (default: tagline, then subtitle)")
    ap.add_argument("--out", default=None, help="Output path (default: assets/social/<slug>-x-1500x600.png)")
    a = ap.parse_args(argv)

    rh = _load_render_hub()
    stories = {rh.story_slug(s): s for s in rh.discover_stories()}
    s = stories.get(a.slug)
    if not s:
        print(f"No published story with slug {a.slug!r}.")
        print("Have: " + ", ".join(sorted(stories)))
        return 1

    hero = a.hero if a.hero is not None else str(s.get("title", "")).strip()
    dek = a.dek if a.dek is not None else str(s.get("tagline") or s.get("subtitle") or "").strip()
    published = str(s.get("published", "")).strip()
    author = str(s.get("author") or "626 Labs").strip()
    read_min = rh._reading_minutes(str(s.get("_body", "")))

    img = build_header(hero, dek, published, author, read_min)
    out = Path(a.out) if a.out else OUT_DIR / f"{a.slug}-x-{W}x{H}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG", optimize=True)
    print(f"wrote {out}  ({W}x{H}, 5:2)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
