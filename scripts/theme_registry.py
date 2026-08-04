#!/usr/bin/env python3
"""The theme registry: one switch for which theme is live.

active = the live theme. queue = approved themes awaiting rotation (FIFO).
archive = frozen past themes, never re-rendered.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "content" / "themes.json"
REQUIRED_FILES = ("tokens.css", "theme.json")
MONTH_RE = re.compile(r"^\d{4}-\d{2}$")


def load(root: Path = ROOT) -> dict:
    return json.loads((root / "content" / "themes.json").read_text(encoding="utf-8"))


def active_slug(reg: dict) -> str:
    return reg["active"]


def theme_dir(slug: str, root: Path = ROOT) -> Path:
    return root / "themes" / slug


def _theme_complete(slug: str, root: Path) -> list[str]:
    d = theme_dir(slug, root)
    if not d.is_dir():
        return [f"theme dir missing: {d}"]
    errs = [f"theme {slug} missing {f}" for f in REQUIRED_FILES if not (d / f).exists()]
    # The shell is now archetype-aware: a theme either carries the legacy
    # single shell.html or has extracted archetypes/home.html (the "home"
    # archetype — index.html, the only archetype render-hub.py resolves
    # today). Requiring shell.html unconditionally would flag a theme that
    # has already migrated as incomplete. See scripts/archetypes.py and
    # docs/theme-archetypes.md.
    if not (d / "shell.html").exists() and not (d / "archetypes" / "home.html").exists():
        errs.append(f"theme {slug} missing shell.html or archetypes/home.html")
    return errs


def validate(reg: dict, root: Path = ROOT) -> list[str]:
    errs: list[str] = []
    active = reg.get("active")
    if not isinstance(active, str) or not active:
        errs.append("active must be a non-empty slug")
    else:
        errs += _theme_complete(active, root)
    queue = reg.get("queue", [])
    if not isinstance(queue, list):
        errs.append("queue must be a list")
        queue = []
    if len(set(queue)) != len(queue):
        errs.append("queue has duplicate slugs")
    if active in queue:
        errs.append(f"active theme {active} must not also sit in the queue")
    for slug in queue:
        errs += _theme_complete(slug, root)
    months = []
    for entry in reg.get("archive", []):
        for key in ("slug", "month", "url"):
            if key not in entry:
                errs.append(f"archive entry missing {key}: {entry}")
        month = entry.get("month", "")
        if month and not MONTH_RE.match(month):
            errs.append(f"archive month not YYYY-MM: {month}")
        months.append(month)
    if len(set(months)) != len(months):
        errs.append("archive has duplicate months")
    return errs


def rotate(reg: dict, month: str) -> dict:
    """Pure: promote queue[0] to active, archive the outgoing theme."""
    queue = list(reg.get("queue", []))
    if not queue:
        raise ValueError("queue is empty")
    outgoing = reg["active"]
    return {
        **{k: v for k, v in reg.items() if k not in ("active", "queue", "archive")},
        "active": queue[0],
        "queue": queue[1:],
        "archive": list(reg.get("archive", []))
        + [{"slug": outgoing, "month": month, "url": f"/themes/archive/{month}/"}],
    }
