#!/usr/bin/env python3
"""archetypes.py — the archetype contract for 626labs.dev theme rotation.

The site rotates its whole visual identity monthly (a hard pivot — no
shared invariants between one theme and the next). Rotating ~39 pages by
hand-authoring 39 shells per month is impossible, so a theme instead
designs FOUR archetype dresses: home, product, reading, utility. Every
public page maps to exactly one archetype; a theme's CSS + shell markup
for that archetype has to work on every page mapped to it.

This module is the load-bearing contract every later task (the home
renderer, the reading renderer, the plugin renderer, theme-doctor's
archetype gate, the About reading-dress toggle) builds on:

- ARCHETYPES   — the four fixed archetype names.
- VOCABULARY   — per archetype, the required semantic class names a
                 theme's dress can rely on finding in that archetype's
                 markup. See docs/theme-archetypes.md for what each class
                 means and which real page it was derived from.
- load()       — reads content/page-archetypes.json, the page->archetype
                 mapping every public page appears in exactly once.
- archetype_for() — look up one page's archetype, failing loudly (naming
                 the page) when it's unmapped.
- validate()   — the drift gate: every mapped page must exist on disk,
                 every archetype value must be a known archetype, and
                 every public page actually on disk must be mapped. Used
                 by theme-doctor (a later task) and CI so a new page can
                 never ship unthemed by accident.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ARCHETYPES = ("home", "product", "reading", "utility")

# Directories that legitimately contain *.html but are never public site
# pages: design references/exploration previews, SDD scratch, announcement
# drafts, the widget's Vite dev entry, and theme *infrastructure* (a theme's
# own archetypes/*.html, tokens.css, theme.json — the dress itself, not a
# page being dressed). Kept as directory *names*, matched against any path
# component, so it doesn't matter how deep the offending file sits.
EXCLUDED_DIRS = {
    "node_modules",
    ".git",
    "__pycache__",
    ".superpowers",  # SDD plans, task briefs, brainstorm scratch
    "Design",        # brand reference + one-off exploration/preview HTML
    "docs",          # announcement drafts (x-article.html) — social copy
    "apps",          # apps/widget-bacon-trail is Vite SOURCE, never served
    "themes",        # a theme's own archetypes/*.html, tokens.css, theme.json
}

# Specific files, excluded by exact repo-relative (posix) path.
EXCLUDED_FILES = {
    "admin-dashboard.html",  # internal tool, never themed
}

# The per-archetype vocabulary. Each set is the REQUIRED floor: the real
# class names a theme's CSS can count on finding in that archetype's
# markup today. A theme is free to vary CSS and structural arrangement
# around these classes, but it never invents a new class name for an
# existing semantic element — see docs/theme-archetypes.md for the full
# rule, the evidence page each class was pulled from, and what each one
# means.
VOCABULARY: dict[str, set[str]] = {
    "home": {
        "nav",
        "hero",
        "section",
        "products",
        "product",
        "field-notes",
        "field-note",
        "lab",
        "lab-runs",
        "play",
        "support",
        "contact",
        "footer-inner",
    },
    "product": {
        "top",
        "hero",
        "install",
        "brain",
        "card",
        "family",
        "family-card",
        "work",
        "section-head",
    },
    "reading": {
        "ed-page",
        "lnt-nav",
        "lnt-header",
        "ed-title",
        "ed-dek",
        "lnt-main",
        "lnt-record",
        "lnt-prose",
        "lnt-pull-quote",
        "lnt-footer",
    },
    "utility": {
        "nav",
        "page-hero",
        "page-title",
        "page-meta",
        "footer-inner",
    },
}


def _public_pages(root: Path = ROOT) -> set[str]:
    """Every *.html file under `root` that is a real public page: not
    excluded by directory or filename. Returns repo-relative, posix-style
    paths (forward slashes) to match the JSON mapping's key format."""
    pages: set[str] = set()
    for path in root.rglob("*.html"):
        rel = path.relative_to(root)
        if any(part in EXCLUDED_DIRS for part in rel.parts[:-1]):
            continue
        rel_str = rel.as_posix()
        if rel_str in EXCLUDED_FILES:
            continue
        pages.add(rel_str)
    return pages


def load(root: Path = ROOT) -> dict:
    """The page->archetype mapping from content/page-archetypes.json,
    with the `$comment` documentation key stripped out."""
    raw = json.loads((root / "content" / "page-archetypes.json").read_text(encoding="utf-8"))
    return {k: v for k, v in raw.items() if not k.startswith("$")}


def archetype_for(page: str, mapping: dict) -> str:
    """The archetype `page` maps to. Raises KeyError naming the page
    when it isn't in `mapping` — never a silent default."""
    if page not in mapping:
        raise KeyError(page)
    return mapping[page]


def validate(mapping: dict, root: Path = ROOT) -> list[str]:
    """The drift gate. Checks, in order:
    - every mapped page exists on disk
    - every mapped archetype value is one of ARCHETYPES
    - every public page actually on disk is present in `mapping`

    Returns a list of human-readable failure strings; empty when the
    mapping is fully valid.
    """
    errors: list[str] = []

    for page, archetype in mapping.items():
        if not (root / page).exists():
            errors.append(f"mapped page does not exist on disk: {page}")
        if archetype not in ARCHETYPES:
            errors.append(f"{page}: unknown archetype {archetype!r}")

    on_disk = _public_pages(root)
    for page in sorted(on_disk - set(mapping)):
        errors.append(f"public page on disk is not mapped: {page}")

    return errors
