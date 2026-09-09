"""Extract the localized card text for make_frames.py.

Parses ROROROblox docs/videos/launch-video-script.md (the trailer's
visual layer — three cards, seven languages, slot budgets) into
src/card-text.json keyed lang -> element -> string. Where the doc
provides a shorter alternate (the line outgrew its slot), the alternate
wins — that is what the alternates are for.
"""
import json
import os
import re
import subprocess
import sys

REPO = r"C:\Users\estev\Projects\ROROROblox"
REF = "origin/main"
OUT = r"C:\Users\estev\Projects\626labs-hub\assets\video\rororo\src\card-text.json"

LANG_NAMES = {"Français": "fr", "Deutsch": "de", "Русский": "ru",
              "Português (BR)": "pt-BR", "Polski": "pl", "Español": "es"}
# (card heading fragment, element heading) -> our key
ELEMENTS = {
    ("Card 1", "Tagline"): "tagline",
    ("Card 1", "Badge"): "badge",
    ("Card 2", "Eyebrow"): "kicker",
    ("Card 2", "Headline"): "features_heading",
    ("Card 2", "1 Label"): "f1_label", ("Card 2", "1 Body"): "f1_body",
    ("Card 2", "2 Label"): "f2_label", ("Card 2", "2 Body"): "f2_body",
    ("Card 2", "3 Label"): "f3_label", ("Card 2", "3 Body"): "f3_body",
    ("Card 2", "4 Label"): "f4_label", ("Card 2", "4 Body"): "f4_body",
    ("Card 2", "5 Label"): "f5_label", ("Card 2", "5 Body"): "f5_body",
    ("Card 2", "6 Label"): "f6_label", ("Card 2", "6 Body"): "f6_body",
    ("Card 3", "Badge"): "cta_badge",
    ("Card 3", "Headline"): "cta_heading",
    ("Card 3", "Note"): "cta_note",
    ("Card 3", "Disclaimer"): "cta_legal",
}


def clean(cell):
    s = cell.strip()
    s = re.sub(r"\*\(\d+\)\*", "", s)          # *(34)* char counts
    s = s.replace("✓", "").strip()
    s = s.strip("`")
    return s


def main():
    md = subprocess.run(
        ["git", "-C", REPO, "show", f"{REF}:docs/videos/launch-video-script.md"],
        capture_output=True, text=True, encoding="utf-8", check=True).stdout

    data = {code: {} for code in LANG_NAMES.values()}
    card = None
    element = None
    for line in md.splitlines():
        h2 = re.match(r"## (Card \d)", line)
        if h2:
            card = h2.group(1)
            continue
        if line.startswith("## "):
            card = None
            continue
        h3 = re.match(r"### (.+)", line)
        if h3:
            element = h3.group(1).strip()
            continue
        if not (card and element) or (card, element) not in ELEMENTS:
            continue
        if not line.startswith("|") or line.startswith("|---") or "| Language |" in line:
            continue
        cells = [c for c in line.split("|")][1:-1]
        if len(cells) < 4:
            continue
        lang_name = cells[0].strip()
        if lang_name not in LANG_NAMES:
            continue
        primary, shorter = clean(cells[1]), clean(cells[3])
        value = shorter if shorter and shorter != "—" else primary
        data[LANG_NAMES[lang_name]][ELEMENTS[(card, element)]] = value

    expected = set(ELEMENTS.values())
    for code, d in data.items():
        missing = expected - set(d)
        if missing:
            raise SystemExit(f"{code}: missing {sorted(missing)}")
    json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"card-text.json: {len(data)} languages x {len(expected)} elements")


if __name__ == "__main__":
    sys.exit(main())
