#!/usr/bin/env python3
"""freeze-theme.py — turn a retiring theme into a permanent dated archive.

A frozen archive is a dated artifact: it must never re-render and must never
rot. That's why it gets its own local copy of the theme's tokens.css instead
of linking back to /themes/<slug>/tokens.css (which keeps moving as themes
rotate), and why it's marked noindex — it's history, not a live page search
engines should rank.

Usage:
  python scripts/freeze-theme.py <YYYY-MM>

Freezes the CURRENTLY RENDERED root/index.html plus the active theme's
tokens.css into root/themes/archive/<YYYY-MM>/. Refuses to overwrite an
archive that already exists for that month.
"""
from __future__ import annotations

import re
import sys
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

ROBOTS_META = '<meta name="robots" content="noindex">'

BANNER_TEMPLATE = (
    '<div style="background:#111;color:#eee;font:14px/1.5 system-ui;'
    'padding:10px 16px;text-align:center">\n'
    "  Archived: the site as it looked in {month_name}. "
    '<a href="/" style="color:#17d4fa">Go to the live site</a>.\n'
    "</div>"
)


def freeze(month: str, root: Path = ROOT) -> Path:
    """Freeze the current index.html + active theme's tokens.css to an archive.

    Returns the archive directory (root/themes/archive/<month>/). Raises
    FileExistsError if that directory already exists — archives are
    write-once, never silently re-frozen.
    """
    archive_dir = root / "themes" / "archive" / month
    if archive_dir.exists():
        raise FileExistsError(f"archive already exists: {archive_dir}")

    reg = theme_registry.load(root)
    slug = theme_registry.active_slug(reg)
    tokens_src = theme_registry.theme_dir(slug, root) / "tokens.css"

    html = (root / "index.html").read_text(encoding="utf-8")

    month_name = datetime.strptime(month, "%Y-%m").strftime("%B %Y")
    banner = BANNER_TEMPLATE.format(month_name=month_name)

    html = HEAD_OPEN_RE.sub(lambda m: f"{m.group(0)}\n  {ROBOTS_META}", html, count=1)
    html = BODY_OPEN_RE.sub(lambda m: f"{m.group(0)}{banner}", html, count=1)
    html = html.replace(f'href="/themes/{slug}/tokens.css"', 'href="tokens.css"')

    archive_dir.mkdir(parents=True)
    (archive_dir / "index.html").write_text(html, encoding="utf-8")
    copyfile(tokens_src, archive_dir / "tokens.css")

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
