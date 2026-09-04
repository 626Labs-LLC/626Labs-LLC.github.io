"""Build branded social/OG cards — one per local Field Note — in the ACTIVE
theme's raster treatment.

Every on-site Field Note gets a unique 1200x630 share image instead of the
generic brand banner. The card is the theme's field (scripts/
raster_theme.py: color, texture, glows when the theme glows) with the
story's title as the hero in Space Grotesk, a rule under it (the cyan->
magenta hairline, or the printer's color bar when the theme carries one),
the dek (Inter italic, or Source Serif 4 when the theme's `bodyFace` is
serif), a mono dateline top-right, and a footer. render-hub.py points each
story page's og:image (and its BlogPosting JSON-LD `image`) at the
generated card when it exists, and falls back to
assets/brand/medium-header-1500x600.png when it doesn't.

Inputs:
  content/stories/*.md          — local published Field Notes (frontmatter)
  assets/brand/icon-transparent-512.png — the lockup mark
  themes/<active>/theme.json    — the `raster` block
  fonts/SpaceGrotesk-Variable.ttf, fonts/Inter-Italic-Variable.ttf,
  fonts/SourceSerif4-Variable.ttf, fonts/JetBrainsMono-Variable.ttf

Outputs (under assets/og/ — generated; don't hand-edit):
  assets/og/<slug>.png          — one per local published story, 1200x630

CI runs this automatically: rebuild-hub.yml builds the cards before rendering
on any push to content/stories/**, and rotate-theme.yml rebuilds them in the
incoming theme on the 1st, so a new story or a new month gets its cards with
no manual step. Run it by hand only for a local preview.

Usage:
  python scripts/build-og-cards.py          # (re)generate every card
  python scripts/build-og-cards.py --check   # CI/idempotency: nonzero if any
                                             # card is missing or out of date
  python scripts/build-og-cards.py --theme <slug> --out <dir>   # a queued theme,
                                             # written outside the tree

Determinism: PIL writes no timestamp chunk and the grain is seeded, so
identical frontmatter -> identical bytes on one platform. --check
regenerates in memory and byte-compares, so a stale or missing card fails
loudly the same way render-hub --check catches drift. FreeType rasterizes a
few bytes differently across platforms, so the ubuntu runner is the source
of truth for assets/og and a Windows --check shows a harmless diff.
"""
from __future__ import annotations

import importlib.util
import io
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
import raster_theme as rt  # noqa: E402 — sibling module in scripts/

ASSETS = ROOT / "assets"
OUT = ASSETS / "og"
FONTS = ROOT / "fonts"
ICON = ASSETS / "brand" / "icon-transparent-512.png"

CYAN = rt.CYAN
MAGENTA = rt.MAGENTA

W, H = 1200, 630
MARGIN = 72

SG = FONTS / "SpaceGrotesk-Variable.ttf"
INTER_IT = FONTS / "Inter-Italic-Variable.ttf"
SERIF = FONTS / "SourceSerif4-Variable.ttf"
MONO = FONTS / "JetBrainsMono-Variable.ttf"


def _load_render_hub():
    """Import render-hub.py (hyphenated -> not a normal module name) so we
    reuse its story discovery, slug, and reading-time logic instead of
    re-parsing frontmatter and drifting from the renderer."""
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
            pass  # not a variable font / wrong axis count — use the default instance
    return f


def _gradient_strip(width: int, height: int, c1, c2) -> Image.Image:
    """Horizontal c1->c2 gradient, vectorized."""
    import numpy as np
    t = np.linspace(0, 1, max(1, width))[None, :, None]
    row = (np.array(c1) * (1 - t) + np.array(c2) * t).astype(np.uint8)  # (1,width,3)
    arr = np.repeat(row, height, axis=0)
    return Image.fromarray(arr, "RGB").convert("RGBA")


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_w: int) -> list[str]:
    """Greedy word wrap to fit max_w; long single words are left intact."""
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


def _dek_font(raster: rt.Raster, size: int) -> ImageFont.FreeTypeFont:
    """The dek's face follows the theme's body face: Inter italic on a lit
    theme, Source Serif 4 (roman, weight 400, optical size at the pixel
    size) on a printed one."""
    if raster.body_face == "serif":
        return _font(SERIF, size, [400, max(8, min(60, size))])
    return _font(INTER_IT, size, [14, 400])


def build_card(story: dict, rh, raster: rt.Raster | None = None) -> Image.Image:
    """Compose the 1200x630 card for one story in `raster` (the active
    theme's when None)."""
    if raster is None:
        raster = rt.load()
    title = str(story.get("title", "")).strip()
    dek = str(story.get("subtitle") or story.get("tagline") or "").strip()
    published = str(story.get("published", "")).strip()
    author = str(story.get("author") or "626 Labs").strip()
    read_min = rh._reading_minutes(str(story.get("_body", "")))
    ink = raster.ink + (255,)
    dim = raster.dim + (255,)

    canvas = rt.paint_field(W, H, raster, glows=(
        (0.16, 0.22, CYAN, 78, 0.55),
        (0.86, 0.84, MAGENTA, 66, 0.58),
    ))
    draw = ImageDraw.Draw(canvas)

    # --- top band: icon + "626 Labs" lockup (left), FIELD NOTE dateline (right) ---
    icon = Image.open(ICON).convert("RGBA")
    icon_h = 52
    icon = icon.resize((icon_h, icon_h), Image.LANCZOS)
    top_y = MARGIN
    canvas.alpha_composite(icon, dest=(MARGIN, top_y - 2))

    word_font = _font(SG, 30, [700])
    wx = MARGIN + icon_h + 18
    word_mid_y = top_y + icon_h // 2 - 22
    draw.text((wx, word_mid_y), "626", font=word_font, fill=CYAN + (255,))
    c_w = draw.textlength("626", font=word_font)
    draw.text((wx + c_w, word_mid_y), " Labs", font=word_font, fill=ink)

    eyebrow = f"FIELD NOTE  ·  {published}" if published else "FIELD NOTE"
    eb_font = _font(MONO, 20, [500])
    eb_w = draw.textlength(eyebrow, font=eb_font)
    draw.text((W - MARGIN - eb_w, top_y + 6), eyebrow, font=eb_font, fill=dim)

    # --- centered stack: title -> rule -> dek, in the band below the lockup ---
    band_top = top_y + icon_h + 40
    footer_top = H - MARGIN - 30
    avail_w = W - 2 * MARGIN
    bottom_gap = 26                       # keep the dek clear of the footer
    avail_h = footer_top - band_top - bottom_gap

    # Dek wrap is independent of title size — measure it first so the title
    # fitter can budget the vertical space it leaves behind.
    dek_size = 27
    dek_font = _dek_font(raster, dek_size) if dek else None
    dek_lines = _wrap(draw, dek, dek_font, avail_w)[:2] if dek else []
    dek_gap = int(dek_size * 0.28)
    dek_pad_top = 28 if dek_lines else 0
    dek_h = (len(dek_lines) * dek_size + (len(dek_lines) - 1) * dek_gap) if dek_lines else 0

    # The rule under the title: the cyan->magenta hairline, or the printer's
    # color bar standing in for it on a theme that carries one.
    rule_pad_top, rule_h, rule_w = 30, 5, 320
    if raster.color_bar:
        rule_h = rt.color_bar_size(H)
    rule_block = rule_pad_top + rule_h

    # Largest Space Grotesk Bold where the title wraps into <= 3 lines AND the
    # whole stack (title + rule + dek) fits the vertical budget. Short-worded
    # titles otherwise stay big enough at 3 lines to shove the dek into the
    # footer — shrink against height, not just line count.
    def _title_at(size):
        f = _font(SG, size, [700])
        ls = _wrap(draw, title, f, avail_w)
        lg = int(size * 0.16)
        return f, ls, lg, len(ls) * size + (len(ls) - 1) * lg

    t_size = 78
    while t_size > 42:
        title_font, lines, line_gap, title_h = _title_at(t_size)
        if len(lines) <= 3 and title_h + rule_block + dek_pad_top + dek_h <= avail_h:
            break
        t_size -= 2
    else:
        title_font, lines, line_gap, _ = _title_at(42)
        lines = lines[:3]
        title_h = len(lines) * 42 + (len(lines) - 1) * line_gap

    stack_h = title_h + rule_block + dek_pad_top + dek_h
    y = band_top + max(0, (avail_h - stack_h) // 2)

    for ln in lines:
        draw.text((MARGIN, y), ln, font=title_font, fill=ink)
        y += t_size + line_gap
    y += rule_pad_top - line_gap
    if raster.color_bar:
        canvas.alpha_composite(rt.color_bar(raster, rule_h), dest=(MARGIN, y))
    else:
        canvas.alpha_composite(_gradient_strip(rule_w, rule_h, CYAN, MAGENTA), dest=(MARGIN, y))
    y += rule_h + dek_pad_top
    for ln in dek_lines:
        draw.text((MARGIN, y), ln, font=dek_font, fill=dim)
        y += dek_size + dek_gap

    # --- footer: domain (left), author + reading time (right) ---
    dom_font = _font(SG, 25, [600])
    draw.text((MARGIN, footer_top), "626labs.dev", font=dom_font, fill=ink)
    foot_r = f"{author}  ·  {read_min} min read"
    fr_font = _font(MONO, 20, [400])
    fr_w = draw.textlength(foot_r, font=fr_font)
    draw.text((W - MARGIN - fr_w, footer_top + 2), foot_r, font=fr_font, fill=dim)

    return canvas.convert("RGB")


def _png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def main(argv: list[str]) -> int:
    slug, out_dir, rest = rt.parse_args(argv)
    check = "--check" in rest
    unknown = [a for a in rest if a != "--check"]
    if unknown:
        print(f"usage: build-og-cards.py [--check] [--theme <slug>] [--out <dir>]  (unknown: {unknown})",
              file=sys.stderr)
        return 2
    out = out_dir or OUT
    raster = rt.load(slug)
    rh = _load_render_hub()
    stories = [s for s in rh.discover_stories() if not s.get("external_url")]

    if check:
        stale: list[str] = []
        for s in stories:
            slug_ = rh.story_slug(s)
            path = out / f"{slug_}.png"
            want = _png_bytes(build_card(s, rh, raster))
            have = path.read_bytes() if path.exists() else None
            if have != want:
                stale.append(slug_ + ("" if path.exists() else " (missing)"))
        if stale:
            print(f"OG cards out of date ({raster.slug}):")
            for s in stale:
                print(f"  - {s}")
            print("Run: python scripts/build-og-cards.py")
            return 1
        print(f"OG cards up to date ({len(stories)} cards, {raster.slug}).")
        return 0

    out.mkdir(parents=True, exist_ok=True)
    for s in stories:
        slug_ = rh.story_slug(s)
        path = out / f"{slug_}.png"
        path.write_bytes(_png_bytes(build_card(s, rh, raster)))
        print(f"  wrote {path}  ({W}x{H})")
    print(f"{len(stories)} OG card(s) built ({raster.slug}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
