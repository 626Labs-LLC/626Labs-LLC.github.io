"""refresh-roundup.py -- re-harvest assets/roundup/ from the sibling repos, and
write assets/roundup/index.json, the manifest that says what is in it.

Three modes:

  (default)      DRY RUN. Reads each product's source repo under
                 C:\\Users\\estev\\Projects and reports, per product, what is
                 NEW in the source, CHANGED (by content hash) or GONE from it,
                 against what assets/roundup holds. Writes nothing.
  --apply        Copies new and changed images in, then regenerates index.json.
                 Never deletes anything unless --prune is also given, and then
                 only files whose mapped source is GONE.
  --index-only   Regenerates index.json from what is in assets/roundup and
                 content/site.json. Reads no repo, so it is the one CI-safe
                 mode. Add --check to exit 1 instead of writing when the
                 committed index.json would change.

THIS BOX ONLY. The dry run and --apply read Este's estate at a fixed Windows
path; they refuse to run on anything that is not Windows, in CI (CI or
GITHUB_ACTIONS set), or when that path is missing. No workflow may call them.

What gets harvested is the PRODUCTS mapping below, and nothing else: it names
each product's local clone and its source files or directories. The rules the
July 2026 harvest followed (assets/roundup/README.md) are enforced here:

  * images only: a non-image is never copied, whatever a mapped dir holds;
  * largest variant only: in a mapped dir, files that differ only by a size
    token (app-tile-71x71 / -150x150 / -300x300) collapse to the largest;
  * no MSIX scale armies: *.scale-NNN, *.targetsize-NN, *altform-* are skipped
    in mapped dirs (a single scale variant can still be named file-by-file,
    as SnipSnap's logo-1240.png is);
  * never Marcus\\ (employer tenant) and never the work-adjacent repos
    (PriceScout*, theatre-operations-platform, CompReport). FORBIDDEN is
    checked against every mapped path before anything is read.

SVGs are hashed with CRLF folded to LF: git checks them out CRLF on this box,
so a raw-byte hash would report every SVG as changed.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROUNDUP_REL = "assets/roundup"
PROJECTS = Path(r"C:\Users\estev\Projects")

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico"}
# The only non-images assets/roundup may hold (site-doctor enforces it too).
ALLOWED_NON_IMAGES = {"README.md", "index.json"}
FIRST_HARVEST = "2026-07-08"

# Top-level directories under PROJECTS that are never read. Prefix match, so
# every PriceScout* clone is covered.
FORBIDDEN = ("Marcus", "PriceScout", "theatre-operations-platform", "CompReport")

# MSIX scale armies and friends. Skipped in mapped DIRS only.
SCALE_ARMY_RE = re.compile(r"\.scale-\d+\.|\.targetsize-\d+|altform-", re.I)
# A size token in a file name: 300x300, -1080x1080, -512 (2-4 digits).
SIZE_TOKEN_RE = re.compile(r"[-_]?\d{2,4}x\d{2,4}|[-_]\d{2,4}(?=[-_.]|$)", re.I)

NOTE = (
    "Raw brand material harvested from the 626 Labs repos, one folder per "
    "product. Paths are repo-root-relative; prefix with / for a URL on "
    "626labs.dev. icon/logo/hero are picked by name and dimensions. "
    "Regenerate with: python scripts/refresh-roundup.py --index-only"
)

# ---------------------------------------------------------------------------
# The mapping. One entry per assets/roundup/<id>/ folder.
#
#   name     display name (site.json's title wins when siteId is set)
#   siteId   the content/site.json products[] id, when there is one
#   local    the clone's directory under PROJECTS; None = no local source
#   repo     owner/repo from that clone's remote.origin.url; None = no remote.
#            Stored here so --index-only never has to read a repo; the dry
#            run re-reads the remote and reports drift.
#   rules    ("file", <src rel to clone>, <dest rel to the product folder>)
#            ("dir",  <src dir>,         <dest dir, "" = folder root>,
#                     {"variants": bool, "exclude": [regex, ...]})
#            The first rule's directory is the manifest's sourceDir.
#
# Notes on choices that are not obvious:
#   * Duplicate clones: Chef-I-s (Chef-Is has no remote), Estessistant
#     (Estesstant has none either; Estessistant is where the icon lives).
#     The July harvest used Cleanup-Ranger and Safety_Assistant; those
#     directories are gone, the space-named clones carry the same remotes.
#   * 626-labs-mod-manager reads _old-626-labs-mod-manager, the archived
#     predecessor of 626-mod-launcher (no remote).
#   * koii-tracker and rotemplate have no local source left; they stay as
#     harvested and are reported as orphans.
#   * MSIX package dirs are mapped file-by-file (the 310x310 tile and the
#     StoreLogo), never as dirs: they are build inputs, not marketing.
#   * ROROROblox docs/store/* holds listing copy next to the images; the
#     images-only rule keeps the copy out. pushover-icon is a third party's.
# ---------------------------------------------------------------------------
DIR = "dir"
FILE = "file"
SHOTS = {"variants": False}
VARIANTS = {"variants": True}

PRODUCTS: dict[str, dict] = {
    "626-labs-mod-manager": {
        "name": "626 Labs Mod Manager", "siteId": None,
        "local": "_old-626-labs-mod-manager", "repo": None,
        "rules": [
            (FILE, "shell/assets/icon-512.png", "icon-512.png"),
            (FILE, "shell/assets/icon.ico", "icon.ico"),
        ],
    },
    "626-mod-launcher": {
        "name": "626 Mod Launcher", "siteId": "mod-launcher",
        "local": "626-mod-launcher", "repo": "estevanhernandez-stack-ed/626-mod-launcher",
        "rules": [
            (FILE, "assets/release/hero.png", "hero.png"),
            (FILE, "src/ModManager.App/Assets/icon.ico", "icon.ico"),
            (DIR, "docs/store-assets", "store-assets", VARIANTS),
            (DIR, "docs/store-assets/screenshots-0.17", "screenshots", SHOTS),
        ],
    },
    "626labs-dashboard": {
        "name": "626 Labs Dashboard", "siteId": None,
        "local": "Project-626Labs-1", "repo": "estevanhernandez-stack-ed/Project-626Labs",
        "rules": [
            (FILE, "public/favicon.ico", "favicon.ico"),
            (FILE, "vscode-extension/resources/icon.png", "vscode-icon.png"),
            (FILE, "vscode-extension/resources/icon.svg", "vscode-icon.svg"),
        ],
    },
    "626labs-design": {
        "name": "626 Labs Design System", "siteId": None,
        "local": "626labs-design", "repo": "estevanhernandez-stack-ed/626labs-design",
        "rules": [(FILE, "assets/626Labs-logo.png", "626Labs-logo.png")],
    },
    "626labs-themes": {
        "name": "626 Labs Themes", "siteId": None,
        "local": "626labs-themes", "repo": "estevanhernandez-stack-ed/626labs-themes",
        "rules": [(FILE, "icon.png", "icon.png")],
    },
    "626mcp-vscode-extension": {
        "name": "626MCP VS Code Extension", "siteId": None,
        "local": "626MCP-VsCodeExtension", "repo": "estevanhernandez-stack-ed/626MCP-VsCodeExtension",
        "rules": [
            (FILE, "vscode-extension/resources/icon.png", "icon.png"),
            (FILE, "vscode-extension/resources/icon.svg", "icon.svg"),
        ],
    },
    "6deux6": {
        "name": "6deux6", "siteId": None,
        "local": "6deux6", "repo": "estevanhernandez-stack-ed/6deux6",
        "rules": [(FILE, "assets/icon-1024.png", "icon-1024.png")],
    },
    "beatsmasher": {
        "name": "BeatsMasher", "siteId": None,
        "local": "BeatsMasher", "repo": "estevanhernandez-stack-ed/BeatsMasher",
        "rules": [(FILE, "artifacts/beats-masher/public/favicon.svg", "favicon.svg")],
    },
    "build-party": {
        "name": "Build Party", "siteId": None,
        "local": "Build Party", "repo": None,
        "rules": [(FILE, "vscode-extension/resources/toy-icon.svg", "toy-icon.svg")],
    },
    "celestia3": {
        "name": "Celestia 3", "siteId": "celestia-3",
        "local": "Celestia3", "repo": "estevanhernandez-stack-ed/Celestia3",
        "rules": [
            (FILE, "assets/icon.png", "icon.png"),
            (FILE, "public/assets/celestia_logo_icon.png", "celestia_logo_icon.png"),
            (FILE, "public/icons/icon-512.png", "icon-512.png"),
        ],
    },
    "chef-is": {
        "name": "Chef I's", "siteId": None,
        "local": "Chef-I-s", "repo": "estevanhernandez-stack-ed/Chef-I-s",
        "rules": [
            (FILE, "static/chef-icon.png", "chef-icon.png"),
            (FILE, "Chef Inspection Icon.png", "chef-inspection-icon.png"),
        ],
    },
    "cleanup-ranger": {
        "name": "Cleanup Ranger", "siteId": None,
        "local": "Cleanup Ranger", "repo": "estevanhernandez-stack-ed/Cleanup-Ranger",
        "rules": [
            (FILE, "public/favicon.png", "favicon.png"),
            (FILE, "public/hero.png", "hero.png"),
        ],
    },
    "estessistant": {
        "name": "Estessistant", "siteId": None,
        "local": "Estessistant", "repo": None,
        "rules": [(FILE, "notepad_icon.png", "notepad_icon.png")],
    },
    "koii-tracker": {
        "name": "Koii Tracker", "siteId": None, "local": None, "repo": None, "rules": [],
    },
    "ladder": {
        "name": "LADDER", "siteId": None,
        "local": "LADDER", "repo": "estevanhernandez-stack-ed/LADDER",
        "rules": [(FILE, "public/favicon.svg", "favicon.svg")],
    },
    "opsgen": {
        "name": "OPsGen", "siteId": None,
        "local": "OPsGen", "repo": "estevanhernandez-stack-ed/OPsGen",
        "rules": [(FILE, "QR_Generator/static/logo.png", "qr-generator-logo.png")],
    },
    "pod-pipeline": {
        "name": "626 POD Pipeline", "siteId": "pod-pipeline",
        "local": "POD_Pipeline", "repo": "626Labs-LLC/626labs-pod-pipeline",
        "rules": [
            (FILE, "626labs_logo_transparent.png", "626labs_logo_transparent.png"),
            (FILE, "conundrum_logo_transparent.png", "conundrum_logo_transparent.png"),
        ],
    },
    "poster-colorizer": {
        "name": "Poster Colorizer", "siteId": None,
        "local": "Poster-Colorizer", "repo": "estevanhernandez-stack-ed/Poster-Colorizer",
        "rules": [
            (FILE, "assets/images/icon.png", "icon.png"),
            (FILE, "assets/images/splash-icon.png", "splash-icon.png"),
        ],
    },
    "powertoys-snipsnap": {
        "name": "SnapSnip (PowerToys fork)", "siteId": "snapsnip",
        "local": "PowerToys-snipsnap", "repo": "estevanhernandez-stack-ed/PowerToys",
        "rules": [
            (FILE, "installer/PowerToysSetupVNext/Images/logo.png", "installer-logo.png"),
            (FILE, "doc/images/readme/Release-Banner.png", "Release-Banner.png"),
        ],
    },
    "quizshow": {
        "name": "QuizShow", "siteId": None,
        "local": "QuizShow", "repo": "estevanhernandez-stack-ed/QuizShow",
        "rules": [
            (FILE, "apps/cinema/public/favicon.svg", "favicon-cinema.svg"),
            (FILE, "apps/bacon-trail/public/favicon.svg", "favicon-bacon-trail.svg"),
            (FILE, "apps/reel-battles/public/favicon.svg", "favicon-reel-battles.svg"),
            (FILE, "apps/reel-words/public/favicon.svg", "favicon-reel-words.svg"),
        ],
    },
    "rbx15-shirt-and-pants": {
        "name": "RBX15 Classic Shirt and Pants Maker", "siteId": "rbx15-shirt-pants",
        "local": "RBX15-Shirt-and-Pants", "repo": "estevanhernandez-stack-ed/RBX15-Shirt-and-Pants",
        "rules": [
            (DIR, "docs/store-assets", "", VARIANTS),
            (DIR, "docs/screenshots", "screenshots", SHOTS),
            (FILE, "windows/msix/Images/Square310x310Logo.png", "Square310x310Logo.png"),
            (FILE, "windows/msix/Images/StoreLogo.png", "StoreLogo.png"),
        ],
    },
    "reel-battles": {
        "name": "Reel Battles", "siteId": None,
        "local": "Reel-Battles", "repo": "estevanhernandez-stack-ed/Reel-Battles",
        "rules": [
            (FILE, "client/public/favicon.png", "favicon.png"),
            (FILE, "generated-icon.png", "generated-icon.png"),
        ],
    },
    "reel-words": {
        "name": "Reel Words", "siteId": None,
        "local": "QuizShow", "repo": "estevanhernandez-stack-ed/QuizShow",
        "rules": [(FILE, "apps/reel-words/public/favicon.svg", "favicon.svg")],
    },
    "rororo-mac": {
        "name": "RORORO for Mac", "siteId": None,
        "local": "rororo-mac", "repo": "estevanhernandez-stack-ed/rororo-mac",
        # hero.png and hero@2x.png are both kept, as harvested: @2x is not a
        # size token the variant collapse knows.
        "rules": [(DIR, "docs/marketing", "marketing", SHOTS)],
    },
    "rororo-ur-afk": {
        "name": "Ur AFK", "siteId": None,
        "local": "rororo-ur-afk", "repo": "estevanhernandez-stack-ed/rororo-ur-afk",
        "rules": [(FILE, "icon.png", "icon.png")],
    },
    "rororo-ur-task": {
        "name": "Ur Task", "siteId": None,
        "local": "rororo-ur-task", "repo": "estevanhernandez-stack-ed/rororo-ur-task",
        "rules": [(FILE, "icon.png", "icon.png")],
    },
    "rororoblox": {
        "name": "RORORO", "siteId": "rororo",
        "local": "ROROROblox", "repo": "estevanhernandez-stack-ed/ROROROblox",
        "rules": [
            (DIR, "docs/images", "", SHOTS),
            (DIR, "docs/screenshots", "screenshots", SHOTS),
            (FILE, "src/ROROROblox.App/Package/Logos/AppIcon.ico", "AppIcon.ico"),
            (DIR, "docs/store/graphics", "store-graphics",
             {"variants": True, "exclude": [r"^pushover-"]}),
            (DIR, "docs/store/screenshots", "store-screenshots", SHOTS),
        ],
    },
    "rotemplate": {
        "name": "RoTemplate", "siteId": None, "local": None, "repo": None, "rules": [],
    },
    "rtclickpng": {
        "name": "Right Click PNG", "siteId": "rtclickpng",
        "local": "RTClickPng", "repo": "estevanhernandez-stack-ed/RTClickPng",
        "rules": [
            (FILE, "src/Package/Assets/Square310x310Logo.png", "Square310x310Logo.png"),
            (FILE, "src/Package/Assets/StoreLogo.png", "StoreLogo.png"),
        ],
    },
    "safety-assistant": {
        "name": "Safety Assistant", "siteId": None,
        "local": "Safety Assistant", "repo": "estevanhernandez-stack-ed/Safety_Assistant",
        "rules": [
            (FILE, "icon.png", "icon.png"),
            (FILE, "icon.svg", "icon.svg"),
        ],
    },
    "sanduhr": {
        "name": "Sanduhr für Claude", "siteId": "sanduhr",
        "local": "Sanduhr", "repo": "estevanhernandez-stack-ed/Sanduhr_f-r_Claude",
        "rules": [
            (DIR, "docs/store-assets", "", VARIANTS),
            (FILE, "docs/images/icon-1024-rgb.png", "icon-1024-rgb.png"),
            (DIR, "docs/images/screenshots", "images-screenshots", SHOTS),
            (DIR, "docs/screenshots/windows", "screenshots/windows", SHOTS),
            (FILE, "windows-dotnet/src/Sanduhr.App/Package/Logos/StoreLogo.png", "StoreLogo.png"),
        ],
    },
    "snipsnap": {
        "name": "SnapSnip", "siteId": "snapsnip",
        "local": "SnipSnap", "repo": "estevanhernandez-stack-ed/SnipSnap",
        "rules": [
            (DIR, "docs/screenshots", "screenshots", SHOTS),
            (FILE, "src/SnipSnap.Standalone/Assets/Square310x310Logo.scale-400.png", "logo-1240.png"),
            (FILE, "src/SnipSnap.Standalone/Assets/StoreLogo.scale-400.png", "store-logo-200.png"),
            (FILE, "src/SnipSnap.UI/Resources/SnipSnapLogo.ico", "SnipSnapLogo.ico"),
            (FILE, "src/SnipSnap.UI/Resources/SnipSnapLogo.png", "SnipSnapLogo.png"),
            (DIR, "src/SnipSnap.Standalone/Assets/Marketing", "marketing", VARIANTS),
        ],
    },
    "tagthatline": {
        "name": "Tag That Line", "siteId": None,
        "local": "tagthatline", "repo": "estevanhernandez-stack-ed/tagthatline",
        "rules": [
            (FILE, "docs/icon.png", "icon.png"),
            (FILE, "docs/icon.svg", "icon.svg"),
        ],
    },
    "the-lineup": {
        "name": "The Lineup", "siteId": None,
        "local": "The Lineup", "repo": None,
        "rules": [(FILE, "public/favicon.svg", "favicon.svg")],
    },
    "ur-ocr": {
        "name": "Ur OCR", "siteId": None,
        "local": "Ur-OCR", "repo": "estevanhernandez-stack-ed/Ur-OCR",
        "rules": [(FILE, "icon.png", "icon.png")],
    },
    "weseeyouatthemovies": {
        "name": "We See You at the Movies", "siteId": None,
        "local": "WeSeeYouAtTheMovies", "repo": "estevanhernandez-stack-ed/WeSeeYouAtTheMovies",
        "rules": [(FILE, "frontend/public/movie-icon.svg", "movie-icon.svg")],
    },
}


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
def is_image(p: Path) -> bool:
    return p.suffix.lower() in IMAGE_EXTS


def is_forbidden(local: str | None) -> bool:
    if not local:
        return False
    top = Path(local).parts[0]
    return any(top.startswith(f) for f in FORBIDDEN)


def content_hash(p: Path) -> str:
    data = p.read_bytes()
    if p.suffix.lower() == ".svg":
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def normalize_repo(url: str | None) -> str | None:
    """git remote URL (https or ssh, with or without .git) -> owner/repo."""
    if not url:
        return None
    u = url.strip().rstrip("/")
    if u.endswith(".git"):
        u = u[:-4]
    m = re.search(r"github\.com[:/]+([^/]+)/([^/]+)$", u)
    return f"{m.group(1)}/{m.group(2)}" if m else u


def _svg_dims(p: Path):
    text = p.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"<svg\b[^>]*>", text, re.S)
    if not m:
        return None
    tag = m.group(0)

    def attr(name):
        a = re.search(rf'\b{name}\s*=\s*"([\d.]+)(px)?"', tag)
        return float(a.group(1)) if a else None

    w, h = attr("width"), attr("height")
    if w and h:
        return (w, h)
    vb = re.search(r'viewBox\s*=\s*"([^"]+)"', tag)
    if vb:
        parts = vb.group(1).replace(",", " ").split()
        if len(parts) == 4:
            return (float(parts[2]), float(parts[3]))
    return None


def image_dims(p: Path):
    if p.suffix.lower() == ".svg":
        return _svg_dims(p)
    try:
        from PIL import Image

        with Image.open(p) as im:
            return im.size
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Classification + the manifest
# ---------------------------------------------------------------------------
LOCKUP_RE = re.compile(r"logo-(square|portrait)|wordmark|lockup", re.I)
HERO_RE = re.compile(r"^hero|[-_]hero|banner", re.I)
FORMAT_RANK = {".png": 2, ".jpg": 2, ".jpeg": 2, ".webp": 2, ".gif": 2, ".svg": 1, ".ico": 0}


def classify(files: list[tuple[str, tuple | None]]) -> dict:
    """files: [(path relative to the product folder, (w, h) or None)].

    Order matters: screenshots, then the hero, then the logo, then the icon;
    whatever is left is `other`.
      screenshots  anything under a directory whose name mentions screenshot
      hero         hero*/banner by name, widest first then largest; else the
                   largest wide (>= 1.6:1) image
      logo         a lockup by name (logo-square, logo-portrait, wordmark), or a
                   *logo* that is not square; largest wins
      icon         the largest square-ish mark (within 15%): raster beats SVG
                   beats ICO, a name with "icon" beats one without, splash art
                   loses
    """
    out = {"icon": None, "logo": None, "hero": None, "screenshots": [], "other": []}
    rest = []
    for rel, dims in sorted(files):
        if any("screenshot" in seg.lower() for seg in rel.split("/")[:-1]):
            out["screenshots"].append(rel)
        else:
            rest.append((rel, dims))

    def aspect(d):
        return (d[0] / d[1]) if d and d[1] else None

    def area(d):
        return (d[0] * d[1]) if d else 0

    def name(rel):
        return rel.rsplit("/", 1)[-1]

    heroes = [f for f in rest if HERO_RE.search(name(f[0]))]
    if heroes:
        pick = max(heroes, key=lambda f: ((aspect(f[1]) or 0) >= 1.3, area(f[1]), f[0]))
        out["hero"] = pick[0]
        rest = [f for f in rest if f not in heroes]
        out["other"] += [f[0] for f in heroes if f is not pick]

    def squareish(d):
        a = aspect(d)
        return a is not None and 0.85 <= a <= 1.18

    logos = [
        f for f in rest
        if LOCKUP_RE.search(name(f[0]))
        or ("logo" in name(f[0]).lower() and f[1] and not squareish(f[1]))
    ]
    if logos:
        pick = max(logos, key=lambda f: (area(f[1]), f[0]))
        out["logo"] = pick[0]
        rest = [f for f in rest if f is not pick]

    icons = [f for f in rest if squareish(f[1])]
    if icons:
        def icon_key(f):
            n = name(f[0]).lower()
            ext = "." + n.rsplit(".", 1)[-1]
            return ("splash" not in n, FORMAT_RANK.get(ext, 0), "icon" in n, area(f[1]), f[0])

        pick = max(icons, key=icon_key)
        out["icon"] = pick[0]
        rest = [f for f in rest if f is not pick]

    if out["hero"] is None:
        wide = [f for f in rest if (aspect(f[1]) or 0) >= 1.6]
        if wide:
            pick = max(wide, key=lambda f: (area(f[1]), f[0]))
            out["hero"] = pick[0]
            rest = [f for f in rest if f is not pick]

    out["other"] += [f[0] for f in rest]
    out["other"].sort()
    return out


def _site_products(root: Path) -> list[dict]:
    site = json.loads((root / "content" / "site.json").read_text(encoding="utf-8"))
    return site.get("products", [])


def _existing_harvested(root: Path) -> dict:
    p = root / ROUNDUP_REL / "index.json"
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return {e["id"]: e.get("harvested") for e in data.get("products", [])}
    except (ValueError, KeyError, TypeError):
        return {}


def build_index(root: Path = ROOT, harvested: dict | None = None) -> dict:
    """The manifest, from the tree alone: assets/roundup + content/site.json +
    the PRODUCTS mapping. Reads no sibling repo."""
    ru = root / ROUNDUP_REL
    titles = {p.get("id"): p.get("title") for p in _site_products(root)}
    prior = _existing_harvested(root)
    if harvested:
        prior.update(harvested)

    products = []
    for d in sorted(p for p in ru.iterdir() if p.is_dir()):
        pid = d.name
        meta = PRODUCTS.get(pid, {})
        files = []
        for f in sorted(d.rglob("*")):
            if f.is_file() and is_image(f):
                files.append((f.relative_to(d).as_posix(), image_dims(f)))
        cls = classify(files)
        prefix = f"{ROUNDUP_REL}/{pid}/"

        def full(rel):
            return prefix + rel if rel else None

        site_id = meta.get("siteId")
        rules = meta.get("rules", [])
        source_dir = None
        if rules:
            first = rules[0]
            source_dir = first[1] if first[0] == DIR else (Path(first[1]).parent.as_posix())
        products.append({
            "id": pid,
            "name": titles.get(site_id) or meta.get("name") or pid.replace("-", " ").title(),
            "siteId": site_id,
            "repo": meta.get("repo"),
            "sourceDir": source_dir,
            "harvested": prior.get(pid) or FIRST_HARVEST,
            "icon": full(cls["icon"]),
            "logo": full(cls["logo"]),
            "hero": full(cls["hero"]),
            "screenshots": [full(r) for r in cls["screenshots"]],
            "other": [full(r) for r in cls["other"]],
        })

    covered = {p["siteId"] for p in products if p["siteId"]}
    site_ids = sorted(i for i in titles if i)
    gaps = {
        "siteProductsWithoutRoundup": [i for i in site_ids if i not in covered],
        "roundupWithoutIcon": [p["id"] for p in products if not p["icon"]],
    }
    return {
        "generated": max((p["harvested"] for p in products), default=FIRST_HARVEST),
        "note": NOTE,
        "products": products,
        "gaps": gaps,
    }


def render_index(obj: dict) -> str:
    return json.dumps(obj, indent=1, ensure_ascii=False) + "\n"


def write_index(root: Path, obj: dict) -> Path:
    p = root / ROUNDUP_REL / "index.json"
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render_index(obj))
    return p


# ---------------------------------------------------------------------------
# Harvest (this box only)
# ---------------------------------------------------------------------------
def _group_key(name: str) -> str:
    stem, dot, ext = name.rpartition(".")
    return SIZE_TOKEN_RE.sub("", stem).lower() + dot + ext.lower()


def expected_files(meta: dict, projects: Path) -> dict[str, Path]:
    """dest rel path -> source file, for every image the mapping harvests."""
    base = projects / meta["local"]
    want: dict[str, Path] = {}
    for rule in meta["rules"]:
        kind, src, dest = rule[0], rule[1], rule[2]
        opts = rule[3] if len(rule) > 3 else {}
        if kind == FILE:
            p = base / src
            if p.is_file() and is_image(p):
                want[dest] = p
            continue
        sdir = base / src
        if not sdir.is_dir():
            continue
        excl = [re.compile(x, re.I) for x in opts.get("exclude", [])]
        cands = [
            f for f in sorted(sdir.iterdir())
            if f.is_file() and is_image(f)
            and not SCALE_ARMY_RE.search(f.name)
            and not any(x.search(f.name) for x in excl)
        ]
        if opts.get("variants"):
            best: dict[str, Path] = {}
            for f in cands:
                k = _group_key(f.name)
                d = image_dims(f)
                a = d[0] * d[1] if d else 0
                cur = best.get(k)
                if cur is None or a > cur[1]:
                    best[k] = (f, a)
            cands = sorted(v[0] for v in best.values())
        for f in cands:
            want[(dest + "/" if dest else "") + f.name] = f
    return want


def declared_dests(meta: dict) -> tuple[set[str], list[str]]:
    """Dest files named by FILE rules, and dest dirs owned by DIR rules."""
    files, dirs = set(), []
    for rule in meta["rules"]:
        if rule[0] == FILE:
            files.add(rule[2])
        else:
            dirs.append(rule[2])
    return files, dirs


def _owned(rel: str, files: set[str], dirs: list[str]) -> bool:
    if rel in files:
        return True
    parent = rel.rsplit("/", 1)[0] if "/" in rel else ""
    return parent in dirs


def plan_product(pid: str, meta: dict, root: Path, projects: Path) -> dict:
    ru = root / ROUNDUP_REL / pid
    have = {
        f.relative_to(ru).as_posix(): f
        for f in (ru.rglob("*") if ru.is_dir() else [])
        if f.is_file() and is_image(f)
    }
    res = {"new": [], "changed": [], "gone": [], "untracked": [], "note": None}
    if not meta.get("local"):
        res["note"] = "no local source; kept as harvested"
        res["untracked"] = sorted(have)
        return res
    base = projects / meta["local"]
    if not base.is_dir():
        res["note"] = f"local clone missing: {meta['local']}"
        res["untracked"] = sorted(have)
        return res
    want = expected_files(meta, projects)
    files, dirs = declared_dests(meta)
    for dest, src in sorted(want.items()):
        if dest not in have:
            res["new"].append((dest, src))
        elif content_hash(src) != content_hash(have[dest]):
            res["changed"].append((dest, src))
    for rel in sorted(have):
        if rel in want:
            continue
        if _owned(rel, files, dirs):
            res["gone"].append(rel)
        else:
            res["untracked"].append(rel)
    live = normalize_repo(_git_remote(base))
    if live != meta.get("repo"):
        res["note"] = f"remote drift: mapping says {meta.get('repo')}, clone says {live}"
    return res


def _git_remote(path: Path) -> str | None:
    try:
        r = subprocess.run(
            ["git", "-C", str(path), "config", "--get", "remote.origin.url"],
            capture_output=True, text=True, timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() or None


def harvest_refusal(projects: Path) -> str | None:
    if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
        return "refusing to harvest in CI: this reads Este's local estate. Use --index-only."
    if os.name != "nt":
        return "refusing to harvest off Windows: the estate lives at a Windows path. Use --index-only."
    if not projects.is_dir():
        return f"refusing to harvest: {projects} does not exist on this machine."
    bad = [pid for pid, m in PRODUCTS.items() if is_forbidden(m.get("local"))]
    if bad:
        return f"refusing to harvest: mapping points into a walled repo for {bad}"
    return None


def run_harvest(root: Path, projects: Path, apply: bool, prune: bool) -> int:
    why = harvest_refusal(projects)
    if why:
        print(why, file=sys.stderr)
        return 2
    today = _dt.date.today().isoformat()
    totals = {"new": 0, "changed": 0, "gone": 0}
    touched: dict[str, str] = {}
    mode = "APPLY" if apply else "DRY RUN"
    print(f"=== refresh-roundup ({mode}) against {projects} ===")
    ru_dirs = sorted(p.name for p in (root / ROUNDUP_REL).iterdir() if p.is_dir())
    for pid in sorted(set(PRODUCTS) | set(ru_dirs)):
        meta = PRODUCTS.get(pid)
        if meta is None:
            print(f"{pid}: not in the PRODUCTS mapping; left alone")
            continue
        r = plan_product(pid, meta, root, projects)
        n, c, g = len(r["new"]), len(r["changed"]), len(r["gone"])
        for k, v in (("new", n), ("changed", c), ("gone", g)):
            totals[k] += v
        line = f"{pid}: new {n}, changed {c}, gone {g}"
        if r["untracked"]:
            line += f", untracked {len(r['untracked'])}"
        if r["note"]:
            line += f"  [{r['note']}]"
        print(line)
        for dest, _ in r["new"]:
            print(f"    + {dest}")
        for dest, _ in r["changed"]:
            print(f"    ~ {dest}")
        for dest in r["gone"]:
            print(f"    - {dest}" + ("" if prune else "  (kept; --prune deletes)"))
        if apply:
            for dest, src in r["new"] + r["changed"]:
                target = root / ROUNDUP_REL / pid / dest
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, target)
                touched[pid] = today
            if prune:
                for dest in r["gone"]:
                    (root / ROUNDUP_REL / pid / dest).unlink()
                    touched[pid] = today
    print(
        f"TOTAL: new {totals['new']}, changed {totals['changed']}, gone {totals['gone']}"
        + ("" if apply else "  (dry run: nothing written; --apply to copy)")
    )
    if apply:
        p = write_index(root, build_index(root, harvested=touched))
        print(f"wrote {p.relative_to(root).as_posix()}")
    return 0


def main(argv=None, root: Path = ROOT, projects: Path = PROJECTS) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--apply", action="store_true", help="copy new/changed images in, rewrite index.json")
    ap.add_argument("--prune", action="store_true", help="with --apply: delete images whose source is gone")
    ap.add_argument("--index-only", action="store_true", help="rewrite index.json from the tree only (CI-safe)")
    ap.add_argument("--check", action="store_true", help="with --index-only: exit 1 if index.json would change")
    args = ap.parse_args(argv)

    if args.index_only:
        text = render_index(build_index(root))
        path = root / ROUNDUP_REL / "index.json"
        current = path.read_bytes() if path.exists() else b""
        if args.check:
            if current != text.encode("utf-8"):
                print("index.json is stale: run python scripts/refresh-roundup.py --index-only")
                return 1
            print("index.json is current")
            return 0
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print(f"wrote {path.relative_to(root).as_posix()}"
              + (" (unchanged)" if current == text.encode("utf-8") else ""))
        return 0
    if args.prune and not args.apply:
        ap.error("--prune only means something with --apply")
    return run_harvest(root, projects, apply=args.apply, prune=args.prune)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
