#!/usr/bin/env python3
"""
626 Labs hub renderer — materializes index.html from content/site.json.

Marker-based partial rendering: the renderer finds pairs of
`<!-- SITE_JSON:<zone>:start -->` and `:end` comments in index.html and
replaces the content between them with HTML generated from site.json.

Zones handled:
- hero         — eyebrow, h1, sub, actions, meta
- hero-chips   — chips around the animated logo
- products     — the 5 product cards in the Work section
- thinking     — the Thinking section essays
- stories      — auto-discovered Field Notes from content/stories/*.md
                 (any frontmatter-fenced .md without `draft: true`)
- lab-runs     — "How the lab runs" section
- play         — the Play section
- about        — the About section
- support      — the Support CTA section
- contact      — the Contact section
- lab-pool     — the JS LAB_POOL array that drives "Also from the lab"
                 (uses `// SITE_JSON:lab-pool:start/end` line comments)

Zones NOT handled (stay hand-edited in index.html):
- nav / footer
- Manifesto / principles

Stdlib only — runs in any Python 3.10+ on CI without `pip install`.
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

import site_facts  # sibling module in scripts/ (added to sys.path when run as a script)

# ─── paths ──────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
SITE_JSON = ROOT / "content" / "site.json"
INDEX_HTML = ROOT / "index.html"
STORIES_DIR = ROOT / "content" / "stories"

# Repo slug used to deep-link each Field Note's "Read on GitHub" CTA at the
# raw markdown source. Per-story rendered HTML pages can be a follow-up; for
# v1 the reading experience is GitHub's markdown renderer.
STORIES_GITHUB_REPO = "626Labs-LLC/626Labs-LLC.github.io"
STORIES_GITHUB_BRANCH = "main"

# ─── feed (Atom syndication for Field Notes) ────────────────────────
FEED_PATH = ROOT / "feed.xml"
SITE_URL = "https://626labs.dev"
FEED_TITLE = "626 Labs — Field Notes"
FEED_SUBTITLE = "What we shipped, what bit us, what we'd do differently."
FEED_AUTHOR = "626 Labs"
# Atom requires <updated>; with zero published stories we anchor to a fixed
# date so an empty feed still renders deterministically (idempotent --check).
FEED_EPOCH = "2026-01-01T00:00:00Z"


# ─── helpers ────────────────────────────────────────────────────────
def esc(s: str | None) -> str:
    """HTML-escape user content (text nodes)."""
    return html.escape(s or "", quote=False)


def attr(s: str | None) -> str:
    """HTML-escape for attribute values."""
    return html.escape(s or "", quote=True)


def xesc(s: str | None) -> str:
    """Escape for XML text + attribute contexts (the Atom feed)."""
    return html.escape(s or "", quote=True)


def substitute_zone(source: str, zone: str, rendered: str, js: bool = False) -> str:
    """Replace the content between SITE_JSON:<zone>:start/end markers.

    HTML zones use `<!-- SITE_JSON:<zone>:start -->` comments.
    JS zones use `// SITE_JSON:<zone>:start` line comments (js=True).
    Markers themselves are preserved so future renders find them.
    """
    if js:
        pattern = re.compile(
            r"(//\s*SITE_JSON:"
            + re.escape(zone)
            + r":start)(.*?)(//\s*SITE_JSON:"
            + re.escape(zone)
            + r":end)",
            re.DOTALL,
        )
    else:
        pattern = re.compile(
            r"(<!--\s*SITE_JSON:"
            + re.escape(zone)
            + r":start\s*-->)(.*?)(<!--\s*SITE_JSON:"
            + re.escape(zone)
            + r":end\s*-->)",
            re.DOTALL,
        )
    match = pattern.search(source)
    if not match:
        raise RuntimeError(f"zone marker not found in index.html: {zone!r}")

    start_marker = match.group(1)
    end_marker = match.group(3)
    # Walk backwards from the end marker to figure out its column, so the
    # rebuilt block closes at the same indent.
    block = match.group(0)
    last_line = block.splitlines()[-1]
    end_indent = len(last_line) - len(last_line.lstrip(" "))
    return pattern.sub(
        lambda _m: start_marker + "\n" + rendered.rstrip("\n") + "\n" + " " * end_indent + end_marker,
        source,
        count=1,
    )


# ─── hero ───────────────────────────────────────────────────────────
def render_hero(hero: dict) -> str:
    eyebrow = esc(hero.get("eyebrow", ""))
    headline = esc(hero.get("headline", ""))
    accent = esc(hero.get("headlineAccent", ""))
    subhead = esc(hero.get("subhead", ""))
    primary = hero.get("primaryCta") or {}
    secondary = hero.get("secondaryCta") or {}
    meta = hero.get("meta") or []

    primary_html = ""
    if primary.get("label"):
        primary_html = (
            f'<a class="btn btn-primary" href="{attr(primary.get("href", "#"))}">'
            f"{esc(primary['label'])}"
            '<svg class="ic" viewBox="0 0 24 24"><path d="M5 12h14M13 5l7 7-7 7"/></svg>'
            "</a>"
        )
    secondary_html = ""
    if secondary.get("label"):
        secondary_html = (
            f'<a class="btn btn-ghost" href="{attr(secondary.get("href", "#"))}">'
            f"{esc(secondary['label'])}</a>"
        )

    meta_rows = "\n".join(
        f'        <div>{esc(m.get("label", ""))}<b>{esc(m.get("value", ""))}</b></div>'
        for m in meta
    )

    return f"""\
      <div class="eyebrow">
        <span class="pulse"></span>
        <span>{eyebrow}</span>
        <span class="line"></span>
      </div>
      <h1>
        {headline}<br/>
        <span class="accent">{accent}</span>
      </h1>
      <p class="hero-sub">
        {subhead}
      </p>
      <div class="hero-actions">
        {primary_html}
        {secondary_html}
      </div>
      <div class="hero-meta">
{meta_rows}
      </div>"""


# ─── hero chips ─────────────────────────────────────────────────────
CHIP_POSITIONS = ["chip-a", "chip-b", "chip-c", "chip-d"]
CHIP_TONE_CLASS = {
    "cyan": "",
    "magenta": " magenta",
    "success": " success",
}


def render_chips(chips: list[dict]) -> str:
    items = []
    for i, chip in enumerate(chips[:4]):
        pos = CHIP_POSITIONS[i]
        tone = CHIP_TONE_CLASS.get(chip.get("tone", "cyan"), "")
        items.append(
            f'        <div class="mark-chip{tone} {pos}">'
            f'<span class="dot"></span>{esc(chip.get("label", ""))}'
            "</div>"
        )
    return '      <div class="mark-chips">\n' + "\n".join(items) + "\n      </div>"


# ─── products ───────────────────────────────────────────────────────
TONE_TO_TAG_CLASS = {
    "cyan": "cyan",
    "magenta": "magenta",
    "live": "live",
    "wip": "wip",
    "success": "live",
}

# Hand-tuned SVG sigils per product id. Unknown ids get a generic square.
PRODUCT_SIGILS = {
    "vibe-cartographer": (
        '<svg class="ic-xl ic" viewBox="0 0 24 24">'
        '<path d="M1 6v16l7-3 8 3 7-3V3l-7 3-8-3-7 3z"/>'
        '<path d="M8 3v16M16 6v16"/></svg>'
    ),
    "vibe-iterate": (
        '<svg class="ic-lg ic" viewBox="0 0 24 24">'
        '<circle cx="12" cy="12" r="9"/>'
        '<path d="M12 3v18M3 12h18"/>'
        '<path d="M12 7l3 5-3 5-3-5z"/></svg>'
    ),
    "vibe-doc": (
        '<svg class="ic-lg ic" viewBox="0 0 24 24">'
        '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
        '<path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/></svg>'
    ),
    "vibe-taker": (
        '<svg class="ic-lg ic" viewBox="0 0 24 24">'
        '<rect x="2" y="6" width="7" height="12" rx="1"/>'
        '<rect x="15" y="6" width="7" height="12" rx="1"/>'
        '<path d="M9 12h6M13 9l3 3-3 3"/></svg>'
    ),
    "vibe-test": (
        '<svg class="ic-lg ic" viewBox="0 0 24 24">'
        '<path d="M10 2v7.31M14 9.3V2M8.5 2h7M14 9.3a6.5 6.5 0 1 1-4 0M7 18h10"/></svg>'
    ),
    "sanduhr": (
        '<svg class="ic-lg ic" viewBox="0 0 24 24">'
        '<path d="M6 2h12M6 22h12M6 2v4c0 2.5 6 4 6 6s-6 1.5-6 4v6M18 2v4c0 2.5-6 4-6 6s6 1.5 6 4v6"/></svg>'
    ),
    "vibe-sec": (
        '<svg class="ic-lg ic" viewBox="0 0 24 24">'
        '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>'
    ),
    "vibe-wrap": (
        # Breadcrumb trail rising into a wrapped summary card with a check.
        '<svg class="ic-lg ic" viewBox="0 0 24 24">'
        '<rect x="10.5" y="7" width="10.5" height="12" rx="2"/>'
        '<path d="M13 13.2l1.7 1.9 3.3-3.9"/>'
        '<circle cx="3.4" cy="20.2" r="0.95" fill="currentColor" stroke="none"/>'
        '<circle cx="6.4" cy="17.4" r="0.95" fill="currentColor" stroke="none"/>'
        '<circle cx="9.4" cy="14.6" r="0.95" fill="currentColor" stroke="none"/></svg>'
    ),
    "vibe-insights": (
        # Magnifier over a rising trend line — insight into your usage.
        '<svg class="ic-lg ic" viewBox="0 0 24 24">'
        '<path d="M2 17l4-4 3 2 4-6"/>'
        '<circle cx="15.5" cy="8.5" r="3.5"/>'
        '<path d="M18 11l3.5 3.5"/></svg>'
    ),
    "rbx15-shirt-pants": (
        # T-shirt outline
        '<svg class="ic-lg ic" viewBox="0 0 24 24">'
        '<path d="M4 7l5-3 3 2 3-2 5 3-2 3-2-1v11H8V9L6 10z"/></svg>'
    ),
    "rtclickpng": (
        # Cursor arrow
        '<svg class="ic-lg ic" viewBox="0 0 24 24">'
        '<path d="M5 3v17l4.5-3.5 2.5 5 2-1-2.5-5h5.5z"/></svg>'
    ),
    "celestia-3": (
        # Celestial sparkle + star accent
        '<svg class="ic-lg ic" viewBox="0 0 24 24">'
        '<path d="M12 2l2.2 7.8L22 12l-7.8 2.2L12 22l-2.2-7.8L2 12l7.8-2.2z"/>'
        '<circle cx="18.5" cy="5.5" r="1.3"/></svg>'
    ),
}

# Flagship-only decorative preview (terminal mock + bullets), keyed by id.
# If someone flips flagship: true on a product that isn't in this map, the
# card renders flagship-sized but without the preview block.
FLAGSHIP_PREVIEWS = {
    "vibe-cartographer": """
        <div class="product-preview">
          <div class="preview-frame">
            <div class="preview-dots"><span></span><span></span><span></span></div>
            <div class="preview-body">
              <div><span class="muted">/</span><span class="k">vibe-cartographer</span> <span class="muted">// session state</span></div>
              <div><span class="s"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="vertical-align:-2px"><polyline points="20 6 9 17 4 12"/></svg></span> onboard · builder profile loaded</div>
              <div><span class="s"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="vertical-align:-2px"><polyline points="20 6 9 17 4 12"/></svg></span> scope · focused project brief</div>
              <div><span class="s"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="vertical-align:-2px"><polyline points="20 6 9 17 4 12"/></svg></span> prd · acceptance criteria drafted</div>
              <div><span class="s"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="vertical-align:-2px"><polyline points="20 6 9 17 4 12"/></svg></span> spec · technical blueprint</div>
              <div><span class="muted"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="vertical-align:-2px"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg> checklist · build · iterate · reflect</span></div>
              <div><span class="muted">level </span><span class="m">3.5</span><span class="muted"> · self-evolving memory · 16 patterns</span></div>
            </div>
          </div>
          <div class="preview-bullets">
            <div class="preview-bullet">
              <div class="num">01</div>
              <div class="txt"><b>Spec-driven.</b> Eleven commands walk idea → shipped app without losing the thread.</div>
            </div>
            <div class="preview-bullet">
              <div class="num">02</div>
              <div class="txt"><b>Self-evolving.</b> Reads its own usage, surfaces friction, rewrites its own guidance.</div>
            </div>
            <div class="preview-bullet">
              <div class="num">03</div>
              <div class="txt"><b>Level 3.5.</b> Highest rung any public plugin has reached on the maturity ladder.</div>
            </div>
            <div class="preview-bullet">
              <div class="num">04</div>
              <div class="txt"><b>Stack.</b> Claude Code · SKILL files · npm · Apache-licensed framework spec.</div>
            </div>
          </div>
        </div>""",
}

# Badge palette defaults — matches the current hard-coded palette.
BADGE_COLOR_CYAN = "17d4fa"
BADGE_COLOR_MAGENTA = "f22f89"
BADGE_COLOR_GREEN = "2bd99a"
BADGE_LABEL_BG = "0f1f31"

# Per-plugin release-badge overrides. shields.io's github/v/release reads
# *published Releases*, not git tags — so two cases need special handling:
#   1. Monorepo packaging: the release lives in vibe-plugins, not the
#      standalone repo (which carries tags but no Releases). Point `repo` at
#      the monorepo and `filter` at the package's tag prefix.
#   2. No Release yet (WIP): suppress the badge with `hide` rather than let
#      shields render "no matching releases found".
# Plugins not listed here resolve against their own `repo` with no filter.
SHIELDS_RELEASE = {
    "vibe-test": {"repo": "estevanhernandez-stack-ed/vibe-plugins", "filter": "vibe-test-v*"},
    "vibe-sec": {"hide": True},
}

# Category label that sits under the flagship tag row ("SPEC-DRIVEN · SELF-EVOLVING").
# Keyed by product id. Flagship-only.
PRODUCT_CATEGORY_LABELS = {
    "vibe-cartographer": "SPEC-DRIVEN · SELF-EVOLVING",
}

# Foot-row meta text now lives on each product entry in site.json as `meta`.
# (Previously hardcoded here; moved so admin-dash edits flow through.)

# Icons used by the Microsoft Store + GitHub download badges.
MS_STORE_ICON_SVG = (
    '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">'
    '<path d="M3 3h8.5v8.5H3zm9.5 0H21v8.5h-8.5zM3 12.5h8.5V21H3zm9.5 0H21V21h-8.5z"/>'
    '</svg>'
)
GITHUB_ICON_SVG = (
    '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">'
    '<path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/>'
    '</svg>'
)


CLAUDE_CODE_BADGE = (
    # Claude Code skill — Anthropic-orange (D97757), dark label (141414),
    # Anthropic sparkle loaded via shields.io's simpleicons integration.
    'https://img.shields.io/badge/Claude%20Code-skill-D97757?'
    'style=flat-square&logo=anthropic&logoColor=F5F5F0&labelColor=141414'
)

ANTHROPIC_APPROVED_BADGE = (
    # Anthropic-approved — same Anthropic-orange visual treatment as the
    # Claude Code skill badge, but flips the label to read "Anthropic |
    # approved". Set `anthropicApproved: true` on a product to opt in —
    # carried by every plugin published in Anthropic's official Claude Code
    # plugins directory.
    'https://img.shields.io/badge/Anthropic-approved-D97757?'
    'style=flat-square&logo=anthropic&logoColor=F5F5F0&labelColor=141414'
)


def render_badges(p: dict) -> str:
    """Claude Code skill (if applicable) + npm version + downloads (maskable) + release + npm license.

    License comes from the npm metadata (/npm/l/) so it reflects the
    actual published state — unpublished packages get auto-hidden by
    maskStaleBadges() on the client.
    """
    npm = p.get("npm")
    claude_code = bool(p.get("claudeCode"))
    anthropic_approved = bool(p.get("anthropicApproved"))

    # If it's not a Claude Code plugin AND has no npm, nothing to show.
    if not claude_code and not npm:
        return ""

    # Canonical order: most common → least common, so badges that exist on
    # every plugin sit in the same column position regardless of which card
    # you're on. The order is:
    #   1. Claude Code skill         (universal status marker)
    #   2. GitHub release            (universal — any repo)
    #   3. License                   (universal — npm-source if published)
    #   4. npm version               (npm-only)
    #   5. npm downloads             (npm-only)
    #   6. Anthropic approved        (rarest — Cart only)
    # Plugins without npm just stop after position 3 (or position 1 if they
    # don't have a tagged release path either).
    approved_badge_line = (
        f'\n          <img src="{attr(ANTHROPIC_APPROVED_BADGE)}" alt="Anthropic approved">'
        if anthropic_approved else ""
    )

    # No npm (pure Claude Code plugin) → just the Claude Code badge,
    # with Anthropic-approved at the end if applicable.
    if not npm:
        return f"""\
        <div class="badges">
          <img src="{attr(CLAUDE_CODE_BADGE)}" alt="Claude Code skill">{approved_badge_line}
        </div>"""
    repo = p.get("repo") or ""
    pid = p.get("id", "")
    rel = SHIELDS_RELEASE.get(pid, {})
    rel_repo = rel.get("repo", repo)
    rel_filter = rel.get("filter")

    # Order: CC, release, license, npm version, npm downloads, [Anthropic
    # approved]. npm-specific badges sit after the universal ones so cards
    # stay column-aligned regardless of which plugin you're on; Anthropic-
    # approved comes absolute last (rarest). Built as a list so a suppressed
    # release badge (WIP plugins) just drops a row without disturbing the rest.
    rows: list[str] = []
    if claude_code:
        rows.append(f'          <img src="{attr(CLAUDE_CODE_BADGE)}" alt="Claude Code skill">')
    if not rel.get("hide"):
        if rel_filter:
            release_url = (
                f"https://img.shields.io/github/v/release/{rel_repo}"
                f"?filter={rel_filter}&color={BADGE_COLOR_GREEN}&labelColor={BADGE_LABEL_BG}&style=flat-square&label=release"
            )
        else:
            release_url = (
                f"https://img.shields.io/github/v/release/{rel_repo}"
                f"?color={BADGE_COLOR_GREEN}&labelColor={BADGE_LABEL_BG}&style=flat-square&label=release"
            )
        rows.append(f'          <img data-maskable="true" src="{attr(release_url)}" alt="latest release">')
    rows.append(f'          <img data-maskable="true" src="https://img.shields.io/npm/l/{attr(npm)}?color={BADGE_COLOR_GREEN}&labelColor={BADGE_LABEL_BG}&style=flat-square" alt="MIT license">')
    rows.append(f'          <img data-maskable="true" src="https://img.shields.io/npm/v/{attr(npm)}?color={BADGE_COLOR_CYAN}&labelColor={BADGE_LABEL_BG}&style=flat-square" alt="npm version">')
    rows.append(f'          <img data-maskable="true" src="https://img.shields.io/npm/dt/{attr(npm)}?color={BADGE_COLOR_MAGENTA}&labelColor={BADGE_LABEL_BG}&style=flat-square&label=downloads" alt="total downloads">')
    if anthropic_approved:
        rows.append(f'          <img src="{attr(ANTHROPIC_APPROVED_BADGE)}" alt="Anthropic approved">')
    body = "\n".join(rows)
    return f"""\
        <div class="badges">
{body}
        </div>"""


def render_install(p: dict) -> str:
    install = p.get("install")
    if not install:
        return ""
    return f"""\
        <div class="install">
          <span class="label">Install in Claude Code</span>
          <code><span class="prompt">&gt;</span>{esc(install)}</code>
        </div>"""


def render_tags(tags: list[dict]) -> str:
    out = []
    for t in tags or []:
        cls = TONE_TO_TAG_CLASS.get(t.get("tone", "cyan"), "cyan")
        out.append(f'<span class="tag {cls}">{esc(t.get("label", ""))}</span>')
    return "".join(out)


def render_product_visual(p: dict) -> str:
    """Banner image at the top of the card, bleeding to card edges.

    Rendered only when the product has a `banner` field. CSS (.product-visual)
    already lives in index.html and handles the negative margin + border.
    """
    banner = p.get("banner")
    if not banner:
        return ""
    alt = f"{p.get('title', '')} — card banner screenshot"
    return (
        '        <div class="product-visual">\n'
        f'          <img src="{attr(banner)}" alt="{attr(alt)}" loading="lazy" />\n'
        '        </div>'
    )


def render_store_badges(p: dict) -> str:
    """Matched Microsoft Store + GitHub badge pair.

    Rendered only when the product has a `storeUrl`. The GitHub half appears
    only when `repo` is set and public.
    """
    store_url = p.get("storeUrl")
    if not store_url:
        return ""
    repo = p.get("repo") or ""
    parts = [
        '        <div class="badge-row">',
        f'          <a class="store-badge" href="{attr(store_url)}" rel="noopener">',
        f'            {MS_STORE_ICON_SVG}',
        '            <div class="store-badge-text">',
        '              <span class="store-badge-top">Get it from</span>',
        '              <span class="store-badge-bottom">Microsoft Store</span>',
        '            </div>',
        '          </a>',
    ]
    if repo:
        parts.extend([
            f'          <a class="store-badge" href="https://github.com/{attr(repo)}" rel="noopener">',
            f'            {GITHUB_ICON_SVG}',
            '            <div class="store-badge-text">',
            '              <span class="store-badge-top">View on</span>',
            '              <span class="store-badge-bottom">GitHub</span>',
            '            </div>',
            '          </a>',
        ])
    parts.append('        </div>')
    return "\n".join(parts)


def render_product_cta(p: dict) -> str:
    """Primary launch CTA for hosted web-app products (those with a liveUrl).

    Renders a gradient primary button to the live app plus an optional ghost
    'Watch demo' button. Plugin / native-store products don't set liveUrl and
    skip this entirely.
    """
    live = p.get("liveUrl")
    if not live:
        return ""
    label = esc(p.get("liveCtaLabel", "Open app"))
    arrow = '<svg class="ic" viewBox="0 0 24 24"><path d="M5 12h14M13 5l7 7-7 7"/></svg>'
    parts = [
        '        <div class="product-cta">',
        f'          <a class="btn btn-primary" href="{attr(live)}" target="_blank" rel="noopener">{label}{arrow}</a>',
    ]
    demo = p.get("demoUrl")
    if demo:
        parts.append(
            f'          <a class="btn btn-ghost" href="{attr(demo)}" target="_blank" rel="noopener">Watch demo</a>'
        )
    parts.append('        </div>')
    return "\n".join(parts)


def render_product_foot(p: dict) -> str:
    """Foot row: product-meta + product-link."""
    pid = p.get("id", "")
    repo = p.get("repo", "")
    product_page = p.get("productPage")
    store_url = p.get("storeUrl")
    meta = p.get("meta", "")

    if product_page:
        link = (
            f'<a class="product-link" href="{attr(product_page)}">'
            "Open product page "
            '<svg class="ic arrow" viewBox="0 0 24 24"><path d="M5 12h14M13 5l7 7-7 7"/></svg>'
            "</a>"
        )
    elif store_url:
        # Store badge pair is already the CTA; a repo link here is redundant.
        link = ""
    elif p.get("liveUrl"):
        # Hosted web app — the launch CTA buttons are the action, no repo link.
        link = ""
    elif p.get("status") == "wip":
        link = (
            f'<a class="product-link" href="https://github.com/{attr(repo)}">'
            "Framework doc "
            '<svg class="ic arrow" viewBox="0 0 24 24"><path d="M7 17L17 7M7 7h10v10"/></svg>'
            "</a>"
        )
    else:
        link = (
            f'<a class="product-link" href="https://github.com/{attr(repo)}">'
            "Open repo "
            '<svg class="ic arrow" viewBox="0 0 24 24"><path d="M7 17L17 7M7 7h10v10"/></svg>'
            "</a>"
        )

    if link:
        return f"""\
        <div class="product-foot">
          <div class="product-meta">{meta}</div>
          {link}
        </div>"""
    return f"""\
        <div class="product-foot">
          <div class="product-meta">{meta}</div>
        </div>"""


def render_product(p: dict) -> str:
    flagship = bool(p.get("flagship"))
    wip = p.get("status") == "wip"
    classes = ["product"]
    if flagship:
        classes.append("flagship")
    if wip:
        classes.append("wip")
    class_attr = " ".join(classes)

    pid = p.get("id", "")
    sigil = PRODUCT_SIGILS.get(pid, PRODUCT_SIGILS["vibe-cartographer"])
    title = esc(p.get("title", ""))
    description = esc(p.get("description", ""))
    tags_html = render_tags(p.get("tags", []))
    badges_html = render_badges(p)
    install_html = render_install(p)
    visual_html = render_product_visual(p)
    store_badges_html = render_store_badges(p)
    cta_html = render_product_cta(p)
    preview_html = FLAGSHIP_PREVIEWS.get(pid, "") if flagship else ""
    foot_html = "" if flagship else render_product_foot(p)

    # Flagship cards get a heavier head with a category label.
    if flagship:
        category = PRODUCT_CATEGORY_LABELS.get(pid, "FLAGSHIP")
        head = f"""\
        <div class="product-head">
          <div style="display:flex;align-items:center;gap:16px">
            <div class="product-sigil">
              {sigil}
            </div>
            <div>
              <div class="product-tags" style="margin-bottom:4px">
                {tags_html}
              </div>
              <div style="font-family:var(--font-mono);font-size:11px;color:var(--fg-muted);letter-spacing:.08em">{esc(category)}</div>
            </div>
          </div>
          <a class="product-link" href="https://github.com/{attr(p.get("repo", ""))}">
            Open repo
            <svg class="ic arrow" viewBox="0 0 24 24"><path d="M7 17L17 7M7 7h10v10"/></svg>
          </a>
        </div>"""
    else:
        head = f"""\
        <div class="product-head">
          <div class="product-sigil">
            {sigil}
          </div>
          <div class="product-tags">
            {tags_html}
          </div>
        </div>"""

    parts = [f'      <article class="{class_attr}">']
    if visual_html:
        parts.append(visual_html)
    parts.extend([head, f"        <h3>{title}</h3>"])
    parts.append(f'        <p class="product-desc">{description}</p>')
    if badges_html:
        parts.append(badges_html)
    if install_html:
        parts.append(install_html)
    if cta_html:
        parts.append(cta_html)
    if store_badges_html:
        parts.append(store_badges_html)
    if preview_html:
        parts.append(preview_html)
    if foot_html:
        parts.append(foot_html)
    parts.append("      </article>")
    return "\n".join(parts)


def render_products(products: list[dict]) -> str:
    return "\n\n".join(render_product(p) for p in products)


# ─── lab pool ───────────────────────────────────────────────────────
def render_lab_pool(lab: list[dict]) -> str:
    """Emit a JavaScript array literal matching the shape app.jsx expects.

    We use json.dumps with indent=6 so the output is valid JS (JSON is a
    subset of JS), then trim the outer brackets so it slots inside
    `const LAB_POOL = [ ... ];` cleanly.
    """
    # Strip fields the runtime doesn't consume (id is admin-only).
    stripped = []
    for item in lab:
        entry = {k: v for k, v in item.items() if k != "id"}
        stripped.append(entry)
    body = json.dumps(stripped, indent=6, ensure_ascii=False)
    # json.dumps returns:  [\n      {...},\n      {...}\n]
    # We want the inner items at 6-space indent so they sit inside
    # `const LAB_POOL = [` already at 4-space indent in the source.
    # Strip outer [] and re-indent lines.
    inner = body[1:-1].rstrip("\n")
    return inner


# ─── play section (embedded games) ──────────────────────────────────
def render_play_section(play: dict) -> str:
    """Render the `.play` section — 'Also, we make games.'

    Emits the section markup + a <link>/<script>/init sequence for each
    widget listed in `play.widgets`. Forward-compatible: to add the
    CinePerks widget alongside the bacon trail one, append a second entry
    to `play.widgets` in site.json.
    """
    eyebrow = esc(play.get("eyebrow", "05 · Play"))
    headline = esc(play.get("headline", "Also, we make games."))
    lead = esc(play.get("lead", "Try one."))
    widgets = play.get("widgets") or []

    # Optional standalone-page link, rendered beneath the lead in the
    # section head. Shape: play.link = {"href": "...", "label": "..."}.
    link = play.get("link") or {}
    link_href = link.get("href")
    link_label = link.get("label")
    if link_href and link_label:
        aside = (
            '<div class="play-aside">\n'
            f'        <p>{esc(lead)}</p>\n'
            f'        <a class="play-link" href="{attr(link_href)}">{esc(link_label)}</a>\n'
            '      </div>'
        )
    else:
        aside = f'<p>{esc(lead)}</p>'

    # Widget mount-points (empty <div>s keyed by id).
    mounts = "\n        ".join(
        f'<div id="{attr(w.get("id", ""))}" class="play-widget"></div>'
        for w in widgets
    )

    # Stylesheets loaded first (before the script that mounts).
    stylesheets = "\n      ".join(
        f'<link rel="stylesheet" href="{attr(w.get("stylesheet", ""))}" />'
        for w in widgets if w.get("stylesheet")
    )

    # Scripts + inline init calls, one per widget.
    script_blocks: list[str] = []
    for w in widgets:
        src = w.get("script")
        init_fn = w.get("initFn")
        widget_id = w.get("id")
        cfg = w.get("config") or {}
        if not (src and init_fn and widget_id):
            continue
        # Inline config object serialized to JS-object literal.
        cfg_entries = [
            f'container: document.getElementById({json.dumps(widget_id)})',
            *(f"{json.dumps(k)}: {json.dumps(v)}" for k, v in cfg.items()),
        ]
        cfg_js = ", ".join(cfg_entries)
        script_blocks.append(
            f'<script src="{attr(src)}" defer></script>\n      '
            f'<script>window.addEventListener("DOMContentLoaded", function(){{'
            f'if(window.{init_fn.split(".")[0]})'
            f'{{{init_fn}({{{cfg_js}}});}}'
            f'}});</script>'
        )
    scripts = "\n      ".join(script_blocks)

    grid_class = "play-grid" + (" two-up" if len(widgets) >= 2 else "")

    return f"""\
<section class="section play" id="play">
  <div class="wrap">
    <div class="section-head">
      <div>
        <div class="eyebrow"><span>{eyebrow}</span><span class="line"></span></div>
        <h2>{headline}</h2>
      </div>
      {aside}
    </div>
    <div class="{grid_class}">
        {mounts}
    </div>
    <!-- widget assets -->
    {stylesheets}
    {scripts}
  </div>
</section>"""


# ─── lab runs (behind the scenes) ───────────────────────────────────
def render_lab_runs(lab_runs: dict) -> str:
    """Render the `.lab-runs` section — Dashboard screenshots + caption.

    `frames` is a list of { tag, src, alt } — 1 to 4 images shown as the
    private-Dashboard montage. `caption` is a list of plain text paragraphs
    shown below the frames.
    """
    eyebrow = esc(lab_runs.get("eyebrow", ""))
    headline = esc(lab_runs.get("headline", ""))
    lead = esc(lab_runs.get("lead", ""))
    frames = lab_runs.get("frames") or []
    caption = lab_runs.get("caption") or []

    frames_html = "\n".join(
        f"""      <div class="frame">
        <span class="frame-tag">{esc(f.get("tag", ""))}</span>
        <img src="{attr(f.get("src", ""))}" alt="{attr(f.get("alt", ""))}" loading="lazy"/>
      </div>"""
        for f in frames
    )

    caption_html = "\n".join(f"      <p>{esc(p)}</p>" for p in caption)

    return f"""\
<section class="section lab-runs" id="lab-runs">
  <div class="wrap">
    <div class="section-head">
      <div>
        <div class="eyebrow"><span>{eyebrow}</span><span class="line"></span></div>
        <h2>{headline}</h2>
      </div>
      <p>{lead}</p>
    </div>
    <div class="frames">
{frames_html}
    </div>
    <div class="caption">
{caption_html}
    </div>
  </div>
</section>"""


# ─── thinking / thesis ──────────────────────────────────────────────
def render_thinking(thinking: dict) -> str:
    """Render the `.thinking` section — the Self-Evolving Plugin Framework pitch.

    paragraphs[] are emitted as raw HTML so inline <strong>/<em> carry
    through. CTA is optional — omit the block entirely when absent.
    `artifacts[]` (optional) renders companion thesis pieces as cards
    after the main CTA.
    """
    eyebrow = esc(thinking.get("eyebrow", ""))
    headline = esc(thinking.get("headline", ""))
    lead = esc(thinking.get("lead", ""))
    quote = esc(thinking.get("quote", ""))
    paragraphs = thinking.get("paragraphs") or []
    cta = thinking.get("cta") or {}
    artifacts = thinking.get("artifacts") or []

    para_html = "\n".join(f"    <p>{p}</p>" for p in paragraphs)  # raw HTML on purpose

    cta_html = ""
    if cta.get("label") and cta.get("href"):
        cta_html = (
            '    <div class="thinking-link">\n'
            f'      <a href="{attr(cta["href"])}">\n'
            f'        {esc(cta["label"])}\n'
            '        <svg class="ic" viewBox="0 0 24 24"><path d="M5 12h14M13 5l7 7-7 7"/></svg>\n'
            '      </a>\n'
            '    </div>'
        )

    blockquote_html = f'    <blockquote>\n      {quote}\n    </blockquote>' if quote else ""

    artifacts_html = ""
    if artifacts:
        cards = []
        for art in artifacts:
            a_eyebrow = esc(art.get("eyebrow", ""))
            a_title = esc(art.get("title", ""))
            a_blurb = esc(art.get("blurb", ""))
            links = art.get("links") or []
            link_lines = [
                f'          <a href="{attr(l["href"])}">{esc(l["label"])} '
                f'<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
                f'stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" '
                f'aria-hidden="true"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg></a>'
                for l in links if l.get("label") and l.get("href")
            ]
            cards.append(
                '      <div class="thinking-artifact">\n'
                f'        <div class="artifact-eyebrow">{a_eyebrow}</div>\n'
                f'        <h3 class="artifact-title">{a_title}</h3>\n'
                f'        <p class="artifact-blurb">{a_blurb}</p>\n'
                '        <div class="artifact-links">\n'
                + "\n".join(link_lines) + "\n"
                + '        </div>\n'
                '      </div>'
            )
        artifacts_html = '    <div class="thinking-artifacts">\n' + "\n".join(cards) + "\n    </div>"

    parts = [
        '<section class="section thinking" id="thinking">',
        '  <div class="wrap">',
        '    <div class="section-head">',
        '      <div>',
        f'        <div class="eyebrow"><span>{eyebrow}</span><span class="line"></span></div>',
        f'        <h2>{headline}</h2>',
        '      </div>',
        f'      <p>{lead}</p>',
        '    </div>',
    ]
    if blockquote_html:
        parts.append(blockquote_html)
    if para_html:
        parts.append(para_html)
    if cta_html:
        parts.append(cta_html)
    if artifacts_html:
        parts.append(artifacts_html)
    parts.append('  </div>')
    parts.append('</section>')
    return "\n".join(parts)


# ─── support / sponsors CTA ─────────────────────────────────────────
SPONSOR_HEART_SVG = (
    '<svg viewBox="0 0 16 16" aria-hidden="true">'
    '<path d="M4.25 2.5c-1.336 0-2.75 1.164-2.75 3 0 2.15 1.58 4.144 3.365 5.682A20.565 20.565 0 008 13.393a20.561 20.561 0 003.135-2.211C12.92 9.644 14.5 7.65 14.5 5.5c0-1.836-1.414-3-2.75-3-1.373 0-2.609.986-3.029 2.456a.749.749 0 01-1.442 0C6.859 3.486 5.623 2.5 4.25 2.5zM8 14.25l-.345.666-.002-.001-.006-.003-.018-.01a7.643 7.643 0 01-.31-.17 22.075 22.075 0 01-3.434-2.414C2.045 10.731 0 8.35 0 5.5 0 2.836 2.086 1 4.25 1 5.797 1 7.153 1.802 8 3.02 8.847 1.802 10.203 1 11.75 1 13.914 1 16 2.836 16 5.5c0 2.85-2.045 5.231-3.885 6.818a22.08 22.08 0 01-3.744 2.584l-.018.01-.006.003h-.002L8 14.25z"/>'
    '</svg>'
)


def render_support(support: dict) -> str:
    """Render the `.support` section — sponsor CTA band."""
    headline = esc(support.get("headline", ""))
    body = esc(support.get("body", ""))
    cta = support.get("cta") or {}
    cta_label = esc(cta.get("label", ""))
    cta_href = attr(cta.get("href", "#"))
    return f"""\
<section class="support" id="support">
  <div class="wrap">
    <div class="support-box">
      <div class="support-copy">
        <h3>{headline}</h3>
        <p>{body}</p>
      </div>
      <a class="sponsor-cta" href="{cta_href}">
        {SPONSOR_HEART_SVG}
        {cta_label}
      </a>
    </div>
  </div>
</section>"""


# ─── contact ────────────────────────────────────────────────────────
def render_contact(contact: dict) -> str:
    """Render the `.contact` section — primary CTA + info rows."""
    eyebrow = esc(contact.get("eyebrow", ""))
    headline = esc(contact.get("headline", ""))
    lead = esc(contact.get("lead", ""))
    pcta = contact.get("primaryCta") or {}
    pcta_label = esc(pcta.get("label", ""))
    pcta_href = attr(pcta.get("href", "#"))
    rows = contact.get("rows") or []

    arrow_svg = '<svg class="ic arrow ic-lg" viewBox="0 0 24 24"><path d="M7 17L17 7M7 7h10v10"/></svg>'
    mail_svg = '<svg class="ic" viewBox="0 0 24 24"><path d="M4 4h16v16H4zM4 4l8 8 8-8"/></svg>'

    def row_html(r: dict) -> str:
        href = r.get("href", "#")
        is_external = href.startswith("http://") or href.startswith("https://")
        target_attrs = ' target="_blank" rel="noopener"' if is_external else ""
        return (
            f'      <a class="contact-row" href="{attr(href)}"{target_attrs}>\n'
            '        <div>\n'
            f'          <div class="label">{esc(r.get("label", ""))}</div>\n'
            f'          <div class="value">{esc(r.get("value", ""))}</div>\n'
            '        </div>\n'
            f'        {arrow_svg}\n'
            '      </a>'
        )
    rows_html = "\n".join(row_html(r) for r in rows)

    return f"""\
<section class="section contact" id="contact">
  <div class="wrap contact-inner">
    <div>
      <div class="eyebrow"><span>{eyebrow}</span><span class="line"></span></div>
      <h2>{headline}</h2>
      <p class="contact-sub">{lead}</p>
      <a class="btn btn-gradient" href="{pcta_href}">
        {pcta_label}
        {mail_svg}
      </a>
    </div>
    <div class="contact-list">
{rows_html}
    </div>
  </div>
</section>"""


# ─── about / manifesto ──────────────────────────────────────────────
def render_about(about: dict) -> str:
    """Render the `.manifesto` section — 'About 626 Labs'.

    paragraphs[] are emitted as raw HTML (not escaped) so the caller can
    include inline <strong>/<em> tags freely. Trust boundary is fine —
    only admins with repo push rights can edit this field.
    """
    eyebrow = esc(about.get("eyebrow", ""))
    headline = esc(about.get("headline", ""))
    accent = esc(about.get("headlineAccent", ""))
    stack = about.get("stack") or []
    paragraphs = about.get("paragraphs") or []
    principles = about.get("principles") or []

    stack_html = "\n".join(
        f'        <span class="stack-chip">{esc(s)}</span>'
        for s in stack
    )
    para_html = "\n".join(
        f"      <p>{p}</p>"  # raw HTML passthrough on purpose
        for p in paragraphs
    )
    principles_html = "\n".join(
        f"""      <div class="principle">
        <div class="num">{esc(pr.get("num", ""))}</div>
        <h4>{esc(pr.get("heading", ""))}</h4>
        <p>{esc(pr.get("body", ""))}</p>
      </div>"""
        for pr in principles
    )

    accent_html = f" <em>{accent}</em>" if accent else ""

    return f"""\
<section class="section manifesto" id="about">
  <div class="wrap manifesto-inner">
    <div>
      <div class="eyebrow"><span>{eyebrow}</span><span class="line"></span></div>
      <h2>{headline}{accent_html}</h2>
      <div class="stack">
{stack_html}
      </div>
    </div>
    <div class="manifesto-body">
{para_html}
    </div>
  </div>

  <div class="wrap">
    <div class="principles">
{principles_html}
    </div>
  </div>
</section>"""


# ─── field notes (auto-discovered stories) ──────────────────────────
# Frontmatter values we trust as raw strings. Quoted-or-unquoted scalars
# only — no nested objects, arrays, or multi-line literals. Story authors
# write frontmatter using the admin's Stories tab, so the surface stays
# narrow on purpose; if a field needs richer typing, special-case it
# below (e.g. `draft` is coerced to a bool).
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_FM_LINE_RE = re.compile(r'^([A-Za-z0-9_]+):\s*(.*?)\s*$')


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value[1:-1]
    return value


def parse_story_frontmatter(text: str) -> tuple[dict, str]:
    """Parse a ---fenced YAML-subset frontmatter block.

    Stdlib-only (no PyYAML). Handles the shape the admin's Stories tab
    writes: simple key/value pairs, quoted strings, ISO dates, booleans.
    Returns (fields_dict, body_markdown). Returns ({}, text) when the
    file has no frontmatter fence — the body is still usable, just lacks
    metadata to surface in the Field Notes card.
    """
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    block = m.group(1)
    body = text[m.end():]
    fields: dict[str, object] = {}
    for line in block.splitlines():
        line = line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        match = _FM_LINE_RE.match(line)
        if not match:
            continue
        key, raw = match.group(1), match.group(2)
        raw_lower = raw.lower()
        if raw_lower in ("true", "false"):
            fields[key] = (raw_lower == "true")
        elif raw == "" or raw_lower in ("null", "~"):
            fields[key] = None
        else:
            fields[key] = _strip_quotes(raw)
    return fields, body


def discover_stories() -> list[dict]:
    """Walk content/stories/, return non-draft entries newest-first.

    Each entry is the parsed frontmatter dict plus the source filename
    (used to build the GitHub link). Files without frontmatter are
    skipped — there's no card to render without title + published date.
    Files with `draft: true` are also skipped — the publishing fence.
    """
    if not STORIES_DIR.is_dir():
        return []
    entries: list[dict] = []
    for path in sorted(STORIES_DIR.glob("*.md")):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        fields, _ = parse_story_frontmatter(text)
        if not fields:
            continue
        if fields.get("draft") is True:
            continue
        if not fields.get("title") or not fields.get("published"):
            # Need both to render a useful card; otherwise skip silently.
            continue
        fields["_filename"] = path.name
        entries.append(fields)
    # Newest-first by `published` (ISO date strings sort lexicographically).
    entries.sort(key=lambda e: str(e.get("published", "")), reverse=True)
    return entries


def story_link(story: dict) -> str:
    """Canonical URL for a Field Note. `external_url` wins when set (a post
    whose canonical home is off-site, e.g. Medium); otherwise the GitHub
    markdown source. Used by both the card CTA and the Atom feed."""
    ext = story.get("external_url")
    if ext:
        return str(ext)
    filename = story.get("_filename", "")
    return (
        f"https://github.com/{STORIES_GITHUB_REPO}/blob/"
        f"{STORIES_GITHUB_BRANCH}/content/stories/{filename}"
    )


def render_field_note(story: dict) -> str:
    """One card. Eyebrow (date · product · source), title, subtitle, tagline, link.

    `external_url` points the CTA at an off-site canonical home; `source`
    labels it in the eyebrow + CTA ("Read on Medium"). Both optional — a
    story without them renders the GitHub-source card exactly as before."""
    title = esc(str(story.get("title", "")))
    subtitle = esc(str(story.get("subtitle", "")))
    tagline = esc(str(story.get("tagline", "")))
    published = esc(str(story.get("published", "")))
    product = esc(str(story.get("product", "")))
    source = esc(str(story.get("source", "")))
    is_external = bool(story.get("external_url"))
    eyebrow_parts = [p for p in (published, product, source) if p]
    eyebrow = " · ".join(eyebrow_parts)
    link_url = story_link(story)
    cta = f"Read on {source}" if (is_external and source) else "Read the full story"

    parts = [
        '      <article class="field-note">',
        f'        <div class="field-note-eyebrow">{eyebrow}</div>',
        f'        <h3 class="field-note-title">{title}</h3>',
    ]
    if subtitle:
        parts.append(f'        <p class="field-note-subtitle">{subtitle}</p>')
    if tagline:
        parts.append(f'        <p class="field-note-tagline">{tagline}</p>')
    parts.append('        <div class="field-note-link">')
    parts.append(
        f'          <a href="{attr(link_url)}" target="_blank" rel="noopener">'
        f'{esc(cta)} '
        '<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" '
        'aria-hidden="true"><path d="M7 17L17 7M7 7h10v10"/></svg></a>'
    )
    parts.append('        </div>')
    parts.append('      </article>')
    return "\n".join(parts)


def render_field_notes(stories: list[dict]) -> str:
    """Whole `<section>` block. Returns "" when no published stories.

    When empty, the SITE_JSON:stories zone collapses to nothing — no
    section, no nav anchor target. The nav link still exists (see
    index.html) but jumps to the top of the page until the first story
    is published. Acceptable v1 — single follow-up commit fixes it.
    """
    if not stories:
        return ""
    cards = "\n".join(render_field_note(s) for s in stories)
    return f"""\
<section class="section field-notes" id="field-notes">
  <div class="wrap">
    <div class="section-head">
      <div>
        <div class="eyebrow"><span>Field Notes</span><span class="line"></span></div>
        <h2>What we shipped, what bit us, what we'd do differently.</h2>
      </div>
      <p>Long-form retrospectives — the unfiltered version of what each launch actually looked like.</p>
    </div>
    <div class="field-notes-grid">
{cards}
    </div>
    <a class="field-notes-subscribe" href="/feed.xml">Subscribe via Atom<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 11a9 9 0 0 1 9 9"/><path d="M4 4a16 16 0 0 1 16 16"/><circle cx="5" cy="19" r="1"/></svg></a>
  </div>
</section>"""


# ─── feed (Atom syndication for Field Notes) ────────────────────────
def _rfc3339(value: object) -> str:
    """Coerce a story's `published` (date-only ISO, e.g. 2026-04-23) into an
    RFC-3339 datetime for Atom. Pass through anything already carrying a time;
    fall back to FEED_EPOCH when empty."""
    s = str(value or "").strip()
    if not s:
        return FEED_EPOCH
    return s if "T" in s else f"{s}T00:00:00Z"


def render_atom_feed(stories: list[dict]) -> str:
    """Build the Field Notes Atom feed from the discovered stories.

    Deterministic by design: the feed's <updated> derives from the newest
    story's published date (never wall-clock), so `--check` stays idempotent
    and CI never sees phantom drift. Each <entry> links to its canonical home
    — external_url for off-site posts, the GitHub source otherwise."""
    updated = _rfc3339(stories[0].get("published")) if stories else FEED_EPOCH
    entries = []
    for s in stories:
        link = story_link(s)
        when = _rfc3339(s.get("published"))
        summary = str(s.get("subtitle") or s.get("tagline") or "")
        author = str(s.get("author") or FEED_AUTHOR)
        entries.append(
            "  <entry>\n"
            f"    <title>{xesc(str(s.get('title', '')))}</title>\n"
            f'    <link href="{xesc(link)}"/>\n'
            f"    <id>{xesc(link)}</id>\n"
            f"    <updated>{when}</updated>\n"
            f"    <published>{when}</published>\n"
            f"    <author><name>{xesc(author)}</name></author>\n"
            f"    <summary>{xesc(summary)}</summary>\n"
            "  </entry>"
        )
    body = ("\n" + "\n".join(entries)) if entries else ""
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<feed xmlns="http://www.w3.org/2005/Atom">\n'
        f"  <title>{xesc(FEED_TITLE)}</title>\n"
        f"  <subtitle>{xesc(FEED_SUBTITLE)}</subtitle>\n"
        f'  <link href="{SITE_URL}/#field-notes"/>\n'
        f'  <link rel="self" type="application/atom+xml" href="{SITE_URL}/feed.xml"/>\n'
        f"  <id>{SITE_URL}/feed.xml</id>\n"
        f"  <updated>{updated}</updated>\n"
        f"  <author><name>{xesc(FEED_AUTHOR)}</name></author>"
        f"{body}\n"
        "</feed>\n"
    )


# ─── sitemap (XML sitemap for search crawlers) ──────────────────────
SITEMAP_PATH = ROOT / "sitemap.xml"
# Directories that have an index.html but should NOT be advertised to
# crawlers. Empty today — every public page is fair game. Add a dir name
# here to keep a future preview/private surface out of the sitemap.
SITEMAP_EXCLUDE: frozenset[str] = frozenset()
# Root-level *.html files that should NOT appear in the sitemap. index.html
# maps to "/" on its own; 404.html is an error page; admin-dashboard.html is
# the PAT-gated admin surface and must stay out of crawler view. Every other
# top-level page (rororo, thesis, workflow, privacy, ...) is public content.
SITEMAP_ROOT_HTML_EXCLUDE: frozenset[str] = frozenset(
    {"index.html", "404.html", "admin-dashboard.html"}
)


def render_sitemap(root: Path = ROOT) -> str:
    """Build an XML sitemap from the pages actually on disk.

    Enumerates three page classes, all filesystem-derived so the sitemap never
    drifts from what actually ships:
      1. the root index.html              -> "/"             (daily, 1.0)
      2. every <dir>/index.html one down  -> "/<dir>/"       (weekly, 0.8)
      3. standalone root <name>.html      -> "/<name>.html"  (monthly, 0.6)
    Class 3 covers the hand-authored content pages (rororo, thesis, workflow,
    privacy) the dir walk would otherwise miss; SITEMAP_ROOT_HTML_EXCLUDE keeps
    index/404/admin out. Add a page and it appears here automatically.
    Deterministic ordering (home, then dirs, then root pages — each alphabetical)
    keeps --check idempotent.
    """
    pages: list[tuple[str, str, str]] = []  # (loc, changefreq, priority)
    if (root / "index.html").exists():
        pages.append((f"{SITE_URL}/", "daily", "1.0"))
    for idx in sorted(root.glob("*/index.html"), key=lambda p: p.parent.name):
        name = idx.parent.name
        if name in SITEMAP_EXCLUDE:
            continue
        pages.append((f"{SITE_URL}/{name}/", "weekly", "0.8"))
    for html in sorted(root.glob("*.html"), key=lambda p: p.name):
        if html.name in SITEMAP_ROOT_HTML_EXCLUDE:
            continue
        pages.append((f"{SITE_URL}/{html.name}", "monthly", "0.6"))

    urls = "\n".join(
        "  <url>\n"
        f"    <loc>{xesc(loc)}</loc>\n"
        f"    <changefreq>{cf}</changefreq>\n"
        f"    <priority>{pr}</priority>\n"
        "  </url>"
        for loc, cf, pr in pages
    )
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}\n"
        "</urlset>\n"
    )


# ─── section toggles ────────────────────────────────────────────────
# Maps sections keys in site.json → DOM id of the <section> element.
SECTION_IDS = {
    "thinking": "thinking",
    "labRuns":  "lab-runs",
    "lab":      "lab",
    "play":     "play",
    "about":    "about",
    "support":  "support",
    "contact":  "contact",
}


def toggle_section(html: str, section_id: str, enabled: bool) -> str:
    """Add or strip the HTML `hidden` attribute on the section with this id.

    Native `<section hidden>` gets display:none in every browser. Preserves
    the section's content so toggling back on restores it instantly — no
    regeneration needed.
    """
    pattern = re.compile(
        r"(<section\s[^>]*id=\"" + re.escape(section_id) + r"\"[^>]*>)",
        re.IGNORECASE,
    )

    def replace(m: re.Match) -> str:
        tag = m.group(1)
        # Strip any existing `hidden` attribute (idempotent).
        tag = re.sub(r'\s+hidden(?=[\s>])', "", tag)
        if not enabled:
            tag = tag[:-1] + " hidden>"
        return tag

    return pattern.sub(replace, html, count=1)


def apply_section_toggles(html: str, sections: dict) -> str:
    for key, dom_id in SECTION_IDS.items():
        enabled = bool((sections.get(key) or {}).get("enabled", True))
        html = toggle_section(html, dom_id, enabled)
    return html


# ─── main ───────────────────────────────────────────────────────────
def main(argv: list[str]) -> int:
    content = json.loads(SITE_JSON.read_text(encoding="utf-8"))
    content = site_facts.resolve_tokens(content, site_facts.facts())
    src = INDEX_HTML.read_text(encoding="utf-8")

    stories = discover_stories()

    out = src
    out = substitute_zone(out, "hero", render_hero(content["hero"]))
    out = substitute_zone(out, "hero-chips", render_chips(content["hero"]["chips"]))
    out = substitute_zone(out, "products", render_products(content["products"]))
    out = substitute_zone(out, "lab-pool", render_lab_pool(content["lab"]), js=True)
    if "thinking" in content:
        out = substitute_zone(out, "thinking", render_thinking(content["thinking"]))
    out = substitute_zone(out, "stories", render_field_notes(stories))
    if "labRuns" in content:
        out = substitute_zone(out, "lab-runs", render_lab_runs(content["labRuns"]))
    if "play" in content:
        out = substitute_zone(out, "play", render_play_section(content["play"]))
    if "about" in content:
        out = substitute_zone(out, "about", render_about(content["about"]))
    if "support" in content:
        out = substitute_zone(out, "support", render_support(content["support"]))
    if "contact" in content:
        out = substitute_zone(out, "contact", render_contact(content["contact"]))
    out = apply_section_toggles(out, content.get("sections") or {})

    feed_new = render_atom_feed(stories)
    feed_old = FEED_PATH.read_text(encoding="utf-8") if FEED_PATH.exists() else None

    sitemap_new = render_sitemap()
    sitemap_old = SITEMAP_PATH.read_text(encoding="utf-8") if SITEMAP_PATH.exists() else None

    index_changed = out != src
    feed_changed = feed_new != feed_old
    sitemap_changed = sitemap_new != sitemap_old

    if "--check" in argv:
        stale = [name for name, drifted in
                 (("index.html", index_changed), ("feed.xml", feed_changed),
                  ("sitemap.xml", sitemap_changed)) if drifted]
        if stale:
            print(
                f"{' and '.join(stale)} out of date relative to content. "
                "Run scripts/render-hub.py.",
                file=sys.stderr,
            )
            return 1
        print("index.html, feed.xml and sitemap.xml are up to date.")
        return 0

    if index_changed:
        INDEX_HTML.write_text(out, encoding="utf-8")
        print(f"index.html rebuilt from {SITE_JSON.relative_to(ROOT)}")
    else:
        print("index.html already matches content/site.json — no change.")

    if feed_changed:
        FEED_PATH.write_text(feed_new, encoding="utf-8")
        print(f"feed.xml rebuilt from {STORIES_DIR.relative_to(ROOT)}/")
    else:
        print("feed.xml already current — no change.")

    if sitemap_changed:
        SITEMAP_PATH.write_text(sitemap_new, encoding="utf-8")
        print("sitemap.xml rebuilt from the page tree.")
    else:
        print("sitemap.xml already current — no change.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
