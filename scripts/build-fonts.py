#!/usr/bin/env python3
"""Build the self-hosted web fonts (woff2) the site serves from /fonts/.

Source TTFs live in fonts/. Three families ship as variable TTFs already
(Inter, Inter Italic, Space Grotesk); JetBrains Mono shipped as a static
Regular, so this fetches the official variable build (OFL) once to keep the
mono weight range (the brand's UPPERCASE meta labels use the heavier weights).

Run after changing any source TTF:

    python scripts/build-fonts.py

Outputs fonts/*.woff2, consumed by fonts/fonts.css. Idempotent — re-running
just rewrites the woff2 from current sources. Needs fontTools + brotli.
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

# (source TTF, output woff2) — every source must carry the full weight range
# the site asks for so self-hosting never regresses a weight.
JOBS = [
    ("Inter-Variable.ttf", "Inter-Variable.woff2"),
    ("Inter-Italic-Variable.ttf", "Inter-Italic-Variable.woff2"),
    ("SpaceGrotesk-Variable.ttf", "SpaceGrotesk-Variable.woff2"),
    ("JetBrainsMono-Variable.ttf", "JetBrainsMono-Variable.woff2"),
]


def ensure_jbmono() -> None:
    if JBMONO_TTF.exists():
        return
    print(f"fetching JetBrains Mono variable -> {JBMONO_TTF.name}")
    req = urllib.request.Request(JBMONO_URL, headers={"User-Agent": "curl/8"})
    data = urllib.request.urlopen(req, timeout=60).read()
    # Sanity-check it actually carries a wght axis before trusting it.
    axes = {a.axisTag for a in TTFont(io.BytesIO(data))["fvar"].axes}
    if "wght" not in axes:
        sys.exit("fetched JetBrains Mono has no wght axis — aborting")
    JBMONO_TTF.write_bytes(data)


def main() -> int:
    ensure_jbmono()
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
