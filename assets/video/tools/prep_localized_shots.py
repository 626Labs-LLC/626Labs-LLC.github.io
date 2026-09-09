"""Prepare per-language screenshot sets for a localized trailer build.

Derives the English crop boxes by locating each shots-remote/cropped/
image inside its uncropped original (exact subimage match — the crops
came from these exact files), records them to shot-crops.json, then
pulls each language's captures from the ROROROblox repo and applies the
same boxes. The capture harness is language-independent (ROROROblox
#206), so window geometry — and therefore the boxes — transfer.

Language folders resolve `-en`-suffixed reuse files (a shot the fleet
deliberately reused from English) to their base names.

Output: src/shots-<lang>/cropped/*.png + src/shot-crops.json.
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image

SRC = r"C:\Users\estev\Projects\626labs-hub\assets\video\rororo\src"
REPO = r"C:\Users\estev\Projects\ROROROblox"
REF = "origin/main"
LANGS = ["fr", "de", "ru", "pt-BR", "pl", "es"]
SHOTS = ["01-accounts-running", "02-themes", "04-games", "05-diagnostics",
         "06-history", "07-plugins", "08-theme-builder", "09-compact",
         "10-multi-instance"]


def find_box(original, cropped):
    """Locate cropped inside original by matching a distinctive scanline."""
    o = np.asarray(original.convert("RGB"))
    c = np.asarray(cropped.convert("RGB"))
    ch, cw = c.shape[:2]
    probe_row = ch // 2
    probe = c[probe_row]
    oh, ow = o.shape[:2]
    for y in range(oh - ch + 1):
        row = o[y + probe_row]
        # slide horizontally: compare the full probe row at each x
        for x in range(ow - cw + 1):
            if np.array_equal(row[x:x + cw], probe):
                if np.array_equal(o[y:y + ch, x:x + cw], c):
                    return (x, y, x + cw, y + ch)
    raise RuntimeError("crop not found in original")


def derive_crops():
    crops_path = os.path.join(SRC, "shot-crops.json")
    if os.path.exists(crops_path):
        return json.load(open(crops_path))
    crops = {}
    for name in SHOTS:
        orig = Image.open(os.path.join(SRC, "shots-remote", f"{name}.png"))
        crop = Image.open(os.path.join(SRC, "shots-remote", "cropped", f"{name}.png"))
        box = find_box(orig, crop)
        crops[name] = box
        print(f"{name}: box {box}", flush=True)
    json.dump(crops, open(crops_path, "w"), indent=2)
    return crops


def repo_file(path):
    p = subprocess.run(["git", "-C", REPO, "show", f"{REF}:{path}"],
                       capture_output=True, check=True)
    return p.stdout


def main():
    crops = derive_crops()
    listing = subprocess.run(
        ["git", "-C", REPO, "ls-tree", "-r", REF, "--name-only",
         "docs/store/screenshots"],
        capture_output=True, text=True, check=True).stdout.splitlines()
    for lang in LANGS:
        out = os.path.join(SRC, f"shots-{lang}", "cropped")
        os.makedirs(out, exist_ok=True)
        reused = []
        for name in SHOTS:
            candidates = [p for p in listing
                          if p.startswith(f"docs/store/screenshots/{lang}/{name}")]
            if not candidates:
                raise SystemExit(f"{lang}: no capture for {name}")
            path = candidates[0]
            if path.endswith("-en.png"):
                reused.append(name)
            raw = os.path.join(SRC, f"shots-{lang}", f"{name}.png")
            with open(raw, "wb") as f:
                f.write(repo_file(path))
            im = Image.open(raw)
            if im.size != (1920, 1080):
                raise SystemExit(f"{lang}/{name}: unexpected size {im.size}")
            im.crop(crops[name]).save(os.path.join(out, f"{name}.png"))
        note = f" (EN reuse: {', '.join(reused)})" if reused else ""
        print(f"{lang}: {len(SHOTS)} shots cropped{note}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
