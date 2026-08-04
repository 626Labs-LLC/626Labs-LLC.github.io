#!/usr/bin/env python3
"""freeze-theme.py — turn a retiring theme into a permanent dated archive.

A frozen archive is a dated artifact: it must never re-render and must never
rot. That's why it gets LOCAL copies of every stylesheet it links instead of
linking back to the live paths (which keep moving — themes rotate, and the
base /Design/*.css layer can retokenize at any time), and why it's marked
noindex — it's history, not a live page search engines should rank.

The freeze does NOT localize everything the page references — some live
references are an accepted, documented boundary rather than an oversight:

  - /fonts/* — never linked via <link rel="stylesheet"> today (the shell
    pulls font faces in through an inline @import inside its own <style>
    block, which this script doesn't touch), but excluded on principle too:
    variable font files are megabytes and font infrastructure doesn't
    retokenize the way brand CSS does.
  - /widget-bacon-trail/* — an interactive widget stylesheet, not a design
    surface. Freezing a widget's CSS per archived month buys nothing; the
    live widget is fine to keep sharing.
  - /assets/* images — accepted by the original spec; archives may show a
    since-replaced screenshot or OG image and that's fine.
  - the runtime `fetch("data/plugin-versions.json")` call in the page's own
    <script> — a relative path that 404s harmlessly from the nested archive
    URL (it degrades to "no version chip," not a broken page).

Usage:
  python scripts/freeze-theme.py <YYYY-MM>
  python scripts/freeze-theme.py --screenshot <slug> <out_path>

Freezes the CURRENTLY RENDERED root/index.html into root/themes/archive/
<YYYY-MM>/, along with a local copy of every root-relative
<link rel="stylesheet" href="/..."> it references (except the excluded
prefixes above), rewriting each href to point at its local copy. Refuses to
overwrite an archive that already exists for that month.

The `--screenshot` form is a separate, unrelated capability that lives here
for CLI convenience (the rotation workflow already invokes this file):
`capture_theme_screenshot(slug, out_path)` renders `slug`'s home archetype
fresh (independent of whatever is currently live) and saves a deterministic
1440x900 PNG to `out_path`. See that function's docstring for what
"deterministic" means and why it's needed twice per rotation — once for the
theme freeze() just archived, once for the theme it's being replaced by.
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from collections import Counter
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
STYLESHEET_LINK_RE = re.compile(r'<link\b[^>]*\brel="stylesheet"[^>]*>', re.I)
HREF_ATTR_RE = re.compile(r'href="([^"]*)"')

ROBOTS_META = '<meta name="robots" content="noindex">'

BANNER_TEMPLATE = (
    '<div style="background:#111;color:#eee;font:14px/1.5 system-ui;'
    'padding:10px 16px;text-align:center">\n'
    "  Archived: the site as it looked in {month_name}. "
    '<a href="/" style="color:#17d4fa">Go to the live site</a>.\n'
    "</div>"
)

# Root-relative <link rel="stylesheet"> hrefs that resolve inside the repo but
# are deliberately NOT localized into the archive. See the module docstring
# for why each is an accepted live reference rather than a missed one.
FREEZE_EXCLUDE_PREFIXES = ("/widget-bacon-trail/", "/fonts/")


def _local_stylesheet_hrefs(html: str, root: Path) -> list[str]:
    """Root-relative stylesheet hrefs in `html` that resolve to a real file
    under `root`, in first-seen order, deduplicated, minus the excluded
    prefixes. External stylesheets (http(s):, protocol-relative, or anything
    that isn't root-relative) are left alone — nothing to localize."""
    hrefs: list[str] = []
    seen: set[str] = set()
    for tag in STYLESHEET_LINK_RE.findall(html):
        m = HREF_ATTR_RE.search(tag)
        if not m:
            continue
        href = m.group(1)
        if href in seen:
            continue
        seen.add(href)
        if not href.startswith("/"):
            continue  # external or already-relative — not ours to touch
        if any(href.startswith(p) for p in FREEZE_EXCLUDE_PREFIXES):
            continue
        if (root / href.lstrip("/")).is_file():
            hrefs.append(href)
    return hrefs


def _flatten_filenames(hrefs: list[str]) -> dict[str, str]:
    """href -> archive-local filename. Basenames collide across different
    directories (two files both named tokens.css is the textbook case), so:
    default to the plain basename, and only for hrefs whose basename isn't
    unique across this freeze, fall back to the full path with "/" flattened
    to "__" (deterministic — same href always maps to the same filename, no
    ordering dependence, no counters)."""
    counts = Counter(Path(href).name for href in hrefs)
    mapping = {}
    for href in hrefs:
        name = Path(href).name
        if counts[name] > 1:
            mapping[href] = href.lstrip("/").replace("/", "__")
        else:
            mapping[href] = name
    return mapping


def freeze(month: str, root: Path = ROOT) -> Path:
    """Freeze the current index.html + its local stylesheets to an archive.

    Every root-relative <link rel="stylesheet" href="/..."> the page
    references (minus FREEZE_EXCLUDE_PREFIXES) gets copied alongside the
    frozen index.html and its href rewritten to the local copy — so a later
    retokenize of the live /Design/*.css or /themes/<slug>/tokens.css layer
    can never silently repaint an archived month.

    Returns the archive directory (root/themes/archive/<month>/). Raises
    FileExistsError if that directory already exists — archives are
    write-once, never silently re-frozen.
    """
    archive_dir = root / "themes" / "archive" / month
    if archive_dir.exists():
        raise FileExistsError(f"archive already exists: {archive_dir}")

    html = (root / "index.html").read_text(encoding="utf-8")

    month_name = datetime.strptime(month, "%Y-%m").strftime("%B %Y")
    banner = BANNER_TEMPLATE.format(month_name=month_name)

    html = HEAD_OPEN_RE.sub(lambda m: f"{m.group(0)}\n  {ROBOTS_META}", html, count=1)
    html = BODY_OPEN_RE.sub(lambda m: f"{m.group(0)}{banner}", html, count=1)

    hrefs = _local_stylesheet_hrefs(html, root)
    filenames = _flatten_filenames(hrefs)
    for href, filename in filenames.items():
        html = html.replace(f'href="{href}"', f'href="{filename}"')

    archive_dir.mkdir(parents=True)
    (archive_dir / "index.html").write_text(html, encoding="utf-8")
    for href, filename in filenames.items():
        copyfile(root / href.lstrip("/"), archive_dir / filename)

    return archive_dir


# ─── deterministic theme screenshots ───────────────────────────────────
#
# One PNG per theme (assets/themes/<slug>.png), captured twice a rotation:
# once for the theme freeze() just archived (still true even after it's
# retired — a slug's screenshot never changes once captured, same posture
# as an archived month's HTML), once for the theme that just went live.
# themes.html reads this exact path per slug (see render-hub.py's
# `_theme_thumbnail_href`) — a theme with no file there yet renders its
# card without a thumbnail, not with a broken <img>.
def _import_sync_playwright():
    """Lazy import guard, mirroring theme-doctor.py's own — playwright is
    never a hard dependency of this repo (content-health.yml's pytest job
    never installs it), so only capture_theme_screenshot() pays for it, and
    only at call time."""
    try:
        from playwright.sync_api import sync_playwright
        return sync_playwright
    except ImportError:
        return None


# Determinism has to be a property of the CAPTURE, not of whatever happens
# to be on-screen or gated behind reduced-motion in today's markup. Two real
# sources of frame-to-frame variance live in index.html today — an
# unconditional `Math.random()` shuffle picking 8 of the Lab pool
# (renderLabShelf) and a `performance.now()`/`requestAnimationFrame`-driven
# canvas reveal (the About star map). Both happen to be invisible in a
# 1440x900 VIEWPORT screenshot purely because they sit below the fold today
# — that's a coincidence of current layout, not a guarantee: a taller hero,
# a reflowed Lab section, or a future theme's own home archetype could lift
# either into frame with no code change here to catch it. So this init
# script runs BEFORE any page script (Playwright's add_init_script hook),
# replacing Math.random with a fixed-seed generator and freezing the
# animation clock so performance.now() and every requestAnimationFrame
# callback observe the same instant on every capture. Verified with a
# full-page (not just viewport) byte-compare — see the task report — so the
# proof exercises exactly the code paths this comment describes.
_DETERMINISTIC_CAPTURE_INIT_SCRIPT = """
(() => {
  // Fixed-seed PRNG (mulberry32) replaces Math.random — same sequence
  // every capture, whatever a page's shuffle/jitter/dust code draws from it.
  var a = 0x626c0de;
  function mulberry32() {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    var t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }
  Math.random = mulberry32;

  // Frozen animation clock: performance.now() always returns the same
  // instant, and requestAnimationFrame callbacks are always handed that
  // same instant too (the native rAF's timestamp argument is NOT derived
  // from performance.now(), so both need overriding independently).
  // setTimeout(..., 16) (not 0) keeps any self-perpetuating rAF loop
  // throttled to ~60/s instead of a synchronous busy-loop, in case a
  // future page's animation isn't gated behind prefers-reduced-motion.
  var FROZEN_NOW = 0;
  window.performance.now = function () { return FROZEN_NOW; };
  window.requestAnimationFrame = function (cb) {
    return window.setTimeout(function () { cb(FROZEN_NOW); }, 16);
  };
  window.cancelAnimationFrame = function (id) { window.clearTimeout(id); };
})();
"""


def _render_theme_home(slug: str) -> str:
    """`slug`'s home archetype, rendered fresh via render-hub.py's own
    preview mode — the exact subprocess call theme-doctor.py already makes
    to check an arbitrary theme's home page without touching the live
    site. Independent of whatever content/themes.json currently says is
    active, so capture order relative to the registry rotation never
    matters."""
    with tempfile.TemporaryDirectory(prefix="capture-theme-") as tmp:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "render-hub.py"), "--theme", slug, "--out", tmp],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"render-hub.py --theme {slug} --out failed:\n{result.stdout}{result.stderr}"
            )
        return (Path(tmp) / "index.html").read_text(encoding="utf-8")


def capture_theme_screenshot(slug: str, out_path: Path, full_page: bool = False) -> Path:
    """Deterministic PNG of `slug`'s home archetype at a fixed 1440x900
    viewport, written to `out_path`. `full_page=False` (the default, and
    what the rotation workflow always uses for the gallery thumbnail) crops
    to that viewport; `full_page=True` captures the entire scrollable page
    instead — used by this function's own determinism proof, so the proof
    exercises sections a viewport-only thumbnail would never render at all
    (see the module-level comment above `_DETERMINISTIC_CAPTURE_INIT_SCRIPT`
    for why that distinction matters).

    Deterministic means:

    - Fixed viewport (1440x900, no responsive breakpoint or scrollbar to
      shift the capture).
    - Fonts settled (`document.fonts.ready`) — no FOIT/FOUT frame.
    - Animations off (`reduced_motion="reduce"` — Playwright emulates the
      `prefers-reduced-motion: reduce` media feature; index.html's own CSS
      already collapses every `animation`/`transition` under that query to
      near-zero duration, so no page code changes for this).
    - `Math.random()` reseeded and the animation clock frozen BEFORE any
      page script runs (`_DETERMINISTIC_CAPTURE_INIT_SCRIPT`, injected via
      `page.add_init_script`) — a capture-level guarantee, not a bet that
      every current and future bit of page JS gates its own randomness or
      timing behind `prefers-reduced-motion`.

    Uses the same local-static-server + Playwright harness theme-doctor.py
    already runs for its own browser checks: serve the repo root on an
    ephemeral port, override "/" and "/index.html" with the freshly
    rendered preview so every other root-relative asset (tokens.css, fonts,
    images) still resolves against the real repo tree, exactly as it would
    on the live site.

    Raises RuntimeError if playwright isn't importable, the preview render
    fails, or the browser can't launch — this only ever runs from a
    rotation step that already requires the browser gate to pass, so a
    silent skip here would ship a rotation with a missing or stale
    thumbnail and nobody would know.
    """
    sync_playwright = _import_sync_playwright()
    if sync_playwright is None:
        raise RuntimeError("playwright is not installed — capture_theme_screenshot requires it")

    html_text = _render_theme_home(slug)

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

        def log_message(self, fmt, *args):  # quiet — no per-request noise
            pass

    try:
        httpd = socketserver.TCPServer(("127.0.0.1", 0), _Handler)
    except OSError as e:
        raise RuntimeError(f"could not start local server: {e}") from e
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch()
            except Exception as e:  # pragma: no cover — environment-dependent
                raise RuntimeError(f"could not launch chromium: {e}") from e
            try:
                page = browser.new_page(
                    viewport={"width": 1440, "height": 900},
                    device_scale_factor=1,
                    reduced_motion="reduce",
                )
                try:
                    # Must be registered before navigation — add_init_script
                    # runs before any of the page's own scripts, every time
                    # this page navigates.
                    page.add_init_script(_DETERMINISTIC_CAPTURE_INIT_SCRIPT)
                    page.goto(f"http://127.0.0.1:{port}/", wait_until="load", timeout=15000)
                    page.evaluate("document.fonts.ready")
                    page.wait_for_timeout(300)  # let deferred/async scripts settle
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    page.screenshot(path=str(out_path), full_page=full_page)
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        httpd.shutdown()
        httpd.server_close()

    return out_path


def main(argv: list[str]) -> int:
    if argv[:1] == ["--screenshot"]:
        if len(argv) != 3:
            print("usage: freeze-theme.py --screenshot <slug> <out_path>", file=sys.stderr)
            return 2
        slug, out_path = argv[1], Path(argv[2])
        try:
            out = capture_theme_screenshot(slug, out_path)
        except RuntimeError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        print(f"captured {slug} -> {out}")
        return 0

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
