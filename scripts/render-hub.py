#!/usr/bin/env python3
"""
626 Labs hub renderer — materializes index.html from content/site.json.

Marker-based partial rendering: the renderer finds pairs of
`<!-- SITE_JSON:<zone>:start -->` and `:end` comments in index.html and
replaces the content between them with HTML generated from site.json.

Zones handled (Phase 2):
- hero         — eyebrow, h1, sub, actions, meta
- hero-chips   — chips around the animated logo
- products     — the 5 product cards in the Work section
- lab-pool     — the JS LAB_POOL array that drives "Also from the lab"

Zones NOT handled (stay hand-edited in index.html):
- nav / footer
- Thinking section
- How the lab runs section
- Manifesto / principles
- Support CTA body
- Contact section

Stdlib only — runs in any Python 3.10+ on CI without `pip install`.
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

# ─── paths ──────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
SITE_JSON = ROOT / "content" / "site.json"
INDEX_HTML = ROOT / "index.html"


# ─── helpers ────────────────────────────────────────────────────────
def esc(s: str | None) -> str:
    """HTML-escape user content (text nodes)."""
    return html.escape(s or "", quote=False)


def attr(s: str | None) -> str:
    """HTML-escape for attribute values."""
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
    "vibe-doc": (
        '<svg class="ic-lg ic" viewBox="0 0 24 24">'
        '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
        '<path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/></svg>'
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
              <div><span class="s">✓</span> onboard · builder profile loaded</div>
              <div><span class="s">✓</span> scope · focused project brief</div>
              <div><span class="s">✓</span> prd · acceptance criteria drafted</div>
              <div><span class="s">✓</span> spec · technical blueprint</div>
              <div><span class="muted">→ checklist · build · iterate · reflect</span></div>
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

SHIELDS_RELEASE_FILTER = {
    # Monorepo: filter by tag prefix for the package releases.
    "vibe-test": "?filter=vibe-test-v*",
}

# Category label that sits under the flagship tag row ("SPEC-DRIVEN · SELF-EVOLVING").
# Keyed by product id. Flagship-only.
PRODUCT_CATEGORY_LABELS = {
    "vibe-cartographer": "SPEC-DRIVEN · SELF-EVOLVING",
}

# Foot-row meta text per product id (left half of product-foot).
# Wrapped in <code>…</code> if the pattern is a slash command.
PRODUCT_FOOT_META = {
    "vibe-doc": "<code>/vibe-doc</code> · gap analyzer",
    "vibe-test": "<code>/vibe-test:audit</code> · harness-aware",
    "sanduhr": "SwiftUI · WinUI · menu bar",
    "vibe-sec": "/vibe-sec · drafting",
}


CLAUDE_CODE_BADGE = (
    # Claude Code skill — Anthropic-orange (D97757), dark label (141414),
    # Anthropic sparkle loaded via shields.io's simpleicons integration.
    'https://img.shields.io/badge/Claude%20Code-skill-D97757?'
    'style=flat-square&logo=anthropic&logoColor=F5F5F0&labelColor=141414'
)


def render_badges(p: dict) -> str:
    """Claude Code skill (if applicable) + npm version + downloads (maskable) + release + license."""
    npm = p.get("npm")
    claude_code = bool(p.get("claudeCode"))

    # WIP plugins that aren't on npm still get the Claude Code signal if flagged.
    if not npm and not claude_code:
        return ""

    # When there's no npm but the product is a Claude Code plugin (wip/coming-soon),
    # show only the Claude Code badge.
    if not npm:
        return f"""\
        <div class="badges">
          <img src="{attr(CLAUDE_CODE_BADGE)}" alt="Claude Code skill">
        </div>"""
    repo = p.get("repo") or ""
    pid = p.get("id", "")
    filt = SHIELDS_RELEASE_FILTER.get(pid, "")
    # Release badge always points at the GitHub repo in .repo. For the
    # monorepo-based plugins, filter narrows to the package's tag prefix.
    release_url = (
        f"https://img.shields.io/github/v/release/{repo}{filt}"
        f"&color={BADGE_COLOR_GREEN}" if filt
        else f"https://img.shields.io/github/v/release/{repo}?color={BADGE_COLOR_GREEN}"
    )
    # Re-structure: always use a clean query string.
    if filt:
        release_url = (
            f"https://img.shields.io/github/v/release/{repo}"
            f"{filt}&color={BADGE_COLOR_GREEN}&labelColor={BADGE_LABEL_BG}&style=flat-square&label=release"
        )
    else:
        release_url = (
            f"https://img.shields.io/github/v/release/{repo}"
            f"?color={BADGE_COLOR_GREEN}&labelColor={BADGE_LABEL_BG}&style=flat-square&label=release"
        )
    cc_badge = (
        f'          <img src="{attr(CLAUDE_CODE_BADGE)}" alt="Claude Code skill">\n'
        if claude_code else ""
    )
    return f"""\
        <div class="badges">
{cc_badge}          <img src="https://img.shields.io/npm/v/{attr(npm)}?color={BADGE_COLOR_CYAN}&labelColor={BADGE_LABEL_BG}&style=flat-square" alt="npm version">
          <img data-maskable="true" src="https://img.shields.io/npm/dt/{attr(npm)}?color={BADGE_COLOR_MAGENTA}&labelColor={BADGE_LABEL_BG}&style=flat-square&label=downloads" alt="total downloads">
          <img src="{attr(release_url)}" alt="latest release">
          <img src="https://img.shields.io/npm/l/{attr(npm)}?color={BADGE_COLOR_GREEN}&labelColor={BADGE_LABEL_BG}&style=flat-square" alt="MIT license">
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


def render_product_foot(p: dict) -> str:
    """Foot row: product-meta + product-link."""
    pid = p.get("id", "")
    repo = p.get("repo", "")
    product_page = p.get("productPage")
    meta = PRODUCT_FOOT_META.get(pid, "")

    if product_page:
        link = (
            f'<a class="product-link" href="{attr(product_page)}">'
            "Open product page "
            '<svg class="ic arrow" viewBox="0 0 24 24"><path d="M5 12h14M13 5l7 7-7 7"/></svg>'
            "</a>"
        )
    elif p.get("status") == "wip":
        link = (
            f'<a class="product-link" href="https://github.com/{attr(repo)}/tree/main/packages/{attr(pid)}">'
            "Framework doc "
            '<svg class="ic arrow" viewBox="0 0 24 24"><path d="M7 17L17 7M7 7h10v10"/></svg>'
            "</a>"
        )
    else:
        link_target = f"https://github.com/{repo}"
        if pid == "vibe-test":
            link_target += "/tree/main/packages/vibe-test"
        link = (
            f'<a class="product-link" href="{attr(link_target)}">'
            "Open repo "
            '<svg class="ic arrow" viewBox="0 0 24 24"><path d="M7 17L17 7M7 7h10v10"/></svg>'
            "</a>"
        )

    return f"""\
        <div class="product-foot">
          <div class="product-meta">{meta}</div>
          {link}
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

    parts = [f'      <article class="{class_attr}">', head, f"        <h3>{title}</h3>"]
    parts.append(f'        <p class="product-desc">{description}</p>')
    if badges_html:
        parts.append(badges_html)
    if install_html:
        parts.append(install_html)
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


# ─── section toggles ────────────────────────────────────────────────
# Maps sections keys in site.json → DOM id of the <section> element.
SECTION_IDS = {
    "thinking": "thinking",
    "labRuns":  "lab-runs",
    "lab":      "lab",
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
    src = INDEX_HTML.read_text(encoding="utf-8")

    out = src
    out = substitute_zone(out, "hero", render_hero(content["hero"]))
    out = substitute_zone(out, "hero-chips", render_chips(content["hero"]["chips"]))
    out = substitute_zone(out, "products", render_products(content["products"]))
    out = substitute_zone(out, "lab-pool", render_lab_pool(content["lab"]), js=True)
    out = apply_section_toggles(out, content.get("sections") or {})

    changed = out != src
    if "--check" in argv:
        if changed:
            print("index.html is out of date relative to content/site.json. Run scripts/render-hub.py.", file=sys.stderr)
            return 1
        print("index.html is up to date.")
        return 0

    if changed:
        INDEX_HTML.write_text(out, encoding="utf-8")
        print(f"index.html rebuilt from {SITE_JSON.relative_to(ROOT)}")
    else:
        print("index.html already matches content/site.json — no change.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
