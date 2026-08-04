#!/usr/bin/env python3
"""theme-doctor.py — the contract gate for 626labs.dev theme rotation.

Checks all four archetypes (scripts/archetypes.py: home, product, reading,
utility) a theme has to dress. First, completeness: tokens.css/theme.json,
all four archetypes/*.html, AND archetypes/product.css + archetypes/
utility.css + archetypes/reading.css (the three CSS artifacts real,
unguarded consumers read at render time — see REQUIRED_ARCHETYPE_CSS). Then,
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
horizontal scroll at 1440/768/390px and zero browser console errors. Without
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
import theme_registry  # noqa: E402 — sibling module in scripts/

ZONES = ("hero", "hero-chips", "products", "lab-pool", "thinking", "founding",
         "stories", "lab-runs", "play", "about", "support", "contact")

# CSS artifacts a theme's real consumers read with no existence guard, beyond
# the tokens.css/theme.json REQUIRED_FILES and archetypes/*.html
# REQUIRED_ARCHETYPES theme_registry already enforces (A5's review flagged
# this as a carried requirement, not a nice-to-have): render-plugin-pages.py
# does `theme_dir(active)/archetypes/product.css` and reads it unguarded —
# a theme rotating in without it raises an uncaught FileNotFoundError and
# crashes all 15 plugin pages. press.html/privacy.html resolve
# archetypes/utility.css the same unguarded way (render-hub.py's
# UTILITY_CSS_HREFS zone). `reading` joins them as of A7: about.html's
# client-side easter-egg toggle points a <link> at
# `/themes/<slug>/archetypes/reading.css` for every theme it offers, and
# this module's own reading-archetype gate reads the same file as the CSS
# half of the vocabulary check (see `_archetype_source`/`_check_archetype`)
# — a theme rotating in without it would break both. `home` needs no entry,
# since its CSS is the inline <style> block in archetypes/home.html itself,
# already covered by REQUIRED_ARCHETYPES.
REQUIRED_ARCHETYPE_CSS = {"product": "product.css", "utility": "utility.css", "reading": "reading.css"}

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


def _run_browser_checks(html_text: str, require: bool = False) -> list[str]:
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
                        errors += _check_viewport(page, f"http://127.0.0.1:{port}/", width)
                    finally:
                        page.close()
            finally:
                browser.close()
    finally:
        httpd.shutdown()
        httpd.server_close()
    return errors


def _check_viewport(page, url: str, width: int) -> list[str]:
    """Load `url` in an already-created page-like object at `width` and check it.

    Split out from `_run_browser_checks` so it's unit-testable with a stub page
    (no real browser/server needed) — see test_theme_doctor.py.

    The page under test failing — `page.goto` raising (navigation error, timeout)
    or a non-2xx response for the page itself — is a GATE FAILURE, not a graceful
    skip: this is the one thing standing between a broken theme and an unattended
    monthly promotion to live (T5's scheduled rotation calls `--browser` as its
    gate). A theme whose rendered page throws or hangs on load must fail the gate,
    not get silently skipped and waved through.
    """
    console_errors: list[str] = []
    page.on(
        "console",
        lambda msg: console_errors.append(msg.text) if msg.type == "error" else None,
    )
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
        return about_html, reading_css, False
    css_filename = REQUIRED_ARCHETYPE_CSS[archetype]
    shell_html = (tdir / "archetypes" / f"{archetype}.html").read_text(encoding="utf-8")
    own_css = (tdir / "archetypes" / css_filename).read_text(encoding="utf-8")
    inline_css = "\n".join(STYLE_BLOCK_RE.findall(shell_html))
    return shell_html, f"{inline_css}\n{own_css}\n{tokens_css}", False


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

    if pairs:
        applicable = _applicable_contrast_pairs(css, pairs)
        if not applicable:
            print(f"contrast [{archetype}]: no declared pair's custom properties "
                  f"resolve in this archetype's own CSS — unverified for {archetype}")
        else:
            for fg_name, bg_name, ratio in evaluate_contrast_pairs(css, applicable):
                if ratio is None:
                    print(f"contrast [{archetype}]: {fg_name} on {bg_name} = unresolved")
                else:
                    verdict = "pass" if ratio >= AA_MIN_RATIO else "FAIL"
                    print(f"contrast [{archetype}]: {fg_name} on {bg_name} = {ratio:.2f} "
                          f"({verdict}, AA >= {AA_MIN_RATIO})")
            contrast_failures, contrast_advisories = check_contrast(css, applicable)
            errors += [f"{archetype}: {e}" for e in contrast_failures]
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
        errors += [f"{archetype}: {e}" for e in _run_browser_checks(html_text, require=require)]
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
        for filename in REQUIRED_ARCHETYPE_CSS.values()
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

    tokens_css = (tdir / "tokens.css").read_text(encoding="utf-8")
    theme_meta = json.loads((tdir / "theme.json").read_text(encoding="utf-8"))
    pairs = theme_meta.get("contrastPairs")

    errors: list[str] = []
    archetype_html: dict[str, str] = {}
    for archetype in archetypes.ARCHETYPES:
        html, css, zones_flag = _archetype_source(archetype, tdir, home_html, tokens_css)
        archetype_html[archetype] = html
        errors += _check_archetype(archetype, html, css, zones_flag, pairs)

    if browser:
        errors += _run_browser_checks_all(archetype_html, require=require_browser)

    if errors:
        print(f"FAIL {slug}")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"PASS {slug}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
