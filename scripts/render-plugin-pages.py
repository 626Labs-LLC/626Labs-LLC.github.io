"""Render per-plugin landing pages for the Vibe Plugins family.

Reads content/plugin-pages.json (one entry per plugin + a shared family
list) and emits <plugin-id>/index.html for each, plus plugins/index.html
(the family index). Same no-build, inline-CSS idiom as render-hub.py.

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

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "content" / "plugin-pages.json"

# ── Shared CSS (identical on every plugin page + the family index) ──────
STYLE = """
    /* 626 Labs Design System tokens — see ../Design/colors_and_type.css */
    @import url('/fonts/fonts.css');

    :root {
      --navy-deep: #0f1f31;
      --navy-mid:  #192e44;
      --navy-hi:   #223a54;
      --navy-line: #2a3a5c;
      --cyan:      #17d4fa;
      --cyan-pale: #5ce6ff;
      --cyan-dim:  #0fa8c9;
      --magenta:   #f22f89;
      --magenta-pale: #ff66a8;
      --success:   #2bd99a;
      --ink-0:     #ffffff;
      --ink-100:   #e8eef7;
      --ink-200:   #c0cad8;
      --ink-300:   #a4afbf;
      --ink-400:   #97a4b5;
      --r-sm: 6px;
      --r-md: 10px;
      --r-lg: 14px;
      --r-xl: 20px;
      --maxw: 1240px;
      --gutter: 24px;
      --grad-duo: linear-gradient(135deg, var(--cyan) 0%, var(--magenta) 100%);
    }

    * { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; }
    body {
      background: var(--navy-deep);
      color: var(--ink-100);
      font-family: 'Inter', system-ui, sans-serif;
      font-size: 16px;
      line-height: 1.55;
      -webkit-font-smoothing: antialiased;
    }
    a { color: var(--cyan); text-decoration: none; }
    a:hover { text-decoration: underline; text-decoration-color: var(--magenta); }

    .skip-link {
      position: absolute; left: 8px; top: -52px; z-index: 200;
      background: var(--cyan); color: var(--navy-deep);
      padding: 8px 16px; border-radius: var(--r-md);
      font-family: 'Inter', sans-serif; font-weight: 600; font-size: 14px;
      transition: top 120ms ease;
    }
    .skip-link:focus { top: 8px; outline: 2px solid var(--ink-0); outline-offset: 2px; }

    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
      }
    }

    .container { max-width: var(--maxw); margin: 0 auto; padding: 0 var(--gutter); }

    .eyebrow {
      font-family: 'JetBrains Mono', ui-monospace, monospace;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: var(--cyan);
    }

    h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; color: var(--ink-0); margin: 0 0 16px; font-weight: 600; }
    h1 { font-size: clamp(40px, 5vw, 64px); letter-spacing: -0.025em; line-height: 1.05; }
    h2 { font-size: clamp(28px, 3vw, 40px); letter-spacing: -0.02em; line-height: 1.1; }
    h3 { font-size: clamp(22px, 2vw, 28px); line-height: 1.2; }

    .btn {
      display: inline-block;
      padding: 12px 20px;
      border-radius: var(--r-md);
      font-family: 'Inter', sans-serif;
      font-size: 15px;
      font-weight: 500;
      transition: all 120ms cubic-bezier(.2,.7,.2,1);
      cursor: pointer;
      border: none;
      text-decoration: none;
    }
    .btn-primary { background: var(--grad-duo); color: var(--ink-0); }
    .btn-primary:hover { filter: brightness(1.08); box-shadow: 0 0 24px rgba(23,212,250,.35); text-decoration: none; }
    .btn-ghost { background: transparent; color: var(--ink-0); border: 1px solid rgba(255,255,255,.16); }
    .btn-ghost:hover { background: rgba(255,255,255,.06); border-color: rgba(255,255,255,.32); text-decoration: none; }

    nav.top {
      position: sticky; top: 0; z-index: 50;
      background: rgba(15,31,49,.7);
      backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
      border-bottom: 1px solid rgba(255,255,255,.06);
    }
    nav.top .row { display: flex; align-items: center; justify-content: space-between; height: 56px; }
    nav.top .brand-row { display: flex; align-items: center; gap: 12px; min-width: 0; }
    nav.top .brand { display: flex; align-items: center; gap: 8px; color: var(--ink-200); font-family: 'Space Grotesk', sans-serif; font-weight: 600; font-size: 16px; }
    nav.top .brand:hover { text-decoration: none; color: var(--ink-0); }
    nav.top .brand img { height: 26px; width: auto; }
    nav.top .brand-sep { color: var(--ink-400); font-size: 18px; }
    nav.top .brand-current { display: flex; align-items: center; gap: 8px; color: var(--ink-0); font-family: 'Space Grotesk', sans-serif; font-weight: 600; font-size: 16px; }
    nav.top .vibe-mark { width: 28px; height: 28px; border-radius: var(--r-sm); background: rgba(23,212,250,.12); display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0; }
    nav.top .vibe-mark img { width: 20px; height: 20px; display: block; }
    @media (max-width: 520px) {
      nav.top .brand span { display: none; }
      nav.top .brand-sep { display: none; }
    }

    footer {
      margin-top: 96px; padding: 32px 0 48px;
      border-top: 1px solid rgba(255,255,255,.06);
      color: var(--ink-300); font-size: 14px;
    }
    footer .row { display: flex; justify-content: space-between; gap: 24px; flex-wrap: wrap; }
    footer .tagline { font-family: 'Space Grotesk', sans-serif; color: var(--ink-200); }
    footer .links { display: flex; gap: 20px; }

    /* Hero */
    section.hero { position: relative; padding: 80px 0 96px; overflow: hidden; }
    section.hero::before {
      content: ''; position: absolute; inset: 0;
      background:
        radial-gradient(60% 50% at 30% 20%, rgba(23,212,250,.18) 0%, transparent 60%),
        radial-gradient(40% 40% at 80% 60%, rgba(242,47,137,.14) 0%, transparent 60%);
      pointer-events: none; z-index: 0;
    }
    section.hero .container { position: relative; z-index: 1; }
    .hero-grid { display: grid; grid-template-columns: 1.1fr 1fr; gap: 48px; align-items: center; }
    .hero-grid.solo { grid-template-columns: 1fr; max-width: 760px; }
    .hero-left .eyebrow { margin-bottom: 16px; display: inline-block; }
    .hero-subhead { color: var(--ink-200); font-size: clamp(17px, 1.4vw, 19px); max-width: 560px; margin: 0 0 28px; }
    .hero-ctas { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 28px; }
    .hero-meta { display: flex; gap: 16px; flex-wrap: wrap; color: var(--ink-300); font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 13px; }
    .hero-meta span { color: var(--ink-200); }
    .hero-validated { margin-top: 14px; max-width: 560px; font-size: 13px; line-height: 1.5; color: var(--ink-300); }
    .hero-validated .vtag { font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em; color: var(--success); margin-right: 10px; }
    .hero-caps { margin-top: 10px; font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 13px; color: var(--ink-200); }
    .hero-caps .captag { font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em; color: var(--cyan); margin-right: 10px; }
    .hero-mark { display: flex; align-items: center; justify-content: center; position: relative; }
    .hero-mark::before { content: ''; position: absolute; width: 72%; height: 72%; border-radius: 50%; background: radial-gradient(circle, rgba(23,212,250,.22) 0%, rgba(242,47,137,.12) 45%, transparent 72%); filter: blur(28px); z-index: 0; }
    .hero-mark img { position: relative; z-index: 1; width: min(340px, 78%); height: auto; }
    @media (max-width: 900px) { .hero-mark { display: none; } }

    .term { background: var(--navy-mid); border-radius: var(--r-lg); box-shadow: inset 0 0 0 1px rgba(255,255,255,.06), 0 8px 32px rgba(0,0,0,.35); overflow: hidden; }
    .term-bar { display: flex; align-items: center; gap: 8px; padding: 10px 14px; background: rgba(0,0,0,.18); border-bottom: 1px solid rgba(255,255,255,.04); }
    .term-dot { width: 10px; height: 10px; border-radius: 50%; }
    .term-dot.r { background: #ff5f57; }
    .term-dot.y { background: #febc2e; }
    .term-dot.g { background: #28c840; }
    .term-label { margin-left: 12px; font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 12px; color: var(--ink-300); }
    .term-body { padding: 20px; font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 13px; line-height: 1.65; color: var(--ink-200); max-height: 460px; overflow: hidden; }
    .term-body .prompt { color: var(--cyan); }
    .term-body .cmd { color: var(--ink-0); }
    .term-body .agent { color: var(--cyan); }
    .term-body .path { color: var(--cyan-pale); }
    .term-body .key { color: var(--magenta-pale); }
    .term-body .ok { color: var(--success); }
    .term-body .muted { color: var(--ink-300); }
    .term-cursor { display: inline-block; width: 8px; height: 14px; background: var(--cyan); vertical-align: -2px; animation: blink 1.05s steps(1) infinite; }
    @keyframes blink { 50% { opacity: 0; } }

    /* Sections */
    section.work, section.brain, section.install, section.family { padding: 80px 0; }
    .section-head { margin-bottom: 40px; }
    .section-head .eyebrow { display: inline-block; margin-bottom: 12px; }
    .section-head .lead { color: var(--ink-200); font-size: 17px; max-width: 640px; margin: 8px 0 0; }

    .card { background: var(--navy-mid); border: 1px solid rgba(255,255,255,.08); border-radius: var(--r-lg); padding: 24px; transition: border-color 120ms cubic-bezier(.2,.7,.2,1); }
    .card:hover { border-color: rgba(23,212,250,.45); }
    .card .cmd { font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--cyan); display: inline-block; margin-bottom: 10px; word-break: break-word; }
    .card h3 { margin: 0 0 8px; font-size: 22px; }
    .card .desc { color: var(--ink-200); margin: 0 0 12px; }
    .card .reach { color: var(--ink-300); font-size: 14px; border-top: 1px solid rgba(255,255,255,.06); padding-top: 12px; margin-top: 12px; }
    .card .reach em { color: var(--magenta-pale); font-style: normal; }

    .cards-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
    .cards-grid.cols-3 { grid-template-columns: repeat(3, 1fr); }

    .sub-head { margin-top: 56px; margin-bottom: 24px; display: flex; align-items: baseline; justify-content: space-between; gap: 16px; }
    .sub-head h3 { margin: 0; }
    .sub-head .hint { color: var(--ink-300); font-size: 14px; }
    .mini-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
    .mini { background: var(--navy-mid); border: 1px solid rgba(255,255,255,.08); border-radius: var(--r-md); padding: 16px 18px; transition: border-color 120ms cubic-bezier(.2,.7,.2,1); }
    .mini:hover { border-color: rgba(23,212,250,.45); }
    .mini .name { font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 13px; color: var(--cyan); display: block; margin-bottom: 4px; }
    .mini .desc { color: var(--ink-200); font-size: 14px; margin: 0; }

    section.brain { background: linear-gradient(180deg, transparent 0%, rgba(23,212,250,.03) 100%); }
    .brain-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 48px; align-items: start; }
    .brain-grid p { color: var(--ink-200); margin: 0 0 16px; max-width: 540px; }
    .brain-grid strong { color: var(--ink-0); font-weight: 500; }
    .callout { margin-top: 32px; padding: 20px 24px; border-top: 1px solid rgba(23,212,250,.35); border-bottom: 1px solid rgba(23,212,250,.35); background: rgba(23,212,250,.04); font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 14px; color: var(--ink-100); max-width: 540px; }

    .install-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 24px; }
    .install-grid.solo { grid-template-columns: 1fr; max-width: 620px; }
    .install-card { padding: 24px; }
    .install-card h3 { display: flex; align-items: center; gap: 10px; margin: 0 0 6px; }
    .install-card .badge { font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; padding: 3px 8px; border-radius: var(--r-sm); background: rgba(23,212,250,.12); color: var(--cyan); }
    .install-card .badge.magenta { background: rgba(242,47,137,.12); color: var(--magenta-pale); }
    .install-card .blurb { color: var(--ink-200); margin: 0 0 16px; font-size: 14px; }
    .codeblock { position: relative; background: var(--navy-deep); border: 1px solid rgba(23,212,250,.25); border-radius: var(--r-md); padding: 14px 44px 14px 16px; font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 13px; color: var(--ink-100); line-height: 1.7; overflow-x: auto; }
    .codeblock .copybtn { position: absolute; top: 8px; right: 8px; background: transparent; border: 1px solid rgba(255,255,255,.12); border-radius: var(--r-sm); padding: 4px 8px; cursor: pointer; color: var(--ink-300); font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 11px; transition: all 120ms cubic-bezier(.2,.7,.2,1); }
    .codeblock .copybtn:hover { color: var(--cyan); border-color: rgba(23,212,250,.45); }
    .codeblock .copybtn.ok { color: var(--success); border-color: rgba(43,217,154,.45); }
    .install-note { margin-top: 20px; color: var(--ink-300); font-size: 14px; }

    .family-lead { color: var(--ink-200); margin: 0 0 32px; max-width: 640px; }
    .family-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
    .family-card { background: var(--navy-mid); border: 1px solid rgba(255,255,255,.08); border-radius: var(--r-md); padding: 18px 20px; display: flex; gap: 14px; align-items: flex-start; color: var(--ink-100); transition: all 120ms cubic-bezier(.2,.7,.2,1); }
    .family-card:hover { border-color: rgba(23,212,250,.45); text-decoration: none; }
    .family-card.here { border-color: rgba(23,212,250,.55); box-shadow: 0 0 24px rgba(23,212,250,.18); }
    .family-card .fc-mark { width: 48px; height: 48px; border-radius: var(--r-md); background: rgba(23,212,250,.10); display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0; }
    .family-card .fc-mark img { width: 36px; height: 36px; display: block; }
    .family-card .name { font-family: 'Space Grotesk', sans-serif; font-size: 17px; font-weight: 600; color: var(--ink-0); margin-bottom: 2px; }
    .family-card .role { color: var(--ink-300); font-size: 14px; }
    .family-card .fc-caps { font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 11px; color: var(--ink-400); margin-top: 6px; }
    .family-card .you { font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em; color: var(--cyan); margin-top: 6px; }

    @media (max-width: 900px) {
      .hero-grid { grid-template-columns: 1fr; gap: 32px; }
      .mini-grid { grid-template-columns: repeat(2, 1fr); }
      .cards-grid.cols-3 { grid-template-columns: repeat(2, 1fr); }
      .brain-grid { grid-template-columns: 1fr; gap: 24px; }
    }
    @media (max-width: 720px) {
      footer .row { flex-direction: column; gap: 12px; }
      .cards-grid, .cards-grid.cols-3 { grid-template-columns: 1fr; }
      section.work, section.brain, section.install, section.family { padding: 56px 0; }
      .card { padding: 20px; }
      .install-grid { grid-template-columns: 1fr; }
      .family-grid { grid-template-columns: 1fr; }
    }
    @media (max-width: 540px) {
      .mini-grid { grid-template-columns: 1fr; }
    }
"""

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


def render_index(data):
    """The /plugins/ family index."""
    family = data["family"]
    cards = []
    for f in family:
        caps = caps_text(f["id"])
        caps_html = f'\n              <div class="fc-caps">{caps}</div>' if caps else ""
        cards.append(f"""          <a href="{e(f['href'])}" class="family-card">
            <span class="fc-mark" aria-hidden="true"><img src="{icon_path(f['id'])}" alt="" /></span>
            <div>
              <div class="name">{e(f['name'])}</div>
              <div class="role">{e(f['role'])}</div>{caps_html}
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
    return head + nav + "\n  <main id=\"main\">\n" + hero + grid + "\n  </main>\n" + render_footer() + "\n</body>\n</html>\n"


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
