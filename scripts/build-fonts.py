#!/usr/bin/env python3
"""Build the self-hosted web fonts (woff2) the site serves from /fonts/.

Source TTFs live in fonts/. Three families arrived as variable TTFs (Inter,
Inter Italic, Space Grotesk). Two more are fetched once from their upstream
releases (SIL OFL) so the weight range the site asks for is never narrower
than the source: JetBrains Mono shipped as a static Regular, and the brand's
UPPERCASE meta labels use the heavier weights; Source Serif 4 was never
vendored at all, and the Slate Broadsheet (2026-10) sets body copy in it,
so every page reading --font-body or --font-serif fell to Georgia.

Run after changing any source TTF:

    python scripts/build-fonts.py

Outputs fonts/*.woff2, consumed by fonts/fonts.css. Idempotent — re-running
just rewrites the woff2 from current sources; an upstream fetch only happens
when its TTF is absent. Needs fontTools + brotli.
"""
from __future__ import annotations

import io
import sys
import urllib.request
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "fonts"

# Official JetBrains Mono variable font (SIL OFL) — wght axis, unlike the
# static Regular originally vendored here.
JBMONO_URL = "https://github.com/JetBrains/JetBrainsMono/raw/master/fonts/variable/JetBrainsMono%5Bwght%5D.ttf"
JBMONO_TTF = FONTS / "JetBrainsMono-Variable.ttf"

# Official Source Serif 4 variable fonts (SIL OFL), roman and italic, pinned
# to the 4.005R release tag so a re-fetch reproduces the same bytes. Both
# carry wght 200-900 and opsz 8-60.
SOURCE_SERIF_ROMAN_URL = "https://github.com/adobe-fonts/source-serif/raw/4.005R/VAR/SourceSerif4Variable-Roman.ttf"
SOURCE_SERIF_ITALIC_URL = "https://github.com/adobe-fonts/source-serif/raw/4.005R/VAR/SourceSerif4Variable-Italic.ttf"
SOURCE_SERIF_ROMAN_TTF = FONTS / "SourceSerif4-Variable.ttf"
SOURCE_SERIF_ITALIC_TTF = FONTS / "SourceSerif4-Italic-Variable.ttf"

# (upstream URL, local TTF) — fetched once, then treated like any vendored
# source. Each is sanity-checked for a wght axis before it is trusted.
UPSTREAM = [
    (JBMONO_URL, JBMONO_TTF),
    (SOURCE_SERIF_ROMAN_URL, SOURCE_SERIF_ROMAN_TTF),
    (SOURCE_SERIF_ITALIC_URL, SOURCE_SERIF_ITALIC_TTF),
]

# (source TTF, output woff2) — every source must carry the full weight range
# the site asks for so self-hosting never regresses a weight.
JOBS = [
    ("Inter-Variable.ttf", "Inter-Variable.woff2"),
    ("Inter-Italic-Variable.ttf", "Inter-Italic-Variable.woff2"),
    ("SpaceGrotesk-Variable.ttf", "SpaceGrotesk-Variable.woff2"),
    ("JetBrainsMono-Variable.ttf", "JetBrainsMono-Variable.woff2"),
    ("SourceSerif4-Variable.ttf", "SourceSerif4-Variable.woff2"),
    ("SourceSerif4-Italic-Variable.ttf", "SourceSerif4-Italic-Variable.woff2"),
]


def ensure_upstream(url: str, dest: Path) -> None:
    if dest.exists():
        return
    print(f"fetching {dest.name} <- {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
    data = urllib.request.urlopen(req, timeout=60).read()
    # Sanity-check it actually carries a wght axis before trusting it.
    axes = {a.axisTag for a in TTFont(io.BytesIO(data))["fvar"].axes}
    if "wght" not in axes:
        sys.exit(f"fetched {dest.name} has no wght axis — aborting")
    dest.write_bytes(data)


def main() -> int:
    for url, dest in UPSTREAM:
        ensure_upstream(url, dest)
    for src_name, out_name in JOBS:
        src = FONTS / src_name
        if not src.exists():
            sys.exit(f"missing source font: {src.relative_to(ROOT)}")
        f = TTFont(src)
        f.flavor = "woff2"
        f.save(FONTS / out_name)
        kb_in, kb_out = src.stat().st_size // 1024, (FONTS / out_name).stat().st_size // 1024
        print(f"  {out_name:34} {kb_in:4}KB -> {kb_out:4}KB")
    print(f"{len(JOBS)} web fonts built into {FONTS.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
