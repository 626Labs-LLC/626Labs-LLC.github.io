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
        # The reading measure is part of the contract (Este's ruling,
        # 2026-09-04, from PR #97's open question). press.html and
        # privacy.html own no chrome; `.wrap` is the column their prose
        # sits in and `.nav-inner` is the nav's, and a utility.css that
        # styles neither ships both pages full-bleed at 1440. These two
        # are credited from a CSS selector in utility.css ONLY, never from
        # the shell's markup (theme-doctor's UTILITY_CSS_ONLY_CLASSES): the
        # theme's own utility.html carries both class names, so markup
        # credit would pass an unstyled measure. Both live themes style
        # both; a theme whose utility.css drops either fails the
        # vocabulary check instead of shipping.
        "wrap",
        "nav-inner",
    },
}


# The base CSS custom-property vocabulary a theme's tokens.css (and, since
# press.html/privacy.html carry no local fallback of their own,
# archetypes/utility.css — and archetypes/reading.css, for the same reason,
# once thesis.html/workflow.html gave up their private token blocks) has to
# actually DEFINE. VOCABULARY (above) is the
# markup-side anchor — class names a theme's dress can rely on finding.
# REQUIRED_TOKENS is the CSS-side twin: the var(--x) names themes.html's own
# <style> block and press.html's/privacy.html's own residual <style> (the
# page-specific rules left after utility.css's A4 extraction — .copy-block/
# .asset-grid/.tldr and friends) read but never define themselves. Nothing
# before this required a theme to actually supply them: themes.html and
# index.html each carry a hardcoded LOCAL fallback :root (today's Phosphor
# Blueprint values, cascade-earlier than the theme's own <link>), so a theme
# that drops or renames one of these doesn't error, it just silently leaves
# themes.html showing the OUTGOING theme's stale color/spacing/type forever.
# press.html/privacy.html have no such fallback at all (their <style> was
# trimmed to page-specific rules only, A4) — for them, a missing/renamed
# token is a straight unresolved var(), not a stale-but-valid one.
#
# Derived by reading, not designed in the abstract (same discipline
# VOCABULARY documents): union of every var(--x) actually referenced in
# themes.html's inline <style>, plus press.html's and privacy.html's own
# residual <style> blocks. One theme-bespoke name found there is
# deliberately excluded: press.html's `.asset-preview` background reads
# `var(--pb-field)`, Phosphor Blueprint's OWN treatment-layer token (defined
# in both tokens.css and utility.css's "Phosphor Blueprint — treatment
# layer" section, never in the shared base) — a real, live coupling, but not
# a base-vocabulary name any future theme is obligated to define under that
# exact, PB-specific name. See docs/theme-archetypes.md for the full
# derivation, the pb-field exclusion, and why each group of tokens matters.
#
# Three names joined later, when thesis.html/workflow.html stopped carrying
# private token blocks and started reading the theme (`--bg-2`, `--dur-med`,
# `--r-xl`). Each was admitted on one test and one test only: is a SIBLING of
# its own scale already required? `--bg-0`/`--bg-1` were, so a page reading
# `--bg-2` is reading a hole in a scale the contract already half-covers, not
# asking for a new concept. Same for `--dur-med` beside `--dur-fast`, and
# `--r-xl` beside all five other radius steps. Completing a scale the
# contract already commits to is the contract doing its job; every theme in
# the repo already defined all three, so nothing was asked of anyone.
#
# A fourth joined on the same test when conundrum.html/rororo-plugins.html
# did the same: `--fg-muted`. Its siblings `--fg-1`, `--fg-2` and `--fg-3`
# were ALL already required — three quarters of a four-member alias family,
# with the fourth left out for no reason anyone recorded. Its underlying
# value (`--text-mute`) was required too, so the contract already obliged
# every theme to HAVE the color and merely declined to name the alias the
# pages actually read. tokens.css, product.css, utility.css and reading.css
# each already defined it, so admission cost this theme nothing; it binds
# the next one.
#
# `--shadow-2` failed that test and is deliberately NOT here, though
# workflow.html and rororo-plugins.html both read it: no shadow-scale name
# (`--shadow-1`, `--shadow-3`, `--glow-cyan`, `--glow-duo`) is in this set,
# so admitting it would start a new group on the strength of two pages'
# usage — which is how a contract becomes a junk drawer. It stays a
# documented page-to-theme coupling instead. See the task-1 and task-2
# reports' coupling sections.
REQUIRED_TOKENS: frozenset[str] = frozenset({
    # backgrounds
    "--bg-0", "--bg-1", "--bg-2",
    # foreground / text
    "--fg-1", "--fg-2", "--fg-3", "--fg-muted",
    "--text", "--text-sec", "--text-dim", "--text-mute",
    # brand color + accent
    "--cyan", "--cyan-pale", "--magenta", "--magenta-pale",
    "--navy-deep", "--navy-mid", "--navy-hi", "--ink-950", "--ok",
    "--brand-gradient", "--brand-gradient-soft",
    # borders + panel effects
    "--border-1", "--border-2", "--border-accent", "--inner-stroke",
    # typography
    "--font-display", "--font-body", "--font-mono",
    # motion
    "--dur-fast", "--dur-med", "--ease-out",
    # spacing scale
    "--s-2", "--s-3", "--s-4", "--s-5", "--s-6", "--s-8", "--s-10", "--s-12", "--s-16",
    # radius scale
    "--r-xs", "--r-sm", "--r-md", "--r-lg", "--r-xl", "--r-pill",
})


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
