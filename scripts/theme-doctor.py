#!/usr/bin/env python3
"""theme-doctor.py — the contract gate for 626labs.dev theme rotation.

Checks all four archetypes (scripts/archetypes.py: home, product, reading,
utility) a theme has to dress. First, completeness: tokens.css/theme.json,
all four archetypes/*.html, AND archetypes/product.css + archetypes/
product-tokens.css + archetypes/utility.css + archetypes/reading.css (the
five CSS artifacts real, unguarded consumers read at render time — see
REQUIRED_ARCHETYPE_CSS and PRODUCT_TOKENS_CSS), AND that every member of
REQUIRED_TOKEN_CSS actually
DEFINES every custom property in archetypes.REQUIRED_TOKENS —
themes.html/press.html/privacy.html/thesis.html/workflow.html/
conundrum.html/rororo-plugins.html read these via var(--x) but carry no
theme-owned fallback of their own (see
check_required_tokens and REQUIRED_TOKENS's docstring). Every member of
TOKEN_ONLY_CSS additionally has to contain NOTHING BUT token definitions
(check_token_css_declares_only_tokens) — a token file that grows an
element rule reaches two hand-authored pages that link it for their
palette alone. Then every var(--x) a theme spends has to resolve inside
the RESOLUTION GROUP that reads it — the set of stylesheets one real
consumer loads together, derived per run from render-hub.py and
render-plugin-pages.py rather than listed here (see resolution_groups and
check_theme_reads_only_what_it_defines). Then,
per archetype: page chrome (skip-link/nav/footer/analytics, per
ARCHETYPE_CHROME's real per-archetype profile), every internal href resolves
to a real file, the archetype's required vocabulary class set
(archetypes.VOCABULARY) is present as either an HTML class or a CSS
selector, and any WCAG contrast pairs the theme declares in theme.json meet
AA (>= 4.5) wherever that pair's custom properties actually resolve in that
archetype's own CSS. `home` additionally gets the twelve-SITE_JSON-zone
check — the only archetype with a full end-to-end renderer today. See
`_archetype_source`'s docstring for exactly which artifact stands in for
each archetype's "dress" and why — `reading` is the one archetype where
vocabulary is split: its 3 shared `ed-*` leaves are credited from
about.html's markup (theme-agnostic on purpose, styled by the shared
Design/editorial.css), but its 7 `lnt-*` structural classes are checked
CSS-selector-only against the THEME's own archetypes/reading.css (A7's
easter-egg toggle target) — see `_check_archetype`'s docstring for why that
split exists and what it closes.

This is the ONLY thing standing between a theme and unattended monthly
rotation (the scheduled workflow promotes queue[0] to active with no human
in the loop) — it has to fail honestly. A check that always passes is worse
than no check: it turns a real gate into a rubber stamp.

Usage:
  python scripts/theme-doctor.py <slug> [--browser] [--require-browser]

Exit 0 and "PASS <slug>" when every check clears. Exit 1 and a bulleted
failure list under "FAIL <slug>" otherwise.

--browser additionally drives Playwright (if the `playwright` package is
importable — it is never a hard dependency of this repo) to assert no
horizontal scroll at 1440/768/390px and zero browser console errors, and on
the two pages that own none of their own chrome (DRESS_OUTCOME_PAGES) to
assert the theme's dress actually ARRIVED — see check_page_renders_dressed,
which grades computed outcome and never a list of rules the theme must
carry. Without
it, or without playwright installed, those two checks are skipped with a
one-line note and never fail the gate on their own — that's the local
convenience path, for a machine that hasn't run `playwright install`.

--require-browser (implies --browser) is the opposite contract: the browser
path becoming unavailable — playwright not importable, the local preview
server failing to bind, or chromium failing to launch — is itself a gate
FAILURE, not a skip. Use this anywhere the gate result gets trusted
unattended (the scheduled rotation workflow passes it) — a silent skip there
means the horizontal-scroll and console-error checks never actually run and
the gate rubber-stamps every rotation forever.
"""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT = SCRIPTS_DIR.parent
if str(SCRIPTS_DIR) not in sys.path:
    # Loaded two ways: `python scripts/theme-doctor.py` (Python already puts
    # the script's own dir on sys.path[0]) and importlib.util loading by
    # explicit file path from tests/ (it does NOT). Insert explicitly so
    # `import theme_registry` below works either way.
    sys.path.insert(0, str(SCRIPTS_DIR))
import archetypes      # noqa: E402 — sibling module in scripts/ — VOCABULARY, ARCHETYPES
import browser_origin  # noqa: E402 — sibling module in scripts/ — third-party isolation
import theme_registry  # noqa: E402 — sibling module in scripts/

ZONES = ("hero", "hero-chips", "products", "lab-pool", "thinking", "founding",
         "stories", "lab-runs", "play", "about", "support", "contact")

# CSS artifacts a theme's real consumers read with no existence guard, beyond
# the tokens.css/theme.json REQUIRED_FILES and archetypes/*.html
# REQUIRED_ARCHETYPES theme_registry already enforces (A5's review flagged
# this as a carried requirement, not a nice-to-have): render-plugin-pages.py
# does `theme_dir(active)/archetypes/product.css` and reads it unguarded —
# a theme rotating in without it raises an uncaught FileNotFoundError and
# crashes all 15 plugin pages (it reads archetypes/product-tokens.css the
# same unguarded way — see PRODUCT_TOKENS_CSS below, which is where
# conundrum.html and rororo-plugins.html get their vocabulary).
# press.html/privacy.html resolve
# archetypes/utility.css the same unguarded way (render-hub.py's
# THEME_CSS_HREFS zone). `reading` joins them as of A7: about.html's
# client-side easter-egg toggle points a <link> at
# `/themes/<slug>/archetypes/reading.css` for every theme it offers, and
# this module's own reading-archetype gate reads the same file as the CSS
# half of the vocabulary check (see `_archetype_source`/`_check_archetype`)
# — a theme rotating in without it would break both. thesis.html and
# workflow.html then made it load-bearing a third way: they link it
# directly for their base token vocabulary, so a theme without it leaves
# both pages with unresolved var()s and no fallback. `home` needs no entry,
# since its CSS is the inline <style> block in archetypes/home.html itself,
# already covered by REQUIRED_ARCHETYPES.
REQUIRED_ARCHETYPE_CSS = {"product": "product.css", "utility": "utility.css", "reading": "reading.css"}

# The token half of the product archetype, split out of product.css so the
# four bespoke product pages — conundrum.html, rororo-plugins.html,
# rororo.html, mod-launcher-games.html — can link the VOCABULARY without
# inheriting the DRESS (bare `body`/`a:hover`/`section.hero`/`.card`/`.btn`
# rules written for render-plugin-pages.py's templates, not for their
# hand-authored markup). Required as its own file, and not folded into
# REQUIRED_ARCHETYPE_CSS, because that dict is one-CSS-per-archetype and is
# also what _archetype_source reads as "the archetype's dress."
#
# It has to be REQUIRED rather than optional-with-a-fallback: all four
# pages resolve it through an unguarded <link>, and render-plugin-pages.py
# reads it with no existence guard, so a theme rotating in without it 404s
# four live pages and raises FileNotFoundError across the other 15 —
# unattended, on the 1st.
PRODUCT_TOKENS_CSS = "product-tokens.css"

# The same split, applied to the reading archetype BEFORE it cost anything.
# archetypes/reading.css is the Long Now Terminal dress about.html's
# easter-egg theme picker wears; thesis.html and workflow.html only ever
# wanted its palette. Its two unscoped element rules (`* { box-sizing }`,
# `body { margin: 0 }`) are provable no-ops on both pages — each declares
# them itself, identically, after the <link> — but "no-op today" is not a
# property a gate can rely on, and three things invited a future reading.css
# to grow a real one: the build instructions say to mirror this theme,
# check_vocabulary REQUIRES the seven lnt-* classes to appear as selectors
# in that file, and nothing covered element rules at all.
READING_TOKENS_CSS = "reading-tokens.css"

# Every stylesheet some page reads BASE VOCABULARY out of, repo-relative to
# the theme dir. All four must define archetypes.REQUIRED_TOKENS in full.
REQUIRED_TOKEN_CSS = (
    "tokens.css",                        # themes.html, index.html
    # conundrum.html, rororo-plugins.html, rororo.html,
    # mod-launcher-games.html, +15 inlined
    f"archetypes/{PRODUCT_TOKENS_CSS}",
    f"archetypes/{READING_TOKENS_CSS}",  # thesis.html, workflow.html
    "archetypes/utility.css",            # press.html, privacy.html
)

# Of those, the ones that must contain NOTHING BUT token definitions: the
# files a hand-authored page links for its palette and nothing else.
#
# archetypes/utility.css is deliberately absent, and as of 2026-08-04 that is
# a SETTLED position rather than a description of open work. press.html and
# privacy.html wear a foreign element dress with no page-side statement of
# their own — `a { color: inherit }`, `body`, `h1..h4`, `nav.nav`,
# `header.page-hero`, `footer` — and Este's ruling is that they KEEP wearing
# it, so a new month actually restyles them. Splitting utility.css would close
# the exposure by removing the dependency, and would also make them the two
# pages a September theme cannot reach.
#
# So the exposure closes by VERIFICATION instead: check_page_renders_dressed
# opens both pages under the theme being doctored and asserts the dress
# arrived, on computed outcome rather than on a required-rules manifest.
TOKEN_ONLY_CSS = (
    f"archetypes/{PRODUCT_TOKENS_CSS}",
    f"archetypes/{READING_TOKENS_CSS}",
)

# Real, hand-authored pages --browser opens in addition to the theme's own
# archetype shells. Everything else in the browser check grades a shell the
# theme ships; these grade a page the SITE ships, dressed by the theme
# under test. Each is read from render-hub.py's preview output, so its
# stylesheet <link> points at the theme being doctored rather than the
# active one.
#
# All six hand-authored pages that link a theme stylesheet, because each is
# a page the unattended rotation could otherwise promote a theme onto with
# nothing ever opening it. The reading pair (thesis.html, workflow.html) is
# here for the identical reason as the product four; it was held out for no
# reason beyond the order the conversions landed in, and both are among the
# pages that used to render on a white field under a treatment-less theme. `rororo.html` in particular is the expensive omission: its
# `.install-grid` is `repeat(3, 1fr)` holding `code` blocks at
# `white-space: pre`, so a queued theme shipping a `--font-body` stack with
# wider metrics overflows it at 390px — exactly what the horizontal-scroll
# check is for.
#
# An earlier cut held the two live-data pages out on the grounds that
# `mod-launcher-games.html` fetches from raw.githubusercontent.com and would
# make this gate depend on a third-party host. The premise was true; the
# conclusion was not. Every page here already loads
# `//gc.zgo.at/count.js`, so the dependency already existed and merely
# changed count. It is closed properly instead, in `_check_viewport`: the
# browser context aborts off-origin requests and drops console errors
# attributed to off-origin URLs. See that function's docstring for what that
# does and does not still cover.
# press.html and privacy.html join on a STRONGER argument than the other six.
# The six link a theme file for its token vocabulary and keep their own dress.
# These two keep no chrome of their own at all: measured against the live DOM,
# 49 of archetypes/utility.css's 50 selectors reach press.html and 48 reach
# privacy.html, and the two pages' own <style> blocks (52 and 21 selectors)
# redeclare NOT ONE of them — zero overlap. Their entire nav, hero, type,
# link and footer treatment arrives from the theme. So they are the two pages
# a second theme's utility.css can silently change or break, and they were the
# two pages nothing ever opened. See check_page_renders_dressed for the
# outcome gate that rides along with opening them.
BROWSER_CHECK_LIVE_PAGES = (
    "conundrum.html", "rororo-plugins.html", "rororo.html",
    "mod-launcher-games.html", "thesis.html", "workflow.html",
    "press.html", "privacy.html",
)

# The pages `check_page_renders_dressed` additionally grades — the ones that
# borrow their whole chrome from the theme and state nothing of their own
# about it. Exactly the utility archetype's two live pages; every other page
# the browser gate opens owns enough of its own dress that a theme dropping a
# rule degrades it rather than stripping it.
DRESS_OUTCOME_PAGES = ("press.html", "privacy.html")

# A page named here but absent from the tuple above would be handed
# `dress_outcome=False` by _run_browser_checks_all's dict lookup and skipped
# in total silence — the one failure class this module refuses everywhere
# else. Asserted at import so it can never be a runtime surprise on the 1st.
assert set(DRESS_OUTCOME_PAGES) <= set(BROWSER_CHECK_LIVE_PAGES), (
    "every DRESS_OUTCOME_PAGES entry must also be in BROWSER_CHECK_LIVE_PAGES, "
    "or the browser gate never opens it and the dress check silently no-ops"
)

# Real, live chrome varies by archetype today — verified by grep against the
# actual shipped pages (vibe-cartographer/index.html, press.html,
# privacy.html, about.html), not assumed. Loosening a requirement to match
# reality isn't the same as skipping it: nav/footer/links/vocabulary still
# have to hold for every archetype; this table only says which of
# skip-link/analytics are real, universal facts of that archetype's pages
# today, so the gate doesn't invent a failure this task didn't cause and
# isn't scoped to fix. See docs/theme-archetypes.md and the A6 report for
# the evidence trail (`grep -n "skip-link\|<nav\|<footer\|data-goatcounter"`
# against vibe-cartographer/index.html, press.html/privacy.html, about.html).
ARCHETYPE_CHROME = {
    "home":    dict(skip_link=True,  nav=True, footer=True, analytics=True),
    "product": dict(skip_link=True,  nav=True, footer=True, analytics=False),
    "reading": dict(skip_link=False, nav=True, footer=True, analytics=True),
    "utility": dict(skip_link=False, nav=True, footer=True, analytics=True),
}

HREF_RE = re.compile(r'href="([^"]*)"')
STYLE_BLOCK_RE = re.compile(r"<style[^>]*>(.*?)</style>", re.S)
CLASS_ATTR_RE = re.compile(r'class="([^"]*)"')
CSS_CLASS_SELECTOR_RE = re.compile(r"\.([A-Za-z][\w-]*)")

CUSTOM_PROP_RE = re.compile(r"(--[\w-]+)\s*:\s*([^;]+);")
HEX_RE = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
RGB_FUNC_RE = re.compile(
    r"^rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:,\s*[\d.]+\s*)?\)$"
)
VAR_RE = re.compile(r"^var\(\s*(--[\w-]+)\s*(?:,\s*(.+))?\)$")

AA_MIN_RATIO = 4.5


# ─── static checks — (html, css) -> list[str], per T3's contract ──────────
def check_zones(html: str, css: str) -> list[str]:
    """Every zone in ZONES needs both its start and end SITE_JSON marker."""
    errors = []
    for zone in ZONES:
        if f"SITE_JSON:{zone}:start" not in html:
            errors.append(f"zone {zone}: missing SITE_JSON:{zone}:start marker")
        if f"SITE_JSON:{zone}:end" not in html:
            errors.append(f"zone {zone}: missing SITE_JSON:{zone}:end marker")
    return errors


def check_chrome(
    html: str, css: str, *,
    skip_link: bool = True, nav: bool = True, footer: bool = True, analytics: bool = True,
) -> list[str]:
    """Baseline page chrome a theme is never allowed to drop.

    The four elements default to required (unchanged 2-arg behavior for
    every existing caller/test — this is still the `home` archetype's
    contract). The archetype loop in `main()` passes ARCHETYPE_CHROME's
    per-archetype profile instead: `product` and `reading` pages carry no
    GoatCounter script today, and `utility` pages carry no skip-link —
    real, verified facts about the live site, not a relaxed requirement
    invented to make the gate pass."""
    errors = []
    if skip_link and 'class="skip-link"' not in html:
        errors.append('chrome: missing skip-link (class="skip-link")')
    if nav and "<nav" not in html:
        errors.append("chrome: missing <nav>")
    if footer and "<footer" not in html:
        errors.append("chrome: missing <footer>")
    if analytics and "data-goatcounter" not in html:
        errors.append("chrome: missing analytics (data-goatcounter)")
    return errors


def check_internal_links(html: str, css: str) -> list[str]:
    """Every non-external href resolves to a real file under the repo root."""
    errors = []
    seen = set()
    for href in HREF_RE.findall(html):
        target = href.split("#", 1)[0].split("?", 1)[0]
        if (
            href.startswith("http")
            or href.startswith("mailto:")
            or href.startswith("#")
            or target == ""
        ):
            continue
        if href in seen:
            continue
        seen.add(href)
        rel = target.lstrip("/")
        path = ROOT / rel
        ok = (path / "index.html").exists() if path.is_dir() else path.exists()
        if not ok:
            errors.append(f"internal link target missing: {href}")
    return errors


# ─── vocabulary ─────────────────────────────────────────────────────────
def _html_classes(html: str) -> set[str]:
    """Every literal `class="..."` token in `html`, space-split."""
    classes: set[str] = set()
    for value in CLASS_ATTR_RE.findall(html):
        classes.update(value.split())
    return classes


def _css_classes(css: str) -> set[str]:
    """Every `.classname` CSS selector token in `css`. Requires a leading
    letter so a bare decimal (`opacity: .5`, `rgba(0,0,0,.42)`) never reads
    as a class named "5" or "42" — CSS_CLASS_SELECTOR_RE encodes that."""
    return set(CSS_CLASS_SELECTOR_RE.findall(css))


def check_vocabulary(html: str, css: str, archetype: str) -> list[str]:
    """Enforces archetypes.VOCABULARY[archetype]: every required class has
    to appear as a literal HTML class attribute OR as a CSS selector —
    the theme's dress can supply the semantic anchor through markup (a
    section wrapper the theme's own shell owns, e.g. `<section class="hero">`)
    or through styling alone (a class a Python renderer supplies at
    render time — e.g. `product`'s `.card`/`.family-card`/`.section-head`,
    which render-plugin-pages.py stamps onto the DOM and the theme merely
    has to style — see docs/theme-archetypes.md, "product" archetype file).
    A class present only as an unrelated CSS selector never satisfies a
    DIFFERENT required name — no substring matching, no fuzzy match: the
    one rule (docs/theme-archetypes.md) is that a theme never renames the
    semantic anchor, so this check is exact-token-only by design.

    This function itself stays archetype-agnostic — it just unions two
    sets and diffs. `_check_archetype` is where per-archetype judgment
    calls about WHAT to pass as `html`/`css` live; see it for why `reading`
    feeds a synthetic, 3-class `html` string instead of about.html's real
    (theme-invariant) markup.

    Failure strings name both the archetype and the missing class, per the
    brief ("per-archetype failures name the archetype in the message")."""
    required = archetypes.VOCABULARY.get(archetype)
    if required is None:
        return [f"{archetype}: vocabulary: unknown archetype"]
    found = _html_classes(html) | _css_classes(css)
    return [
        f"{archetype}: vocabulary missing required class {cls!r} "
        f"(not found as an HTML class or a CSS selector)"
        for cls in sorted(required)
        if cls not in found
    ]


# ─── required tokens (final review Fix 1) ──────────────────────────────
def check_required_tokens(css: str) -> list[str]:
    """Enforces archetypes.REQUIRED_TOKENS: every base custom property
    themes.html's own <style> and the residual <style> of press.html,
    privacy.html, thesis.html and workflow.html read via var(--x) but never
    define themselves has to actually be DEFINED somewhere in `css` — not
    merely referenced. A theme that renames or drops one passes every other
    gate today (vocabulary only checks class names; chrome/links don't look
    at custom properties at all) and silently ships stale colors
    (themes.html/index.html, which fall back to their own hardcoded
    pre-rotation values) or unresolved var()s (the other four, which have no
    fallback of their own).

    Reuses `_parse_custom_properties` — the same last-declaration-wins
    parse `check_contrast` already trusts to resolve `:root` values — so a
    token counts as "defined" the same way contrast resolution already
    treats it as defined, no new parsing rule to keep in sync."""
    declared = _parse_custom_properties(css)
    return [
        f"missing required custom property {tok!r}"
        for tok in sorted(archetypes.REQUIRED_TOKENS)
        if tok not in declared
    ]


_COMMENT_RE = re.compile(r"/\*.*?\*/", re.S)
_TOKEN_ONLY_BLOCK_RE = re.compile(r"(?P<sel>[^{}]*)\{(?P<body>[^{}]*)\}", re.S)
# Every {…} block, so the at-rule scan can look at what is left.
_BLOCK_RE = re.compile(r"\{[^{}]*\}", re.S)


def check_token_css_declares_only_tokens(css: str) -> list[str]:
    """Enforces that a token-vocabulary stylesheet contains custom-property
    definitions and NOTHING that paints.

    Why this is a gate and not a style note. conundrum.html and
    rororo-plugins.html are hand-authored: they keep their own layout and
    link a theme file only for its palette. Before this split they linked
    the product DRESS, and it shipped a regression no other gate could
    see — `a:hover { text-decoration: underline; text-decoration-color:
    var(--magenta) }` at specificity (0,1,1) outranks `.merch-card`,
    `.shop-cta`, `.repo-cta` and `footer a`, so 14 links on the shop page
    and 18 on the marketplace page grew a magenta hover underline that had
    never been there. A pixel harness samples the resting state; hover is
    out of frame by construction, so the bug was invisible to every
    automated check the repo has.

    The fix was structural (the two pages link tokens, not dress) and this
    keeps it structural. Without it, a future theme's product-tokens.css
    can quietly grow `p { margin: 0 0 24px }` and land it on both pages
    unattended on the 1st. Missing NAMES are caught by
    check_required_tokens; extra RULES are caught here. Neither catches the
    other.

    Rules:
    - every block's selector must be exactly `:root` (after comment strip)
    - every declaration inside must be a custom property (`--x: …`)
    - no at-rules that can carry style (`@media`, `@supports`, `@import`)

    utility.css and reading.css are deliberately NOT held to this, for
    two DIFFERENT reasons, and the difference matters.

    utility.css was extracted FROM press.html, so its element rules are
    those pages' own dress coming home — they have no page-side dress to
    fall back on. That exemption is now a settled position (2026-08-04):
    those two pages keep wearing the theme's dress so the rotation can
    restyle them, and what a token-only split would have bought is bought
    instead by check_page_renders_dressed, which grades the RESULT in the
    browser rather than the rules in the file.

    reading.css is exempt for the opposite reason: it is ABOUT.HTML's dress
    now. The part that was extracted from thesis.html/workflow.html lives in
    archetypes/reading-tokens.css, which IS held to this gate. Same for
    product.css and product-tokens.css. See TOKEN_ONLY_CSS.
    """
    errors: list[str] = []
    stripped = _COMMENT_RE.sub("", css)

    # Scan for at-rules OUTSIDE any {…} block. Scanning the whole text
    # matches inside token VALUES too, so a legitimate
    # `--contact: url("mailto:a@b")` failed the gate with a baffling "found
    # at-rule '@b'" — a false positive that blocks a valid theme, which is
    # worse than the hole it was guarding.
    outside = _BLOCK_RE.sub(" ", stripped)
    for at_rule in re.findall(r"@[\w-]+", outside):
        if at_rule.lower() not in ("@charset",):
            errors.append(
                f"token stylesheet must declare tokens only, found at-rule "
                f"{at_rule!r} — put it in the archetype's dress instead"
            )

    for m in _TOKEN_ONLY_BLOCK_RE.finditer(stripped):
        selector = " ".join(m.group("sel").split())
        if selector != ":root":
            errors.append(
                f"token stylesheet must declare tokens only, found selector "
                f"{selector!r} — put it in the archetype's dress instead"
            )
            continue
        for decl in m.group("body").split(";"):
            prop = decl.split(":", 1)[0].strip()
            if prop and not prop.startswith("--"):
                errors.append(
                    f"token stylesheet must declare tokens only, found "
                    f"non-token declaration {prop!r} in :root"
                )
    return errors


# ─── contrast ───────────────────────────────────────────────────────────
def _parse_custom_properties(css: str) -> dict[str, str]:
    """Last declaration wins — approximates the cascade for :root vars."""
    props: dict[str, str] = {}
    for name, value in CUSTOM_PROP_RE.findall(css):
        props[name.strip()] = value.strip()
    return props


def _hex_to_rgb(value: str) -> tuple[int, int, int] | None:
    m = HEX_RE.match(value)
    if not m:
        return None
    h = m.group(1)
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _rgb_func_to_rgb(value: str) -> tuple[int, int, int] | None:
    m = RGB_FUNC_RE.match(value)
    if not m:
        return None
    # Alpha is ignored: every alpha use in this codebase's tokens is a
    # translucent panel over a same-or-near color field (e.g. rgba(0,0,0,.72)
    # over rgb(0,0,0)) where compositing wouldn't move the channel values
    # enough to change an AA verdict. Treating rgb(a) uniformly keeps the
    # resolver simple and honest about what it does NOT model (true alpha
    # compositing against an arbitrary backdrop).
    return tuple(int(round(float(g))) for g in m.groups())  # type: ignore[return-value]


def _resolve_value(value: str, props: dict[str, str], seen: set[str]) -> tuple[int, int, int] | None:
    value = value.strip()
    m = VAR_RE.match(value)
    if m:
        ref, fallback = m.group(1), m.group(2)
        resolved = _resolve_color(ref, props, seen)
        if resolved is not None:
            return resolved
        if fallback:
            return _resolve_value(fallback, props, seen)
        return None
    return _hex_to_rgb(value) or _rgb_func_to_rgb(value)


def _resolve_color(
    name: str, props: dict[str, str], seen: set[str] | None = None
) -> tuple[int, int, int] | None:
    seen = seen if seen is not None else set()
    if name in seen or name not in props:
        return None
    seen.add(name)
    return _resolve_value(props[name], props, seen)


def _srgb_to_linear(channel: int) -> float:
    c = channel / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    r, g, b = (_srgb_to_linear(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast_ratio(rgb_a: tuple[int, int, int], rgb_b: tuple[int, int, int]) -> float:
    l1, l2 = _relative_luminance(rgb_a), _relative_luminance(rgb_b)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def evaluate_contrast_pairs(
    css: str, pairs: list[list[str]]
) -> list[tuple[str, str, float | None]]:
    """Per declared pair: (fg name, bg name, ratio or None if unresolvable)."""
    props = _parse_custom_properties(css)
    results = []
    for pair in pairs:
        fg_name, bg_name = pair[0], pair[1]
        fg = _resolve_color(fg_name, props)
        bg = _resolve_color(bg_name, props)
        ratio = _contrast_ratio(fg, bg) if fg is not None and bg is not None else None
        results.append((fg_name, bg_name, ratio))
    return results


def _applicable_contrast_pairs(css: str, pairs: list[list[str]]) -> list[list[str]]:
    """Pairs where BOTH custom properties are actually declared in `css`.

    theme.json's contrastPairs is one flat list per theme, written against
    whatever token vocabulary its author had in mind — today that's home's
    shared `--fg-*`/`--pb-*` names. `product`'s CSS uses a wholly separate
    `--ink-*` palette that was never retrofit onto those shared names (a
    later-task migration, not an A6 gap to invent a fix for — see
    docs/theme-archetypes.md's "product" archetype section), and `reading`'s
    CSS (as of A7, the theme's own `archetypes/reading.css` — see
    `_archetype_source`) uses its own `--at-lnt-*`/`--ed-*` tokens. A pair
    naming custom properties an archetype's own CSS never declares isn't a
    real per-archetype finding — it's a token-vocabulary mismatch outside
    this check's scope, so it's filtered out here rather than reported as
    "unresolved" (which check_contrast would otherwise flag as a failure)."""
    declared = _parse_custom_properties(css)
    return [pair for pair in pairs if pair[0] in declared and pair[1] in declared]


# ─── resolution groups ────────────────────────────────────────────────
#
# A custom property resolves against the stylesheets ONE DOCUMENT has
# loaded, never against "every file in the theme directory." Grading a
# theme as a single pool is therefore wrong in exactly the direction that
# matters, and it shipped that way: phosphor-blueprint defines ten --pb-*
# names across the theme, archetypes/product.css reads nine of them, and
# tokens.css alone defines eight of that nine — so a definition in
# tokens.css satisfied reads in archetypes/utility.css, the one file
# press.html and privacy.html link, with tokens.css nowhere in their
# <head>. Delete utility.css's own --pb-* block (the plausible edit when
# retokenizing a copied theme, since those names look redundant next to
# tokens.css) and both pages render on rgba(0,0,0,0) with every gate, this
# one included, green.
#
# So the unit of grading is a RESOLUTION GROUP: the set of stylesheets one
# real consumer loads TOGETHER. Seven ship today, and none of them is the
# whole theme:
#
#   index.html                          {tokens.css, archetypes/home.html}
#                                       + widget-bacon-trail/widget.css
#   press.html, privacy.html            {archetypes/utility.css}
#   themes.html                         {tokens.css}
#   thesis.html, workflow.html          {archetypes/reading-tokens.css}
#   conundrum.html + 3 product pages    {archetypes/product-tokens.css}
#   plugins/*/index.html (15 generated) {archetypes/product.css,
#                                        archetypes/product-tokens.css}
#   about.html                          {archetypes/reading.css}
#                                       + Design/editorial.css
#
# That table is DOCUMENTATION. `resolution_groups` below derives the real
# thing every run, from the code that actually serves those pages — a tuple
# here would be the same class of bug this scoping exists to fix.
#
# index.html's group is the one derived from the theme UNDER TEST rather
# than from the site: its <link> tags live in archetypes/home.html, a
# THEME-AUTHORED file that changes with every new theme. It was missing
# from the first cut of this scoping, on the reasoning that index.html
# loads tokens.css plus a widget stylesheet and is therefore a strictly
# LOOSER group than themes.html's {tokens.css}. True of today's theme, and
# irrelevant: a theme is free to link an archetypes/home.css, or to reuse
# archetypes/reading.css on a homepage strip. Both were built and both
# PASSED the gate at exit 0 — the first because no group and no floor named
# home.css, the second because reading.css is graded by about.html's group,
# where Design/editorial.css resolves the five --ed-* names index.html
# links nothing for. That is the utility-dress bug relocated to the
# highest-traffic page on the site.
#
# archetypes/home.html enters its own group as a READER as well as a
# definer: home's dress is the inline <style> block in that shell (there is
# no archetypes/home.css today), so a var() spent there is exactly as
# unresolved as one spent in a linked file. main() extracts the <style>
# blocks for any group member ending in .html — see _group_stylesheet_text.

# `<link rel=stylesheet href=...>`, attribute order and quote style
# independent, because about.html and every theme's home shell are
# hand-authored; only render-hub.py's emitted links are guaranteed to look
# alike.
_LINK_TAG_RE = re.compile(r"<link\b[^>]*>", re.I)
_REL_STYLESHEET_RE = re.compile(r"\brel\s*=\s*[\"']?stylesheet\b", re.I)
_HREF_RE = re.compile(r"\bhref\s*=\s*[\"']([^\"']+)[\"']", re.I)
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
# A stylesheet the browser loads but does not APPLY to the screen defines
# nothing for this gate's purposes. Both exclusions are in the narrowing
# direction on purpose — crediting a print-only or disabled sheet as a
# definer is what licenses an unresolved read.
_DISABLED_RE = re.compile(r"\bdisabled\b", re.I)
_MEDIA_RE = re.compile(r"\bmedia\s*=\s*[\"']([^\"']*)[\"']", re.I)
# /themes/<slug>/<rest> — the shape render-hub.py's theme-css zone and
# about.html's dress picker both emit. The slug is discarded on purpose:
# a group is a set of stylesheet NAMES, graded against whichever theme is
# under test, never against whichever theme happens to be live.
_THEME_HREF_RE = re.compile(r"^/themes/[^/]+/(.+)$")

# The floor under `resolution_groups`: every stylesheet a theme is REQUIRED
# to ship has to end up inside some group, or the scoping above quietly
# grades less than the theme-wide pool did. Hand-written, and safe to be —
# it is a floor, not a pool, so a stale entry here can only ever produce an
# extra error, never license an unresolved read. Built from the same
# constants the completeness check uses so the two cannot disagree.
GRADED_THEME_CSS = (
    "tokens.css",
    *(f"archetypes/{f}" for f in REQUIRED_ARCHETYPE_CSS.values()),
    f"archetypes/{PRODUCT_TOKENS_CSS}",
    f"archetypes/{READING_TOKENS_CSS}",
)


def _load_sibling_script(filename: str, module_name: str):
    """Import a hyphenated sibling in scripts/ by path.

    `render-hub.py` and `render-plugin-pages.py` are not importable by name.
    Loaded lazily, inside `resolution_groups`, so importing THIS module (as
    tests/ do, by explicit path) never drags in render-hub.py's `markdown`
    dependency or render-plugin-pages.py's active-theme file reads.
    """
    spec = importlib.util.spec_from_file_location(module_name, SCRIPTS_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _page_stylesheets(page: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """(theme-relative, repo-relative) stylesheets `page` links and APPLIES.

    Two halves because a page's <head> mixes them. THEME links
    (/themes/<slug>/x.css) come back stripped of their slug — a group is a
    set of stylesheet NAMES, graded against whichever theme is under test,
    never against whichever theme happens to be live. SITE links are
    everything else inside the repo: about.html links /Design/editorial.css,
    and archetypes/reading.css legitimately spends five names that file
    defines (--font-serif, --ed-t-body, --ed-t-pull, --ed-lh-body,
    --ed-lh-pull). That fact used to live in a theme-WIDE tuple, which meant
    archetypes/product.css could read an --ed-* name and pass despite no
    product consumer linking editorial.css at all. Read off each page
    instead, so the definition travels with the document that loads it.

    Three exclusions, all of them in the NARROWING direction, because
    crediting a stylesheet the browser never applies is what licenses an
    unresolved read:

      - anything inside an HTML comment (commented-out <link> tags are how
        a page stops loading a stylesheet without deleting the line)
      - `disabled`, and any `media` that names neither `screen` nor `all`
      - off-origin, including protocol-relative `//host/x.css` — the form
        every analytics and CDN link in this repo uses, and the one an
        origin test reading `://` alone waves straight through
    """
    if not page.exists():
        return (), ()
    html = _HTML_COMMENT_RE.sub("", page.read_text(encoding="utf-8"))
    theme: list[str] = []
    site: list[str] = []
    for tag in _LINK_TAG_RE.findall(html):
        if not _REL_STYLESHEET_RE.search(tag) or _DISABLED_RE.search(tag):
            continue
        media = _MEDIA_RE.search(tag)
        if media and not re.search(r"\b(screen|all)\b", media.group(1), re.I):
            continue
        m = _HREF_RE.search(tag)
        if not m:
            continue
        href = m.group(1)
        theme_rel = _THEME_HREF_RE.match(href)
        if theme_rel:
            theme.append(theme_rel.group(1))
        elif "://" not in href and not href.startswith("//"):
            site.append(href.lstrip("/"))
    return tuple(dict.fromkeys(theme)), tuple(dict.fromkeys(site))


def _page_site_stylesheets(page: Path) -> tuple[str, ...]:
    """The site half of `_page_stylesheets` — the common case."""
    return _page_stylesheets(page)[1]


def _inlined_theme_css(style: str, source_dir: Path) -> tuple[str, ...]:
    """Which of `source_dir`'s stylesheets appear VERBATIM inside the <style>
    block render-plugin-pages.py inlines into its 15 generated pages.

    Read out of the concatenation rather than named here. Today it is
    archetypes/product.css + archetypes/product-tokens.css; a renderer that
    starts inlining a third file brings that file into this group the same
    commit, which a list in this module would not.

    `source_dir` is the theme render-plugin-pages.py itself resolved through
    `theme_registry.theme_dir` — the same call, so the two always look at the
    same directory even when a test monkeypatches it to a stub. That may be a
    DIFFERENT theme from the one under test (the doctor grades queued themes
    while the renderer reads the active one); only relative NAMES are
    borrowed, never content.
    """
    found: list[str] = []
    for path in sorted(source_dir.rglob("*.css")):
        text = path.read_text(encoding="utf-8").strip()
        if text and text in style:
            found.append(path.relative_to(source_dir).as_posix())
    if not found:
        # Not a skip and not an empty group: an empty group grades nothing
        # and reports nothing, which is the rubber stamp this whole module
        # exists to refuse.
        raise RuntimeError(
            f"render-plugin-pages.py's inlined <style> matches no stylesheet in "
            f"{source_dir}, so this gate can no longer see what its 15 generated "
            f"pages are served"
        )
    return tuple(dict.fromkeys(found))


def _about_dress_css(render_hub, about_page: Path, root: Path) -> tuple[str, ...]:
    """The theme stylesheets about.html's reading-dress picker can point at.

    about.html is hand-authored except for one renderer-owned zone
    (render_about_theme_dresses), and that zone is the only place a theme
    stylesheet reaches the page. Derived in two hops so neither end can
    drift alone: render-hub.py is asked for the zone's element id by
    rendering an EMPTY registry (which touches no theme on disk and so
    survives a monkeypatched theme_dir), then that element is read out of
    `about_page` for the hrefs actually served.
    """
    probe = render_hub.render_about_theme_dresses({}, root)
    m = re.search(r"\bid\s*=\s*[\"']([^\"']+)[\"']", probe)
    if not m:
        raise RuntimeError(
            "render_about_theme_dresses no longer emits an id, so about.html's "
            "reading dress cannot be located and would go ungraded"
        )
    html = about_page.read_text(encoding="utf-8")
    block = re.search(
        rf"<script\b[^>]*\bid\s*=\s*[\"']{re.escape(m.group(1))}[\"'][^>]*>(.*?)</script>",
        html, re.S,
    )
    if not block:
        raise RuntimeError(
            f"{about_page.name} carries no {m.group(1)} block, so its "
            f"reading dress cannot be located and would go ungraded"
        )
    hrefs: list[str] = []
    for entry in json.loads(block.group(1)):
        theme_href = _THEME_HREF_RE.match(entry.get("css") or "")
        if theme_href:
            hrefs.append(theme_href.group(1))
    return tuple(dict.fromkeys(hrefs))


def resolution_groups(
    tdir: Path, root: Path = ROOT
) -> dict[str, tuple[tuple[str, ...], tuple[str, ...]]]:
    """{consumer: (theme stylesheets, site stylesheets)} for every set of
    stylesheets some real consumer loads together.

    Four live sources, one per way a theme stylesheet reaches a document:

      1. render-hub.py's THEME_CSS_HREFS — the renderer-owned "theme-css"
         <link> on each hand-authored page. Exactly one theme stylesheet per
         page by construction; the page's <head> owns any others.
      2. render-plugin-pages.py's STYLE — the concatenation inlined into the
         15 generated plugin pages. No <link> at all, and notably no
         tokens.css.
      3. render-hub.py's render_about_theme_dresses — about.html's
         easter-egg dress picker.
      4. `tdir`'s own home shell — the <link> tags index.html renders with.
         The only source that reads the theme UNDER TEST rather than the
         site, and it has to be: those tags are theme-authored and change
         with every new theme. Located without a literal anywhere —
         render-hub.py names the page it renders from a theme shell,
         content/page-archetypes.json names that page's archetype, and the
         archetype names its shell.

    `root` is honored by all four: THEME_CSS_HREFS and ABOUT_HTML are
    absolute Paths baked from render-hub.py's own ROOT, so they are re-rooted
    by name here rather than used as-is. A parameter that silently applied to
    some sources and not others would be a trap.

    Pages that load an IDENTICAL set collapse into one group keyed by all of
    their names, so press.html and privacy.html are graded once and the
    error names both. index.html and themes.html do NOT collapse — index
    also links the widget stylesheet — which is the correct outcome: the
    tighter group still grades tokens.css alone.
    """
    render_hub = _load_sibling_script("render-hub.py", "_theme_doctor_render_hub")
    plugin_pages = _load_sibling_script(
        "render-plugin-pages.py", "_theme_doctor_render_plugin_pages"
    )

    specs: dict[tuple[tuple[str, ...], tuple[str, ...]], list[str]] = {}

    def add(consumer: str, theme_css, site_css) -> None:
        key = (tuple(sorted(set(theme_css))), tuple(sorted(set(site_css))))
        specs.setdefault(key, []).append(consumer)

    for page, href in render_hub.THEME_CSS_HREFS.items():
        add(page.name, (href,), _page_site_stylesheets(root / page.name))
    inline_source = theme_registry.theme_dir(
        theme_registry.active_slug(theme_registry.load(root)), root
    )
    add("plugins/*/index.html", _inlined_theme_css(plugin_pages.STYLE, inline_source), ())
    about_page = root / render_hub.ABOUT_HTML.name
    add(
        about_page.name,
        _about_dress_css(render_hub, about_page, root),
        _page_site_stylesheets(about_page),
    )

    # index.html, from the theme under test's own home shell. archetype_for
    # raises KeyError naming the page if index.html ever leaves the mapping —
    # loud, never a silent default, which is the whole point of putting the
    # site's busiest page in a group at all.
    index_page = render_hub.INDEX_HTML.name
    shell = f"archetypes/{archetypes.archetype_for(index_page, archetypes.load(root))}.html"
    shell_theme_css, shell_site_css = _page_stylesheets(tdir / shell)
    add(index_page, (shell, *shell_theme_css), shell_site_css)

    return {", ".join(sorted(consumers)): key for key, consumers in specs.items()}


def _group_stylesheet_text(path: Path) -> str:
    """The CSS a group member contributes to its group.

    A .html member is a SHELL whose dress is its inline <style> block.
    archetypes/home.html is the only one today, and it is where the ENTIRE
    home treatment lives — no theme ships an archetypes/home.css — so
    reading it as a group member both credits what it defines and grades
    what it spends. Every other member is a stylesheet and contributes its
    whole text.
    """
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".html", ".htm"):
        return "\n".join(STYLE_BLOCK_RE.findall(text))
    return text


def check_every_required_stylesheet_is_graded(
    groups: dict[str, tuple[tuple[str, ...], tuple[str, ...]]]
) -> list[str]:
    """Every stylesheet a theme MUST ship has to land in some resolution
    group.

    The backstop that makes derived groups safe. Scoping the reads-check
    per group trades a pool that was too WIDE for a set of pools that could
    silently become too NARROW — repoint THEME_CSS_HREFS away from
    archetypes/utility.css and that file's var() reads stop being graded by
    anything, with no error anywhere. Grading less than you claim to is the
    failure mode this module was written against; it gets an error, not a
    shrug.
    """
    graded = {label for theme_css, _ in groups.values() for label in theme_css}
    return [
        f"{label} is loaded by no consumer this gate knows about, so nothing "
        f"grades what it reads"
        for label in sorted(set(GRADED_THEME_CSS) - graded)
    ]


def check_theme_reads_only_what_it_defines(
    group: str, theme_css: dict[str, str], site_css: dict[str, str] | None = None
) -> list[str]:
    """Every var(--x) in the theme stylesheets ONE consumer group loads must
    resolve inside that same group, or carry a fallback.

    The theme-side twin of the rule the converted pages now follow. Those
    pages were fixed by giving every theme-bespoke read a fallback; this
    catches the same defect one level up, where a token-completeness check
    structurally cannot see it — check_required_tokens grades the CONTRACT
    names, and --pb-* is deliberately not among them.

    `theme_css` is the group's theme stylesheets (graded as readers AND
    credited as definers); `site_css` is the repo-owned stylesheets that
    same group links (credited as definers only — editorial.css reading a
    name it does not define is not a theme's finding to report).

    Within a group, cross-file resolution is correct and expected:
    archetypes/product.css spends names archetypes/product-tokens.css
    defines, and render-plugin-pages.py concatenates the pair before either
    is served. ACROSS groups it is a defect — see the resolution-group
    header above for the transparent-body failure that pooling hid.
    """
    defined: set[str] = set()
    for text in theme_css.values():
        defined |= set(_parse_custom_properties(text))
    for text in (site_css or {}).values():
        defined |= set(_parse_custom_properties(text))

    errors: list[str] = []
    for label, text in sorted(theme_css.items()):
        body = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
        unguarded = set()
        for m in re.finditer(r"var\(\s*(--[\w-]+)", body):
            depth, i, has_fallback = 1, m.end(), False
            while i < len(body) and depth:
                if body[i] == "(":
                    depth += 1
                elif body[i] == ")":
                    depth -= 1
                elif body[i] == "," and depth == 1:
                    has_fallback = True
                i += 1
            if not has_fallback and m.group(1) not in defined:
                unguarded.add(m.group(1))
        for name in sorted(unguarded):
            errors.append(
                f"{label}: reads {name}, which nothing loaded by {group} defines "
                f"and which carries no fallback"
            )
    return errors


def check_contrast(
    css: str, pairs: list[list[str]] | None
) -> tuple[list[str], list[str]]:
    """Returns (failures, advisories). Absent pairs is advisory, not failure —
    a theme states what it wants checked; nothing declared means nothing to
    fail on, but the gap is worth flagging, not hiding."""
    if not pairs:
        return [], ["no contrastPairs declared — contrast unverified"]
    failures = []
    for fg_name, bg_name, ratio in evaluate_contrast_pairs(css, pairs):
        if ratio is None:
            failures.append(f"contrast: could not resolve {fg_name} / {bg_name} to colors")
        elif ratio < AA_MIN_RATIO:
            failures.append(
                f"contrast: {fg_name} on {bg_name} = {ratio:.2f} "
                f"(below AA {AA_MIN_RATIO})"
            )
    return failures, []


# ─── browser checks (optional, --browser / --require-browser) ─────────
def _import_sync_playwright():
    """Import hook, split out so tests can force "unavailable" deterministically
    (monkeypatch this instead of fighting sys.modules/import machinery)."""
    try:
        from playwright.sync_api import sync_playwright
        return sync_playwright
    except ImportError:
        return None


def _degrade(msg: str, require: bool) -> list[str]:
    """One unavailability event, routed by --require-browser: a hard FAILURE
    when the caller demanded the browser path actually run (the scheduled
    rotation, unattended), or a printed skip-and-continue otherwise (the local
    convenience path, for a machine without `playwright install`)."""
    if require:
        return [f"browser: {msg} (--require-browser was set)"]
    print(f"browser checks skipped: {msg}")
    return []


def _run_browser_checks(
    html_text: str, require: bool = False, dress_outcome: bool = False
) -> list[str]:
    sync_playwright = _import_sync_playwright()
    if sync_playwright is None:
        return _degrade("playwright not installed", require)

    import http.server
    import socketserver
    import threading

    class _Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(ROOT), **kw)

        def do_GET(self):  # noqa: N802 — stdlib method name
            if self.path in ("/", "/index.html"):
                body = html_text.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            super().do_GET()

        def log_message(self, fmt, *args):  # quiet — the doctor has its own output
            pass

    errors: list[str] = []
    try:
        httpd = socketserver.TCPServer(("127.0.0.1", 0), _Handler)
    except OSError as e:
        # Environment degradation — says nothing about the theme, UNLESS the
        # caller required the browser path to run (then it's a gate failure).
        return _degrade(f"could not start local server ({e})", require)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch()
            except Exception as e:  # pragma: no cover — environment-dependent
                # Environment degradation — same require-gated routing as above.
                return _degrade(f"could not launch chromium ({e})", require)
            try:
                for width in (1440, 768, 390):
                    page = browser.new_page(viewport={"width": width, "height": 900})
                    try:
                        errors += _check_viewport(
                            page, f"http://127.0.0.1:{port}/", width,
                            dress_outcome=dress_outcome,
                        )
                    finally:
                        page.close()
            finally:
                browser.close()
    finally:
        httpd.shutdown()
        httpd.server_close()
    return errors


# Third-party isolation lives in browser_origin.py because scripts/
# freeze-theme.py needs the identical rule and runs EARLIER in the same
# rotation — see that module's docstring. Re-exported under the private
# names this file already used so nothing here reads as indirection.
_page_origin = browser_origin.page_origin
_is_off_origin = browser_origin.is_off_origin
_console_message_url = browser_origin.console_message_url


# Off-origin URLs answered from a committed fixture instead of aborted.
#
# Exactly one entry, and it buys back real coverage: mod-launcher-games.html
# renders its ENTIRE body from a manifest on raw.githubusercontent.com, so
# under the isolation below the gate would only ever see its fetch-failed
# fallback panel — chrome, and nothing else. The page whose layout is the
# most complex of the six (a cover rail plus two long game-row lists) would
# be the one page checked in its emptiest state.
#
# Substitution, not exemption: the body is on disk, nothing leaves the
# machine, and the render is identical run to run. See the fixture's own
# $comment for what it has to contain and why (long and unbreakable names —
# a name that cannot wrap is what overflows a narrow viewport).
_GAME_FEED_FIXTURE = ROOT / "scripts" / "fixtures" / "mod-launcher-supported-games.json"
_OFF_ORIGIN_FIXTURES = {
    "626-game-manifest": (
        "application/json",
        _GAME_FEED_FIXTURE.read_text(encoding="utf-8"),
    ),
}


# ─── the borrowed dress, gated on OUTCOME ────────────────────────────────
#
# THE CORE IS A REGION DIFFERENTIAL, not an inspection of what any element
# computes. Each page is measured twice in one load — once with its theme
# stylesheet linked, once with that <link> disabled — and each of the page's
# own named regions has to render DIFFERENTLY between the two. That is the
# strongest available form of "the theme dresses this region": it makes no
# claim about technique, about syntax, about values, or about which element
# carries the paint. Values are only ever compared for INEQUALITY as opaque
# strings, so a theme writing `oklch(...)`, `color-mix(...)`, `lab(...)` or a
# color space invented next year is graded exactly as well as one writing hex.
#
# The first cut of this gate read each element's computed background and
# asked whether it painted. That was wrong twice over, and both were the same
# mistake arriving through values instead of through selectors:
#
#   1. It parsed colors. `oklch(0.18 0.04 250)` is a fully opaque field that
#      an rgb()/rgba() parser reads as alpha 0. September writes one correct
#      theme and the rotation aborts at 09:00 UTC on the 1st, unattended,
#      because the GATE was wrong.
#   2. It constrained technique. A nav in normal flow that never overlaps
#      needs no z-index; a footer separated by a hairline `border-top` on the
#      shared field paints no background of its own; a field can live on a
#      full-bleed overlay or `body::before` — the technique phosphor already
#      uses for `.pb-scanlines`. All four are legitimate designs the first cut
#      would have failed, which is a manifest wearing an outcome's clothes.
#
# The differential closes both without a single color parse. Two things make
# the overlay technique count, and BOTH are needed — the first cut shipped only
# the first and still failed a correct overlay theme: `::before` and `::after`
# are in every region's fingerprint, AND the field region reaches `body > div`,
# the page's own full-bleed overlay element. See _DRESS_REGIONS for the
# measurement that forced the second.
#
# The selectors this names — `nav.nav`, `header.page-hero`, `main`, `footer`,
# `h1.page-title`, `a.inline-link` — are press.html's and privacy.html's OWN
# markup, which is theme-invariant and is what a theme is supposed to be able
# to find. Nothing here names a selector that must exist in the THEME's CSS.

# Every region's fingerprint is built from these, for the element and for its
# ::before and ::after. Broad on purpose: the test is inequality, never a
# threshold, so a property that no theme ever moves costs nothing and a
# property left out is a way for a real difference to hide.
_DRESS_PROPS = (
    "color background-color background-image background-size background-position "
    "border-top-color border-bottom-color border-left-color border-top-width "
    "border-bottom-width border-top-style border-top-left-radius "
    "box-shadow text-shadow filter backdrop-filter opacity mix-blend-mode "
    "font-family font-size font-weight font-style line-height letter-spacing "
    "text-transform text-decoration-line text-decoration-color fill stroke "
    "padding-top padding-left margin-top margin-left display position z-index "
    "overflow-x transform content mask-image max-width"
).split()

# The page field is graded on these instead of the full set, and the narrowing
# is load-bearing rather than an optimisation. `html` and `body` are moved by
# any bare reset — `* { box-sizing }`, `html, body { margin: 0 }` — which is
# not a field.
#
# Measured both ways rather than argued. A theme carrying tokens plus those
# two reset rules and nothing else was built and run through this gate:
#
#   field region on the FULL prop set  ->  1 of 2 differ, DIFFERS  (false pass:
#                                          all five regions green)
#   field region on _FIELD_PROPS       ->  0 of 2 differ, IDENTICAL (caught)
#
# Backgrounds, and the pseudo-element `content` that switches an overlay on,
# are what "there is a field" actually means.
_FIELD_PROPS = (
    "background-color background-image background-size background-position "
    "background-repeat background-attachment background-clip background-origin "
    "opacity filter backdrop-filter mask-image mix-blend-mode content"
).split()

# `main` is `<main class="kit">` on press.html and `<main class="policy">` on
# privacy.html — the bare tag is what both share.
#
# (label, selector, scope, props, geometry). Scope "self" fingerprints only
# the matched elements; "subtree" fingerprints each match and all of its
# descendants. `geometry` adds each element's own WIDTH and HEIGHT.
#
# Its own width and height, and deliberately NOT its x/y. Where an element
# lands is a consequence of whatever sits above it, so with x/y in the
# fingerprint a footer whose every property was byte-identical still counted
# as "rendering differently" because content further up the page had resized.
# Measured, against a theme carrying no rule that paints at all: the x/y
# channel alone reported the footer AND the field as dressed. An element's own
# box belongs to its own dress; where that box lands does not.
#
# The field region carries no geometry, which is the same rule applied
# consistently rather than a special case: `html` and `body` resize with their
# content, so a rect there measures the page's length and not whether it has a
# field.
_DRESS_REGIONS = (
    # `body > div` reaches the page's own full-bleed overlay, which is the
    # only NON-PSEUDO surface a theme can put a field on here — a theme cannot
    # add elements, so its choices on these two pages are `html`/`body`, their
    # pseudos, and the one `<div>` each page ships as a direct child of body.
    # Without it the region failed a theme that moved the entire field onto
    # that div at `z-index: -1` with html and body painting nothing: a
    # perfectly correct dark page, exit 1, rotation aborted. Measured, and the
    # narrower `html, body` alternative measured alongside it:
    #
    #   selector                 live   (a) tokens  (b) resets  (c) ::before  (d) overlay div
    #   html, body               1/2    0/2   OK    0/2   OK    1/2    OK     0/2  FALSE FAIL
    #   html, body, body > div   2/3    0/3   OK    0/3   OK    1/3    OK     1/3  OK
    #   html, body, body > *     4/9    0/9   OK    0/9   OK    1/9    OK     1/9  OK
    #
    # `body > *` also works and is deliberately NOT used: it would let a
    # background on the nav alone satisfy "the page has a field", and nav,
    # hero, main and footer each already have a region of their own.
    ("the page field", "html, body, body > div", "self", _FIELD_PROPS, False),
    ("nav.nav", "nav.nav", "subtree", _DRESS_PROPS, True),
    ("header.page-hero", "header.page-hero", "subtree", _DRESS_PROPS, True),
    ("main", "main", "subtree", _DRESS_PROPS, True),
    ("footer", "footer", "subtree", _DRESS_PROPS, True),
)

_DRESS_PROBE_JS = r"""
(regions) => {
  // ── ORDER IS LOAD-BEARING ────────────────────────────────────────────
  // Every element-level reading happens FIRST, on a page nothing has
  // touched. The differential's stylesheet toggle comes last, and NOTHING
  // reads after it.
  //
  // Because the toggle does not fully reverse, and that was measured rather
  // than feared. Disabling the sheet and re-enabling it restores
  // `body`'s font-family and even the resolved value of a custom property,
  // but leaves `a.inline-link`'s color at the UA's `rgb(0, 0, 238)`:
  // Chromium does not invalidate its cached `:link` style when
  // CSSStyleSheet.disabled goes back to false. The first version of this
  // read the links after the toggle, and a restore self-check keyed on
  // font-family reported "restored: true" while every link on the page was
  // still undressed — so the gate failed the LIVE, correct theme with "the
  // theme dresses links not at all". A convenient-looking self-check that
  // was measuring the wrong property.

  const rd = (el) => {
    if (!el) return null;
    const cs = getComputedStyle(el);
    return {color: cs.color, fontFamily: cs.fontFamily, fontSize: cs.fontSize};
  };

  // The undressed baseline, read from a blank same-document iframe: zero
  // author CSS, so what it computes is this browser's own default. Measured
  // at runtime rather than written down, which is what keeps a Windows dev
  // box and the ubuntu runner grading the same thing. It makes no network
  // request, so the off-origin abort route never sees it.
  let ua = null;
  const probe = document.createElement('iframe');
  probe.setAttribute('aria-hidden', 'true');
  probe.style.cssText = 'position:absolute;width:0;height:0;border:0;visibility:hidden';
  document.body.appendChild(probe);
  const doc = probe.contentDocument;
  if (doc && doc.body) {
    doc.body.innerHTML = '<h1>H</h1><a href="#">a</a>';
    const ub = getComputedStyle(doc.body);
    const uh = getComputedStyle(doc.body.querySelector('h1'));
    const ul = getComputedStyle(doc.body.querySelector('a'));
    ua = {
      fontFamily: ub.fontFamily,
      headingRatio: parseFloat(uh.fontSize) / parseFloat(ub.fontSize),
      linkColor: ul.color,
    };
  }
  probe.remove();

  const body = rd(document.body);
  const title = rd(document.querySelector('h1.page-title'));

  // EVERY inline link, each against ITS OWN PARENT's color — not against
  // body's. Sampling the first link and comparing to body was blind on
  // privacy.html by construction: its first inline link sits in
  // `main.policy p`, which the page colors --fg-2 while body is --fg-1, so an
  // undressed link inherited a color that matched neither body's nor UA blue
  // and both halves passed while every link on the page was identical to the
  // prose around it. "Distinguishable from prose" means distinguishable from
  // the text it actually sits in.
  const inlineLinks = Array.from(document.querySelectorAll('a.inline-link')).map((a) => ({
    color: getComputedStyle(a).color,
    parentColor: a.parentElement ? getComputedStyle(a.parentElement).color : null,
  }));

  // ── the region differential ──────────────────────────────────────────
  const fingerprint = (selector, scope, props, geometry) => {
    const roots = Array.from(document.querySelectorAll(selector));
    if (!roots.length) return null;
    const els = [];
    for (const r of roots) {
      els.push(r);
      if (scope === 'subtree') els.push(...r.querySelectorAll('*'));
    }
    return els.map((el) => {
      const row = [el.tagName];
      for (const pseudo of [null, '::before', '::after']) {
        const cs = getComputedStyle(el, pseudo);
        for (const p of props) row.push(cs.getPropertyValue(p));
      }
      if (geometry) {
        const b = el.getBoundingClientRect();
        row.push(Math.round(b.width), Math.round(b.height));
      }
      return row.join('\u0001');
    });
  };
  const sweep = () =>
    regions.map(([, sel, scope, props, geom]) => fingerprint(sel, scope, props, geom));

  // The page's OWN linked stylesheets. render-hub.py owns the single
  // `SITE_JSON:theme-css` <link> on both of these pages and their own CSS is
  // an inline <style>, so "every link[rel=stylesheet]" IS "the theme's dress"
  // here — a premise pinned by a test against the shipped files rather than
  // assumed, and reported back so a page that grows a second linked
  // stylesheet cannot make this silently mean something else.
  //
  // CSSStyleSheet.disabled, NOT HTMLLinkElement.disabled: toggling the
  // ELEMENT's property off and back on does not restore the sheet
  // synchronously in Chromium, which left the whole page undressed for every
  // read that followed it.
  const links = Array.from(document.querySelectorAll('link[rel="stylesheet"]'));
  const sheets = links.map((l) => l.sheet).filter(Boolean);

  // Rule count, so "the region did not change" can be told apart from "the
  // stylesheet arrived empty" — a 404 or a parse failure would otherwise be
  // reported as five regions the theme forgot to dress.
  let styleRules = 0;
  for (const s of sheets) { try { styleRules += s.cssRules.length; } catch (e) { } }

  const dressed = sweep();
  sheets.forEach((s) => { s.disabled = true; });
  // Proof the toggle took, asked of the CSSOM itself rather than inferred
  // from a property. The first version compared body's font-family before
  // and after and called that "the toggle took effect" — which is false for
  // any theme that sets no font-family, exactly the token-only theme this
  // gate exists to reject. It short-circuited and hid the five region
  // findings behind a diagnosis that was about the gate, not the theme.
  const toggled = sheets.every((s) => s.disabled === true);
  const undressed = sweep();   // getComputedStyle forces a synchronous recalc
  sheets.forEach((s) => { s.disabled = false; });

  const diffs = regions.map(([label], i) => {
    const a = dressed[i], b = undressed[i];
    if (a === null) return {label: label, present: false, differing: 0, total: 0};
    let differing = 0;
    const n = Math.min(a.length, b.length);
    for (let k = 0; k < n; k++) if (a[k] !== b[k]) differing++;
    // A theme that changes the ELEMENT COUNT of a region cannot have left it
    // undressed, so a length mismatch counts as difference rather than being
    // silently truncated away by the min() above.
    differing += Math.abs(a.length - b.length);
    return {label: label, present: true, differing: differing, total: a.length};
  });

  return {
    regions: diffs,
    linkedStylesheets: links.length,
    toggledStylesheets: sheets.length,
    toggleTookEffect: toggled,
    styleRules: styleRules,
    ua: ua,
    body: body,
    title: title,
    links: inlineLinks,
  };
}
"""


def _first_family(font_family: str) -> str:
    """The first family in a computed font-family list, unquoted and
    casefolded. The only value this module parses at all, and it parses a
    font NAME rather than a color — see the module comment above
    `_DRESS_PROPS` for why nothing here reads a color any more."""
    first = (font_family or "").split(",")[0].strip()
    return first.strip("\"'").strip().casefold()


def check_page_renders_dressed(page, width: int) -> list[str]:
    """Assert that a page which owns none of its own chrome still RENDERS
    dressed under the theme being doctored. Returns a list of failure strings,
    each naming the outcome that went missing.

    press.html and privacy.html take their entire nav/hero/type/link/footer
    treatment from `archetypes/utility.css` and restate none of it — measured,
    not assumed: 49 of that file's 50 selectors reach press.html and 48 reach
    privacy.html, and the overlap between each page's own <style> selectors
    and that file's is EXACTLY ZERO. The pages dress their content; the theme
    dresses everything else. So a second theme whose utility.css drops a
    load-bearing rule changes or breaks both pages while every other gate in
    this repo stays green: the token contract counts NAMES, and a name can be
    present in a file that no longer carries the rule that spends it.

    Este's ruling (2026-08-04) is that these two keep wearing the theme's
    dress, so a new month actually restyles them. The exposure therefore has
    to close by verification rather than by removal, which is what this is.

    ── The region differential (the core) ────────────────────────────────
    Each of `_DRESS_REGIONS` must render DIFFERENTLY with the page's theme
    stylesheet linked than with it disabled. Both measurements happen in one
    page load; the stylesheet is re-enabled afterwards. No value is
    interpreted — fingerprints are compared as opaque strings — so no color
    syntax, present or future, can be misread as "paints nothing", and no
    technique is required: a transparent nav in normal flow, a footer marked
    only by a hairline, a field on `body::before`, and an `oklch` field all
    differ from themselves undressed, which is the only thing being asked.
    A theme doing all four of those at once was built and passes.

    WHAT THE DIFFERENTIAL DOES NOT CLAIM, stated because a gate that oversells
    itself is the failure mode this file keeps relearning. Both are measured:

    - `main` is the weakest region on these two pages, and legitimately so.
      Their own content rules spend theme tokens (`var(--s-*)`, `var(--bg-1)`,
      `var(--border-1)`), so a theme carrying tokens and NO rule at all still
      moves 185 of press.html's 198 elements in that region. It reaches
      `main`; it just does not dress anything. The other four regions catch
      that theme (0 differing, all four), and so do all three element-level
      assertions.
    - A theme carrying tokens plus bare resets moves nav, hero and footer via
      box metrics alone (6/23, 9/14, 4/13). Only the field region catches it
      among the five. That is why `_FIELD_PROPS` is narrowed, and why the
      element-level assertions below are not decoration.
    - The field region reaches `html`, `body`, their pseudos, and `body > div`.
      A theme that painted the field on some OTHER element the page ships —
      inside `main`, say — would not register there. That is a narrower gap
      than it sounds, because a theme cannot add elements to these pages and
      those are the surfaces that can go full-bleed; but it is a gap, and it
      is the third different answer this region has had. The first cut asked
      each element whether it painted and failed four legitimate techniques.
      The second reached only `html`/`body` and their pseudos, and the fix
      round's own disclosure called the overlay-div case a blind spot that
      "would pass" — it was the opposite, a false FAIL on a correct page,
      found by review and reproduced at exit 1 on both pages.

    ── The three element-level assertions that still earn their place ─────
    Each is something the differential structurally cannot see, because a
    region differs for a hundred reasons at once.

    1. Body type is not the browser's own — the first family in `body`'s
       computed font-family differs from the family an undressed document
       computes. A theme that dresses every region and forgets `font-family`
       leaves both pages in Times New Roman with every region still differing.
       No family is required and no generic is banned; the comparison target
       is measured at runtime.

       THE ONE TYPE CHOICE THIS FORBIDS, stated rather than discovered on the
       1st: a stack whose FIRST family is the browser's own standard font.
       `Georgia, serif`, bare `serif`, `system-ui` and `"Iowan Old Style",
       Times, serif` all pass; `"Times New Roman", serif` does not. A
       newspaper-styled month that wants Times first has to name a specific
       cut of it, or put it second. That is the honest cost of measuring
       against the browser's default instead of hardcoding one: the assertion
       cannot tell "chose Times" from "chose nothing", and "chose nothing" is
       the defect it exists for.
    2. The page title outscales a bare heading — `h1.page-title`'s font-size
       relative to body text exceeds what an UNDRESSED `<h1>` computes in the
       same browser (2.00x). HEADROOM, measured on this theme so whoever hits
       this on the 1st is not guessing: 3.50x at 1440px and 2.25x at 390px,
       where the `clamp()` floor of 36px meets a 16px body. A theme whose
       floor lands at 32px fails, and that verdict is correct rather than
       tunable: a hero at exactly browser proportions is not dressed. This
       threshold is the minimum honest statement of the outcome, not a
       constant to relax when it becomes inconvenient.

       IT IS A RATIO, so raising BODY type eats the headroom. Those 2.25x and
       3.50x figures are against a 16px body, the only body size this theme
       ships. With a 40px title: 14px, 16px and 18px bodies pass, 20px lands
       at exactly 2.00x and FAILS. A theme that raises body type has to raise
       the hero with it — which is what a type scale does anyway, but the
       failure would read as being about the hero when the cause was the body.
    3. Inline links are distinguishable from the prose they sit in — EVERY
       `a.inline-link` resolves a color that is neither its own parent's color
       nor the browser's default link color. Both halves are load-bearing:
       dropping `a.inline-link { color }` leaves links inheriting their
       parent, and dropping the bare `a { color: inherit }` too drops them to
       UA blue, which the first half would wave through.

    ── What is deliberately NOT asserted ─────────────────────────────────
    `h1.page-title`'s font-weight. The UA's own `h1` default is already 700,
    so "a non-default weight" is satisfied by a completely undressed page —
    zero detection, real over-constraint on a theme that wants a light hero.

    Anything about `nav.nav`'s z-index. The only way to satisfy a
    stacking-order requirement on a nav that never overlaps is to write a
    declaration that does nothing, which is a manifest entry by another name.

    Whether any particular element paints a background. See the module
    comment above `_DRESS_PROPS` for the two independent reasons that was
    wrong, and `the page field` region for what replaced it.
    """
    m = page.evaluate(_DRESS_PROBE_JS, [list(r) for r in _DRESS_REGIONS])
    errors: list[str] = []

    def fail(msg: str) -> None:
        errors.append(f"browser: dress at {width}px: {msg}")

    # Never a soft skip, on either premise this rests on. Without a linked
    # stylesheet there is nothing to undress and the differential compares a
    # page to itself; without the baseline the element-level assertions
    # silently cover less than they claim. Both are the failure mode this
    # whole gate exists to prevent.
    if not m.get("toggledStylesheets"):
        fail(f"the page has no linked stylesheet the differential could remove "
             f"({m.get('linkedStylesheets', 0)} <link rel=stylesheet> found), so "
             f"there was no dress to take off and nothing was graded")
        return errors
    if not m.get("toggleTookEffect"):
        fail("the browser refused to disable the page's stylesheet, so the "
             "differential compared the page to itself and graded nothing")
        return errors
    if not m.get("styleRules"):
        fail("the page's theme stylesheet loaded no rules at all (404, or it failed "
             "to parse), so there is no dress to grade")
        return errors

    for region in m.get("regions", ()):
        if not region["present"]:
            fail(f"region {region['label']} is not present on the page, so its dress "
                 f"could not be graded")
        elif not region["differing"]:
            fail(f"region {region['label']} renders identically with the theme's "
                 f"stylesheet and without it ({region['total']} elements compared), "
                 f"so the theme does not dress it")

    ua = m.get("ua")
    if not ua:
        fail("could not read the browser's undressed baseline, so nothing was graded")
        return errors

    body = m.get("body") or {}
    body_family = _first_family(body.get("fontFamily", ""))
    if not body_family or body_family == _first_family(ua["fontFamily"]):
        fail(f"body resolves the browser's default type ({body.get('fontFamily')!r}), "
             f"so the theme supplies no type stack")

    title = m.get("title")
    if title is None:
        fail("h1.page-title is not present on the page, so its dress could not be graded")
    elif body:
        try:
            ratio = float(title["fontSize"].rstrip("px")) / float(body["fontSize"].rstrip("px"))
        except (KeyError, ValueError, ZeroDivisionError):
            # A gate that raises is worse than a gate that fails: an
            # unhandled exception here would abort the whole doctor run and
            # take the other archetypes' results with it.
            ratio = None
        if ratio is None:
            fail("h1.page-title's size could not be read")
        elif ratio <= ua["headingRatio"]:
            fail(f"h1.page-title is no larger, relative to body text, than an "
                 f"undressed browser heading ({ratio:.2f}x vs {ua['headingRatio']:.2f}x)")

    links = m.get("links")
    if not links:
        fail("a.inline-link is not present on the page, so its dress could not be graded")
    else:
        same_as_prose = sum(1 for a in links if a["color"] == a["parentColor"])
        if same_as_prose:
            fail(f"{same_as_prose} of {len(links)} a.inline-link elements resolve the "
                 f"same color as the prose they sit in, so links are indistinguishable "
                 f"from body copy")
        ua_blue = sum(1 for a in links if a["color"] == ua["linkColor"])
        if ua_blue:
            fail(f"{ua_blue} of {len(links)} a.inline-link elements resolve the "
                 f"browser's own default link color, so the theme dresses links not "
                 f"at all")

    return errors


def _check_viewport(page, url: str, width: int, dress_outcome: bool = False) -> list[str]:
    """Load `url` in an already-created page-like object at `width` and check it.

    `dress_outcome=True` additionally runs `check_page_renders_dressed` — see
    DRESS_OUTCOME_PAGES for which pages get it and why only those.

    Split out from `_run_browser_checks` so it's unit-testable with a stub page
    (no real browser/server needed) — see test_theme_doctor.py.

    The page under test failing — `page.goto` raising (navigation error, timeout)
    or a non-2xx response for the page itself — is a GATE FAILURE, not a graceful
    skip: this is the one thing standing between a broken theme and an unattended
    monthly promotion to live (T5's scheduled rotation calls `--browser` as its
    gate). A theme whose rendered page throws or hangs on load must fail the gate,
    not get silently skipped and waved through.

    ── Third-party isolation, and why it is not optional ──────────────────
    This gate opens twelve documents: one per archetype plus the eight live
    pages in BROWSER_CHECK_LIVE_PAGES. Three of the four archetype documents
    are shells the theme ships; `reading`'s is `about.html`, which
    `_archetype_source` swaps in because the Field Note shell carries only 3
    of that archetype's 10 required classes. ELEVEN of the twelve carry
    `<script async src="//gc.zgo.at/count.js">`, which over `http://127.0.0.1`
    resolves to a real third-party host. (The twelfth is the `product`
    archetype's own shell, which ARCHETYPE_CHROME marks `analytics=False`.)
    Counted by grep against the shipped files, not incremented.
    So this gate ALREADY depended on gc.zgo.at being up at 09:00 UTC on the
    1st, through two channels: a failed load logs a console error (reported
    as the theme's fault), and an `async` script still delays the `load`
    event `page.goto` waits for, so a slow host eats the 15s timeout and
    fails the gate outright.

    Both channels are closed here rather than worked around: off-origin
    requests are aborted before they leave, and console errors attributed to
    an off-origin URL — including the `net::ERR_FAILED` those aborts produce
    — are dropped. What remains is the page's OWN errors, which is what this
    gate was always claiming to grade.

    One page's third-party load is a WEBFONT rather than analytics, and it was
    checked rather than waved past: index.html embeds the Bacon Trail widget,
    whose own widget-bacon-trail/widget.css opens with a fonts.googleapis.com
    @import (deliberate — that widget also renders on third-party domains,
    where /fonts/ would resolve to the host; see fonts/fonts.css's header).
    On THIS page it is redundant: index.html already loads the same families
    from the same-origin /fonts/fonts.css, whose @font-face rules apply
    document-wide, widget included. So blocking it moves no metric — which is
    the claim the full gate passing with the block in place actually tests.

    ── What this asks of every page the gate opens ───────────────────────
    A NEW constraint, undocumented before and worth stating because nothing
    else enforces it: every page here must tolerate TOTAL off-origin failure
    without logging a console error or throwing. That is not free. The
    `home` archetype's shell embeds the Bacon Trail widget, a React bundle
    built from a different directory (apps/widget-bacon-trail), and its
    off-origin dependencies are not one host but three — api.themoviedb.org,
    image.tmdb.org, and the fonts.googleapis.com @import in widget.css.
    React logs on an uncaught render error, so a future widget build that
    stops handling its own fetch failure turns this gate red for reasons
    that have nothing to do with the theme under test. Whoever hits that:
    the fix belongs in the widget's error handling, not in loosening this.

    So `mod-launcher-games.html` is NOT the only page whose off-origin
    content is absent here — an earlier version of this comment said it was,
    and index.html was already the counterexample. The cost, stated rather
    than hidden: any page whose content arrives over an off-origin fetch
    renders its fetch-failed state. mod-launcher-games.html's game manifest
    lives on raw.githubusercontent.com, so this gate grades its chrome and
    its fallback panel, not its 150-row populated layout. That was already
    true and merely racy before: `_check_viewport` waits 300ms after `load`,
    which a cross-country fetch does not reliably beat. Deterministically
    grading a known state beats sometimes grading either. `rororo.html`'s
    feed is same-origin (`data/rororo-plugins.json`, served by the local
    server), so it populates fully and IS graded populated.

    ── What `page.route` does NOT cover ──────────────────────────────────
    WebSocket handshakes, Service Worker requests, and requests from popup
    pages all bypass a page-level route handler. No page here opens any of
    the three today; a page that starts to would reopen the exposure quietly,
    so this is written down rather than assumed away.
    """
    origin = _page_origin(url)
    browser_origin.block_off_origin(page, url, fulfill=_OFF_ORIGIN_FIXTURES)
    console_errors: list[str] = []
    page.on(
        "console",
        lambda msg: console_errors.append(msg.text)
        if msg.type == "error" and not _is_off_origin(_console_message_url(msg), origin)
        else None,
    )
    # An UNCAUGHT exception is not a console message. Measured, not assumed:
    # a page whose inline script calls an undefined function delivers
    # "x is not defined" on `pageerror` and NOTHING on `console`. So the
    # docstring above — and the comment on BROWSER_CHECK_LIVE_PAGES — claimed
    # this gate catches a page "throwing" when it never had. It does now.
    #
    # No origin filter is needed on this channel, and that is a consequence
    # of the abort above rather than an oversight: with every off-origin
    # request aborted, no third-party script executes, so any exception
    # reaching here is the page's own by construction.
    page_errors: list[str] = []
    page.on("pageerror", lambda exc: page_errors.append(str(exc)))
    try:
        response = page.goto(url, wait_until="load", timeout=15000)
    except Exception as e:
        return [f"browser: page failed to load at {width}px: {e}"]

    if response is not None and response.status >= 400:
        return [f"browser: page returned HTTP {response.status} at {width}px"]

    errors: list[str] = []
    page.wait_for_timeout(300)  # let deferred scripts settle
    scroll_width = page.evaluate("document.documentElement.scrollWidth")
    client_width = page.evaluate("document.documentElement.clientWidth")
    if scroll_width > client_width + 1:
        errors.append(
            f"browser: horizontal scroll at {width}px "
            f"(scrollWidth {scroll_width} > clientWidth {client_width})"
        )
    for msg in console_errors:
        errors.append(f"browser: console error at {width}px: {msg}")
    for msg in page_errors:
        errors.append(f"browser: uncaught page error at {width}px: {msg}")
    # Last, so the probe's throwaway iframe cannot be in the DOM while
    # scrollWidth is measured above.
    if dress_outcome:
        errors += check_page_renders_dressed(page, width)
    return errors


# ─── per-archetype loop ───────────────────────────────────────────────
def _archetype_source(
    archetype: str, tdir: Path, home_html: str, tokens_css: str,
) -> tuple[str, str, bool]:
    """(html, css, check_zones) — what "this theme's dress" means for one
    archetype, and why it differs per archetype:

    `home`: the theme's real, live output — render-hub.py's `--theme`
    preview (already rendered into `home_html` by the caller), merged with
    tokens.css. The only archetype with a full end-to-end renderer today,
    so it's the only one checked for SITE_JSON zone markers too.

    `product` / `utility`: `archetypes/product.html` and
    `archetypes/utility.html` have NO live render-hub.py or
    render-plugin-pages.py consumer (documented in
    docs/theme-archetypes.md: product's real markup comes from
    render-plugin-pages.py's Python templates, not this shell; utility's
    real pages — press.html/privacy.html — are hand-authored, only their
    stylesheet <link> is renderer-owned). So the theme's own archetype file
    plus its own CSS artifact (REQUIRED_ARCHETYPE_CSS) together ARE the
    theme's dress for that archetype — checked as raw text, unresolved
    `{{PRODUCT:...}}`/`{{UTILITY:...}}` tokens included, since the required
    chrome/vocabulary/link markup lives outside those tokens.

    `reading`: NOT `archetypes/reading.html` (the Field Note shell) —  that
    file only ever carries 3 of the 10 required `reading` classes
    (`ed-page`/`ed-title`/`ed-dek`, and only once rendered, since the raw
    shell holds them as `{{READING:...}}` tokens). The other seven
    (`lnt-*`) are About's Long Now Terminal structure, which
    docs/theme-archetypes.md documents as a PERMANENT split, not a
    migration gap: About's markup already IS the full reading vocabulary,
    and about.html is explicitly NOT a themes/<slug>/ consumer — its
    structure doesn't move. What DOES move, as of A7: the DRESS over that
    structure. `html` here is still about.html, read fresh off disk (not
    per-theme — its markup is genuinely identical for every theme, that's
    the whole point of the override), but `css` is now the THEME's own
    `archetypes/reading.css` (REQUIRED_ARCHETYPE_CSS), not about.html's own
    inline `<style>`. See `_check_archetype` for the other half of this
    fix: crediting about.html's real markup toward the CSS-anchored `lnt-*`
    classes would make the check pass for literally any theme's
    reading.css, including an empty one, so `_check_archetype` doesn't do
    that — only the vocabulary's 3 shared `ed-*` leaves get credited from
    markup there."""
    if archetype == "home":
        inline_css = "\n".join(STYLE_BLOCK_RE.findall(home_html))
        return home_html, f"{inline_css}\n{tokens_css}", True
    if archetype == "reading":
        about_html = (ROOT / "about.html").read_text(encoding="utf-8")
        reading_css = (tdir / "archetypes" / REQUIRED_ARCHETYPE_CSS["reading"]).read_text(encoding="utf-8")
        return about_html, f"{reading_css}\n{_archetype_token_css(archetype, tdir)}", False
    css_filename = REQUIRED_ARCHETYPE_CSS[archetype]
    shell_html = (tdir / "archetypes" / f"{archetype}.html").read_text(encoding="utf-8")
    own_css = (tdir / "archetypes" / css_filename).read_text(encoding="utf-8")
    inline_css = "\n".join(STYLE_BLOCK_RE.findall(shell_html))
    return (
        shell_html,
        f"{inline_css}\n{own_css}\n{tokens_css}\n{_archetype_token_css(archetype, tdir)}",
        False,
    )


# The file each archetype's LINKING pages resolve their tokens from, appended
# last by _archetype_token_css so it wins the cascade the same way it wins in
# the browser.
#
# "utility" maps to utility.css, which _archetype_source ALSO passes as the
# archetype's own dress — so that file is appended twice. Deliberate, and the
# duplication is the point: press.html and privacy.html link
# archetypes/utility.css and NOTHING else, so tokens.css must not be the last
# word on their token values. Without this entry the gate graded utility's
# contrast against tokens.css's ramp, which is the exact bug
# _archetype_token_css was written to fix for product and reading, left
# unclosed for the third archetype. Safe to have shipped only because the two
# files happen to agree on every value today; a theme where they diverge would
# have had utility graded on a page nobody serves.
ARCHETYPE_TOKEN_CSS = {
    "product": PRODUCT_TOKENS_CSS,
    "reading": READING_TOKENS_CSS,
    "utility": REQUIRED_ARCHETYPE_CSS["utility"],
}


def _archetype_token_css(archetype: str, tdir: Path) -> str:
    """The token file an archetype's LINKING pages actually resolve from,
    appended last so it wins the same way it wins in the browser.

    Without it the contrast numbers printed for `product` and `reading`
    were not the numbers those pages render. `_archetype_source` built
    product's CSS as shell-inline + product.css + tokens.css, so the
    --fg-* ramp came from tokens.css — but conundrum.html and
    rororo-plugins.html link product-tokens.css, which deliberately carries
    a DIFFERENT ramp (#ffffff/#c4cdda/#a4aebd/#99a4b4 against tokens.css's
    #e8f2ff/#a8c2d9/#9fafc0/#92a5bd). The gate was grading a page nobody
    serves. Same for reading after its split."""
    filename = ARCHETYPE_TOKEN_CSS.get(archetype)
    if filename is None:
        return ""
    return (tdir / "archetypes" / filename).read_text(encoding="utf-8")


# The 3 "ed-*" leaves in archetypes.VOCABULARY["reading"] are styled by the
# shared, theme-agnostic Design/editorial.css (see docs/theme-archetypes.md,
# "reading" section) — no theme's own reading.css is expected to redeclare
# them, any more than a theme redeclares editorial.css's other base rules.
# Derived by prefix, not hardcoded, so it stays correct if the vocabulary
# ever changes: every OTHER "reading" class ("lnt-*") is About's own
# structure with no base stylesheet backing it at all, which is exactly
# what a theme's reading.css exists to dress.
READING_SHARED_LEAF_CLASSES = {c for c in archetypes.VOCABULARY["reading"] if c.startswith("ed-")}


def _check_archetype(
    archetype: str, html: str, css: str, check_zones_flag: bool, pairs: list[list[str]] | None,
) -> list[str]:
    """Runs zones (home only)/chrome/internal-links/vocabulary/contrast for
    one archetype's (html, css), every failure prefixed with the archetype
    name (check_vocabulary already embeds it; the rest are wrapped here so
    their own unit tests — which call them unprefixed — stay unchanged).

    `reading`'s vocabulary check is special-cased: `html` (about.html's real
    markup) is IDENTICAL for every theme — About's structure doesn't move,
    only its dress does (see `_archetype_source`). Crediting that markup
    wholesale toward check_vocabulary would satisfy every required class
    for any theme's reading.css, including an empty one — the exact
    theme-invariance gap A6 flagged for A7 to close. So `reading` feeds
    check_vocabulary a synthetic HTML string carrying only the 3 shared
    `ed-*` leaves (READING_SHARED_LEAF_CLASSES — legitimately theme-agnostic,
    styled by Design/editorial.css, not by any theme's dress) and leaves the
    7 `lnt-*` structural classes to be satisfied ONLY by a CSS selector in
    `css` — the theme's own archetypes/reading.css, which is what actually
    differs from one theme to the next."""
    errors: list[str] = []
    if check_zones_flag:
        errors += [f"{archetype}: {e}" for e in check_zones(html, css)]
    errors += [f"{archetype}: {e}" for e in check_chrome(html, css, **ARCHETYPE_CHROME[archetype])]
    errors += [f"{archetype}: {e}" for e in check_internal_links(html, css)]
    if archetype == "reading":
        anchor_html = "".join(f'<div class="{c}"></div>' for c in sorted(READING_SHARED_LEAF_CLASSES))
        errors += check_vocabulary(anchor_html, css, archetype)
    else:
        errors += check_vocabulary(html, css, archetype)

    # Contrast. Two holes were closed here, and both were the same shape:
    # the gate printing something reassuring and returning no error.
    #
    # 1. `if pairs:` guarded the whole block, so a theme that declares NO
    #    contrastPairs got no contrast checking at all — and check_contrast's
    #    own "no contrastPairs declared" advisory, written for exactly that
    #    case, was unreachable from main(). It is called unconditionally now.
    # 2. When every declared pair filtered out (a theme mirroring this one's
    #    contrastPairs but naming tokens its own CSS never declares), this
    #    printed "unverified" and appended ZERO errors. Four archetypes could
    #    print "unverified" and the theme still rotated, unattended, with its
    #    contrast never graded once. An ungraded check is a failed check.
    applicable = _applicable_contrast_pairs(css, pairs) if pairs else []
    if pairs and not applicable:
        errors.append(
            f"{archetype}: none of the {len(pairs)} declared contrastPairs name "
            f"custom properties this archetype's own CSS declares, so its "
            f"contrast was never graded"
        )
    for fg_name, bg_name, ratio in evaluate_contrast_pairs(css, applicable):
        if ratio is None:
            print(f"contrast [{archetype}]: {fg_name} on {bg_name} = unresolved")
        else:
            verdict = "pass" if ratio >= AA_MIN_RATIO else "FAIL"
            print(f"contrast [{archetype}]: {fg_name} on {bg_name} = {ratio:.2f} "
                  f"({verdict}, AA >= {AA_MIN_RATIO})")
    contrast_failures, contrast_advisories = check_contrast(css, applicable)
    errors += [f"{archetype}: {e}" for e in contrast_failures]
    # The "no contrastPairs declared" advisory is for a theme that declared
    # NOTHING. A theme that declared pairs which all filtered out already has
    # the error above; printing both reads as two separate problems.
    if not pairs:
        for line in contrast_advisories:
            print(f"[{archetype}] {line}")
    return errors


def _run_browser_checks_all(archetype_html: dict[str, str], require: bool = False) -> list[str]:
    """_run_browser_checks per archetype's checked content, but the
    playwright-availability probe happens ONCE — the environment either has
    it or doesn't, independent of which archetype is under test, so a
    missing install degrades to a single line instead of four identical
    ones. A genuine per-page failure (horizontal scroll, console error,
    navigation failure) still fails per archetype, named in the message."""
    sync_playwright = _import_sync_playwright()
    if sync_playwright is None:
        return _degrade("playwright not installed", require)
    errors: list[str] = []
    for archetype, html_text in archetype_html.items():
        errors += [
            f"{archetype}: {e}"
            for e in _run_browser_checks(
                html_text, require=require,
                dress_outcome=archetype in DRESS_OUTCOME_PAGES,
            )
        ]
    return errors


# ─── main ───────────────────────────────────────────────────────────────
def main(argv: list[str]) -> int:
    require_browser = "--require-browser" in argv
    browser = "--browser" in argv or require_browser
    positional = [a for a in argv if a not in ("--browser", "--require-browser")]
    if not positional:
        print("usage: theme-doctor.py <slug> [--browser] [--require-browser]", file=sys.stderr)
        return 2
    slug = positional[0]

    tdir = theme_registry.theme_dir(slug)
    missing = [f for f in theme_registry.REQUIRED_FILES if not (tdir / f).exists()]
    # Every theme must carry all four archetype dresses — no shell.html
    # fallback (removed in A4; see scripts/theme_registry.py and
    # docs/theme-archetypes.md).
    missing += [
        f"archetypes/{a}.html"
        for a in theme_registry.REQUIRED_ARCHETYPES
        if not (tdir / "archetypes" / f"{a}.html").exists()
    ]
    # CARRIED REQUIREMENT (A5's review, routed to A6): render-plugin-pages.py
    # and press.html/privacy.html resolve archetypes/product.css and
    # archetypes/utility.css with NO existence guard — a theme rotating in
    # without one raises an uncaught FileNotFoundError and crashes every
    # page that reads it. Fail here, before the theme can be queued, not at
    # unattended rotation time.
    missing += [
        f"archetypes/{filename}"
        for filename in (
            *REQUIRED_ARCHETYPE_CSS.values(), PRODUCT_TOKENS_CSS, READING_TOKENS_CSS,
        )
        if not (tdir / "archetypes" / filename).exists()
    ]
    if missing:
        print(f"FAIL {slug}")
        for f in missing:
            print(f"  - theme {slug} missing {f}")
        return 1

    with tempfile.TemporaryDirectory(prefix="theme-doctor-") as tmp:
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "render-hub.py"),
                "--theme", slug,
                "--out", tmp,
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"FAIL {slug}")
            print(f"  - render-hub.py --theme {slug} --out failed:")
            for line in (result.stdout + result.stderr).splitlines():
                print(f"    {line}")
            return 1
        home_html = (Path(tmp) / "index.html").read_text(encoding="utf-8")
        # The hand-authored pages, as the theme UNDER TEST dresses them.
        # render-hub.py's preview mode already wrote each one here with its
        # theme-css zone repointed at `slug` (never at whatever
        # content/themes.json currently says), so this grades the incoming
        # dress rather than the outgoing one.
        #
        # Why these get opened at all: every other browser check runs
        # against a theme's OWN archetypes/*.html shell. Nothing in the
        # unattended gate stack ever rendered a real, hand-authored page —
        # which meant the commercial Etsy surface was one of the pages the
        # rotation could never see. This does not catch silent reflow, and
        # it is not meant to; it catches the page failing to load, throwing,
        # or scrolling sideways under the incoming theme.
        live_page_html: dict[str, str] = {}
        missing_previews: list[str] = []
        for name in BROWSER_CHECK_LIVE_PAGES:
            src = Path(tmp) / name
            if src.exists():
                live_page_html[name] = src.read_text(encoding="utf-8")
            else:
                missing_previews.append(name)

    if missing_previews:
        # Not a soft skip: it means render-hub.py's preview mode stopped
        # emitting a page this gate is supposed to open, so the check would
        # silently cover less than it claims.
        print(f"FAIL {slug}")
        for name in missing_previews:
            print(f"  - render-hub.py --theme/--out did not emit {name} to preview")
        return 1

    tokens_css = (tdir / "tokens.css").read_text(encoding="utf-8")
    theme_meta = json.loads((tdir / "theme.json").read_text(encoding="utf-8"))
    pairs = theme_meta.get("contrastPairs")

    errors: list[str] = []
    # The token-variable contract (final review Fix 1 / archetypes.
    # REQUIRED_TOKENS): themes.html reads tokens.css directly; press.html/
    # privacy.html read archetypes/utility.css; thesis.html/workflow.html
    # read archetypes/reading-tokens.css; the four bespoke product pages read
    # archetypes/product-tokens.css. None of those six carries a local
    # fallback for a name in this set, so for them a missing name is not a
    # stale value, it is an unresolved var() with nothing behind it.
    #
    # Three of them (conundrum/rororo/mod-launcher-games) DO declare a
    # handful of `--page-*` aliases shaped `var(--pb-X, var(--contracted))`.
    # Those guard the THEME-BESPOKE --pb-* names, which are deliberately not
    # in REQUIRED_TOKENS; the contracted name each falls through to has no
    # fallback behind IT, which is the whole reason those aliases end in one. All four files have to actually DEFINE the required set or those
    # pages break on the next rotation (see REQUIRED_TOKENS's docstring) —
    # checked here, before the archetype loop, same completeness spirit as
    # REQUIRED_ARCHETYPE_CSS above, just for file CONTENT instead of file
    # existence.
    #
    # reading.css joined this list the moment thesis.html/workflow.html
    # started depending on it and NOT one commit later: without it, an
    # author writing a genuinely new reading dress (rather than copying
    # phosphor-blueprint's) passes every gate, rotates in unattended on the
    # 1st, and puts two live pages up with dozens of unresolved var()s.
    # product-tokens.css joined on the same rule and in the same commit as
    # its own first linking page, and the stakes there are larger, not
    # smaller: a product vocabulary missing a name breaks conundrum.html and
    # rororo-plugins.html outright (they link it, no fallback) AND leaves
    # the 15 pages render-plugin-pages.py CONCATENATES it into rendering
    # with unresolved var()s too.
    #
    # REQUIRED_TOKEN_CSS is every stylesheet a page reads base vocabulary
    # out of. "home" contributes none: no page links or inlines an
    # archetypes/home.css — index.html is rendered from the theme's
    # shell.html against tokens.css, which is the first entry.
    for label in REQUIRED_TOKEN_CSS:
        text = (tdir / label).read_text(encoding="utf-8")
        errors += [f"{label}: {e}" for e in check_required_tokens(text)]

    # The token files that exist ONLY to hold tokens have to stay that way.
    # product-tokens.css and reading-tokens.css are both files split OUT of
    # a dress precisely so bespoke pages could take the vocabulary without
    # the dress, and each is linked by pages that have their own layout.
    #
    # The two dresses they were split from are excluded, for different
    # reasons: archetypes/reading.css is about.html's dress and no page
    # links it for tokens any more, while archetypes/utility.css is
    # press.html's own dress coming home — those two pages carry no
    # page-side dress at all, and the ruling is that they keep it that way.
    # See TOKEN_ONLY_CSS's comment, and check_page_renders_dressed for what
    # covers them instead.
    for label in TOKEN_ONLY_CSS:
        text = (tdir / label).read_text(encoding="utf-8")
        errors += [f"{label}: {e}" for e in check_token_css_declares_only_tokens(text)]

    # ...and a theme must not read a custom property the DOCUMENT reading it
    # never loads a definition for. See the resolution-group header and
    # check_theme_reads_only_what_it_defines for the failure this catches
    # (press.html/privacy.html on a transparent body, every other gate
    # green). Graded once per resolution group — the set of stylesheets one
    # real consumer loads together — never once per theme.
    groups = resolution_groups(tdir)
    errors += check_every_required_stylesheet_is_graded(groups)
    for group, (theme_labels, site_labels) in groups.items():
        group_css: dict[str, str] = {}
        for label in theme_labels:
            path = tdir / label
            if not path.exists():
                errors.append(f"{group} loads {label}, which this theme does not ship")
                continue
            group_css[label] = _group_stylesheet_text(path)
        # A site stylesheet that has gone missing is skipped rather than
        # crashed on, and skipping it can only NARROW the group's pool —
        # every name it defined turns into a reported unresolved read
        # instead of a silent pass.
        site_css = {
            label: (ROOT / label).read_text(encoding="utf-8")
            for label in site_labels
            if (ROOT / label).exists()
        }
        errors += check_theme_reads_only_what_it_defines(group, group_css, site_css)

    archetype_html: dict[str, str] = {}
    for archetype in archetypes.ARCHETYPES:
        html, css, zones_flag = _archetype_source(archetype, tdir, home_html, tokens_css)
        archetype_html[archetype] = html
        errors += _check_archetype(archetype, html, css, zones_flag, pairs)

    if browser:
        errors += _run_browser_checks_all(
            {**archetype_html, **live_page_html}, require=require_browser
        )

    if errors:
        print(f"FAIL {slug}")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"PASS {slug}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
