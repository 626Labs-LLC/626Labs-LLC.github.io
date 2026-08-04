"""Render per-plugin landing pages for the Vibe Plugins family.

Reads content/plugin-pages.json (one entry per plugin + a shared family
list) and emits <plugin-id>/index.html for each, plus plugins/index.html
(the family index). Same no-build, inline-CSS idiom as render-hub.py —
the page CSS is embedded verbatim in each page's <style> block, sourced
from the active theme's archetypes/product.css + archetypes/
product-tokens.css (see STYLE below) rather than hardcoded in this file.

The design (hero + section cards + install + family + footer) is shared
across every page; only the per-plugin content differs. Change the look
once here, regenerate all pages.

Usage:
  python scripts/render-plugin-pages.py            # write all pages
  python scripts/render-plugin-pages.py --check     # drift check (CI), exit 1 if stale

To add a plugin page: add an entry to content/plugin-pages.json and an
icon/banner via scripts/export-plugin-icons.py, then run this. See
docs/vibe-plugins-pages.md.
"""
import json
import re
import sys
from html import escape
from pathlib import Path

import site_facts  # sibling module in scripts/ (added to sys.path when run as a script)
import theme_registry  # sibling module in scripts/ — active theme's product.css

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "content" / "plugin-pages.json"

# ── Shared CSS (identical on every plugin page + the family index) ──────
#
# This is the `product` archetype's dress (scripts/archetypes.py). The 14
# plugin pages plus plugins/index.html are MARKUP this renderer owns (the
# hero/work/brain/install/family shape below is the product archetype's
# vocabulary in practice — see docs/theme-archetypes.md) but the CSS that
# dresses that markup now lives with the theme, not here: STYLE is read
# from the ACTIVE theme every run, same governance render-hub.py uses for
# its home/reading archetypes and the utility pages' "theme-css" zone. A
# theme rotation's product dress reaches these 15 pages on the next
# render, no code change required. Still inlined (not linked) — this
# file's "no-build, inline-CSS idiom" per the module docstring; only the
# CSS's *source* moved, not its delivery.
#
# TWO files, concatenated:
#   archetypes/product.css         — the element dress
#   archetypes/product-tokens.css  — custom-property definitions only
#
# They are separate on disk because conundrum.html and rororo-plugins.html
# LINK the token half and must not receive the dress half: they are
# hand-authored, keep their own layout, and the dress's bare element
# selectors (`body`, `a:hover`, `section.hero`, `.card`, `.btn`) land on
# markup written for THIS renderer's templates, not theirs. See
# product-tokens.css's header for the measurement behind that split.
# Concatenating here is what keeps the split invisible to these 15 pages:
# they still receive exactly one <style> block holding both halves.
#
# ORDER IS DRESS-FIRST, AND THAT IS NOT A STYLE CHOICE.
#
# product.css opens with `@import url('/fonts/fonts.css')`. CSS requires
# @import to precede every rule but @charset/@layer — put ANY rule in front
# of it and the browser silently drops the import. Concatenating tokens
# first does exactly that: the whole brand type stack (Space Grotesk /
# Inter / JetBrains Mono) stops loading and all 15 pages reflow to fallback
# fonts. Measured, not theorised — tokens-first was tried and moved
# 1,321,489 pixels on plugins/index.html alone and changed every page's
# height. tests/test_render_plugin_pages.py pins the @import to the first
# rule position in STYLE so this cannot regress silently.
#
# Order is otherwise inert: the two files share 11 custom-property names
# and every one carries an identical value (asserted by
# test_product_css_and_tokens_agree_on_every_shared_name), and custom
# properties resolve at computed-value time, so product.css's treatment
# rules read --pb-* fine from a block that appears after them.
_theme_reg = theme_registry.load()
_active_theme = theme_registry.active_slug(_theme_reg)
_ARCHETYPE_DIR = theme_registry.theme_dir(_active_theme) / "archetypes"
_PRODUCT_TOKENS_CSS = _ARCHETYPE_DIR / "product-tokens.css"
_PRODUCT_CSS = _ARCHETYPE_DIR / "product.css"
STYLE = (
    _PRODUCT_CSS.read_text(encoding="utf-8").rstrip("\n")
    + "\n"
    + _PRODUCT_TOKENS_CSS.read_text(encoding="utf-8")
)

COPY_SCRIPT = """
  <script>
    document.querySelectorAll('.copybtn').forEach(function(btn) {
      btn.addEventListener('click', function() {
        var target = document.getElementById(btn.getAttribute('data-target'));
        if (!target || !navigator.clipboard) { return; }
        navigator.clipboard.writeText(target.textContent).then(function() {
          var orig = btn.textContent;
          btn.textContent = 'copied';
          btn.classList.add('ok');
          setTimeout(function() { btn.textContent = orig; btn.classList.remove('ok'); }, 1500);
        }).catch(function() {
          var orig = btn.textContent;
          btn.textContent = 'press Ctrl+C';
          setTimeout(function() { btn.textContent = orig; }, 1500);
        });
      });
    });
  </script>
"""


def num_word(n):
    return site_facts.number_word(n)


def e(s):
    return escape(str(s), quote=True)


def icon_path(plugin_id):
    return f"/assets/brand/plugins/{plugin_id}-icon-transparent-512.png"


# Live plugin versions, refreshed daily by .github/workflows/refresh-plugin-versions.yml
# (id -> "vX.Y.Z"). Baked into each page so versions can't drift from the released
# tags. Missing entries (repos with no tags) fall back to the heroMeta version.
PLUGIN_VERSIONS: dict = {}
_pv_path = ROOT / "data" / "plugin-versions.json"
if _pv_path.exists():
    PLUGIN_VERSIONS = json.loads(_pv_path.read_text(encoding="utf-8"))

# Per-plugin "Validated on" credibility line, excerpted from each repo README.
PLUGIN_VALIDATED: dict = {}
_val_path = ROOT / "content" / "plugin-validated.json"
if _val_path.exists():
    PLUGIN_VALIDATED = json.loads(_val_path.read_text(encoding="utf-8")).get("validated", {})

# Live capability counts, refreshed daily alongside the versions by
# .github/workflows/refresh-plugin-versions.yml (id -> {commands, skills, agents}).
# These mirror Claude Code's pre-install preview — the literal install footprint —
# counted from each repo's file tree. Missing entries render no chip.
PLUGIN_STATS: dict = {}
_ps_path = ROOT / "data" / "plugin-stats.json"
if _ps_path.exists():
    PLUGIN_STATS = json.loads(_ps_path.read_text(encoding="utf-8"))


def caps_text(plugin_id) -> str:
    """Bare 'commands · skills · agents' footprint string — zeros omitted,
    pluralized, ' &middot; '-joined. Empty when we have no counts for this
    plugin. Shared by the hero chip and the family-index cards."""
    s = PLUGIN_STATS.get(plugin_id)
    if not s:
        return ""
    parts = []
    for key, noun in (("commands", "command"), ("skills", "skill"), ("agents", "agent")):
        n = int(s.get(key, 0) or 0)
        if n:
            parts.append(f"{n} {noun}" + ("" if n == 1 else "s"))
    return " &middot; ".join(parts)


def caps_line(plugin_id) -> str:
    """The hero 'Includes …' footprint chip. Empty when no counts."""
    inner = caps_text(plugin_id)
    if not inner:
        return ""
    return f'\n            <p class="hero-caps"><span class="captag">Includes</span>{inner}</p>'


def effective_version(p) -> str | None:
    """Live tag for this plugin if we have one, else the hand-set heroMeta version."""
    hero = [str(x) for x in p.get("heroMeta", [])]
    fallback = next((x for x in hero if re.match(r"^v?\d+\.\d+", x)), None)
    return PLUGIN_VERSIONS.get(p["id"], fallback)


def software_jsonld(p) -> str:
    """SoftwareApplication structured data for a plugin landing page.

    Built with json.dumps so descriptions (em-dashes, apostrophes) escape
    correctly. softwareVersion is parsed from the leading vX.Y token in
    heroMeta; license is emitted only when the plugin actually declares MIT
    there (no guessing for the few that don't). Every family plugin is a free,
    installable Claude Code developer tool, so offers + isAccessibleForFree are
    accurate to assert across the board.
    """
    url = f"https://626labs.dev/{p['id']}/"
    hero = [str(x) for x in p.get("heroMeta", [])]
    version = (effective_version(p) or "").lstrip("v") or None
    is_mit = any(x.upper() == "MIT" for x in hero)
    data = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "@id": url + "#software",
        "name": p["name"],
        "description": p["metaDescription"],
        "url": url,
        "applicationCategory": "DeveloperApplication",
        "operatingSystem": "Claude Code",
        "image": "https://626labs.dev" + p["ogImage"],
        "isAccessibleForFree": True,
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "author": {
            "@type": "Organization",
            "@id": "https://626labs.dev/#org",
            "name": "626 Labs",
            "url": "https://626labs.dev/",
        },
    }
    if version:
        data["softwareVersion"] = version
    if is_mit:
        data["license"] = "https://opensource.org/licenses/MIT"
    # <-escape any "<" so a description can never break out of the script tag.
    payload = json.dumps(data, indent=2, ensure_ascii=False).replace("<", "\\u003c")
    return f'  <script type="application/ld+json">\n{payload}\n  </script>\n'


def render_head(p):
    title = e(p["metaTitle"])
    desc = e(p["metaDescription"])
    url = f"https://626labs.dev/{p['id']}/"
    og = "https://626labs.dev" + p["ogImage"]
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <link rel="preload" as="font" type="font/woff2" href="/fonts/SpaceGrotesk-Variable.woff2" crossorigin />
  <link rel="preload" as="font" type="font/woff2" href="/fonts/Inter-Variable.woff2" crossorigin />
  <title>{title}</title>
  <meta name="description" content="{desc}" />
  <link rel="canonical" href="{url}" />
  <link rel="icon" type="image/png" href="/favicon-626.png" />

  <meta property="og:title" content="{e(p['ogTitle'])}" />
  <meta property="og:description" content="{desc}" />
  <meta property="og:url" content="{url}" />
  <meta property="og:image" content="{og}" />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="626 Labs" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{e(p['ogTitle'])}" />
  <meta name="twitter:description" content="{desc}" />
  <meta name="twitter:image" content="{og}" />

{software_jsonld(p)}
  <style>{STYLE}  </style>
</head>
<body>
  <div class="pb-scanlines" aria-hidden="true"></div>
  <a class="skip-link" href="#main">Skip to content</a>
"""


def render_nav(p):
    return f"""
  <nav class="top">
    <div class="container row">
      <div class="brand-row">
        <a href="/" class="brand">
          <img src="/assets/brand/icon-transparent-256.png" alt="626Labs" />
          <span>626Labs</span>
        </a>
        <span class="brand-sep" aria-hidden="true">/</span>
        <span class="brand-current">
          <span class="vibe-mark" aria-hidden="true"><img src="{icon_path(p['id'])}" alt="" /></span>
          <span>{e(p['name'])}</span>
        </span>
      </div>
      <a href="#install" class="btn btn-ghost">Install</a>
    </div>
  </nav>
"""


def render_hero(p):
    ctas = ['<a href="#install" class="btn btn-primary">%s</a>' % e(p["ctas"]["primary"]["label"])]
    sec = p["ctas"].get("secondary")
    if sec:
        ctas.append(f'<a href="{e(sec["href"])}" class="btn btn-ghost">{e(sec["label"])}</a>')
    hero_meta = list(p["heroMeta"])
    ev = effective_version(p)
    if ev and hero_meta and re.match(r"^v?\d+\.\d+", str(hero_meta[0])):
        hero_meta[0] = ev
    meta = "<span>·</span>".join(f"<span>{e(m)}</span>" for m in hero_meta)

    vtext = PLUGIN_VALIDATED.get(p["id"])
    validated_html = (
        f'\n            <p class="hero-validated"><span class="vtag">Validated</span>{e(vtext)}</p>'
        if vtext else ""
    )
    caps_html = caps_line(p["id"])

    term = p.get("terminal")
    if term:
        lines = "\n".join("                <div>%s</div>" % ln for ln in term["lines"])
        right = f"""
          <div class="hero-right">
            <div class="term">
              <div class="term-bar">
                <span class="term-dot r"></span>
                <span class="term-dot y"></span>
                <span class="term-dot g"></span>
                <span class="term-label">{e(term['label'])}</span>
              </div>
              <div class="term-body">
{lines}
              </div>
            </div>
          </div>"""
        grid_class = "hero-grid"
    else:
        right = ""
        grid_class = "hero-grid solo"

    return f"""
    <section class="hero">
      <div class="container">
        <div class="{grid_class}">
          <div class="hero-left">
            <span class="eyebrow">{e(p['eyebrow'])}</span>
            <h1>{e(p['h1'])}</h1>
            <p class="hero-subhead">{p['subhead']}</p>
            <div class="hero-ctas">
              {''.join(ctas)}
            </div>
            <div class="hero-meta">
              {meta}
            </div>{caps_html}{validated_html}
          </div>
{right}
        </div>
      </div>
    </section>
"""


def render_card(c):
    reach = ""
    if c.get("reach"):
        reach = f'\n            <p class="reach">{c["reach"]}</p>'
    return f"""          <div class="card">
            <span class="cmd">{e(c['command'])}</span>
            <h3>{e(c['title'])}</h3>
            <p class="desc">{c['desc']}</p>{reach}
          </div>"""


def render_cards_section(s):
    cols = " cols-3" if s.get("cols") == 3 else ""
    cards = "\n\n".join(render_card(c) for c in s["cards"])
    extra = ""
    if s.get("mini"):
        hint = f'<span class="hint">{e(s["mini"].get("hint", ""))}</span>' if s["mini"].get("hint") else ""
        minis = "\n".join(
            f"""          <div class="mini">
            <span class="name">{e(m['name'])}</span>
            <p class="desc">{m['desc']}</p>
          </div>""" for m in s["mini"]["items"]
        )
        extra = f"""

        <div class="sub-head">
          <h3>{e(s['mini']['heading'])}</h3>
          {hint}
        </div>
        <div class="mini-grid">
{minis}
        </div>"""
    lead = f'\n          <p class="lead">{s["lead"]}</p>' if s.get("lead") else ""
    return f"""
    <section class="work">
      <div class="container">
        <div class="section-head">
          <span class="eyebrow">{e(s['eyebrow'])}</span>
          <h2>{e(s['heading'])}</h2>{lead}
        </div>

        <div class="cards-grid{cols}">
{cards}
        </div>{extra}
      </div>
    </section>
"""


def render_prose_section(s):
    paras = "\n            ".join(f"<p>{para}</p>" for para in s["paragraphs"])
    callout = ""
    if s.get("callout"):
        callout = f"""
          <div>
            <div class="callout">{e(s['callout'])}</div>
          </div>"""
        grid_open = '<div class="brain-grid">'
    else:
        grid_open = "<div>"
    grid_close = "</div>"
    return f"""
    <section class="brain">
      <div class="container">
        <div class="section-head">
          <span class="eyebrow">{e(s['eyebrow'])}</span>
          <h2>{e(s['heading'])}</h2>
        </div>
        {grid_open}
          <div>
            {paras}
          </div>{callout}
        {grid_close}
      </div>
    </section>
"""


def render_install(p):
    inst = p["install"]
    solo = " solo" if not inst.get("canary") else ""
    cards = [f"""          <div class="card install-card">
            <h3>Stable <span class="badge">marketplace</span></h3>
            <p class="blurb">{e(inst.get('stableBlurb', 'Tagged releases, promoted via the Vibe Plugins marketplace.'))}</p>
            <div class="codeblock">
              <button class="copybtn" data-target="copy-stable" aria-label="Copy stable install command">copy</button>
              <pre id="copy-stable" style="margin:0;white-space:pre">{e(inst['stable'])}</pre>
            </div>
          </div>"""]
    if inst.get("canary"):
        cards.append(f"""          <div class="card install-card">
            <h3>Canary <span class="badge magenta">bleeding edge</span></h3>
            <p class="blurb">{e(inst.get('canaryBlurb', 'Latest main from this repo.'))}</p>
            <div class="codeblock">
              <button class="copybtn" data-target="copy-canary" aria-label="Copy canary install command">copy</button>
              <pre id="copy-canary" style="margin:0;white-space:pre">{e(inst['canary'])}</pre>
            </div>
          </div>""")
    note = f'\n        <p class="install-note">{e(inst["note"])}</p>' if inst.get("note") else ""
    return f"""
    <section class="install" id="install">
      <div class="container">
        <div class="section-head">
          <span class="eyebrow">{e(p.get('installEyebrow', '03 · Get it'))}</span>
          <h2>{e('Two channels.' if inst.get('canary') else 'Install.')}</h2>
        </div>

        <div class="install-grid{solo}">
{chr(10).join(cards)}
        </div>{note}
      </div>
    </section>
"""


def render_family(current_id, family):
    cards = []
    for f in family:
        here = " here" if f["id"] == current_id else ""
        you = '\n            <div class="you">You are here</div>' if f["id"] == current_id else ""
        cards.append(f"""          <a href="{e(f['href'])}" class="family-card{here}">
            <span class="fc-mark" aria-hidden="true"><img src="{icon_path(f['id'])}" alt="" /></span>
            <div>
              <div class="name">{e(f['name'])}</div>
              <div class="role">{e(f['role'])}</div>{you}
            </div>
          </a>""")
    return f"""
    <section class="family">
      <div class="container">
        <div class="section-head">
          <span class="eyebrow">04 · Family</span>
          <h2>One plugin in a family.</h2>
        </div>
        <p class="family-lead">Vibe Plugins are a coordinated family &mdash; installed independently, composed when present.</p>

        <div class="family-grid">
{chr(10).join(cards)}
        </div>
      </div>
    </section>
"""


def render_footer():
    return """
  <footer>
    <div class="container row">
      <div>626Labs LLC · MIT · 2026</div>
      <div class="tagline">Imagine Something Else.</div>
      <div class="links">
        <a href="/plugins/">All plugins</a>
        <a href="https://github.com/estevanhernandez-stack-ed/vibe-plugins">Marketplace</a>
      </div>
    </div>
  </footer>
"""


def render_page(p, family):
    parts = [render_head(p), render_nav(p), "\n  <main id=\"main\">\n", render_hero(p)]
    for s in p["sections"]:
        if s["type"] == "cards":
            parts.append(render_cards_section(s))
        elif s["type"] == "prose":
            parts.append(render_prose_section(s))
    parts.append(render_install(p))
    parts.append(render_family(p["id"], family))
    parts.append("\n  </main>\n")
    parts.append(render_footer())
    parts.append(COPY_SCRIPT)
    parts.append("\n</body>\n</html>\n")
    return "".join(parts)


def render_thesis(thesis):
    """The `.thesis` section on /plugins/ — the Self-Evolving Plugin
    Framework pitch, migrated down from the homepage's `thinking` section
    (content copied verbatim; Task A4 removes the homepage copy).

    Collapses to "" when `thesis` is absent from plugin-pages.json.
    Escaping follows this file's convention: eyebrow/headline/artifact
    title/cta label are escaped; lead/quote/paragraphs/blurb are raw HTML,
    matching the sibling prose fields documented in the file's $comment.
    """
    if not thesis:
        return ""
    eyebrow = e(thesis.get("eyebrow", ""))
    headline = e(thesis.get("headline", ""))
    lead = thesis.get("lead", "")
    quote = thesis.get("quote", "")
    paragraphs = thesis.get("paragraphs") or []
    cta = thesis.get("cta") or {}
    artifacts = thesis.get("artifacts") or []

    lead_html = f'\n          <p class="lead">{lead}</p>' if lead else ""
    quote_html = f'\n        <blockquote>{quote}</blockquote>' if quote else ""
    para_html = "\n".join(f'        <p>{p}</p>' for p in paragraphs)

    cta_html = ""
    if cta.get("label") and cta.get("href"):
        cta_html = f"""
        <div class="thesis-link">
          <a href="{e(cta['href'])}">{e(cta['label'])} <svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg></a>
        </div>"""

    artifacts_html = ""
    if artifacts:
        cards = []
        for art in artifacts:
            a_eyebrow = e(art.get("eyebrow", ""))
            a_title = e(art.get("title", ""))
            a_blurb = art.get("blurb", "")
            links = art.get("links") or []
            link_lines = [
                f'              <a href="{e(l["href"])}">{e(l["label"])} '
                f'<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
                f'stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" '
                f'aria-hidden="true"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg></a>'
                for l in links if l.get("label") and l.get("href")
            ]
            cards.append(
                '          <div class="card thesis-artifact">\n'
                f'            <div class="artifact-eyebrow">{a_eyebrow}</div>\n'
                f'            <h3 class="artifact-title">{a_title}</h3>\n'
                f'            <p class="artifact-blurb">{a_blurb}</p>\n'
                '            <div class="artifact-links">\n'
                + "\n".join(link_lines) + "\n"
                + '            </div>\n'
                '          </div>'
            )
        artifacts_html = '\n        <div class="thesis-artifacts">\n' + "\n".join(cards) + "\n        </div>"

    return f"""
    <section class="thesis" id="thesis">
      <div class="container">
        <div class="section-head">
          <span class="eyebrow">{eyebrow}</span>
          <h2>{headline}</h2>{lead_html}
        </div>{quote_html}
{para_html}{cta_html}{artifacts_html}
      </div>
    </section>
"""


def render_index(data):
    """The /plugins/ family index."""
    family = data["family"]
    cards = []
    for f in family:
        caps = caps_text(f["id"])
        caps_html = f'\n              <div class="fc-caps">{caps}</div>' if caps else ""
        beat_html = f'\n              <div class="fc-beat">{f["beat"]}</div>' if f.get("beat") else ""
        cards.append(f"""          <a href="{e(f['href'])}" class="family-card">
            <span class="fc-mark" aria-hidden="true"><img src="{icon_path(f['id'])}" alt="" /></span>
            <div>
              <div class="name">{e(f['name'])}</div>
              <div class="role">{e(f['role'])}</div>{caps_html}{beat_html}
            </div>
          </a>""")
    count_word = num_word(len(family))
    og = "https://626labs.dev/assets/brand/vibe-plugins-banner-1280x640.png"
    head = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Vibe Plugins · Claude Code plugins by 626Labs</title>
  <meta name="description" content="A coordinated family of Claude Code plugins by 626Labs — planning, iteration, docs, tests, security, and research authoring." />
  <link rel="canonical" href="https://626labs.dev/plugins/" />
  <link rel="icon" type="image/png" href="/favicon-626.png" />
  <meta property="og:title" content="Vibe Plugins · for Claude Code" />
  <meta property="og:description" content="A coordinated family of Claude Code plugins by 626Labs." />
  <meta property="og:url" content="https://626labs.dev/plugins/" />
  <meta property="og:image" content="{og}" />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="626 Labs" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:image" content="{og}" />
  <style>{STYLE}  </style>
</head>
<body>
  <div class="pb-scanlines" aria-hidden="true"></div>
  <a class="skip-link" href="#main">Skip to content</a>
"""
    nav = """
  <nav class="top">
    <div class="container row">
      <a href="/" class="brand">
        <img src="/assets/brand/icon-transparent-256.png" alt="626Labs" />
        <span>626Labs</span>
      </a>
      <a href="https://github.com/estevanhernandez-stack-ed/vibe-plugins" class="btn btn-ghost">Marketplace</a>
    </div>
  </nav>
"""
    hero = """
    <section class="hero">
      <div class="container">
        <div class="hero-grid">
          <div class="hero-left">
            <span class="eyebrow">626Labs · for Claude Code</span>
            <h1>Vibe Plugins.</h1>
            <p class="hero-subhead">A coordinated family of Claude Code plugins &mdash; installed independently, composed when present. Plan it, ship it, iterate it, document it, test it, secure it.</p>
            <div class="hero-ctas">
              <a href="https://github.com/estevanhernandez-stack-ed/vibe-plugins" class="btn btn-primary">Get the marketplace</a>
            </div>
          </div>
          <div class="hero-right hero-mark">
            <img src="/assets/brand/vibe-plugins-mark-transparent-512.png" alt="Vibe Plugins" />
          </div>
        </div>
      </div>
    </section>
"""
    grid = f"""
    <section class="family">
      <div class="container">
        <div class="section-head">
          <span class="eyebrow">The family</span>
          <h2>{count_word} plugins, one playbook.</h2>
          <p class="lead">Each ships on its own. Each composes with the others when they share a repo.</p>
        </div>
        <div class="family-grid">
{chr(10).join(cards)}
        </div>
      </div>
    </section>
"""
    thesis_html = render_thesis(data.get("thesis"))
    return head + nav + "\n  <main id=\"main\">\n" + hero + grid + thesis_html + "\n  </main>\n" + render_footer() + "\n</body>\n</html>\n"


def build():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    data = site_facts.resolve_tokens(data, site_facts.facts())
    family = data["family"]
    outputs = {}
    for pid, p in data["plugins"].items():
        p["id"] = pid
        outputs[ROOT / pid / "index.html"] = render_page(p, family)
    outputs[ROOT / "plugins" / "index.html"] = render_index(data)
    return outputs


def main():
    check = "--check" in sys.argv
    outputs = build()

    # --list-outputs: one repo-relative, posix-style path per line, and
    # nothing else on stdout. The CI workflows' change-detection and
    # `git add` lists used to name these with the glob `vibe-* thesis-engine
    # plugins`, which is wrong in two ways. The glob only self-maintains for
    # ids starting `vibe-` — `thesis-engine` was already the counterexample
    # and had to be hand-listed, so the next non-`vibe-` plugin id renders on
    # the runner and is never committed, silently. And a glob that matches
    # nothing is passed to git literally, which errors, which makes
    # `[ -n "$(…)" ]` evaluate FALSE — reporting "no changes" instead of
    # failing. Both workflows ask this script instead now: it is the only
    # thing that actually knows what it writes.
    if "--list-outputs" in sys.argv:
        # LF explicitly, never the platform default. On Windows print()
        # emits CRLF, and a path with a trailing \r reaches git as a
        # different pathspec — `git add` then dies with
        # "pathspec 'vibe-iterate/index.html?' did not match any files".
        # Same discipline as this script's own write_text(newline="\n").
        # reconfigure() is what actually does it: sys.stdout is a text
        # stream, so on Windows it translates "\n" to "\r\n" on the way out
        # no matter what the caller writes.
        sys.stdout.reconfigure(newline="\n")
        sys.stdout.write(
            "".join(f"{p.relative_to(ROOT).as_posix()}\n" for p in outputs)
        )
        return

    drift = []
    for path, html in outputs.items():
        existing = path.read_text(encoding="utf-8") if path.exists() else None
        if existing != html:
            drift.append(path)
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(html, encoding="utf-8", newline="\n")
    if check:
        if drift:
            print("DRIFT — these pages are stale, run render-plugin-pages.py:")
            for d in drift:
                print(f"  {d.relative_to(ROOT)}")
            sys.exit(1)
        print("plugin pages up to date.")
    else:
        for path in outputs:
            print(f"  wrote {path.relative_to(ROOT)}")
        print(f"{len(outputs)} pages rendered.")


if __name__ == "__main__":
    main()
