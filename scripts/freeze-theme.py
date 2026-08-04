#!/usr/bin/env python3
"""freeze-theme.py — turn a retiring theme into a permanent dated archive.

A frozen archive is a dated artifact: it must never re-render and must never
rot. That's why it gets LOCAL copies of every stylesheet it links instead of
linking back to the live paths (which keep moving — themes rotate, and the
base /Design/*.css layer can retokenize at any time), and why it's marked
noindex — it's history, not a live page search engines should rank.

The freeze does NOT localize everything the page references — some live
references are an accepted, documented boundary rather than an oversight:

  - /fonts/* — never linked via <link rel="stylesheet"> today (the shell
    pulls font faces in through an inline @import inside its own <style>
    block, which this script doesn't touch), but excluded on principle too:
    variable font files are megabytes and font infrastructure doesn't
    retokenize the way brand CSS does.
  - /widget-bacon-trail/* — an interactive widget stylesheet, not a design
    surface. Freezing a widget's CSS per archived month buys nothing; the
    live widget is fine to keep sharing.
  - /assets/* images — accepted by the original spec; archives may show a
    since-replaced screenshot or OG image and that's fine.
  - the runtime `fetch("data/plugin-versions.json")` call in the page's own
    <script> — a relative path that 404s harmlessly from the nested archive
    URL (it degrades to "no version chip," not a broken page).

Usage:
  python scripts/freeze-theme.py <YYYY-MM>

Freezes the CURRENTLY RENDERED root/index.html into root/themes/archive/
<YYYY-MM>/, along with a local copy of every root-relative
<link rel="stylesheet" href="/..."> it references (except the excluded
prefixes above), rewriting each href to point at its local copy. Refuses to
overwrite an archive that already exists for that month.
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from shutil import copyfile

SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT = SCRIPTS_DIR.parent
if str(SCRIPTS_DIR) not in sys.path:
    # Loaded two ways: `python scripts/freeze-theme.py` (Python already puts
    # the script's own dir on sys.path[0]) and importlib.util loading by
    # explicit file path from tests/ (it does NOT). Insert explicitly so
    # `import theme_registry` below works either way.
    sys.path.insert(0, str(SCRIPTS_DIR))
import theme_registry  # noqa: E402 — sibling module in scripts/

HEAD_OPEN_RE = re.compile(r"<head(\s[^>]*)?>", re.I)
BODY_OPEN_RE = re.compile(r"<body(\s[^>]*)?>", re.I)
STYLESHEET_LINK_RE = re.compile(r'<link\b[^>]*\brel="stylesheet"[^>]*>', re.I)
HREF_ATTR_RE = re.compile(r'href="([^"]*)"')

ROBOTS_META = '<meta name="robots" content="noindex">'

BANNER_TEMPLATE = (
    '<div style="background:#111;color:#eee;font:14px/1.5 system-ui;'
    'padding:10px 16px;text-align:center">\n'
    "  Archived: the site as it looked in {month_name}. "
    '<a href="/" style="color:#17d4fa">Go to the live site</a>.\n'
    "</div>"
)

# Root-relative <link rel="stylesheet"> hrefs that resolve inside the repo but
# are deliberately NOT localized into the archive. See the module docstring
# for why each is an accepted live reference rather than a missed one.
FREEZE_EXCLUDE_PREFIXES = ("/widget-bacon-trail/", "/fonts/")


def _local_stylesheet_hrefs(html: str, root: Path) -> list[str]:
    """Root-relative stylesheet hrefs in `html` that resolve to a real file
    under `root`, in first-seen order, deduplicated, minus the excluded
    prefixes. External stylesheets (http(s):, protocol-relative, or anything
    that isn't root-relative) are left alone — nothing to localize."""
    hrefs: list[str] = []
    seen: set[str] = set()
    for tag in STYLESHEET_LINK_RE.findall(html):
        m = HREF_ATTR_RE.search(tag)
        if not m:
            continue
        href = m.group(1)
        if href in seen:
            continue
        seen.add(href)
        if not href.startswith("/"):
            continue  # external or already-relative — not ours to touch
        if any(href.startswith(p) for p in FREEZE_EXCLUDE_PREFIXES):
            continue
        if (root / href.lstrip("/")).is_file():
            hrefs.append(href)
    return hrefs


def _flatten_filenames(hrefs: list[str]) -> dict[str, str]:
    """href -> archive-local filename. Basenames collide across different
    directories (two files both named tokens.css is the textbook case), so:
    default to the plain basename, and only for hrefs whose basename isn't
    unique across this freeze, fall back to the full path with "/" flattened
    to "__" (deterministic — same href always maps to the same filename, no
    ordering dependence, no counters)."""
    counts = Counter(Path(href).name for href in hrefs)
    mapping = {}
    for href in hrefs:
        name = Path(href).name
        if counts[name] > 1:
            mapping[href] = href.lstrip("/").replace("/", "__")
        else:
            mapping[href] = name
    return mapping


def freeze(month: str, root: Path = ROOT) -> Path:
    """Freeze the current index.html + its local stylesheets to an archive.

    Every root-relative <link rel="stylesheet" href="/..."> the page
    references (minus FREEZE_EXCLUDE_PREFIXES) gets copied alongside the
    frozen index.html and its href rewritten to the local copy — so a later
    retokenize of the live /Design/*.css or /themes/<slug>/tokens.css layer
    can never silently repaint an archived month.

    Returns the archive directory (root/themes/archive/<month>/). Raises
    FileExistsError if that directory already exists — archives are
    write-once, never silently re-frozen.
    """
    archive_dir = root / "themes" / "archive" / month
    if archive_dir.exists():
        raise FileExistsError(f"archive already exists: {archive_dir}")

    html = (root / "index.html").read_text(encoding="utf-8")

    month_name = datetime.strptime(month, "%Y-%m").strftime("%B %Y")
    banner = BANNER_TEMPLATE.format(month_name=month_name)

    html = HEAD_OPEN_RE.sub(lambda m: f"{m.group(0)}\n  {ROBOTS_META}", html, count=1)
    html = BODY_OPEN_RE.sub(lambda m: f"{m.group(0)}{banner}", html, count=1)

    hrefs = _local_stylesheet_hrefs(html, root)
    filenames = _flatten_filenames(hrefs)
    for href, filename in filenames.items():
        html = html.replace(f'href="{href}"', f'href="{filename}"')

    archive_dir.mkdir(parents=True)
    (archive_dir / "index.html").write_text(html, encoding="utf-8")
    for href, filename in filenames.items():
        copyfile(root / href.lstrip("/"), archive_dir / filename)

    return archive_dir


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: freeze-theme.py <YYYY-MM>", file=sys.stderr)
        return 2
    month = argv[0]
    if not theme_registry.MONTH_RE.match(month):
        print(f"invalid month, expected YYYY-MM: {month}", file=sys.stderr)
        return 2

    try:
        out = freeze(month)
    except FileExistsError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    print(f"froze theme to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
