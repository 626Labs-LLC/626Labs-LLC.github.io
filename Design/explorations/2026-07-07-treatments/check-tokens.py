#!/usr/bin/env python3
"""Token-discipline gate for the 2026-07-07 treatment exploration.

Every hex literal (raw ``#`` or URL-encoded ``%23``) and every rgb()/rgba()
triple in this directory's HTML files must trace back to a color defined in
Design/colors_and_type.css. Pure white/black are allowed for hairlines and
scrims. Exit 0 = clean, exit 1 = violations listed on stdout.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOKEN_FILE = HERE.parent.parent / "colors_and_type.css"

HEX_RE = re.compile(r"(?:#|%23)([0-9a-fA-F]{6})\b")
RGB_RE = re.compile(r"rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})")


def hexes(text):
    return {"#" + h.lower() for h in HEX_RE.findall(text)}


token_text = TOKEN_FILE.read_text(encoding="utf-8")
allowed_hex = hexes(token_text)
allowed_rgb = {tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for h in allowed_hex}
allowed_rgb |= {(255, 255, 255), (0, 0, 0)}

failures = []
html_files = sorted(HERE.glob("*.html"))
for f in html_files:
    text = f.read_text(encoding="utf-8")
    for h in sorted(hexes(text) - allowed_hex):
        failures.append(f"{f.name}: {h} is not a token color")
    triples = {tuple(map(int, m)) for m in RGB_RE.findall(text)}
    for t in sorted(triples - allowed_rgb):
        failures.append(f"{f.name}: rgb{t} does not derive from a token")

if failures:
    print("\n".join(failures))
    sys.exit(1)
print(f"OK — {len(html_files)} files clean against {TOKEN_FILE.name}")
